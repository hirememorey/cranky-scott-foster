#!/usr/bin/env python3
"""Export Structural Officiating Risk Index (SORI) scores."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))

from referee_fatigue.db import connect, create_referee_tables

import model_baselines
import post_event_risk_model as risk


DEFAULT_VARIANT = "taxonomy_clock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export SORI scores")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--variant", choices=sorted(model_baselines.VARIANTS), default=None)
    parser.add_argument("--event-output", default="results/sori_event_scores.csv")
    parser.add_argument("--game-output", default="results/sori_game_scores.csv")
    parser.add_argument("--category-output", default="results/sori_category_map.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    df = risk.prepare_dataset(risk.load_event_data(conn))
    variant_name = args.variant or choose_variant(df)
    categorical, numeric = model_baselines.VARIANTS[variant_name]
    if variant_name == "baseline_error_rate":
        df["sori_score"] = float(df["incorrect"].mean())
    else:
        pipeline = risk.build_pipeline(categorical, numeric)
        pipeline.fit(df[categorical + numeric], df["incorrect"])
        df["sori_score"] = pipeline.predict_proba(df[categorical + numeric])[:, 1]

    event_scores = event_score_columns(df, variant_name)
    game_scores = game_score_columns(event_scores)
    category_map = category_risk_map(df)

    event_path = PROJECT_ROOT / args.event_output
    game_path = PROJECT_ROOT / args.game_output
    category_path = PROJECT_ROOT / args.category_output
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_scores.to_csv(event_path, index=False)
    game_scores.to_csv(game_path, index=False)
    category_path.write_text(category_map, encoding="utf-8")
    print(f"Wrote {event_path}")
    print(f"Wrote {game_path}")
    print(f"Wrote {category_path}")


def choose_variant(df: pd.DataFrame) -> str:
    seasons = sorted(df["season"].dropna().unique(), key=risk.season_sort_key)
    if len(seasons) < 2:
        return DEFAULT_VARIANT
    rows = []
    for variant_name, (categorical, numeric) in model_baselines.VARIANTS.items():
        if variant_name == "baseline_error_rate":
            continue
        table = risk.rolling_season_evaluation(df, categorical, numeric)
        if table.empty:
            continue
        rows.append((variant_name, table["top_10_lift"].dropna().mean()))
    rows = [(name, lift) for name, lift in rows if not pd.isna(lift)]
    if not rows:
        return DEFAULT_VARIANT
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows[0][0]


def event_score_columns(df: pd.DataFrame, variant_name: str) -> pd.DataFrame:
    columns = [
        "season",
        "game_id",
        "event_index",
        "period",
        "game_clock",
        "call_type",
        "review_decision",
        "incorrect",
        "monitoring_type",
        "clock_bucket",
        "score_state",
        "sori_score",
    ]
    out = df[columns].copy()
    out.insert(0, "sori_variant", variant_name)
    return out.sort_values("sori_score", ascending=False)


def game_score_columns(event_scores: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        event_scores.groupby(["season", "game_id"], dropna=False)
        .agg(
            l2m_events=("event_index", "size"),
            incorrect_events=("incorrect", "sum"),
            mean_sori=("sori_score", "mean"),
            max_sori=("sori_score", "max"),
            top_decile_event_sori=("sori_score", lambda values: values.quantile(0.9)),
        )
        .reset_index()
    )
    return grouped.sort_values(["max_sori", "mean_sori"], ascending=False)


def category_risk_map(df: pd.DataFrame) -> str:
    grouped = (
        df.groupby(["monitoring_type", "clock_bucket"], dropna=False)
        .agg(events=("incorrect", "size"), incorrect=("incorrect", "sum"), error_rate=("incorrect", "mean"))
        .reset_index()
        .sort_values(["monitoring_type", "clock_bucket"])
    )
    lines = [
        "# SORI Category Risk Map",
        "",
        "Observed error rates by frozen structural taxonomy and L2M clock bucket.",
        "",
        risk.dataframe_to_markdown(grouped),
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
