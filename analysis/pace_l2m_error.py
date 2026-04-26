#!/usr/bin/env python3
"""Analyze L2M incorrect decisions against game pace and late-game load."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables


@dataclass
class ModelSummary:
    label: str
    predictor: str
    coefficient: float | None
    p_value: float | None
    odds_ratio: float | None
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pace/load L2M analysis")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/pace_l2m_error_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = load_analysis_data(conn)
    report = build_report(df)
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path}")


def load_analysis_data(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            r.game_id,
            r.season,
            r.game_date,
            r.event_count,
            r.incorrect_count,
            (r.event_count - r.incorrect_count) AS correct_count,
            (r.incorrect_count * 1.0 / NULLIF(r.event_count, 0)) AS l2m_error_rate,
            ra.official_id AS crew_chief_id,
            l.days_rest,
            l.back_to_back,
            l.games_last_7,
            l.travel_miles_last_7_days,
            p.game_minutes,
            p.estimated_possessions,
            p.estimated_pace,
            p.actions_per_minute,
            p.q4_actions_per_minute,
            p.q4_pre_l2m_actions_per_minute,
            p.l2m_actions_per_minute,
            p.q4_shots,
            p.q4_fouls,
            p.q4_turnovers
        FROM l2m_reports r
        JOIN game_pace_features p
            ON r.game_id = p.game_id
        LEFT JOIN referee_assignments ra
            ON r.game_id = ra.game_id AND ra.role = 'crew_chief'
        LEFT JOIN referee_load_features l
            ON r.game_id = l.game_id AND ra.official_id = l.official_id
        WHERE r.has_report = 1 AND r.event_count > 0
        ORDER BY r.game_date, r.game_id
        """,
        conn,
    )


def build_report(df: pd.DataFrame) -> str:
    if df.empty:
        return "\n".join(
            [
                "# Pace / In-Game Load L2M Analysis",
                "",
                "No joined L2M pace rows are available yet.",
                "",
                "Run:",
                "",
                "```bash",
                "python scripts/compute_pace_features.py",
                "python analysis/pace_l2m_error.py",
                "```",
                "",
            ]
        )

    model_df = prepare_model_data(df)
    game_pace_model = fit_model(
        model_df,
        predictor="estimated_pace_5",
        label="estimated full-game pace per 5 possessions",
    )
    q4_pre_l2m_model = fit_model(
        model_df,
        predictor="q4_pre_l2m_actions_per_minute",
        label="Q4 pre-L2M actions per minute",
    )
    l2m_density_model = fit_model(
        model_df,
        predictor="l2m_actions_per_minute",
        label="L2M actions per minute",
    )

    pace_summary = summarize_l2m(
        df.assign(pace_bucket=quantile_bucket(df["estimated_pace"], "pace")),
        "pace_bucket",
    )
    q4_summary = summarize_l2m(
        df.assign(q4_load_bucket=quantile_bucket(df["q4_pre_l2m_actions_per_minute"], "q4_load")),
        "q4_load_bucket",
    )
    l2m_summary = summarize_l2m(
        df.assign(l2m_load_bucket=quantile_bucket(df["l2m_actions_per_minute"], "l2m_load")),
        "l2m_load_bucket",
    )
    decision = make_decision(game_pace_model, q4_pre_l2m_model, l2m_density_model)

    lines = [
        "# Pace / In-Game Load L2M Analysis",
        "",
        "## Headline",
        "",
        f"- L2M games analyzed: **{len(df):,}**",
        f"- L2M events reviewed: **{int(df['event_count'].sum()):,}**",
        f"- L2M incorrect decisions: **{int(df['incorrect_count'].sum()):,}**",
        f"- Baseline L2M error rate: **{df['incorrect_count'].sum() / df['event_count'].sum():.1%}**",
        f"- Full-game pace p-value: **{format_number(game_pace_model.p_value)}**",
        f"- Q4 pre-L2M action density p-value: **{format_number(q4_pre_l2m_model.p_value)}**",
        f"- L2M action density p-value: **{format_number(l2m_density_model.p_value)}**",
        f"- Decision: **{decision}**",
        "",
        "## Full-Game Pace Split",
        "",
        dataframe_to_markdown(pace_summary),
        "",
        "## Q4 Pre-L2M Load Split",
        "",
        dataframe_to_markdown(q4_summary),
        "",
        "## L2M Action Density Split",
        "",
        dataframe_to_markdown(l2m_summary),
        "",
        "## Model Notes",
        "",
        model_line(game_pace_model),
        "",
        model_line(q4_pre_l2m_model),
        "",
        model_line(l2m_density_model),
        "",
    ]
    return "\n".join(lines)


def prepare_model_data(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.dropna(
        subset=[
            "incorrect_count",
            "event_count",
            "crew_chief_id",
            "estimated_pace",
            "q4_pre_l2m_actions_per_minute",
            "l2m_actions_per_minute",
            "days_rest",
            "back_to_back",
            "games_last_7",
            "travel_miles_last_7_days",
        ]
    ).copy()
    clean["l2m_error_rate"] = clean["incorrect_count"] / clean["event_count"]
    clean["estimated_pace_5"] = clean["estimated_pace"] / 5
    clean["days_rest_capped"] = clean["days_rest"].clip(lower=0, upper=7)
    clean["travel_miles_last_7k"] = clean["travel_miles_last_7_days"] / 1000
    clean["back_to_back"] = clean["back_to_back"].astype(int)
    return clean


def fit_model(df: pd.DataFrame, predictor: str, label: str) -> ModelSummary:
    if len(df) < 30 or df[predictor].nunique() < 2 or df["incorrect_count"].sum() == 0:
        return ModelSummary(label, predictor, None, None, None, "Not enough variation.")

    import math

    controls = "days_rest_capped + back_to_back + games_last_7 + travel_miles_last_7k"
    try:
        result = smf.glm(
            f"l2m_error_rate ~ {predictor} + {controls} + C(crew_chief_id)",
            data=df,
            family=sm.families.Binomial(),
            freq_weights=df["event_count"],
        ).fit()
        coef = float(result.params[predictor])
        p_value = float(result.pvalues[predictor])
        return ModelSummary(
            label=label,
            predictor=predictor,
            coefficient=coef,
            p_value=p_value,
            odds_ratio=math.exp(coef),
            note="Crew-chief fixed effects; weighted by L2M event count.",
        )
    except Exception as fixed_error:
        result = smf.glm(
            f"l2m_error_rate ~ {predictor} + {controls}",
            data=df,
            family=sm.families.Binomial(),
            freq_weights=df["event_count"],
        ).fit()
        coef = float(result.params[predictor])
        p_value = float(result.pvalues[predictor])
        return ModelSummary(
            label=label,
            predictor=predictor,
            coefficient=coef,
            p_value=p_value,
            odds_ratio=math.exp(coef),
            note=f"Pooled fallback; fixed-effects model failed: {fixed_error}",
        )


def summarize_l2m(df: pd.DataFrame, column: str) -> pd.DataFrame:
    grouped = (
        df.groupby(column, dropna=False)
        .agg(
            games=("game_id", "count"),
            reviewed_events=("event_count", "sum"),
            incorrect_events=("incorrect_count", "sum"),
        )
        .reset_index()
    )
    grouped["l2m_error_rate"] = grouped["incorrect_events"] / grouped["reviewed_events"]
    return grouped.sort_values(column)


def quantile_bucket(series: pd.Series, prefix: str) -> pd.Series:
    ranks = pd.qcut(series.rank(method="first"), 3, labels=["low", "mid", "high"])
    return prefix + "_" + ranks.astype(str)


def make_decision(*models: ModelSummary) -> str:
    positive_signals = [
        model
        for model in models
        if model.coefficient is not None and model.coefficient > 0 and (model.p_value or 1) < 0.05
    ]
    if positive_signals:
        labels = ", ".join(model.label for model in positive_signals)
        return f"pace/load signal found for: {labels}"
    directional = [
        model
        for model in models
        if model.coefficient is not None and model.coefficient > 0 and (model.p_value or 1) < 0.10
    ]
    if directional:
        labels = ", ".join(model.label for model in directional)
        return f"directional pace/load signal; expand/validate: {labels}"
    return "pace/load proxies do not explain L2M errors in this sample"


def model_line(model: ModelSummary) -> str:
    return (
        f"{model.label}: coef={format_number(model.coefficient)}, "
        f"OR={format_number(model.odds_ratio)}, p={format_number(model.p_value)}. "
        f"{model.note}"
    )


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate"):
            formatted[column] = formatted[column].map(
                lambda value: "n/a" if pd.isna(value) else f"{value:.1%}"
            )
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

