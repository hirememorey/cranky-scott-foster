"""Game pace and late-game action-density features."""

from __future__ import annotations

import re
from typing import Any


def compute_game_pace_features(
    page_props: dict[str, Any],
    game_id: str,
    season: str,
) -> dict[str, Any]:
    """Compute possession-based and action-density pace proxies."""
    game = page_props.get("game", {})
    home_stats = game.get("homeTeam", {}).get("statistics", {})
    away_stats = game.get("awayTeam", {}).get("statistics", {})
    actions = page_props.get("playByPlay", {}).get("actions", [])

    home_possessions = estimate_team_possessions(home_stats)
    away_possessions = estimate_team_possessions(away_stats)
    estimated_possessions = (home_possessions + away_possessions) / 2
    game_minutes = parse_team_minutes(home_stats.get("minutes")) / 5
    estimated_pace = (
        estimated_possessions * 48 / game_minutes
        if game_minutes and game_minutes > 0
        else None
    )

    total_actions = len(actions)
    q4_actions = [
        action for action in actions if int(action.get("period") or 0) == 4
    ]
    q4_pre_l2m_actions = [
        action
        for action in q4_actions
        if (clock_seconds_remaining(action.get("clock")) or 0) > 120
    ]
    l2m_actions = [
        action
        for action in actions
        if _is_l2m_window(action)
    ]

    return {
        "game_id": game_id,
        "season": season,
        "game_minutes": game_minutes,
        "estimated_possessions": estimated_possessions,
        "estimated_pace": estimated_pace,
        "total_actions": total_actions,
        "actions_per_minute": total_actions / game_minutes if game_minutes else None,
        "q4_actions": len(q4_actions),
        "q4_actions_per_minute": len(q4_actions) / 12,
        "q4_pre_l2m_actions": len(q4_pre_l2m_actions),
        "q4_pre_l2m_actions_per_minute": len(q4_pre_l2m_actions) / 10,
        "l2m_actions": len(l2m_actions),
        "l2m_actions_per_minute": len(l2m_actions) / max(l2m_window_minutes(actions), 1),
        "q4_shots": count_action_type(q4_actions, {"2pt", "3pt"}),
        "q4_fouls": count_action_type(q4_actions, {"foul"}),
        "q4_turnovers": count_action_type(q4_actions, {"turnover"}),
    }


def estimate_team_possessions(stats: dict[str, Any]) -> float:
    """Basketball-Reference-style possession estimate from team box score."""
    return (
        float(stats.get("fieldGoalsAttempted") or 0)
        + 0.44 * float(stats.get("freeThrowsAttempted") or 0)
        - float(stats.get("reboundsOffensive") or 0)
        + float(stats.get("turnovers") or 0)
    )


def parse_team_minutes(value: Any) -> float:
    """Parse team minutes like '240:00' into decimal minutes."""
    if value is None:
        return 0
    text = str(value)
    if ":" not in text:
        return float(text)
    minutes, seconds = text.split(":", 1)
    return float(minutes) + float(seconds) / 60


def clock_seconds_remaining(clock: Any) -> float | None:
    """Parse NBA ISO-ish clock strings like PT01M53.90S."""
    if clock is None:
        return None
    match = re.match(r"PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", str(clock))
    if not match:
        return None
    minutes = float(match.group(1) or 0)
    seconds = float(match.group(2) or 0)
    return minutes * 60 + seconds


def count_action_type(actions: list[dict[str, Any]], action_types: set[str]) -> int:
    """Count matching normalized action types."""
    return sum(
        1
        for action in actions
        if str(action.get("actionType") or "").lower() in action_types
    )


def l2m_window_minutes(actions: list[dict[str, Any]]) -> float:
    """Estimate total L2M-observed minutes including overtime periods."""
    periods = {int(action.get("period") or 0) for action in actions}
    minutes = 2 if 4 in periods else 0
    minutes += 2 * sum(1 for period in periods if period >= 5)
    return float(minutes or 2)


def _is_l2m_window(action: dict[str, Any]) -> bool:
    period = int(action.get("period") or 0)
    seconds_remaining = clock_seconds_remaining(action.get("clock"))
    if seconds_remaining is None:
        return False
    return period >= 4 and seconds_remaining <= 120

