#!/usr/bin/env python3
"""Run robustness checks for L2M structural-risk models."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.taxonomy import POSSESSION_BOUNDARY_ADJUDICATION, TIMING_COUNT_JUDGMENT

import post_event_risk_model as risk


SCENARIOS = {
    "full_sample": "Full prepared L2M event sample.",
    "exclude_defense_3_second": "Exclude `Foul: Defense 3 Second` events.",
    "exclude_traveling": "Exclude `Turnover: Traveling` events.",
    "exclude_defense_3_second_and_traveling": (
        "Exclude both `Foul: Defense 3 Second` and `Turnover: Traveling`."
    ),
    "exclude_rare_call_types_lt_100": "Exclude raw call types with fewer than 100 events.",
    "exclude_timing_count_judgment": "Exclude the timing/count structural category.",
    "exclude_possession_boundary_adjudication": "Exclude the possession/boundary structural category.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run L2M robustness checks")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/l2m_robustness_report.md")
    parser.add_argument("--csv-output", default="results/l2m_robustness_report.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = risk.prepare_dataset(risk.load_event_data(conn))

    rows = []
    for scenario_name, scenario_df in scenario_datasets(df).items():
        table = risk.rolling_season_evaluation(scenario_df)
        if table.empty:
            rows.append(empty_scenario_row(scenario_name, scenario_df))
            continue
        table.insert(0, "scenario", scenario_name)
        table.insert(1, "scenario_events", len(scenario_df))
        table.insert(2, "scenario_incorrect", int(scenario_df["incorrect"].sum()))
        table.insert(3, "scenario_error_rate", scenario_df["incorrect"].mean())
        rows.extend(table.to_dict("records"))

    results = pd.DataFrame(rows)
    write_report(results, PROJECT_ROOT / args.output)
    (PROJECT_ROOT / args.csv_output).parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(PROJECT_ROOT / args.csv_output, index=False)
    print(f"Wrote {PROJECT_ROOT / args.output}")
    print(f"Wrote {PROJECT_ROOT / args.csv_output}")


def scenario_datasets(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    counts = df["call_type"].value_counts(dropna=False)
    rare_call_types = set(counts[counts < 100].index)
    return {
        "full_sample": df.copy(),
        "exclude_defense_3_second": df[df["call_type"] != "Foul: Defense 3 Second"].copy(),
        "exclude_traveling": df[df["call_type"] != "Turnover: Traveling"].copy(),
        "exclude_defense_3_second_and_traveling": df[
            ~df["call_type"].isin(["Foul: Defense 3 Second", "Turnover: Traveling"])
        ].copy(),
        "exclude_rare_call_types_lt_100": df[~df["call_type"].isin(rare_call_types)].copy(),
        "exclude_timing_count_judgment": df[df["monitoring_type"] != TIMING_COUNT_JUDGMENT].copy(),
        "exclude_possession_boundary_adjudication": df[
            df["monitoring_type"] != POSSESSION_BOUNDARY_ADJUDICATION
        ].copy(),
    }


def empty_scenario_row(scenario_name: str, df: pd.DataFrame) -> dict:
    return {
        "scenario": scenario_name,
        "scenario_events": len(df),
        "scenario_incorrect": int(df["incorrect"].sum()) if not df.empty else 0,
        "scenario_error_rate": df["incorrect"].mean() if not df.empty else None,
        "holdout_season": None,
        "train_seasons": None,
        "train_events": None,
        "test_events": None,
        "test_incorrect": None,
        "baseline_error_rate": None,
        "roc_auc": None,
        "avg_precision": None,
        "top_10_error_rate": None,
        "top_10_lift": None,
        "top_10_error_capture": None,
    }


def write_report(df: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# L2M Robustness Checks",
        "",
        "Rolling season holdout after excluding key call types or structural categories.",
        "",
        "## Average By Scenario",
        "",
        risk.dataframe_to_markdown(average_by_scenario(df)),
        "",
        "## By Scenario And Season",
        "",
        risk.dataframe_to_markdown(report_columns(df)),
        "",
        "## Scenario Definitions",
        "",
        *scenario_definition_lines(),
        "",
        "## Interpretation",
        "",
        interpretation(average_by_scenario(df)),
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def report_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "scenario",
        "holdout_season",
        "scenario_events",
        "scenario_error_rate",
        "test_events",
        "baseline_error_rate",
        "roc_auc",
        "avg_precision",
        "top_10_error_rate",
        "top_10_lift",
        "top_10_error_capture",
    ]
    return df[[column for column in columns if column in df.columns]].copy()


def average_by_scenario(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    summary = (
        df.groupby("scenario", dropna=False)
        .agg(
            scenario_events=("scenario_events", "max"),
            scenario_error_rate=("scenario_error_rate", "max"),
            holdout_seasons=("holdout_season", "count"),
            mean_roc_auc=("roc_auc", "mean"),
            mean_top_10_lift=("top_10_lift", "mean"),
            mean_top_10_error_rate=("top_10_error_rate", "mean"),
            mean_error_capture=("top_10_error_capture", "mean"),
        )
        .reset_index()
    )
    scenario_order = {name: index for index, name in enumerate(SCENARIOS)}
    summary["scenario_order"] = summary["scenario"].map(scenario_order)
    return summary.sort_values("scenario_order").drop(columns=["scenario_order"])


def scenario_definition_lines() -> list[str]:
    lines = []
    for scenario, description in SCENARIOS.items():
        lines.append(f"- `{scenario}`: {description}")
    return lines


def interpretation(summary: pd.DataFrame) -> str:
    if summary.empty or "mean_top_10_lift" not in summary:
        return "No robustness summary was available."
    full = summary[summary["scenario"] == "full_sample"]
    without_top_two = summary[summary["scenario"] == "exclude_defense_3_second_and_traveling"]
    without_rare = summary[summary["scenario"] == "exclude_rare_call_types_lt_100"]
    parts = []
    if not full.empty:
        row = full.iloc[0]
        parts.append(
            f"The full-sample rolling holdout top-decile lift is {row['mean_top_10_lift']:.1f}x."
        )
    if not without_top_two.empty:
        row = without_top_two.iloc[0]
        parts.append(
            "After excluding defensive three seconds and traveling, mean top-decile "
            f"lift is {row['mean_top_10_lift']:.1f}x."
        )
    if not without_rare.empty:
        row = without_rare.iloc[0]
        parts.append(
            "After excluding raw call types with fewer than 100 events, mean top-decile "
            f"lift is {row['mean_top_10_lift']:.1f}x."
        )
    parts.append(
        "Use these checks to distinguish a broad structural-risk result from a result "
        "driven by one or two high-risk call labels."
    )
    return " ".join(parts)


if __name__ == "__main__":
    main()
