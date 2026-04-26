#!/usr/bin/env python3
"""Extract coach's challenge outcomes from NBA play-by-play."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.game_ids import (
    DEFAULT_SEASONS,
    load_regular_season_game_ids,
    season_from_game_id,
)
from referee_fatigue.nba_stats_client import NBAStatsClient, result_set_to_records

logger = logging.getLogger(__name__)

OUTCOME_PATTERN = re.compile(
    r"OVERTURN|SUCCESSFUL|UNSUCCESSFUL|UPHELD|STANDS|CONFIRMED",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract coach challenge events")
    parser.add_argument("--seasons", nargs="+", default=DEFAULT_SEASONS)
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--resilience-path", type=Path)
    parser.add_argument("--max-games-per-season", type=int)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def extract_challenge_events(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "extract_challenge_events.log"),
            logging.StreamHandler(),
        ],
    )

    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache")
    game_ids_by_season = _game_ids_from_assignments(conn, args.seasons)
    if not any(game_ids_by_season.values()):
        game_ids_by_season = load_regular_season_game_ids(
            args.seasons, PROJECT_ROOT, args.resilience_path
        )

    total_inserted = 0
    for season, game_ids in game_ids_by_season.items():
        if args.max_games_per_season:
            game_ids = game_ids[: args.max_games_per_season]
        logger.info("Extracting challenges for %s (%s games)", season, len(game_ids))

        for game_id in game_ids:
            if not args.force and _challenge_count(conn, game_id) > 0:
                continue
            if args.force:
                conn.execute("DELETE FROM challenge_events WHERE game_id = ?", (game_id,))

            try:
                page_props = client.get_nba_game_page_data(game_id)
                rows = _extract_rows_from_page(conn, game_id, season, page_props)
            except Exception as page_exc:
                logger.info("Game %s page parse failed, falling back to Stats API: %s", game_id, page_exc)
                try:
                    response = client.get_play_by_play(game_id)
                    events = result_set_to_records(response, "PlayByPlay")
                    rows = _extract_rows(conn, game_id, season, events)
                except Exception as exc:
                    logger.warning("Game %s failed: %s", game_id, exc)
                    continue

            try:
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
                    rows,
                )
                conn.commit()
                total_inserted += len(rows)
                if rows:
                    logger.info("Game %s: inserted %s challenge events", game_id, len(rows))
            except Exception as exc:
                logger.warning("Game %s DB write failed: %s", game_id, exc)

    logger.info("Done. Inserted/updated %s challenge event rows.", total_inserted)


def _game_ids_from_assignments(conn, seasons: list[str]) -> dict[str, list[str]]:
    rows = conn.execute(
        """
        SELECT DISTINCT season, game_id
        FROM referee_assignments
        WHERE season IN ({})
        ORDER BY season, game_id
        """.format(",".join("?" for _ in seasons)),
        seasons,
    ).fetchall()
    game_ids_by_season = {season: [] for season in seasons}
    for row in rows:
        game_ids_by_season[row["season"]].append(row["game_id"])
    return game_ids_by_season


def _challenge_count(conn, game_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM challenge_events WHERE game_id = ?",
        (game_id,),
    ).fetchone()
    return int(row["count"])


def _extract_rows(
    conn,
    game_id: str,
    season: str,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    crew_chief_id = _crew_chief_id(conn, game_id)
    rows = []
    for event in events:
        description, side = _event_description(event)
        if not _is_challenge_event(event, description):
            continue
        outcome = _classify_outcome(description)
        if outcome is None:
            continue

        rows.append(
            {
                "game_id": game_id,
                "event_num": int(event.get("EVENTNUM")),
                "season": season or season_from_game_id(game_id),
                "season_type": "Regular Season",
                "period": _to_int(event.get("PERIOD")),
                "game_clock": event.get("PCTIMESTRING"),
                "description": description,
                "original_ruling": "challenged",
                "final_ruling": outcome,
                "overturned": 1 if outcome == "overturned" else 0,
                "crew_chief_id": crew_chief_id,
                "challenging_team": side,
                "event_msg_type": _to_int(event.get("EVENTMSGTYPE")),
            }
        )
    return rows


def _extract_rows_from_page(
    conn,
    game_id: str,
    season: str,
    page_props: dict[str, Any],
) -> list[dict[str, Any]]:
    crew_chief_id = _crew_chief_id(conn, game_id)
    actions = page_props.get("playByPlay", {}).get("actions", [])
    if not actions:
        raise ValueError("NBA page did not include playByPlay.actions")

    rows = []
    for action in actions:
        description = " ".join(
            str(part)
            for part in [
                action.get("description"),
                action.get("actionType"),
                action.get("subType"),
            ]
            if part
        )
        if not _is_page_challenge_action(action, description):
            continue
        outcome = _classify_outcome(description)
        if outcome is None:
            continue

        rows.append(
            {
                "game_id": game_id,
                "event_num": int(action.get("actionNumber")),
                "season": season or season_from_game_id(game_id),
                "season_type": "Regular Season",
                "period": _to_int(action.get("period")),
                "game_clock": action.get("clock"),
                "description": description,
                "original_ruling": "challenged",
                "final_ruling": outcome,
                "overturned": 1 if outcome == "overturned" else 0,
                "crew_chief_id": crew_chief_id,
                "challenging_team": action.get("teamTricode") or None,
                "event_msg_type": None,
            }
        )
    return rows


def _event_description(event: dict[str, Any]) -> tuple[str, str | None]:
    home_desc = event.get("HOMEDESCRIPTION") or ""
    neutral_desc = event.get("NEUTRALDESCRIPTION") or ""
    visitor_desc = event.get("VISITORDESCRIPTION") or ""
    description = " | ".join(part for part in [home_desc, neutral_desc, visitor_desc] if part)
    side = None
    if "CHALLENGE" in home_desc.upper():
        side = "HOME"
    elif "CHALLENGE" in visitor_desc.upper():
        side = "VISITOR"
    return description, side


def _is_challenge_event(event: dict[str, Any], description: str) -> bool:
    event_msg_type = _to_int(event.get("EVENTMSGTYPE"))
    text = description.upper()
    return (
        ("CHALLENGE" in text and OUTCOME_PATTERN.search(text) is not None)
        or (event_msg_type == 18 and "CHALLENGE" in text)
    )


def _is_page_challenge_action(action: dict[str, Any], description: str) -> bool:
    text = description.upper()
    return (
        "CHALLENGE" in text
        and OUTCOME_PATTERN.search(text) is not None
        and (action.get("actionType") == "Instant Replay" or "RULING" in text)
    )


def _classify_outcome(description: str) -> str | None:
    text = description.upper()
    if "UNSUCCESSFUL" in text:
        return "upheld"
    if "OVERTURN" in text or "SUCCESSFUL" in text:
        return "overturned"
    if any(token in text for token in ["UPHELD", "STANDS", "CONFIRMED", "SUPPORT"]):
        return "upheld"
    return None


def _crew_chief_id(conn, game_id: str) -> int | None:
    row = conn.execute(
        """
        SELECT official_id
        FROM referee_assignments
        WHERE game_id = ? AND role = 'crew_chief'
        LIMIT 1
        """,
        (game_id,),
    ).fetchone()
    return int(row["official_id"]) if row else None


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


if __name__ == "__main__":
    extract_challenge_events(parse_args())

