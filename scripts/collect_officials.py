#!/usr/bin/env python3
"""Collect NBA referee assignments into the local referee fatigue database."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.game_ids import DEFAULT_SEASONS, load_regular_season_game_ids
from referee_fatigue.nba_stats_client import NBAStatsClient, result_set_to_records

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect NBA game officials")
    parser.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--resilience-path", type=Path)
    parser.add_argument("--max-games-per-season", type=int)
    parser.add_argument("--force", action="store_true", help="Re-fetch games already present")
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
            except Exception as page_exc:
                logger.info("Game %s page parse failed, falling back to Stats API: %s", game_id, page_exc)
                try:
                    response = client.get_box_score_summary(game_id)
                    rows = _parse_assignment_rows(response, game_id, season)
                except Exception as exc:
                    logger.warning("Game %s failed: %s", game_id, exc)
                    continue

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


def _assignment_count(conn, game_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM referee_assignments WHERE game_id = ?",
        (game_id,),
    ).fetchone()
    return int(row["count"])


def _parse_assignment_rows(
    response: dict[str, Any], game_id: str, season: str
) -> list[dict[str, Any]]:
    officials = result_set_to_records(response, "OfficialsInfo")
    if not officials:
        officials = result_set_to_records(response, "Officials")
    if not officials:
        raise ValueError("No OfficialsInfo/Officials result set found")

    game_summary = _first(result_set_to_records(response, "GameSummary"))
    line_score = result_set_to_records(response, "LineScore")
    home_team_id = _get(game_summary, "HOME_TEAM_ID")
    away_team_id = _get(game_summary, "VISITOR_TEAM_ID")
    game_date = _get(game_summary, "GAME_DATE_EST") or _get(game_summary, "GAME_DATE")
    arena_city = _home_city(line_score, home_team_id)

    sorted_officials = sorted(officials, key=_jersey_sort_key)
    rows = []
    for index, official in enumerate(sorted_officials):
        official_id = _get(official, "OFFICIAL_ID") or _get(official, "PERSON_ID")
        first_name = _get(official, "FIRST_NAME") or ""
        last_name = _get(official, "LAST_NAME") or ""
        jersey_num = str(_get(official, "JERSEY_NUM") or _get(official, "JERSEY_NUMBER") or "")
        official_name = " ".join(part for part in [first_name, last_name] if part).strip()
        if not official_name:
            official_name = str(_get(official, "OFFICIAL_NAME") or official_id)

        rows.append(
            {
                "game_id": game_id,
                "game_date": game_date,
                "season": season,
                "season_type": "Regular Season",
                "arena_city": arena_city,
                "home_team_id": _to_int(home_team_id),
                "away_team_id": _to_int(away_team_id),
                "official_id": _to_int(official_id),
                "official_name": official_name,
                "first_name": first_name,
                "last_name": last_name,
                "jersey_num": jersey_num,
                "role": "crew_chief" if index == 0 else f"official_{index + 1}",
            }
        )
    return rows


def _parse_assignment_rows_from_page(
    page_props: dict[str, Any], game_id: str, season: str
) -> list[dict[str, Any]]:
    game = page_props.get("game", {})
    officials = game.get("officials", [])
    if not officials:
        raise ValueError("NBA page did not include game.officials")

    rows = []
    for index, official in enumerate(sorted(officials, key=_jersey_sort_key)):
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


def _first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def _get(row: dict[str, Any], key: str) -> Any:
    return row.get(key) if row else None


def _home_city(line_score: list[dict[str, Any]], home_team_id: Any) -> str | None:
    for row in line_score:
        if str(row.get("TEAM_ID")) == str(home_team_id):
            return row.get("TEAM_CITY_NAME") or row.get("TEAM_CITY")
    return None


def _jersey_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    jersey = row.get("JERSEY_NUM") or row.get("JERSEY_NUMBER") or row.get("jerseyNum")
    try:
        return int(jersey), str(row)
    except (TypeError, ValueError):
        return 999, str(row)


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


if __name__ == "__main__":
    collect_officials(parse_args())

