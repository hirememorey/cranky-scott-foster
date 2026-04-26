#!/usr/bin/env python3
"""Fast parallel page pull for an immediate H1b smoke test."""

from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.game_ids import load_regular_season_game_ids, season_from_game_id
from referee_fatigue.nba_stats_client import NBAStatsClient

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a quick parallel H1b data pull")
    parser.add_argument("--season", default="2024-25")
    parser.add_argument("--max-games", type=int, default=500)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--resilience-path", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "quick_h1b_sample.log"),
            logging.StreamHandler(),
        ],
    )

    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)

    game_ids = load_regular_season_game_ids(
        [args.season], PROJECT_ROOT, args.resilience_path
    )[args.season][: args.max_games]
    if args.force:
        _delete_games(conn, game_ids)

    pending_ids = [
        game_id
        for game_id in game_ids
        if args.force or _assignment_count(conn, game_id) < 3
    ]
    logger.info(
        "Fetching %s/%s games for %s with %s workers",
        len(pending_ids),
        len(game_ids),
        args.season,
        args.workers,
    )

    inserted_assignments = 0
    inserted_challenges = 0
    failures = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_and_parse_game, game_id, args.season): game_id
            for game_id in pending_ids
        }
        for index, future in enumerate(as_completed(futures), start=1):
            game_id = futures[future]
            try:
                assignment_rows, challenge_rows = future.result()
                _insert_rows(conn, assignment_rows, challenge_rows)
                inserted_assignments += len(assignment_rows)
                inserted_challenges += len(challenge_rows)
            except Exception as exc:
                failures += 1
                logger.warning("Game %s failed: %s", game_id, exc)

            if index % 25 == 0 or index == len(futures):
                logger.info(
                    "Progress %s/%s games; assignments=%s challenges=%s failures=%s",
                    index,
                    len(futures),
                    inserted_assignments,
                    inserted_challenges,
                    failures,
                )

    logger.info(
        "Done. Inserted %s assignment rows and %s challenge rows.",
        inserted_assignments,
        inserted_challenges,
    )


def fetch_and_parse_game(
    game_id: str, season: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache", min_request_interval=0)
    page_props = client.get_nba_game_page_data(game_id)
    return parse_assignments(page_props, game_id, season), parse_challenges(page_props, game_id, season)


def parse_assignments(
    page_props: dict[str, Any], game_id: str, season: str
) -> list[dict[str, Any]]:
    game = page_props.get("game", {})
    officials = game.get("officials", [])
    if not officials:
        raise ValueError("missing game.officials")
    rows = []
    for index, official in enumerate(sorted(officials, key=jersey_sort_key)):
        rows.append(
            {
                "game_id": game_id,
                "game_date": game.get("gameEt") or game.get("gameTimeUTC"),
                "season": season,
                "season_type": "Regular Season",
                "arena_city": (game.get("arena") or {}).get("arenaCity"),
                "home_team_id": to_int(game.get("homeTeamId")),
                "away_team_id": to_int(game.get("awayTeamId")),
                "official_id": to_int(official.get("personId")),
                "official_name": official.get("name") or "",
                "first_name": official.get("firstName") or "",
                "last_name": official.get("familyName") or "",
                "jersey_num": str(official.get("jerseyNum") or "").strip(),
                "role": "crew_chief" if index == 0 else f"official_{index + 1}",
            }
        )
    return rows


def parse_challenges(
    page_props: dict[str, Any], game_id: str, season: str
) -> list[dict[str, Any]]:
    actions = page_props.get("playByPlay", {}).get("actions", [])
    rows = []
    for action in actions:
        description = " ".join(
            str(part)
            for part in [action.get("description"), action.get("actionType"), action.get("subType")]
            if part
        )
        outcome = classify_outcome(description)
        if outcome is None or "CHALLENGE" not in description.upper():
            continue
        rows.append(
            {
                "game_id": game_id,
                "event_num": int(action.get("actionNumber")),
                "season": season or season_from_game_id(game_id),
                "season_type": "Regular Season",
                "period": to_int(action.get("period")),
                "game_clock": action.get("clock"),
                "description": description,
                "original_ruling": "challenged",
                "final_ruling": outcome,
                "overturned": 1 if outcome == "overturned" else 0,
                "crew_chief_id": None,
                "challenging_team": action.get("teamTricode") or None,
                "event_msg_type": None,
            }
        )
    return rows


def classify_outcome(description: str) -> str | None:
    text = description.upper()
    if "UNSUCCESSFUL" in text:
        return "upheld"
    if "OVERTURN" in text or "SUCCESSFUL" in text:
        return "overturned"
    if any(token in text for token in ["UPHELD", "STANDS", "CONFIRMED", "SUPPORT"]):
        return "upheld"
    return None


def _insert_rows(
    conn,
    assignment_rows: list[dict[str, Any]],
    challenge_rows: list[dict[str, Any]],
) -> None:
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
        assignment_rows,
    )

    crew_chief_id = next(
        (row["official_id"] for row in assignment_rows if row["role"] == "crew_chief"),
        None,
    )
    for row in challenge_rows:
        row["crew_chief_id"] = crew_chief_id

    conn.executemany(
        """
        INSERT OR REPLACE INTO challenge_events (
            game_id, event_num, season, season_type, period, game_clock,
            description, original_ruling, final_ruling, overturned,
            crew_chief_id, challenging_team, event_msg_type
        )
        VALUES (
            :game_id, :event_num, :season, :season_type, :period,
            :game_clock, :description, :original_ruling, :final_ruling,
            :overturned, :crew_chief_id, :challenging_team, :event_msg_type
        )
        """,
        challenge_rows,
    )
    conn.commit()


def _assignment_count(conn, game_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM referee_assignments WHERE game_id = ?",
        (game_id,),
    ).fetchone()
    return int(row["count"])


def _delete_games(conn, game_ids: list[str]) -> None:
    for game_id in game_ids:
        conn.execute("DELETE FROM referee_assignments WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM challenge_events WHERE game_id = ?", (game_id,))
    conn.commit()


def jersey_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    try:
        return int(str(row.get("jerseyNum") or "").strip()), str(row)
    except ValueError:
        return 999, str(row)


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


if __name__ == "__main__":
    main()

