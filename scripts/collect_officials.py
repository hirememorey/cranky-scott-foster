#!/usr/bin/env python3
"""Collect NBA referee assignments into the local referee fatigue database.

Officials are read only from www.nba.com embedded game page data (Next.js),
not stats.nba.com — boxscoresummaryv2 has proven unreliable for this workflow.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.crew_features import is_playoff_game_id
from referee_fatigue.game_ids import DEFAULT_SEASONS, load_regular_season_game_ids, season_from_game_id
from referee_fatigue.nba_stats_client import NBAStatsClient

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect NBA game officials")
    parser.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--resilience-path", type=Path)
    parser.add_argument("--max-games-per-season", type=int)
    parser.add_argument("--force", action="store_true", help="Re-fetch games already present")
    parser.add_argument(
        "--from-l2m-reports",
        action="store_true",
        help="Fetch officials for every distinct game_id in l2m_reports (regular + playoff).",
    )
    return parser.parse_args()


def collect_officials(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "collect_officials.log"),
            logging.StreamHandler(),
        ],
    )

    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache")
    game_ids_by_season = load_regular_season_game_ids(
        args.seasons, PROJECT_ROOT, args.resilience_path
    )

    total_inserted = 0

    if args.from_l2m_reports:
        cursor = conn.execute(
            """
            SELECT game_id, home_team_id, away_team_id
            FROM l2m_reports
            WHERE has_report = 1
            ORDER BY game_id
            """
        )
        rows = cursor.fetchall()
        logger.info("Collecting officials for %s L2M games (--from-l2m-reports)", len(rows))
        skipped_already_complete = 0
        fetch_failures = 0
        for row in rows:
            game_id = str(row[0])
            home_tid = row[1]
            away_tid = row[2]
            if not args.force and _assignment_count(conn, game_id) >= 3:
                skipped_already_complete += 1
                continue
            if args.force:
                conn.execute("DELETE FROM referee_assignments WHERE game_id = ?", (game_id,))
            season = _season_from_game_id(game_id)
            try:
                rows_out = _parse_assignment_rows_from_page(
                    client.get_nba_game_page_data(
                        game_id,
                        home_team_id=home_tid,
                        away_team_id=away_tid,
                    ),
                    game_id,
                    season,
                )
            except Exception as exc:
                fetch_failures += 1
                logger.warning("Game %s failed: %s", game_id, exc)
                continue
            _tag_season_type(rows_out, game_id)
            try:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO referee_assignments (
                        game_id, game_date, season, season_type, arena_city,
                        home_team_id, away_team_id, official_id, official_name,
                        first_name, last_name, jersey_num, role
                    )
                    VALUES (
                        :game_id, :game_date, :season, :season_type, :arena_city,
                        :home_team_id, :away_team_id, :official_id, :official_name,
                        :first_name, :last_name, :jersey_num, :role
                    )
                    """,
                    rows_out,
                )
                conn.commit()
                total_inserted += len(rows_out)
                logger.info("Game %s: inserted %s officials", game_id, len(rows_out))
            except Exception as exc:
                logger.warning("Game %s DB write failed: %s", game_id, exc)
        logger.info(
            "Done. Inserted/updated %s referee assignment rows "
            "(skipped %s games already had ≥3 officials, %s fetch/parse failures).",
            total_inserted,
            skipped_already_complete,
            fetch_failures,
        )
        return

    for season, game_ids in game_ids_by_season.items():
        if args.max_games_per_season:
            game_ids = game_ids[: args.max_games_per_season]
        logger.info("Collecting officials for %s (%s games)", season, len(game_ids))

        for game_id in game_ids:
            if not args.force and _assignment_count(conn, game_id) >= 3:
                continue
            if args.force:
                conn.execute("DELETE FROM referee_assignments WHERE game_id = ?", (game_id,))

            try:
                rows = _parse_assignment_rows_from_page(
                    client.get_nba_game_page_data(game_id), game_id, season
                )
            except Exception as exc:
                logger.warning("Game %s failed: %s", game_id, exc)
                continue

            _tag_season_type(rows, game_id)
            try:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO referee_assignments (
                        game_id, game_date, season, season_type, arena_city,
                        home_team_id, away_team_id, official_id, official_name,
                        first_name, last_name, jersey_num, role
                    )
                    VALUES (
                        :game_id, :game_date, :season, :season_type, :arena_city,
                        :home_team_id, :away_team_id, :official_id, :official_name,
                        :first_name, :last_name, :jersey_num, :role
                    )
                    """,
                    rows,
                )
                conn.commit()
                total_inserted += len(rows)
                logger.info("Game %s: inserted %s officials", game_id, len(rows))
            except Exception as exc:
                logger.warning("Game %s DB write failed: %s", game_id, exc)

    logger.info("Done. Inserted/updated %s referee assignment rows.", total_inserted)


def _season_from_game_id(game_id: str) -> str:
    return season_from_game_id(game_id)


def _tag_season_type(rows: list[dict[str, Any]], game_id: str) -> None:
    season_type = "Playoffs" if is_playoff_game_id(game_id) else "Regular Season"
    for row in rows:
        row["season_type"] = season_type


def _assignment_count(conn, game_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM referee_assignments WHERE game_id = ?",
        (game_id,),
    ).fetchone()
    return int(row["count"])


def _parse_assignment_rows_from_page(
    page_props: dict[str, Any], game_id: str, season: str
) -> list[dict[str, Any]]:
    game = page_props.get("game", {})
    officials = game.get("officials", [])
    if not officials:
        raise ValueError("NBA page did not include game.officials")

    rows = []
    for index, official in enumerate(officials):
        rows.append(
            {
                "game_id": game_id,
                "game_date": game.get("gameEt") or game.get("gameTimeUTC"),
                "season": season,
                "season_type": "Regular Season",
                "arena_city": (game.get("arena") or {}).get("arenaCity"),
                "home_team_id": _to_int(game.get("homeTeamId")),
                "away_team_id": _to_int(game.get("awayTeamId")),
                "official_id": _to_int(official.get("personId")),
                "official_name": official.get("name") or "",
                "first_name": official.get("firstName") or "",
                "last_name": official.get("familyName") or "",
                "jersey_num": str(official.get("jerseyNum") or "").strip(),
                "role": "crew_chief" if index == 0 else f"official_{index + 1}",
            }
        )
    return rows


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


if __name__ == "__main__":
    collect_officials(parse_args())

