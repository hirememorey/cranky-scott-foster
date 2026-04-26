#!/usr/bin/env python3
"""Analyze H1b: challenge overturn probability vs. referee workload."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables


@dataclass
class ModelResult:
    model_name: str
    coefficient: float | None
    p_value: float | None
    odds_ratio: float | None
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the H1b challenge overturn analysis")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/h1b_challenge_overturn_report.md")
    parser.add_argument("--min-ref-challenges", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)

    df = load_model_data(conn)
    report = build_report(df, min_ref_challenges=args.min_ref_challenges)

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path}")


def load_model_data(conn) -> pd.DataFrame:
    """Join challenge events to crew-chief workload features."""
    return pd.read_sql_query(
        """
        SELECT
            c.game_id,
            c.event_num,
            c.season,
            c.period,
            c.game_clock,
            c.description,
            c.overturned,
            c.crew_chief_id,
            c.challenging_team,
            l.days_rest,
            l.back_to_back,
            l.games_last_7,
            l.games_last_14,
            ra.official_name AS crew_chief_name
        FROM challenge_events c
        LEFT JOIN referee_load_features l
            ON c.game_id = l.game_id
           AND c.crew_chief_id = l.official_id
        LEFT JOIN referee_assignments ra
            ON c.game_id = ra.game_id
           AND c.crew_chief_id = ra.official_id
        WHERE c.crew_chief_id IS NOT NULL
        ORDER BY c.season, c.game_id, c.event_num
        """,
        conn,
    )


def build_report(df: pd.DataFrame, min_ref_challenges: int = 20) -> str:
    if df.empty:
        return "\n".join(
            [
                "# H1b Challenge Overturn Analysis",
                "",
                "No joined challenge/workload rows are available yet.",
                "",
                "Decision: **inconclusive: collect challenge/workload rows before the Phase 2 decision**.",
                "",
                "Run:",
                "",
                "```bash",
                "python scripts/collect_officials.py",
                "python scripts/extract_challenge_events.py",
                "python scripts/compute_referee_load.py",
                "python analysis/h1b_challenge_overturn.py",
                "```",
                "",
                "Decision rule: scale to Phase 2 only if the back-to-back absolute effect is at least 3 percentage points and p < 0.05.",
                "",
            ]
        )

    clean = prepare_model_data(df, min_ref_challenges=min_ref_challenges)
    baseline = float(df["overturned"].mean())
    b2b_summary = summarize_rate(df, "back_to_back")
    rest_summary = summarize_rate(df.assign(days_rest_bucket=rest_bucket(df)), "days_rest_bucket")
    model_result = fit_primary_model(clean)
    decision = make_decision(b2b_summary, model_result)

    lines = [
        "# H1b Challenge Overturn Analysis",
        "",
        "## Headline",
        "",
        f"- Challenge events analyzed: **{len(df):,}**",
        f"- Baseline overturn rate: **{baseline:.1%}**",
        f"- Primary model: **{model_result.model_name}**",
        f"- Back-to-back coefficient: **{format_number(model_result.coefficient)}**",
        f"- Back-to-back odds ratio: **{format_number(model_result.odds_ratio)}**",
        f"- Back-to-back p-value: **{format_number(model_result.p_value)}**",
        f"- Decision: **{decision}**",
        "",
        "## Back-To-Back Split",
        "",
        dataframe_to_markdown(b2b_summary),
        "",
        "## Days Rest Split",
        "",
        dataframe_to_markdown(rest_summary),
        "",
        "## Model Notes",
        "",
        model_result.note,
        "",
        "## Decision Rule",
        "",
        (
            "Scale to Phase 2 only if the back-to-back absolute effect is at least "
            "3 percentage points and p < 0.05. Otherwise treat H1b as a cheap null "
            "or inconclusive screen and pivot to pace/Q4 or L2M only if there is a "
            "separate reason to continue."
        ),
        "",
    ]
    return "\n".join(lines)


def prepare_model_data(df: pd.DataFrame, min_ref_challenges: int) -> pd.DataFrame:
    clean = df.dropna(
        subset=["overturned", "crew_chief_id", "back_to_back", "days_rest", "games_last_7", "period"]
    ).copy()
    clean["overturned"] = clean["overturned"].astype(int)
    clean["back_to_back"] = clean["back_to_back"].astype(int)
    clean["period"] = clean["period"].astype(int)
    clean["days_rest_capped"] = clean["days_rest"].clip(lower=0, upper=7)
    counts = clean["crew_chief_id"].value_counts()
    keep_refs = counts[counts >= min_ref_challenges].index
    filtered = clean[clean["crew_chief_id"].isin(keep_refs)].copy()
    return filtered if len(filtered) >= 50 else clean


def fit_primary_model(df: pd.DataFrame) -> ModelResult:
    if len(df) < 50 or df["overturned"].nunique() < 2 or df["back_to_back"].nunique() < 2:
        return ModelResult(
            model_name="not fit",
            coefficient=None,
            p_value=None,
            odds_ratio=None,
            note=(
                "Model skipped because the joined dataset does not yet have enough "
                "rows or outcome/back-to-back variation."
            ),
        )

    import math

    try:
        mixed_formula = "overturned ~ back_to_back + days_rest_capped + games_last_7 + C(period)"
        random_effects = {"crew_chief": "0 + C(crew_chief_id)"}
        mixed_model = sm.BinomialBayesMixedGLM.from_formula(
            mixed_formula, random_effects, df
        )
        mixed_result = mixed_model.fit_vb()
        coef_index = mixed_model.fep_names.index("back_to_back")
        coef = float(mixed_result.fe_mean[coef_index])

        fixed_formula = (
            "overturned ~ back_to_back + days_rest_capped + games_last_7 "
            "+ C(period) + C(crew_chief_id)"
        )
        fixed_result = smf.logit(fixed_formula, data=df).fit(disp=False, maxiter=200)
        p_value = float(fixed_result.pvalues["back_to_back"])
        return ModelResult(
            model_name="Bayesian mixed logit with crew-chief random intercepts",
            coefficient=coef,
            p_value=p_value,
            odds_ratio=math.exp(coef),
            note=(
                "Statsmodels BinomialBayesMixedGLM estimates the planned "
                "(1|crew_chief) random intercept. The p-value is reported from a "
                "crew-chief fixed-effects logit because the Bayesian mixed model "
                "does not expose frequentist p-values."
            ),
        )
    except Exception as mixed_error:
        try:
            formula = (
                "overturned ~ back_to_back + days_rest_capped + games_last_7 "
                "+ C(period) + C(crew_chief_id)"
            )
            result = smf.logit(formula, data=df).fit(disp=False, maxiter=200)
            coef = float(result.params["back_to_back"])
            p_value = float(result.pvalues["back_to_back"])
            return ModelResult(
                model_name="logit with crew-chief fixed effects",
                coefficient=coef,
                p_value=p_value,
                odds_ratio=math.exp(coef),
                note=(
                    "Mixed-effects model failed, so the fallback crew-chief "
                    f"fixed-effects logit was used. Mixed-effects error: {mixed_error}"
                ),
            )
        except Exception as fixed_error:
            try:
                formula = "overturned ~ back_to_back + days_rest_capped + games_last_7 + C(period)"
                result = smf.logit(formula, data=df).fit(disp=False, maxiter=200)
                coef = float(result.params["back_to_back"])
                p_value = float(result.pvalues["back_to_back"])
                return ModelResult(
                    model_name="pooled logit without crew-chief effects",
                    coefficient=coef,
                    p_value=p_value,
                    odds_ratio=math.exp(coef),
                    note=(
                        "Mixed and fixed-effects models failed, so the fallback "
                        f"pooled logit was used. Last fixed-effects error: {fixed_error}"
                    ),
                )
            except Exception as pooled_error:
                return ModelResult(
                    model_name="not fit",
                    coefficient=None,
                    p_value=None,
                    odds_ratio=None,
                    note=f"Model failed. Last error: {pooled_error}",
                )


def make_decision(b2b_summary: pd.DataFrame, model_result: ModelResult) -> str:
    effect = back_to_back_effect(b2b_summary)
    if effect is None or model_result.p_value is None:
        return "inconclusive: collect more rows before the Phase 2 decision"
    if abs(effect) >= 0.03 and model_result.p_value < 0.05:
        return "green light Phase 2: add travel miles, time zones, and L2M"
    return "do not scale H1b yet: treat as null/inconclusive and pivot if needed"


def back_to_back_effect(summary: pd.DataFrame) -> float | None:
    if "back_to_back" not in summary.columns:
        return None
    indexed = summary.set_index("back_to_back")
    if 0 not in indexed.index or 1 not in indexed.index:
        return None
    return float(indexed.loc[1, "overturn_rate"] - indexed.loc[0, "overturn_rate"])


def summarize_rate(df: pd.DataFrame, column: str) -> pd.DataFrame:
    summary = (
        df.groupby(column, dropna=False)
        .agg(challenges=("overturned", "size"), overturn_rate=("overturned", "mean"))
        .reset_index()
        .sort_values(column)
    )
    summary["overturn_rate"] = summary["overturn_rate"].astype(float)
    return summary


def rest_bucket(df: pd.DataFrame) -> pd.Series:
    def bucket(value: Any) -> str:
        if pd.isna(value):
            return "unknown"
        value = int(value)
        if value >= 3:
            return "3+"
        return str(value)

    return df["days_rest"].map(bucket)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate"):
            formatted[column] = formatted[column].map(lambda value: f"{value:.1%}")
    headers = list(formatted.columns)
    rows = formatted.astype(str).values.tolist()
    widths = [
        max(len(str(header)), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    lines = [
        "| " + " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers)) + " |",
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(row[index].ljust(widths[index]) for index in range(len(headers))) + " |"
        )
    return "\n".join(lines)


def format_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


if __name__ == "__main__":
    main()

