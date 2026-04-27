#!/usr/bin/env python3
"""Analyze coach challenge alignment with structural L2M risk."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.game_ids import (
    EXPECTED_REGULAR_SEASON_GAME_COUNTS,
    generated_regular_season_game_ids,
    load_regular_season_game_ids,
)
from referee_fatigue.nba_stats_client import NBAStatsClient
from referee_fatigue.taxonomy import (
    CATEGORY_DEFINITIONS,
    POSSESSION_BOUNDARY_ADJUDICATION,
    TIMING_COUNT_JUDGMENT,
    call_detail,
    classify,
)


UNKNOWN_CATEGORY = "unknown_or_unmapped"
UNKNOWN_RAW_TYPE = "Unknown"
ADMIN_ACTION_TYPES = {"Instant Replay", "Substitution", "Timeout"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run coach challenge alignment analysis")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--report-output", default="results/challenge_alignment_report.md")
    parser.add_argument(
        "--event-output",
        default="results/challenge_alignment_events.csv",
    )
    parser.add_argument(
        "--taxonomy-output",
        default="results/challenge_alignment_by_taxonomy.csv",
    )
    parser.add_argument(
        "--raw-type-output",
        default="results/challenge_alignment_by_raw_type.csv",
    )
    parser.add_argument(
        "--resolution-output",
        default="results/challenge_alignment_resolution.csv",
    )
    parser.add_argument(
        "--season-taxonomy-output",
        default="results/challenge_alignment_by_season_taxonomy.csv",
    )
    parser.add_argument(
        "--coverage-output",
        default="results/challenge_coverage_by_season.csv",
    )
    parser.add_argument(
        "--fetch-missing-pages",
        action="store_true",
        help="Fetch NBA game pages when cached page data is missing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)

    challenge_df = load_challenge_events(conn)
    l2m_df = load_l2m_events(conn)
    sori_df = load_sori_scores(PROJECT_ROOT / "results" / "sori_event_scores.csv")

    client = NBAStatsClient(cache_dir=PROJECT_ROOT / "data" / "cache")
    enriched = enrich_challenge_events(
        challenge_df,
        client=client,
        fetch_missing_pages=args.fetch_missing_pages,
    )
    taxonomy_summary = summarize_taxonomy_alignment(enriched, l2m_df, sori_df)
    season_taxonomy_summary = summarize_taxonomy_alignment_by_season(enriched, l2m_df, sori_df)
    raw_type_summary = summarize_raw_types(enriched)
    resolution_summary = summarize_resolution(enriched)
    coverage_summary = summarize_challenge_coverage(enriched, client)
    report = build_report(
        enriched,
        taxonomy_summary,
        season_taxonomy_summary,
        raw_type_summary,
        resolution_summary,
        coverage_summary,
        l2m_df,
        sori_df,
    )

    write_csv(enriched, PROJECT_ROOT / args.event_output)
    write_csv(taxonomy_summary, PROJECT_ROOT / args.taxonomy_output)
    write_csv(season_taxonomy_summary, PROJECT_ROOT / args.season_taxonomy_output)
    write_csv(raw_type_summary, PROJECT_ROOT / args.raw_type_output)
    write_csv(resolution_summary, PROJECT_ROOT / args.resolution_output)
    write_csv(coverage_summary, PROJECT_ROOT / args.coverage_output)
    write_text(report, PROJECT_ROOT / args.report_output)

    print(f"Wrote {PROJECT_ROOT / args.report_output}")
    print(f"Wrote {PROJECT_ROOT / args.event_output}")
    print(f"Wrote {PROJECT_ROOT / args.taxonomy_output}")
    print(f"Wrote {PROJECT_ROOT / args.season_taxonomy_output}")
    print(f"Wrote {PROJECT_ROOT / args.raw_type_output}")
    print(f"Wrote {PROJECT_ROOT / args.resolution_output}")
    print(f"Wrote {PROJECT_ROOT / args.coverage_output}")


def load_challenge_events(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
            game_id,
            event_num,
            season,
            season_type,
            period,
            game_clock,
            description,
            original_ruling,
            final_ruling,
            overturned,
            crew_chief_id,
            challenging_team,
            event_msg_type
        FROM challenge_events
        ORDER BY season, game_id, event_num
        """,
        conn,
    )


def load_l2m_events(conn) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT
            game_id,
            event_index,
            season,
            period,
            game_clock,
            call_type,
            review_decision,
            incorrect
        FROM l2m_events
        WHERE review_decision IN ('CC', 'CNC', 'IC', 'INC')
        """,
        conn,
    )
    if df.empty:
        return df
    out = df.copy()
    out["taxonomy_category"] = out.apply(
        lambda row: classify(row["call_type"], row["review_decision"]),
        axis=1,
    )
    return out


def load_sori_scores(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    required = {"season", "monitoring_type", "sori_score", "incorrect"}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    return df


def enrich_challenge_events(
    df: pd.DataFrame,
    client: NBAStatsClient,
    fetch_missing_pages: bool,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    page_actions_by_game: dict[str, list[dict[str, Any]]] = {}
    rows: list[dict[str, Any]] = []
    for row in df.to_dict("records"):
        game_id = str(row["game_id"])
        if game_id not in page_actions_by_game:
            page_actions_by_game[game_id] = load_page_actions(
                client,
                game_id,
                fetch_missing_pages=fetch_missing_pages,
            )

        actions = page_actions_by_game[game_id]
        challenge_action, challenge_index = find_challenge_action(actions, row)
        challenged_action, resolution_method = resolve_challenged_action(
            actions,
            challenge_action,
            challenge_index,
        )
        mapped = map_challenged_action(challenged_action)

        rows.append(
            {
                **row,
                "challenge_action_number": action_value(challenge_action, "actionNumber"),
                "challenge_action_clock": action_value(challenge_action, "clock"),
                "challenge_action_person_id": action_value(challenge_action, "personId"),
                "resolution_method": resolution_method,
                "challenged_action_number": action_value(challenged_action, "actionNumber"),
                "challenged_period": action_value(challenged_action, "period"),
                "challenged_clock": action_value(challenged_action, "clock"),
                "challenged_action_type": action_value(challenged_action, "actionType"),
                "challenged_action_subtype": action_value(challenged_action, "subType"),
                "challenged_description": action_value(challenged_action, "description"),
                "challenge_raw_type": mapped["raw_type"],
                "taxonomy_category": mapped["taxonomy_category"],
                "taxonomy_label": category_label(mapped["taxonomy_category"]),
                "mapping_note": mapped["mapping_note"],
            }
        )
    return pd.DataFrame(rows)


def load_page_actions(
    client: NBAStatsClient,
    game_id: str,
    fetch_missing_pages: bool,
) -> list[dict[str, Any]]:
    cache_path = nba_game_page_cache_path(client.cache_dir, game_id)
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as handle:
            page_props = json.load(handle)
    elif fetch_missing_pages:
        page_props = client.get_nba_game_page_data(game_id)
    else:
        return []
    return page_props.get("playByPlay", {}).get("actions", []) or []


def nba_game_page_cache_path(cache_dir: Path, game_id: str) -> Path:
    payload = {"endpoint": "nba_game_page", "params": {"GameID": game_id}}
    cache_key = hashlib.md5(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return cache_dir / f"{cache_key}.json"


def play_by_play_cache_path(cache_dir: Path, game_id: str) -> Path:
    payload = {
        "endpoint": "playbyplayv2",
        "params": {
            "GameID": game_id,
            "StartPeriod": "1",
            "EndPeriod": "10",
        },
    }
    cache_key = hashlib.md5(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return cache_dir / f"{cache_key}.json"


def find_challenge_action(
    actions: list[dict[str, Any]],
    row: dict[str, Any],
) -> tuple[dict[str, Any] | None, int | None]:
    event_num = to_int(row.get("event_num"))
    if event_num is None:
        return None, None
    matches = [
        (index, action)
        for index, action in enumerate(actions)
        if to_int(action.get("actionNumber")) == event_num
    ]
    for index, action in matches:
        if action.get("actionType") == "Instant Replay":
            return action, index
    if matches:
        return matches[-1][1], matches[-1][0]
    return None, None


def resolve_challenged_action(
    actions: list[dict[str, Any]],
    challenge_action: dict[str, Any] | None,
    challenge_index: int | None,
) -> tuple[dict[str, Any] | None, str]:
    if not actions or challenge_action is None or challenge_index is None:
        return None, "unresolved_missing_page_action"

    referenced_number = to_int(challenge_action.get("personId"))
    if referenced_number and referenced_number > 0:
        referenced = best_action_for_number(actions, referenced_number)
        if referenced is not None:
            return referenced, "person_id_action_number"

    same_clock = previous_play_action(
        actions,
        challenge_index,
        same_period=challenge_action.get("period"),
        same_clock=challenge_action.get("clock"),
    )
    if same_clock is not None:
        return same_clock, "previous_same_clock"

    previous = previous_play_action(actions, challenge_index)
    if previous is not None:
        return previous, "previous_play"

    return None, "unresolved_no_candidate"


def best_action_for_number(
    actions: list[dict[str, Any]],
    action_number: int,
) -> dict[str, Any] | None:
    matches = [
        action
        for action in actions
        if to_int(action.get("actionNumber")) == action_number
        and action.get("actionType") not in ADMIN_ACTION_TYPES
    ]
    if not matches:
        return None
    with_action_type = [action for action in matches if action.get("actionType")]
    return (with_action_type or matches)[0]


def previous_play_action(
    actions: list[dict[str, Any]],
    challenge_index: int,
    same_period: Any | None = None,
    same_clock: Any | None = None,
    lookback: int = 12,
) -> dict[str, Any] | None:
    start = max(0, challenge_index - lookback)
    for action in reversed(actions[start:challenge_index]):
        if action.get("actionType") in ADMIN_ACTION_TYPES:
            continue
        if not action.get("actionType"):
            continue
        if same_period is not None and action.get("period") != same_period:
            continue
        if same_clock is not None and action.get("clock") != same_clock:
            continue
        return action
    return None


def map_challenged_action(action: dict[str, Any] | None) -> dict[str, str]:
    if action is None:
        return {
            "raw_type": UNKNOWN_RAW_TYPE,
            "taxonomy_category": UNKNOWN_CATEGORY,
            "mapping_note": "No challenged play could be resolved from cached play-by-play.",
        }

    action_type = str(action.get("actionType") or "").strip()
    subtype = str(action.get("subType") or "").strip()
    description = str(action.get("description") or "").strip()
    text = f"{action_type} {subtype} {description}".lower()

    if not action_type:
        return unknown_mapping("Resolved action has no action type.")
    if action_type == "Rebound":
        return {
            "raw_type": raw_type(action_type, subtype),
            "taxonomy_category": POSSESSION_BOUNDARY_ADJUDICATION,
            "mapping_note": "Rebound-linked challenges usually adjudicate possession or boundary state.",
        }
    if action_type in {"Made Shot", "Missed Shot", "Free Throw"}:
        if "goaltending" in text or "basket interference" in text:
            call_type = raw_type("Violation", subtype or "Goaltending")
            return classified_mapping(call_type, "Shot-linked goaltending or basket-interference challenge.")
        return unknown_mapping(
            "Shot/free-throw linked challenge lacks enough text to infer the challenged ruling."
        )
    if action_type == "Jump Ball":
        return classified_mapping("Stoppage: Jump Ball", "Jump-ball challenge mapped as stoppage administration.")
    if action_type == "Turnover" and "shot clock" in text:
        return {
            "raw_type": "Turnover: 24 Second Violation",
            "taxonomy_category": TIMING_COUNT_JUDGMENT,
            "mapping_note": "Shot-clock turnover mapped to timing/count judgment.",
        }
    if action_type == "Turnover" and "step out of bounds" in text:
        call_type = "Turnover: Stepped out of Bounds"
        return classified_mapping(call_type, "Step-out turnover mapped to possession/boundary adjudication.")

    call_type = raw_type(action_type, subtype)
    return classified_mapping(call_type, "Mapped from challenged action type and subtype.")


def raw_type(action_type: str, subtype: str | None) -> str:
    subtype = str(subtype or "").strip()
    if subtype and subtype.lower() != "unknown":
        return f"{action_type}: {subtype}"
    return action_type


def classified_mapping(call_type: str, note: str) -> dict[str, str]:
    return {
        "raw_type": call_type,
        "taxonomy_category": classify(call_type),
        "mapping_note": note,
    }


def unknown_mapping(note: str) -> dict[str, str]:
    return {
        "raw_type": UNKNOWN_RAW_TYPE,
        "taxonomy_category": UNKNOWN_CATEGORY,
        "mapping_note": note,
    }


def summarize_taxonomy_alignment(
    challenge_df: pd.DataFrame,
    l2m_df: pd.DataFrame,
    sori_df: pd.DataFrame,
) -> pd.DataFrame:
    if challenge_df.empty:
        return pd.DataFrame()

    challenge_summary = (
        challenge_df.groupby("taxonomy_category", dropna=False)
        .agg(
            challenges=("overturned", "size"),
            overturned=("overturned", "sum"),
            overturn_rate=("overturned", "mean"),
        )
        .reset_index()
    )
    challenge_summary["challenge_share"] = (
        challenge_summary["challenges"] / challenge_summary["challenges"].sum()
    )
    challenge_summary["taxonomy_label"] = challenge_summary["taxonomy_category"].map(category_label)

    challenge_seasons = sorted(challenge_df["season"].dropna().unique())
    l2m_same_seasons = l2m_df[l2m_df["season"].isin(challenge_seasons)].copy()

    same_season_summary = summarize_l2m_by_category(
        l2m_same_seasons,
        prefix="same_season_l2m",
    )
    all_season_summary = summarize_l2m_by_category(l2m_df, prefix="all_l2m")
    sori_summary = summarize_sori_by_category(sori_df, challenge_seasons)

    out = challenge_summary.merge(
        same_season_summary,
        on="taxonomy_category",
        how="left",
    ).merge(
        all_season_summary,
        on="taxonomy_category",
        how="left",
    ).merge(
        sori_summary,
        on="taxonomy_category",
        how="left",
    )

    out["challenge_minus_same_season_l2m_share"] = (
        out["challenge_share"] - out["same_season_l2m_event_share"]
    )
    return out.sort_values(["challenges", "overturn_rate"], ascending=[False, False])


def summarize_l2m_by_category(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    columns = [
        "taxonomy_category",
        f"{prefix}_events",
        f"{prefix}_incorrect",
        f"{prefix}_error_rate",
        f"{prefix}_event_share",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        df.groupby("taxonomy_category", dropna=False)
        .agg(events=("incorrect", "size"), incorrect=("incorrect", "sum"), error_rate=("incorrect", "mean"))
        .reset_index()
    )
    summary["event_share"] = summary["events"] / summary["events"].sum()
    return summary.rename(
        columns={
            "events": f"{prefix}_events",
            "incorrect": f"{prefix}_incorrect",
            "error_rate": f"{prefix}_error_rate",
            "event_share": f"{prefix}_event_share",
        }
    )[columns]


def summarize_taxonomy_alignment_by_season(
    challenge_df: pd.DataFrame,
    l2m_df: pd.DataFrame,
    sori_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "season",
        "taxonomy_category",
        "taxonomy_label",
        "challenges",
        "overturned",
        "overturn_rate",
        "challenge_share",
        "l2m_events",
        "l2m_incorrect",
        "l2m_error_rate",
        "l2m_event_share",
        "mean_sori",
        "challenge_minus_l2m_event_share",
    ]
    if challenge_df.empty:
        return pd.DataFrame(columns=columns)

    challenge_summary = (
        challenge_df.groupby(["season", "taxonomy_category"], dropna=False)
        .agg(
            challenges=("overturned", "size"),
            overturned=("overturned", "sum"),
            overturn_rate=("overturned", "mean"),
        )
        .reset_index()
    )
    challenge_totals = challenge_summary.groupby("season")["challenges"].transform("sum")
    challenge_summary["challenge_share"] = challenge_summary["challenges"] / challenge_totals
    challenge_summary["taxonomy_label"] = challenge_summary["taxonomy_category"].map(category_label)

    l2m_summary = (
        l2m_df.groupby(["season", "taxonomy_category"], dropna=False)
        .agg(
            l2m_events=("incorrect", "size"),
            l2m_incorrect=("incorrect", "sum"),
            l2m_error_rate=("incorrect", "mean"),
        )
        .reset_index()
    )
    if not l2m_summary.empty:
        l2m_totals = l2m_summary.groupby("season")["l2m_events"].transform("sum")
        l2m_summary["l2m_event_share"] = l2m_summary["l2m_events"] / l2m_totals

    if sori_df.empty:
        sori_summary = pd.DataFrame(columns=["season", "taxonomy_category", "mean_sori"])
    else:
        sori_summary = (
            sori_df.groupby(["season", "monitoring_type"], dropna=False)
            .agg(mean_sori=("sori_score", "mean"))
            .reset_index()
            .rename(columns={"monitoring_type": "taxonomy_category"})
        )

    out = challenge_summary.merge(
        l2m_summary,
        on=["season", "taxonomy_category"],
        how="left",
    ).merge(
        sori_summary,
        on=["season", "taxonomy_category"],
        how="left",
    )
    out["challenge_minus_l2m_event_share"] = out["challenge_share"] - out["l2m_event_share"]
    return out[columns].sort_values(["season", "challenges"], ascending=[True, False])


def summarize_challenge_coverage(
    challenge_df: pd.DataFrame,
    client: NBAStatsClient,
) -> pd.DataFrame:
    seasons = sorted(challenge_df["season"].dropna().unique()) if not challenge_df.empty else []
    if not seasons:
        return pd.DataFrame()

    game_ids_by_season = load_regular_season_game_ids(seasons, PROJECT_ROOT)
    rows = []
    challenge_by_season = (
        challenge_df.groupby("season")
        .agg(
            games_with_challenges=("game_id", "nunique"),
            challenge_events=("game_id", "size"),
            overturn_rate=("overturned", "mean"),
        )
        .reset_index()
        .set_index("season")
    )
    for season in seasons:
        game_ids = game_ids_by_season.get(season, [])
        generated_game_ids = generated_regular_season_game_ids(season)
        if generated_game_ids and len(generated_game_ids) > len(game_ids):
            game_ids = generated_game_ids
        elif not game_ids:
            game_ids = sorted(challenge_df.loc[challenge_df["season"] == season, "game_id"].astype(str).unique())
        cached_pages = sum(
            nba_game_page_cache_path(client.cache_dir, game_id).exists()
            for game_id in game_ids
        )
        cached_pbp = sum(
            play_by_play_cache_path(client.cache_dir, game_id).exists()
            for game_id in game_ids
        )
        cached_any = sum(
            nba_game_page_cache_path(client.cache_dir, game_id).exists()
            or play_by_play_cache_path(client.cache_dir, game_id).exists()
            for game_id in game_ids
        )
        challenge_row = challenge_by_season.loc[season] if season in challenge_by_season.index else None
        games_with_challenges = int(challenge_row["games_with_challenges"]) if challenge_row is not None else 0
        challenge_events = int(challenge_row["challenge_events"]) if challenge_row is not None else 0
        overturn_rate = float(challenge_row["overturn_rate"]) if challenge_row is not None else None
        source_games = len(game_ids)
        expected_games = EXPECTED_REGULAR_SEASON_GAME_COUNTS.get(season, source_games)
        rows.append(
            {
                "season": season,
                "expected_regular_season_games": expected_games,
                "source_games": source_games,
                "source_game_coverage_rate": safe_divide(source_games, expected_games),
                "cached_nba_page_games": cached_pages,
                "cached_playbyplay_games": cached_pbp,
                "cached_any_games": cached_any,
                "cached_expected_coverage_rate": safe_divide(cached_any, expected_games),
                "cache_coverage_rate": safe_divide(cached_any, source_games),
                "games_with_challenges": games_with_challenges,
                "challenge_events": challenge_events,
                "challenge_games_per_cached_game": safe_divide(games_with_challenges, cached_any),
                "challenges_per_cached_game": safe_divide(challenge_events, cached_any),
                "overturn_rate": overturn_rate,
            }
        )
    return pd.DataFrame(rows)


def summarize_sori_by_category(
    sori_df: pd.DataFrame,
    challenge_seasons: list[str],
) -> pd.DataFrame:
    columns = ["taxonomy_category", "same_season_mean_sori", "all_season_mean_sori"]
    if sori_df.empty:
        return pd.DataFrame(columns=columns)

    all_summary = (
        sori_df.groupby("monitoring_type", dropna=False)
        .agg(all_season_mean_sori=("sori_score", "mean"))
        .reset_index()
        .rename(columns={"monitoring_type": "taxonomy_category"})
    )
    same = sori_df[sori_df["season"].isin(challenge_seasons)].copy()
    if same.empty:
        same_summary = pd.DataFrame(columns=["taxonomy_category", "same_season_mean_sori"])
    else:
        same_summary = (
            same.groupby("monitoring_type", dropna=False)
            .agg(same_season_mean_sori=("sori_score", "mean"))
            .reset_index()
            .rename(columns={"monitoring_type": "taxonomy_category"})
        )
    return same_summary.merge(all_summary, on="taxonomy_category", how="outer")[columns]


def summarize_raw_types(challenge_df: pd.DataFrame, min_challenges: int = 5) -> pd.DataFrame:
    if challenge_df.empty:
        return pd.DataFrame()
    summary = (
        challenge_df.groupby(["challenge_raw_type", "taxonomy_category"], dropna=False)
        .agg(
            challenges=("overturned", "size"),
            overturned=("overturned", "sum"),
            overturn_rate=("overturned", "mean"),
        )
        .reset_index()
    )
    summary["challenge_share"] = summary["challenges"] / summary["challenges"].sum()
    summary["call_detail"] = summary["challenge_raw_type"].map(call_detail)
    summary = summary[summary["challenges"] >= min_challenges].copy()
    return summary.sort_values(["challenges", "overturn_rate"], ascending=[False, False])


def summarize_resolution(challenge_df: pd.DataFrame) -> pd.DataFrame:
    if challenge_df.empty:
        return pd.DataFrame()
    summary = (
        challenge_df.groupby("resolution_method", dropna=False)
        .agg(challenges=("overturned", "size"), overturn_rate=("overturned", "mean"))
        .reset_index()
    )
    summary["challenge_share"] = summary["challenges"] / summary["challenges"].sum()
    return summary.sort_values("challenges", ascending=False)


def build_report(
    challenge_df: pd.DataFrame,
    taxonomy_summary: pd.DataFrame,
    season_taxonomy_summary: pd.DataFrame,
    raw_type_summary: pd.DataFrame,
    resolution_summary: pd.DataFrame,
    coverage_summary: pd.DataFrame,
    l2m_df: pd.DataFrame,
    sori_df: pd.DataFrame,
) -> str:
    if challenge_df.empty:
        return "\n".join(
            [
                "# Challenge Alignment Analysis",
                "",
                "No challenge events are available in the local database.",
                "",
                "Run `python scripts/extract_challenge_events.py` before this analysis.",
                "",
            ]
        )

    seasons = sorted(challenge_df["season"].dropna().unique())
    mapped = challenge_df[challenge_df["taxonomy_category"] != UNKNOWN_CATEGORY]
    unknown_count = len(challenge_df) - len(mapped)
    top_category = top_taxonomy_category(taxonomy_summary)
    highest_overturn = top_overturn_category(taxonomy_summary)
    challenge_periods = challenge_df["period"].dropna().astype(int)
    l2m_same_seasons = l2m_df[l2m_df["season"].isin(seasons)].copy()

    lines = [
        "# Challenge Alignment Analysis",
        "",
        "## Headline",
        "",
        f"- Challenge events analyzed: **{len(challenge_df):,}**",
        f"- Challenge seasons covered locally: **{season_range(seasons)}**",
        f"- Baseline overturn rate: **{challenge_df['overturned'].mean():.1%}**",
        f"- Challenges mapped to a structural category: **{len(mapped):,} ({len(mapped) / len(challenge_df):.1%})**",
        f"- Unknown/unmapped challenge links: **{unknown_count:,} ({unknown_count / len(challenge_df):.1%})**",
        f"- Most challenged structural category: **{top_category}**",
        f"- Highest-overturn structural category: **{highest_overturn}**",
        "",
        "## Structural Alignment",
        "",
        dataframe_to_markdown(report_taxonomy_columns(taxonomy_summary)),
        "",
        "## Coverage By Season",
        "",
        dataframe_to_markdown(report_coverage_columns(coverage_summary)),
        "",
        "## Season Stability",
        "",
        dataframe_to_markdown(report_season_taxonomy_columns(season_taxonomy_summary)),
        "",
        "## Most Common Challenged Raw Types",
        "",
        dataframe_to_markdown(report_raw_type_columns(raw_type_summary.head(15))),
        "",
        "## Challenge Resolution Quality",
        "",
        dataframe_to_markdown(resolution_summary),
        "",
        "## Coverage And Comparison Notes",
        "",
        coverage_notes(challenge_df, l2m_df, l2m_same_seasons, sori_df, challenge_periods),
        "",
        "## Interpretation",
        "",
        interpretation(taxonomy_summary),
        "",
        "## Outputs",
        "",
        "- `results/challenge_alignment_events.csv`: event-level challenge mapping.",
        "- `results/challenge_alignment_by_taxonomy.csv`: taxonomy-level challenge, L2M, and SORI comparison.",
        "- `results/challenge_alignment_by_season_taxonomy.csv`: season-by-season taxonomy alignment.",
        "- `results/challenge_alignment_by_raw_type.csv`: raw challenged action type summary.",
        "- `results/challenge_alignment_resolution.csv`: mapping-resolution summary.",
        "- `results/challenge_coverage_by_season.csv`: challenge data coverage by season.",
        "",
    ]
    return "\n".join(lines)


def report_taxonomy_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "taxonomy_category",
        "taxonomy_label",
        "challenges",
        "challenge_share",
        "overturn_rate",
        "same_season_l2m_error_rate",
        "same_season_l2m_event_share",
        "same_season_mean_sori",
        "challenge_minus_same_season_l2m_share",
    ]
    available = [column for column in columns if column in df.columns]
    return df[available].copy()


def report_raw_type_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "challenge_raw_type",
        "taxonomy_category",
        "challenges",
        "challenge_share",
        "overturn_rate",
    ]
    available = [column for column in columns if column in df.columns]
    return df[available].copy()


def report_coverage_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "season",
        "expected_regular_season_games",
        "source_games",
        "source_game_coverage_rate",
        "cached_any_games",
        "cached_expected_coverage_rate",
        "cache_coverage_rate",
        "games_with_challenges",
        "challenge_events",
        "challenges_per_cached_game",
        "overturn_rate",
    ]
    available = [column for column in columns if column in df.columns]
    return df[available].copy()


def report_season_taxonomy_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    focus = df[df["taxonomy_category"].isin([POSSESSION_BOUNDARY_ADJUDICATION, "ordinary_contact_foul", TIMING_COUNT_JUDGMENT])].copy()
    columns = [
        "season",
        "taxonomy_category",
        "challenges",
        "challenge_share",
        "overturn_rate",
        "l2m_error_rate",
        "mean_sori",
    ]
    available = [column for column in columns if column in focus.columns]
    return focus[available].copy()


def coverage_notes(
    challenge_df: pd.DataFrame,
    l2m_df: pd.DataFrame,
    l2m_same_seasons: pd.DataFrame,
    sori_df: pd.DataFrame,
    challenge_periods: pd.Series,
) -> str:
    seasons = sorted(challenge_df["season"].dropna().unique())
    l2m_seasons = sorted(l2m_df["season"].dropna().unique()) if not l2m_df.empty else []
    period_note = "n/a"
    if not challenge_periods.empty:
        l2m_window_share = (challenge_periods >= 4).mean()
        period_note = f"{l2m_window_share:.1%} occurred in period 4 or later"

    sori_note = "SORI scores were available and joined by taxonomy category."
    if sori_df.empty:
        sori_note = "SORI scores were not available, so the comparison uses observed L2M rates only."

    return "\n".join(
        [
            (
                f"The local challenge table currently covers {season_range(seasons)}, "
                f"while the L2M event table covers {season_range(l2m_seasons)}."
            ),
            (
                f"Same-season L2M comparison rows: {len(l2m_same_seasons):,}; "
                f"all L2M comparison rows: {len(l2m_df):,}."
            ),
            (
                "Challenge events are full-game replay events, not only L2M-window "
                f"events; {period_note}. Interpret category comparisons as alignment "
                "evidence, not a direct denominator-matched conversion rate."
            ),
            sori_note,
        ]
    )


def interpretation(taxonomy_summary: pd.DataFrame) -> str:
    if taxonomy_summary.empty:
        return "No taxonomy-level challenge summary could be produced."

    known = taxonomy_summary[taxonomy_summary["taxonomy_category"] != UNKNOWN_CATEGORY].copy()
    if known.empty:
        return (
            "The current extraction identifies challenge outcomes but does not yet expose "
            "enough challenged-play context to test alignment."
        )

    possession = known[
        known["taxonomy_category"] == POSSESSION_BOUNDARY_ADJUDICATION
    ]
    ordinary = known[known["taxonomy_category"] == "ordinary_contact_foul"]
    unknown = taxonomy_summary[
        taxonomy_summary["taxonomy_category"] == UNKNOWN_CATEGORY
    ]
    timing = known[known["taxonomy_category"] == TIMING_COUNT_JUDGMENT]

    parts = []
    if not possession.empty:
        row = possession.iloc[0]
        parts.append(
            "Possession/boundary decisions are a major challenge target "
            f"({row['challenge_share']:.1%} of challenges, "
            f"{row['overturn_rate']:.1%} overturn rate)."
        )
    if not ordinary.empty:
        row = ordinary.iloc[0]
        parts.append(
            "Ordinary contact fouls remain heavily represented in challenge behavior "
            f"({row['challenge_share']:.1%} of challenges), even though L2M reviewed "
            "ordinary contact has a comparatively low observed error rate."
        )
    if not timing.empty:
        row = timing.iloc[0]
        parts.append(
            "Timing/count decisions remain rare in the challenge sample "
            f"({row['challenge_share']:.1%} of challenges) despite elevated L2M "
            "risk, which points toward challengeability or live-detection limits "
            "more than an obvious coaching edge."
        )
    if not unknown.empty and float(unknown.iloc[0]["challenge_share"]) > 0.05:
        parts.append(
            "A non-trivial unknown bucket remains because shot/free-throw-linked replay "
            "rows often do not say what ruling was challenged."
        )
    parts.append(
        "The Sloan-safe claim is that challenge behavior can now be compared against "
        "structural L2M risk, but the full-game challenge sample is narrower than the "
        "JSON-era L2M sample and is not denominator-matched to all challengeable events."
    )
    return " ".join(parts)


def top_taxonomy_category(df: pd.DataFrame) -> str:
    if df.empty:
        return "n/a"
    row = df.sort_values("challenges", ascending=False).iloc[0]
    return f"{row['taxonomy_category']} ({int(row['challenges']):,}, {row['challenge_share']:.1%})"


def top_overturn_category(df: pd.DataFrame) -> str:
    if df.empty:
        return "n/a"
    eligible = df[
        (df["challenges"] >= 20)
        & (df["taxonomy_category"] != UNKNOWN_CATEGORY)
    ].copy()
    if eligible.empty:
        eligible = df[df["taxonomy_category"] != UNKNOWN_CATEGORY].copy()
    if eligible.empty:
        eligible = df
    row = eligible.sort_values(["overturn_rate", "challenges"], ascending=[False, False]).iloc[0]
    return f"{row['taxonomy_category']} ({row['overturn_rate']:.1%}, n={int(row['challenges']):,})"


def category_label(category: str) -> str:
    if category == UNKNOWN_CATEGORY:
        return "Unknown or unmapped"
    definition = CATEGORY_DEFINITIONS.get(category)
    return definition.label if definition else category


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate") or column.endswith("share") or column.endswith("sori"):
            formatted[column] = formatted[column].map(format_percent_or_blank)
        elif column.endswith("gap") or column.startswith("challenge_minus"):
            formatted[column] = formatted[column].map(format_signed_percent_or_blank)
        elif column.endswith("_per_cached_game"):
            formatted[column] = formatted[column].map(format_number_or_blank)
    headers = list(formatted.columns)
    rows = formatted.fillna("").astype(str).values.tolist()
    widths = [
        max(len(str(header)), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    lines = [
        "| " + " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers)) + " |",
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(row[index].ljust(widths[index]) for index in range(len(headers))) + " |"
        )
    return "\n".join(lines)


def format_percent_or_blank(value: Any) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.1%}"


def format_signed_percent_or_blank(value: Any) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):+.1%}"


def format_number_or_blank(value: Any) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.2f}"


def season_range(seasons: list[str]) -> str:
    if not seasons:
        return "none"
    if len(seasons) == 1:
        return seasons[0]
    return f"{seasons[0]} to {seasons[-1]}"


def safe_divide(numerator: int | float, denominator: int | float) -> float | None:
    if denominator in (0, None) or pd.isna(denominator):
        return None
    return float(numerator) / float(denominator)


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def action_value(action: dict[str, Any] | None, key: str) -> Any:
    if action is None:
        return None
    return action.get(key)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
