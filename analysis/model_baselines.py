#!/usr/bin/env python3
"""Compare L2M risk-model baselines under rolling season holdout."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))

from referee_fatigue.db import connect, create_referee_tables

import post_event_risk_model as risk


VARIANTS = {
    "baseline_error_rate": ([], []),
    "call_type_only": (["call_type_grouped"], []),
    "call_vs_non_call": (["decision_kind"], []),
    "taxonomy_only": (["monitoring_type"], []),
    "taxonomy_clock": (["monitoring_type", "clock_bucket", "period_bucket"], []),
    "taxonomy_context_workload": (
        [
            "monitoring_type",
            "clock_bucket",
            "period_bucket",
            "decision_kind",
            "score_state",
            "possession_context",
            "scramble_context",
            "sequence_context_grouped",
        ],
        [
            "clock_seconds",
            "score_margin_abs",
            "days_rest_capped",
            "games_last_7",
            "travel_miles_last_7k",
            "back_to_back",
            "estimated_pace",
            "q4_pre_l2m_actions_per_minute",
            "l2m_actions_per_minute",
        ],
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare rolling holdout baselines")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/model_baselines_report.md")
    parser.add_argument("--csv-output", default="results/model_baselines_report.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = risk.prepare_dataset(risk.load_event_data(conn))
    rows = []
    for variant_name, (categorical, numeric) in VARIANTS.items():
        if variant_name == "baseline_error_rate":
            rows.extend(baseline_rows(df, variant_name))
            continue
        table = risk.rolling_season_evaluation(df, categorical, numeric)
        table.insert(0, "variant", variant_name)
        rows.extend(table.to_dict("records"))

    comparison = pd.DataFrame(rows)
    write_report(comparison, PROJECT_ROOT / args.output)
    (PROJECT_ROOT / args.csv_output).parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(PROJECT_ROOT / args.csv_output, index=False)
    print(f"Wrote {PROJECT_ROOT / args.output}")
    print(f"Wrote {PROJECT_ROOT / args.csv_output}")


def baseline_rows(df: pd.DataFrame, variant_name: str) -> list[dict]:
    rows = []
    seasons = sorted(df["season"].dropna().unique(), key=risk.season_sort_key)
    for holdout_season in seasons[1:]:
        train_df = df[df["season"].map(risk.season_sort_key) < risk.season_sort_key(holdout_season)].copy()
        test_df = df[df["season"] == holdout_season].copy()
        if train_df.empty or test_df.empty:
            continue
        baseline = float(train_df["incorrect"].mean())
        predictions = [baseline] * len(test_df)
        metrics = risk.model_metrics(test_df["incorrect"], predictions)
        lift_table = risk.risk_lift_table(test_df, predictions)
        top_10 = lift_table.loc[lift_table["risk_bucket"] == "top_10pct"].iloc[0]
        rows.append(
            {
                "variant": variant_name,
                "holdout_season": holdout_season,
                "train_seasons": risk.season_range(train_df),
                "train_events": len(train_df),
                "test_events": len(test_df),
                "test_incorrect": int(test_df["incorrect"].sum()),
                "baseline_error_rate": test_df["incorrect"].mean(),
                "roc_auc": metrics["roc_auc"],
                "avg_precision": metrics["avg_precision"],
                "top_10_error_rate": top_10["observed_error_rate"],
                "top_10_lift": top_10["lift_vs_baseline"],
                "top_10_error_capture": top_10["share_of_all_errors_captured"],
            }
        )
    return rows


def write_report(df: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# Model Baseline Comparison",
        "",
        "Rolling season holdout compares each model against future-season L2M outcomes.",
        "",
        "## By Variant And Season",
        "",
        risk.dataframe_to_markdown(df),
        "",
        "## Average By Variant",
        "",
        risk.dataframe_to_markdown(average_by_variant(df)),
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def average_by_variant(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return (
        df.groupby("variant", dropna=False)
        .agg(
            holdout_seasons=("holdout_season", "count"),
            mean_roc_auc=("roc_auc", "mean"),
            mean_top_10_lift=("top_10_lift", "mean"),
            mean_top_10_error_rate=("top_10_error_rate", "mean"),
            mean_error_capture=("top_10_error_capture", "mean"),
        )
        .reset_index()
        .sort_values("mean_top_10_lift", ascending=False)
    )


if __name__ == "__main__":
    main()
