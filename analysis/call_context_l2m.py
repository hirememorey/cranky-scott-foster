#!/usr/bin/env python3
"""Analyze which L2M call contexts carry the most error risk."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd
import statsmodels.formula.api as smf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.arena_locations import ARENA_LOCATIONS_BY_TEAM_ID
from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.taxonomy import call_detail, call_family, classify


@dataclass
class FactorSignal:
    context: str
    factor: str
    n: int
    incorrect: int
    coefficient: float
    p_value: float
    odds_ratio: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run L2M call context analysis")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/call_context_l2m_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = load_event_data(conn)
    report = build_report(df)
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path}")


def load_event_data(conn) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT
            e.game_id,
            e.event_index,
            e.period,
            e.game_clock,
            e.call_type,
            e.review_decision,
            e.incorrect,
            e.committing_player,
            e.disadvantaged_player,
            e.comment,
            r.home_team,
            r.away_team,
            r.home_team_id,
            r.away_team_id,
            ra.official_id AS crew_chief_id,
            l.days_rest,
            l.back_to_back,
            l.games_last_7,
            l.travel_miles_last_7_days,
            p.estimated_pace,
            p.q4_pre_l2m_actions_per_minute,
            p.l2m_actions_per_minute
        FROM l2m_events e
        JOIN l2m_reports r
            ON e.game_id = r.game_id
        LEFT JOIN referee_assignments ra
            ON e.game_id = ra.game_id AND ra.role = 'crew_chief'
        LEFT JOIN referee_load_features l
            ON e.game_id = l.game_id AND ra.official_id = l.official_id
        LEFT JOIN game_pace_features p
            ON e.game_id = p.game_id
        WHERE e.review_decision IN ('CC', 'CNC', 'IC', 'INC')
        """,
        conn,
    )
    return add_context_columns(df)


def add_context_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["call_family"] = out["call_type"].map(call_family)
    out["call_detail"] = out["call_type"].map(call_detail)
    out["taxonomy_category"] = out.apply(
        lambda row: classify(row["call_type"], row["review_decision"]),
        axis=1,
    )
    out["decision_kind"] = out["review_decision"].map(
        {"CC": "call", "IC": "call", "CNC": "non_call", "INC": "non_call"}
    )
    out["clock_seconds"] = out["game_clock"].map(clock_seconds)
    out["clock_bucket"] = out["clock_seconds"].map(clock_bucket)
    out["period_bucket"] = out["period"].map(lambda value: "OT" if str(value).upper() != "Q4" else "Q4")
    out["harmed_team"] = out.apply(harmed_team, axis=1)
    out["harmed_side"] = out.apply(harmed_side, axis=1)
    out["days_rest_capped"] = out["days_rest"].clip(0, 7)
    out["travel_miles_last_7k"] = out["travel_miles_last_7_days"] / 1000
    out["pace_5"] = out["estimated_pace"] / 5
    return out


def build_report(df: pd.DataFrame) -> str:
    call_family_summary = summarize_context(df, "call_family", min_n=50)
    taxonomy_summary = summarize_context(df, "taxonomy_category", min_n=20)
    call_type_summary = summarize_context(df, "call_type", min_n=20)
    decision_summary = summarize_context(df, "decision_kind", min_n=20)
    period_summary = summarize_context(df, "period_bucket", min_n=20)
    clock_summary = summarize_context(df, "clock_bucket", min_n=20)
    harmed_side_summary = summarize_context(df[df["incorrect"] == 1], "harmed_side", min_n=1)
    factor_signals = find_factor_signals(df)

    lines = [
        "# L2M Call Context Analysis",
        "",
        "## Headline",
        "",
        f"- L2M events analyzed: **{len(df):,}**",
        f"- Incorrect decisions: **{int(df['incorrect'].sum()):,}**",
        f"- Baseline event error rate: **{df['incorrect'].mean():.1%}**",
        f"- Highest-risk major family: **{top_label(call_family_summary)}**",
        f"- Highest-risk detailed call type: **{top_label(call_type_summary)}**",
        f"- Fatigue/load context signals found: **{len(factor_signals)}** with p < 0.10",
        "",
        "## Major Call Families",
        "",
        dataframe_to_markdown(call_family_summary),
        "",
        "## Structural Taxonomy",
        "",
        dataframe_to_markdown(taxonomy_summary),
        "",
        "## Highest-Risk Detailed Call Types",
        "",
        dataframe_to_markdown(call_type_summary.head(20)),
        "",
        "## Call vs Non-Call",
        "",
        dataframe_to_markdown(decision_summary),
        "",
        "## Period / Clock Context",
        "",
        dataframe_to_markdown(period_summary),
        "",
        dataframe_to_markdown(clock_summary),
        "",
        "## Who Was Harmed On Incorrect Calls",
        "",
        dataframe_to_markdown(harmed_side_summary),
        "",
        "## Workload Signals Within Contexts",
        "",
        factor_signal_table(factor_signals),
        "",
        "## Interpretation",
        "",
        interpretation(call_family_summary, call_type_summary, factor_signals),
        "",
    ]
    return "\n".join(lines)


def summarize_context(df: pd.DataFrame, column: str, min_n: int) -> pd.DataFrame:
    grouped = (
        df.groupby(column, dropna=False)
        .agg(events=("incorrect", "size"), incorrect=("incorrect", "sum"), error_rate=("incorrect", "mean"))
        .reset_index()
    )
    grouped = grouped[grouped["events"] >= min_n].copy()
    return grouped.sort_values(["error_rate", "events"], ascending=[False, False])


def find_factor_signals(df: pd.DataFrame) -> list[FactorSignal]:
    factors = [
        ("days_rest_capped", "days rest"),
        ("back_to_back", "back-to-back"),
        ("games_last_7", "games last 7d"),
        ("travel_miles_last_7k", "travel miles last 7d, per 1k"),
        ("pace_5", "full-game pace, per 5 poss"),
        ("q4_pre_l2m_actions_per_minute", "Q4 pre-L2M actions/min"),
        ("l2m_actions_per_minute", "L2M actions/min"),
    ]
    contexts = []
    for column in ["call_family", "decision_kind", "clock_bucket"]:
        for value in sorted(df[column].dropna().unique()):
            subset = df[df[column] == value]
            contexts.append((f"{column}={value}", subset))

    signals = []
    for context_label, subset in contexts:
        subset = subset.dropna(
            subset=[
                "incorrect",
                "crew_chief_id",
                "days_rest_capped",
                "back_to_back",
                "games_last_7",
                "travel_miles_last_7k",
                "pace_5",
                "q4_pre_l2m_actions_per_minute",
                "l2m_actions_per_minute",
            ]
        ).copy()
        if len(subset) < 150 or subset["incorrect"].sum() < 10 or subset["incorrect"].nunique() < 2:
            continue
        for factor, label in factors:
            if subset[factor].nunique() < 2:
                continue
            signal = fit_factor(subset, context_label, factor, label)
            if signal and signal.p_value < 0.10:
                signals.append(signal)

    return sorted(signals, key=lambda item: item.p_value)


def fit_factor(
    df: pd.DataFrame,
    context_label: str,
    factor: str,
    factor_label: str,
) -> FactorSignal | None:
    import math

    controls = ["days_rest_capped", "back_to_back", "games_last_7"]
    controls = [control for control in controls if control != factor]
    rhs = " + ".join([factor, *controls])
    try:
        result = smf.logit(
            f"incorrect ~ {rhs} + C(crew_chief_id)",
            data=df,
        ).fit(disp=False, maxiter=200)
    except Exception:
        try:
            result = smf.logit(f"incorrect ~ {rhs}", data=df).fit(disp=False, maxiter=200)
        except Exception:
            return None
    return FactorSignal(
        context=context_label,
        factor=factor_label,
        n=len(df),
        incorrect=int(df["incorrect"].sum()),
        coefficient=float(result.params[factor]),
        p_value=float(result.pvalues[factor]),
        odds_ratio=math.exp(float(result.params[factor])),
    )


def clock_seconds(value: str | None) -> float | None:
    if not value:
        return None
    match = re.match(r"(\d+):(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1)) * 60 + float(match.group(2))


def clock_bucket(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value <= 30:
        return "00-30s"
    if value <= 60:
        return "31-60s"
    if value <= 90:
        return "61-90s"
    return "91-120s"


def harmed_team(row: pd.Series) -> str | None:
    if row["incorrect"] != 1:
        return None
    comment_abbreviations = re.findall(r"\(([A-Z]{2,3})\)", str(row.get("comment") or ""))
    if row["review_decision"] == "INC":
        # Missed infraction: first team is usually the offender, second is harmed.
        if len(comment_abbreviations) >= 2:
            return comment_abbreviations[1]
        return extract_team(row["disadvantaged_player"])
    if row["review_decision"] == "IC":
        awarded_team = awarded_to_team(row)
        if awarded_team:
            return awarded_team
        # Incorrect call: absent clearer language, the player whistled is harmed.
        if comment_abbreviations:
            return comment_abbreviations[0]
        return extract_team(row["committing_player"])
    return None


def harmed_side(row: pd.Series) -> str:
    team = row.get("harmed_team")
    if not team:
        return "unknown"
    home_location = ARENA_LOCATIONS_BY_TEAM_ID.get(row.get("home_team_id"))
    away_location = ARENA_LOCATIONS_BY_TEAM_ID.get(row.get("away_team_id"))
    if home_location and team == home_location.team_abbreviation:
        return "home"
    if away_location and team == away_location.team_abbreviation:
        return "away"
    return "unknown"


def extract_team(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\(([A-Z]{2,3})\)", value)
    return match.group(1) if match else None


def awarded_to_team(row: pd.Series) -> str | None:
    """Infer harmed team from comments like 'should have been awarded to San Antonio'."""
    comment = str(row.get("comment") or "").lower()
    for side in ["home", "away"]:
        team_id = row.get(f"{side}_team_id")
        location = ARENA_LOCATIONS_BY_TEAM_ID.get(team_id)
        if not location:
            continue
        team_name = str(row.get(f"{side}_team") or "").lower()
        city = location.city.lower()
        if f"awarded to {team_name}" in comment or f"awarded to {city}" in comment:
            return location.team_abbreviation
    return None


def top_label(summary: pd.DataFrame) -> str:
    if summary.empty:
        return "n/a"
    row = summary.iloc[0]
    first_col = summary.columns[0]
    return f"{row[first_col]} ({row['error_rate']:.1%}, n={int(row['events'])})"


def factor_signal_table(signals: list[FactorSignal]) -> str:
    if not signals:
        return "No within-context workload/fatigue factors reached p < 0.10."
    rows = pd.DataFrame(
        [
            {
                "context": signal.context,
                "factor": signal.factor,
                "events": signal.n,
                "incorrect": signal.incorrect,
                "odds_ratio": signal.odds_ratio,
                "p_value": signal.p_value,
            }
            for signal in signals
        ]
    )
    return dataframe_to_markdown(rows)


def interpretation(
    call_family_summary: pd.DataFrame,
    call_type_summary: pd.DataFrame,
    factor_signals: list[FactorSignal],
) -> str:
    if factor_signals:
        return (
            "The clearest finding is contextual: error risk varies far more by call "
            "type than by broad fatigue/load variables. Treat any p < 0.10 workload "
            "signals as exploratory because they are sliced across many contexts."
        )
    return (
        "The clearest finding is contextual, not fatigue-driven: error risk varies "
        "substantially by call type, while the workload variables do not show a "
        "stable within-context relationship."
    )


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate"):
            formatted[column] = formatted[column].map(lambda value: f"{value:.1%}")
        elif column in {"p_value", "odds_ratio"}:
            formatted[column] = formatted[column].map(lambda value: f"{value:.4f}")
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


if __name__ == "__main__":
    main()

