#!/usr/bin/env python3
"""Collect official NBA Last Two Minute report JSON into SQLite."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.game_ids import load_regular_season_game_ids
from referee_fatigue.nba_stats_client import NBAStatsClient

logger = logging.getLogger(__name__)

DEFAULT_L2M_SEASONS = [
    "2015-16",
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
]
ARCHIVE_URLS = {
    season: f"https://official.nba.com/{season}-nba-officiating-last-two-minute-reports/"
    for season in DEFAULT_L2M_SEASONS
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect NBA L2M reports")
    parser.add_argument("--season", default="2024-25", choices=sorted(ARCHIVE_URLS))
    parser.add_argument("--seasons", nargs="+", choices=sorted(ARCHIVE_URLS))
    parser.add_argument("--all-seasons", action="store_true")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--max-games", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--summary-output", default="results/l2m_ingestion_summary.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "collect_l2m_reports.log"),
            logging.StreamHandler(),
        ],
    )

    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache", min_request_interval=0.2)

    reports_inserted = 0
    events_inserted = 0
    failures = 0
    seasons = selected_seasons(args)
    regular_season_ids = load_regular_season_game_ids(seasons, PROJECT_ROOT)
    for season in seasons:
        try:
            game_ids = discover_regular_season_l2m_game_ids(
                season,
                regular_season_ids=regular_season_ids.get(season) or None,
            )
        except requests.HTTPError as exc:
            failures += 1
            logger.warning("Skipping %s L2M archive: %s", season, exc)
            continue
        if args.max_games:
            game_ids = game_ids[: args.max_games]
        logger.info("Collecting %s L2M reports for %s", len(game_ids), season)

        for index, game_id in enumerate(game_ids, start=1):
            if not args.force and _has_report(conn, game_id):
                continue
            try:
                payload = client.get_l2m_report_json(game_id)
                report_row, event_rows = parse_l2m_payload(payload, game_id, season)
                insert_l2m_rows(conn, report_row, event_rows)
                reports_inserted += 1
                events_inserted += len(event_rows)
            except Exception as exc:
                failures += 1
                logger.warning("L2M %s failed: %s", game_id, exc)

            if index % 25 == 0 or index == len(game_ids):
                logger.info(
                    "Progress %s %s/%s reports=%s events=%s failures=%s",
                    season,
                    index,
                    len(game_ids),
                    reports_inserted,
                    events_inserted,
                    failures,
                )

    write_ingestion_summary(conn, PROJECT_ROOT / args.summary_output)
    logger.info("Done. Inserted %s reports and %s events.", reports_inserted, events_inserted)


def selected_seasons(args: argparse.Namespace) -> list[str]:
    if args.all_seasons:
        return DEFAULT_L2M_SEASONS
    if args.seasons:
        return args.seasons
    return [args.season]


def discover_regular_season_l2m_game_ids(
    season: str,
    regular_season_ids: list[str] | None = None,
) -> list[str]:
    """Read NBA's public season archive and return regular-season L2M game IDs."""
    response = requests.get(
        ARCHIVE_URLS[season],
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    text = response.text
    section = _regular_season_archive_section(text, season)
    ids = re.findall(r"L2MReport\.html\?gameId=(\d{10})", section)
    if not ids:
        ids = re.findall(r"L2MReport\.html\?gameId=(\d{10})", text)
    ids = _regular_season_only(ids, regular_season_ids)
    # Preserve archive order but de-duplicate.
    return list(dict.fromkeys(ids))


def _regular_season_archive_section(text: str, season: str) -> str:
    start_markers = [
        f"{season} NBA Regular Season",
        f"{season} Regular Season",
        "NBA Regular Season",
        "Regular Season",
    ]
    starts = [text.find(marker) for marker in start_markers if text.find(marker) >= 0]
    if not starts:
        return text
    start = min(starts)
    end_markers = ["NBA Play-In", "Play-In", "NBA Playoffs", "Playoffs"]
    ends = [text.find(marker, start + 1) for marker in end_markers if text.find(marker, start + 1) >= 0]
    end = min(ends) if ends else len(text)
    return text[start:end]


def _regular_season_only(
    game_ids: list[str],
    regular_season_ids: list[str] | None,
) -> list[str]:
    if regular_season_ids:
        regular_set = set(regular_season_ids)
        filtered = [game_id for game_id in game_ids if game_id in regular_set]
        # Local game-ID files can be incomplete for older seasons. Only trust
        # the intersection when it preserves most NBA archive links.
        if filtered and len(filtered) >= len(game_ids) * 0.8:
            return filtered
    return [game_id for game_id in game_ids if str(game_id).startswith("002")]


def parse_l2m_payload(
    payload: dict[str, Any], game_id: str, season: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    game = (payload.get("game") or [{}])[0]
    events = payload.get("l2m") or []
    rows = []
    for index, event in enumerate(events):
        decision = str(event.get("CallRatingName") or "").strip().upper()
        rows.append(
            {
                "game_id": game_id,
                "event_index": index,
                "season": season,
                "period": event.get("PeriodName"),
                "game_clock": event.get("PCTime"),
                "call_type": event.get("CallType"),
                "review_decision": decision,
                "incorrect": 1 if decision in {"IC", "INC"} else 0,
                "committing_player": _clean(event.get("CP")),
                "disadvantaged_player": _clean(event.get("DP")),
                "comment": _clean(event.get("Comment")),
                "difficulty": event.get("Difficulty"),
                "possession_id": event.get("posID"),
                "possession_start": event.get("posStart"),
                "possession_end": event.get("posEnd"),
                "team_id_in_favor": event.get("teamIdInFavor"),
                "error_in_favor": event.get("errorInFavor"),
                "video_event_num": event.get("VideolLink"),
            }
        )

    report = {
        "game_id": game_id,
        "season": season,
        "game_date": game.get("GameDate"),
        "home_team_id": game.get("HomeTeamId"),
        "away_team_id": game.get("AwayTeamId"),
        "home_team": game.get("Home_team"),
        "away_team": game.get("Away_team"),
        "home_score": game.get("HomeTeamScore"),
        "away_score": game.get("VisitorTeamScore"),
        "event_count": len(rows),
        "incorrect_count": sum(row["incorrect"] for row in rows),
        "has_report": 1 if rows else 0,
        "comments": _clean(game.get("L2M_Comments")),
    }
    return report, rows


def insert_l2m_rows(
    conn,
    report: dict[str, Any],
    events: list[dict[str, Any]],
) -> None:
    conn.execute("DELETE FROM l2m_events WHERE game_id = ?", (report["game_id"],))
    conn.execute(
        """
        INSERT OR REPLACE INTO l2m_reports (
            game_id, season, game_date, home_team_id, away_team_id, home_team,
            away_team, home_score, away_score, event_count, incorrect_count,
            has_report, comments
        )
        VALUES (
            :game_id, :season, :game_date, :home_team_id, :away_team_id,
            :home_team, :away_team, :home_score, :away_score, :event_count,
            :incorrect_count, :has_report, :comments
        )
        """,
        report,
    )
    conn.executemany(
        """
        INSERT OR REPLACE INTO l2m_events (
            game_id, event_index, season, period, game_clock, call_type,
            review_decision, incorrect, committing_player, disadvantaged_player,
            comment, difficulty, possession_id, possession_start, possession_end,
            team_id_in_favor, error_in_favor, video_event_num
        )
        VALUES (
            :game_id, :event_index, :season, :period, :game_clock, :call_type,
            :review_decision, :incorrect, :committing_player, :disadvantaged_player,
            :comment, :difficulty, :possession_id, :possession_start, :possession_end,
            :team_id_in_favor, :error_in_favor, :video_event_num
        )
        """,
        events,
    )
    conn.commit()


def _has_report(conn, game_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM l2m_reports WHERE game_id = ? LIMIT 1",
        (game_id,),
    ).fetchone()
    return row is not None


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    return unescape(str(value))


def write_ingestion_summary(conn, output_path: Path) -> None:
    rows = conn.execute(
        """
        SELECT
            r.season,
            COUNT(*) AS reports,
            SUM(r.event_count) AS events,
            SUM(r.incorrect_count) AS incorrect,
            AVG(r.incorrect_count * 1.0 / NULLIF(r.event_count, 0)) AS avg_game_error_rate
        FROM l2m_reports r
        WHERE r.has_report = 1
        GROUP BY r.season
        ORDER BY r.season
        """
    ).fetchall()
    lines = [
        "# L2M Ingestion Summary",
        "",
        "| season | reports | events | incorrect | event_error_rate | avg_game_error_rate |",
        "| ------ | ------- | ------ | --------- | ---------------- | ------------------- |",
    ]
    for row in rows:
        events = int(row["events"] or 0)
        incorrect = int(row["incorrect"] or 0)
        event_error_rate = incorrect / events if events else 0
        lines.append(
            "| {season} | {reports:,} | {events:,} | {incorrect:,} | {event_rate:.1%} | {game_rate:.1%} |".format(
                season=row["season"],
                reports=int(row["reports"] or 0),
                events=events,
                incorrect=incorrect,
                event_rate=event_error_rate,
                game_rate=float(row["avg_game_error_rate"] or 0),
            )
        )
    lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

