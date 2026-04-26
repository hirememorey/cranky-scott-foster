#!/usr/bin/env python3
"""Analyze L2M incorrect decisions and challenge overturns vs. referee workload."""

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
    name: str
    coefficient: float | None
    p_value: float | None
    odds_ratio: float | None
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run L2M workload analysis")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/l2m_error_workload_report.md")
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
    """Load one row per L2M game, joined to crew-chief workload and challenges."""
    return pd.read_sql_query(
        """
        WITH challenge_by_game AS (
            SELECT
                game_id,
                COUNT(*) AS challenge_count,
                SUM(overturned) AS overturned_count,
                AVG(overturned * 1.0) AS challenge_overturn_rate
            FROM challenge_events
            GROUP BY game_id
        )
        SELECT
            r.game_id,
            r.season,
            r.game_date,
            r.home_team,
            r.away_team,
            r.home_score,
            r.away_score,
            r.event_count,
            r.incorrect_count,
            (r.event_count - r.incorrect_count) AS correct_count,
            (r.incorrect_count * 1.0 / NULLIF(r.event_count, 0)) AS l2m_error_rate,
            ra.official_id AS crew_chief_id,
            ra.official_name AS crew_chief_name,
            l.days_rest,
            l.back_to_back,
            l.games_last_7,
            l.games_last_14,
            l.travel_miles_since_last,
            l.time_zones_crossed_since_last,
            l.travel_miles_last_3_days,
            l.travel_miles_last_7_days,
            l.time_zones_crossed_last_3_days,
            l.time_zones_crossed_last_7_days,
            COALESCE(c.challenge_count, 0) AS challenge_count,
            COALESCE(c.overturned_count, 0) AS overturned_count,
            c.challenge_overturn_rate
        FROM l2m_reports r
        LEFT JOIN referee_assignments ra
            ON r.game_id = ra.game_id AND ra.role = 'crew_chief'
        LEFT JOIN referee_load_features l
            ON r.game_id = l.game_id AND ra.official_id = l.official_id
        LEFT JOIN challenge_by_game c
            ON r.game_id = c.game_id
        WHERE r.has_report = 1 AND r.event_count > 0
        ORDER BY r.game_date, r.game_id
        """,
        conn,
    )


def build_report(df: pd.DataFrame) -> str:
    if df.empty:
        return "\n".join(
            [
                "# L2M Error Workload Analysis",
                "",
                "No L2M rows are available yet.",
                "",
                "Run:",
                "",
                "```bash",
                "python scripts/collect_l2m_reports.py --season 2024-25",
                "python scripts/compute_referee_load.py",
                "python analysis/l2m_error_workload.py",
                "```",
                "",
            ]
        )

    model_df = prepare_model_data(df)
    travel_model = fit_l2m_model(
        model_df,
        predictor="travel_miles_last_7k",
        controls=[
            "back_to_back",
            "days_rest_capped",
            "games_last_7",
            "time_zones_crossed_last_7_days",
        ],
        label="travel miles last 7 days",
    )
    immediate_travel_model = fit_l2m_model(
        model_df,
        predictor="travel_miles_since_lastk",
        controls=["back_to_back", "days_rest_capped", "games_last_7"],
        label="travel miles since previous game",
    )
    timezone_model = fit_l2m_model(
        model_df,
        predictor="time_zones_crossed_last_7_days",
        controls=["back_to_back", "days_rest_capped", "games_last_7", "travel_miles_last_7k"],
        label="time zones crossed last 7 days",
    )
    b2b_model = fit_l2m_model(
        model_df,
        predictor="back_to_back",
        controls=["days_rest_capped", "games_last_7"],
        label="back-to-back",
    )
    b2b_summary = summarize_l2m(df, "back_to_back")
    rest_summary = summarize_l2m(df.assign(days_rest_bucket=rest_bucket(df)), "days_rest_bucket")
    travel_summary = summarize_l2m(
        df.assign(travel_bucket=travel_bucket(df["travel_miles_last_7_days"])),
        "travel_bucket",
    )
    tz_summary = summarize_l2m(
        df.assign(tz_bucket=tz_bucket(df["time_zones_crossed_last_7_days"])),
        "tz_bucket",
    )
    challenge_summary = summarize_challenges(df, "back_to_back")
    decision = make_decision(travel_model)

    lines = [
        "# L2M Error Workload Analysis",
        "",
        "## Headline",
        "",
        f"- L2M games analyzed: **{len(df):,}**",
        f"- L2M events reviewed: **{int(df['event_count'].sum()):,}**",
        f"- L2M incorrect decisions: **{int(df['incorrect_count'].sum()):,}**",
        f"- Baseline L2M error rate: **{df['incorrect_count'].sum() / df['event_count'].sum():.1%}**",
        f"- Primary travel model: **{travel_model.name}**",
        f"- Travel miles coefficient, per 1,000 miles in previous 7 days: **{format_number(travel_model.coefficient)}**",
        f"- Travel miles odds ratio, per 1,000 miles: **{format_number(travel_model.odds_ratio)}**",
        f"- Travel miles p-value: **{format_number(travel_model.p_value)}**",
        f"- Immediate previous-game miles p-value: **{format_number(immediate_travel_model.p_value)}**",
        f"- Time-zones-crossed p-value: **{format_number(timezone_model.p_value)}**",
        f"- Back-to-back comparison p-value: **{format_number(b2b_model.p_value)}**",
        f"- Decision: **{decision}**",
        "",
        "## L2M Travel Split",
        "",
        dataframe_to_markdown(travel_summary),
        "",
        "## L2M Time-Zone Split",
        "",
        dataframe_to_markdown(tz_summary),
        "",
        "## L2M Back-To-Back Split",
        "",
        dataframe_to_markdown(b2b_summary),
        "",
        "## L2M Days Rest Split",
        "",
        dataframe_to_markdown(rest_summary),
        "",
        "## Challenge Outcomes On L2M Games",
        "",
        dataframe_to_markdown(challenge_summary),
        "",
        "## Model Notes",
        "",
        travel_model.note,
        "",
        f"Immediate previous-game miles model: {immediate_travel_model.note}",
        "",
        f"Time-zone model: {timezone_model.note}",
        "",
        f"Back-to-back comparison model: {b2b_model.note}",
        "",
    ]
    return "\n".join(lines)


def prepare_model_data(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.dropna(
        subset=[
            "incorrect_count",
            "correct_count",
            "crew_chief_id",
            "days_rest",
            "back_to_back",
            "games_last_7",
            "travel_miles_last_7_days",
            "time_zones_crossed_last_7_days",
        ]
    ).copy()
    clean = clean[clean["event_count"] > 0]
    clean["back_to_back"] = clean["back_to_back"].astype(int)
    clean["days_rest_capped"] = clean["days_rest"].clip(lower=0, upper=7)
    clean["l2m_error_rate"] = clean["incorrect_count"] / clean["event_count"]
    clean["travel_miles_since_lastk"] = clean["travel_miles_since_last"] / 1000
    clean["travel_miles_last_3k"] = clean["travel_miles_last_3_days"] / 1000
    clean["travel_miles_last_7k"] = clean["travel_miles_last_7_days"] / 1000
    return clean


def fit_l2m_model(
    df: pd.DataFrame,
    predictor: str,
    controls: list[str],
    label: str,
) -> ModelSummary:
    if len(df) < 30 or df[predictor].nunique() < 2 or df["incorrect_count"].sum() == 0:
        return ModelSummary(
            name="not fit",
            coefficient=None,
            p_value=None,
            odds_ratio=None,
            note=f"Model skipped because {label} has too little variation after joins.",
        )

    import math

    rhs_terms = [predictor, *controls]
    rhs = " + ".join(dict.fromkeys(rhs_terms))
    try:
        result = smf.glm(
            f"l2m_error_rate ~ {rhs} + C(crew_chief_id)",
            data=df,
            family=sm.families.Binomial(),
            freq_weights=df["event_count"],
        ).fit()
        coef = float(result.params[predictor])
        p_value = float(result.pvalues[predictor])
        return ModelSummary(
            name=f"binomial GLM with crew-chief fixed effects ({label})",
            coefficient=coef,
            p_value=p_value,
            odds_ratio=math.exp(coef),
            note=(
                "The model is weighted by L2M event count per game and includes "
                "crew-chief fixed effects to compare each crew chief against their "
                f"own baseline where data allows. Predictor tested: {label}."
            ),
        )
    except Exception as fixed_error:
        result = smf.glm(
            f"l2m_error_rate ~ {rhs}",
            data=df,
            family=sm.families.Binomial(),
            freq_weights=df["event_count"],
        ).fit()
        coef = float(result.params[predictor])
        p_value = float(result.pvalues[predictor])
        return ModelSummary(
            name=f"binomial GLM without crew-chief fixed effects ({label})",
            coefficient=coef,
            p_value=p_value,
            odds_ratio=math.exp(coef),
            note=f"Crew-chief fixed-effects model failed, fallback pooled model used: {fixed_error}",
        )


def make_decision(model: ModelSummary) -> str:
    if model.coefficient is None or model.p_value is None:
        return "inconclusive: collect/validate more L2M rows"
    if model.coefficient > 0 and model.p_value < 0.05:
        return "travel signal found: scale with multi-season data and time-zone robustness checks"
    if model.coefficient > 0 and model.p_value < 0.10:
        return "directional travel signal: expand to more seasons before trusting it"
    return "travel miles do not explain L2M errors in this sample"


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


def summarize_challenges(df: pd.DataFrame, column: str) -> pd.DataFrame:
    grouped = (
        df.groupby(column, dropna=False)
        .agg(
            games=("game_id", "count"),
            challenges=("challenge_count", "sum"),
            overturned=("overturned_count", "sum"),
        )
        .reset_index()
    )
    grouped["challenge_overturn_rate"] = grouped["overturned"] / grouped["challenges"]
    return grouped.sort_values(column)


def rest_bucket(df: pd.DataFrame) -> pd.Series:
    def bucket(value) -> str:
        if pd.isna(value):
            return "unknown"
        value = int(value)
        return "3+" if value >= 3 else str(value)

    return df["days_rest"].map(bucket)


def travel_bucket(series: pd.Series) -> pd.Series:
    def bucket(value) -> str:
        if pd.isna(value):
            return "unknown"
        if value == 0:
            return "0"
        if value < 1000:
            return "<1000"
        if value < 2000:
            return "1000-1999"
        if value < 3000:
            return "2000-2999"
        return "3000+"

    return series.map(bucket)


def tz_bucket(series: pd.Series) -> pd.Series:
    def bucket(value) -> str:
        if pd.isna(value):
            return "unknown"
        value = int(value)
        if value >= 3:
            return "3+"
        return str(value)

    return series.map(bucket)


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

