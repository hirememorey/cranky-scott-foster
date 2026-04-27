#!/usr/bin/env python3
"""Compute pace and late-game action-density features for L2M games."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.nba_stats_client import NBAStatsClient
from referee_fatigue.pace_features import compute_game_pace_features

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute game pace features")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--season", default="2024-25")
    parser.add_argument("--seasons", nargs="+")
    parser.add_argument("--all-seasons", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "compute_pace_features.log"),
            logging.StreamHandler(),
        ],
    )

    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache", min_request_interval=0.1)
    seasons = _selected_seasons(conn, args)

    inserted = 0
    failures = 0
    for season in seasons:
        game_ids = _l2m_game_ids(conn, season)
        logger.info("Computing pace features for %s L2M games in %s", len(game_ids), season)
        for index, game_id in enumerate(game_ids, start=1):
            if not args.force and _has_features(conn, game_id):
                continue
            try:
                page_props = client.get_nba_game_page_data(game_id)
                row = compute_game_pace_features(page_props, game_id, season)
                _insert_row(conn, row)
                inserted += 1
            except Exception as exc:
                failures += 1
                logger.warning("Pace features failed for %s: %s", game_id, exc)

            if index % 50 == 0 or index == len(game_ids):
                logger.info(
                    "Progress %s %s/%s inserted=%s failures=%s",
                    season,
                    index,
                    len(game_ids),
                    inserted,
                    failures,
                )

    logger.info("Done. Inserted/updated %s pace feature rows.", inserted)


def _selected_seasons(conn, args: argparse.Namespace) -> list[str]:
    if args.all_seasons:
        rows = conn.execute(
            """
            SELECT DISTINCT season
            FROM l2m_reports
            WHERE has_report = 1
            ORDER BY season
            """
        ).fetchall()
        return [row["season"] for row in rows]
    if args.seasons:
        return args.seasons
    return [args.season]


def _l2m_game_ids(conn, season: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT game_id
        FROM l2m_reports
        WHERE season = ? AND has_report = 1
        ORDER BY game_date, game_id
        """,
        (season,),
    ).fetchall()
    return [row["game_id"] for row in rows]


def _has_features(conn, game_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM game_pace_features WHERE game_id = ? LIMIT 1",
        (game_id,),
    ).fetchone()
    return row is not None


def _insert_row(conn, row: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO game_pace_features (
            game_id, season, game_minutes, estimated_possessions, estimated_pace,
            total_actions, actions_per_minute, q4_actions, q4_actions_per_minute,
            q4_pre_l2m_actions, q4_pre_l2m_actions_per_minute, l2m_actions,
            l2m_actions_per_minute, q4_shots, q4_fouls, q4_turnovers
        )
        VALUES (
            :game_id, :season, :game_minutes, :estimated_possessions, :estimated_pace,
            :total_actions, :actions_per_minute, :q4_actions, :q4_actions_per_minute,
            :q4_pre_l2m_actions, :q4_pre_l2m_actions_per_minute, :l2m_actions,
            :l2m_actions_per_minute, :q4_shots, :q4_fouls, :q4_turnovers
        )
        """,
        row,
    )
    conn.commit()


if __name__ == "__main__":
    main()

