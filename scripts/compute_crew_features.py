#!/usr/bin/env python3
"""Compute per-game crew chief and trio familiarity features (CSV export)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.crew_features import (
    compute_game_crew_features,
    games_with_three_officials,
    save_crew_game_table,
)
from referee_fatigue.db import connect, create_referee_tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export crew chief / trio familiarity features")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/crew_chief_game_features.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    games = games_with_three_officials(conn)
    crew = compute_game_crew_features(games)
    save_crew_game_table(PROJECT_ROOT / args.output, crew)
    print(f"Wrote {PROJECT_ROOT / args.output} ({len(crew)} games)")


if __name__ == "__main__":
    main()
