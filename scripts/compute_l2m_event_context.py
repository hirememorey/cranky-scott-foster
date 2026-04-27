#!/usr/bin/env python3
"""Compute event-context features for L2M-reviewed decisions."""

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
from referee_fatigue.nba_stats_client import NBAStatsClient
from referee_fatigue.pace_features import clock_seconds_remaining


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute L2M event-context features")
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
            logging.FileHandler(PROJECT_ROOT / "logs" / "compute_l2m_event_context.log"),
            logging.StreamHandler(),
        ],
    )
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache", min_request_interval=0.1)
    inserted = 0
    failures = 0
    for season in selected_seasons(conn, args):
        game_ids = l2m_game_ids(conn, season)
        logger.info("Computing event context for %s L2M games in %s", len(game_ids), season)
        for index, game_id in enumerate(game_ids, start=1):
            if not args.force and has_context(conn, game_id):
                continue
            try:
                page_props = client.get_nba_game_page_data(game_id)
                rows = compute_game_context_rows(conn, page_props, game_id, season)
                insert_rows(conn, rows)
                inserted += len(rows)
            except Exception as exc:
                failures += 1
                logger.warning("Event context failed for %s: %s", game_id, exc)
            if index % 50 == 0 or index == len(game_ids):
                logger.info(
                    "Progress %s %s/%s inserted_rows=%s failures=%s",
                    season,
                    index,
                    len(game_ids),
                    inserted,
                    failures,
                )
    logger.info("Done. Inserted/updated %s event-context rows.", inserted)


def selected_seasons(conn, args: argparse.Namespace) -> list[str]:
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


def l2m_game_ids(conn, season: str) -> list[str]:
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


def has_context(conn, game_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM l2m_event_context WHERE game_id = ? LIMIT 1",
        (game_id,),
    ).fetchone()
    return row is not None


def compute_game_context_rows(conn, page_props: dict[str, Any], game_id: str, season: str) -> list[dict]:
    actions = page_props.get("playByPlay", {}).get("actions", [])
    if not actions:
        raise ValueError("NBA page did not include playByPlay.actions")
    home_team = page_props.get("game", {}).get("homeTeam", {}).get("teamTricode")
    away_team = page_props.get("game", {}).get("awayTeam", {}).get("teamTricode")
    events = conn.execute(
        """
        SELECT event_index, period, game_clock, comment
        FROM l2m_events
        WHERE game_id = ?
        ORDER BY event_index
        """,
        (game_id,),
    ).fetchall()
    rows = []
    for event in events:
        period = parse_period(event["period"])
        event_clock = parse_l2m_clock(event["game_clock"])
        match_index, action = nearest_action(actions, period, event_clock)
        context_actions = nearby_actions(actions, match_index)
        score_home, score_away = action_score(action)
        score_margin = score_home - score_away if score_home is not None and score_away is not None else None
        action_team = action.get("teamTricode") if action else None
        trailing_team = trailing_team_code(score_home, score_away, home_team, away_team)
        clock_delta = matched_clock_delta(action, event_clock)
        rows.append(
            {
                "game_id": game_id,
                "event_index": event["event_index"],
                "season": season,
                "period": period,
                "game_clock": event["game_clock"],
                "matched_action_number": to_int(action.get("actionNumber") if action else None),
                "matched_clock_delta_seconds": clock_delta,
                "score_home": score_home,
                "score_away": score_away,
                "score_margin": score_margin,
                "score_margin_abs": abs(score_margin) if score_margin is not None else None,
                "tied_game": 1 if score_margin == 0 else 0,
                "one_possession": 1 if score_margin is not None and abs(score_margin) <= 3 else 0,
                "trailing_team": trailing_team,
                "action_team": action_team,
                "trailing_team_possession": (
                    1 if trailing_team and action_team == trailing_team else 0 if trailing_team and action_team else None
                ),
                "final_30_seconds": 1 if event_clock is not None and event_clock <= 30 else 0,
                "overtime": 1 if period and period >= 5 else 0,
                "rebound_scramble_indicator": 1
                if is_scramble_context(event["comment"], context_actions)
                else 0,
                "sequence_context": sequence_context(context_actions),
                "action_type": action.get("actionType") if action else None,
                "action_subtype": action.get("subType") if action else None,
            }
        )
    return rows


def insert_rows(conn, rows: list[dict]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO l2m_event_context (
            game_id, event_index, season, period, game_clock, matched_action_number,
            matched_clock_delta_seconds, score_home, score_away, score_margin,
            score_margin_abs, tied_game, one_possession, trailing_team, action_team,
            trailing_team_possession, final_30_seconds, overtime,
            rebound_scramble_indicator, sequence_context, action_type, action_subtype
        )
        VALUES (
            :game_id, :event_index, :season, :period, :game_clock, :matched_action_number,
            :matched_clock_delta_seconds, :score_home, :score_away, :score_margin,
            :score_margin_abs, :tied_game, :one_possession, :trailing_team, :action_team,
            :trailing_team_possession, :final_30_seconds, :overtime,
            :rebound_scramble_indicator, :sequence_context, :action_type, :action_subtype
        )
        """,
        rows,
    )
    conn.commit()


def nearest_action(actions: list[dict[str, Any]], period: int | None, event_clock: float | None) -> tuple[int, dict]:
    candidates = [
        (index, action)
        for index, action in enumerate(actions)
        if to_int(action.get("period")) == period
    ]
    if not candidates:
        return 0, actions[0]
    if event_clock is None:
        return candidates[0]
    return min(
        candidates,
        key=lambda item: abs((clock_seconds_remaining(item[1].get("clock")) or 0) - event_clock),
    )


def nearby_actions(actions: list[dict[str, Any]], match_index: int) -> list[dict[str, Any]]:
    start = max(match_index - 3, 0)
    end = min(match_index + 3, len(actions))
    return actions[start:end]


def action_score(action: dict | None) -> tuple[int | None, int | None]:
    if not action:
        return None, None
    home = first_present(action, "scoreHome", "homeScore")
    away = first_present(action, "scoreAway", "awayScore")
    return to_int(home), to_int(away)


def trailing_team_code(
    score_home: int | None,
    score_away: int | None,
    home_team: str | None,
    away_team: str | None,
) -> str | None:
    if score_home is None or score_away is None or score_home == score_away:
        return None
    return home_team if score_home < score_away else away_team


def matched_clock_delta(action: dict | None, event_clock: float | None) -> float | None:
    if not action or event_clock is None:
        return None
    action_clock = clock_seconds_remaining(action.get("clock"))
    if action_clock is None:
        return None
    return abs(action_clock - event_clock)


def parse_period(value: Any) -> int | None:
    text = str(value or "").upper()
    if text == "Q4":
        return 4
    match = re.search(r"OT(\d*)", text)
    if match:
        return 4 + int(match.group(1) or 1)
    return to_int(value)


def parse_l2m_clock(value: Any) -> float | None:
    if value is None:
        return None
    match = re.match(r"(\d+):(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1)) * 60 + float(match.group(2))


def is_scramble_context(comment: Any, actions: list[dict[str, Any]]) -> bool:
    text = " ".join(
        [
            str(comment or ""),
            *[
                " ".join(str(action.get(key) or "") for key in ("description", "actionType", "subType"))
                for action in actions
            ],
        ]
    ).lower()
    return any(token in text for token in ("rebound", "loose ball", "scramble", "block", "jump ball"))


def sequence_context(actions: list[dict[str, Any]]) -> str:
    labels = []
    for action in actions:
        action_type = str(action.get("actionType") or "").lower()
        if action_type in {"2pt", "3pt"}:
            labels.append("shot")
        elif action_type in {"rebound", "turnover", "foul", "violation"}:
            labels.append(action_type)
    if not labels:
        return "other"
    return "_".join(labels[-3:])


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if mapping.get(key) not in (None, ""):
            return mapping.get(key)
    return None


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
