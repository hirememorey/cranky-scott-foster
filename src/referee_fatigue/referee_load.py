"""Feature engineering for referee workload."""

from __future__ import annotations

import math
import sqlite3

import pandas as pd

from referee_fatigue.arena_locations import ARENA_LOCATIONS_BY_TEAM_ID


def compute_referee_load_features(conn: sqlite3.Connection) -> pd.DataFrame:
    """Compute days rest and rolling assignment counts for each referee-game."""
    assignments = pd.read_sql_query(
        """
        SELECT game_id, official_id, game_date, season, home_team_id
        FROM referee_assignments
        WHERE game_date IS NOT NULL
        ORDER BY official_id, game_date, game_id
        """,
        conn,
    )
    if assignments.empty:
        return pd.DataFrame(
            columns=[
                "game_id",
                "official_id",
                "game_date",
                "season",
                "days_rest",
                "back_to_back",
                "games_last_7",
                "games_last_14",
                "home_team_id",
                "arena_lat",
                "arena_lon",
                "arena_tz_offset",
                "prev_game_id",
                "prev_game_date",
                "prev_home_team_id",
                "travel_miles_since_last",
                "time_zones_crossed_since_last",
                "travel_miles_last_3_days",
                "travel_miles_last_7_days",
                "time_zones_crossed_last_3_days",
                "time_zones_crossed_last_7_days",
            ]
        )

    assignments["game_date"] = pd.to_datetime(assignments["game_date"]).dt.normalize()
    assignments = assignments.dropna(subset=["game_date"])
    assignments = add_arena_metadata(assignments)

    feature_frames = []
    for _, group in assignments.groupby("official_id", sort=False):
        group = group.sort_values(["game_date", "game_id"]).copy()
        records = group.to_dict("records")
        days_rest = []
        games_last_7 = []
        games_last_14 = []
        prev_game_ids = []
        prev_game_dates = []
        prev_home_team_ids = []
        travel_since_last = []
        tz_crossed_since_last = []
        travel_last_3 = []
        travel_last_7 = []
        tz_last_3 = []
        tz_last_7 = []

        for index, current in enumerate(records):
            current_date = current["game_date"]
            previous_records = records[:index]
            previous = previous_records[-1] if previous_records else None

            if previous is not None:
                days_rest.append((current_date - previous["game_date"]).days)
                prev_game_ids.append(previous["game_id"])
                prev_game_dates.append(previous["game_date"])
                prev_home_team_ids.append(previous["home_team_id"])
                segment_miles = haversine_miles(
                    previous["arena_lat"],
                    previous["arena_lon"],
                    current["arena_lat"],
                    current["arena_lon"],
                )
                segment_tz_crossed = abs(
                    int(current["arena_tz_offset"]) - int(previous["arena_tz_offset"])
                )
            else:
                days_rest.append(pd.NA)
                prev_game_ids.append(None)
                prev_game_dates.append(pd.NaT)
                prev_home_team_ids.append(None)
                segment_miles = 0.0
                segment_tz_crossed = 0

            travel_since_last.append(segment_miles)
            tz_crossed_since_last.append(segment_tz_crossed)

            recent_segments = []
            for previous_index, record in enumerate(records[: index + 1]):
                if previous_index == 0:
                    continue
                days_since_segment_end = (current_date - record["game_date"]).days
                if days_since_segment_end >= 0:
                    previous_record = records[previous_index - 1]
                    recent_segments.append(
                        {
                            "days_since": days_since_segment_end,
                            "miles": haversine_miles(
                                previous_record["arena_lat"],
                                previous_record["arena_lon"],
                                record["arena_lat"],
                                record["arena_lon"],
                            ),
                            "tz_crossed": abs(
                                int(record["arena_tz_offset"])
                                - int(previous_record["arena_tz_offset"])
                            ),
                        }
                    )

            games_last_7.append(
                sum(
                    0 < (current_date - record["game_date"]).days <= 7
                    for record in previous_records
                )
            )
            games_last_14.append(
                sum(
                    0 < (current_date - record["game_date"]).days <= 14
                    for record in previous_records
                )
            )
            travel_last_3.append(
                sum(segment["miles"] for segment in recent_segments if segment["days_since"] <= 3)
            )
            travel_last_7.append(
                sum(segment["miles"] for segment in recent_segments if segment["days_since"] <= 7)
            )
            tz_last_3.append(
                sum(
                    segment["tz_crossed"]
                    for segment in recent_segments
                    if segment["days_since"] <= 3
                )
            )
            tz_last_7.append(
                sum(
                    segment["tz_crossed"]
                    for segment in recent_segments
                    if segment["days_since"] <= 7
                )
            )

        group["days_rest"] = days_rest
        group["back_to_back"] = group["days_rest"].eq(1).fillna(False).astype(int)
        group["games_last_7"] = games_last_7
        group["games_last_14"] = games_last_14
        group["prev_game_id"] = prev_game_ids
        group["prev_game_date"] = prev_game_dates
        group["prev_home_team_id"] = prev_home_team_ids
        group["travel_miles_since_last"] = travel_since_last
        group["time_zones_crossed_since_last"] = tz_crossed_since_last
        group["travel_miles_last_3_days"] = travel_last_3
        group["travel_miles_last_7_days"] = travel_last_7
        group["time_zones_crossed_last_3_days"] = tz_last_3
        group["time_zones_crossed_last_7_days"] = tz_last_7
        feature_frames.append(group)

    features = pd.concat(feature_frames, ignore_index=True)
    features["game_date"] = features["game_date"].dt.strftime("%Y-%m-%d")
    features["prev_game_date"] = pd.to_datetime(features["prev_game_date"]).dt.strftime("%Y-%m-%d")
    features["prev_game_date"] = features["prev_game_date"].where(
        features["prev_game_date"].notna(), None
    )
    return features[
        [
            "game_id",
            "official_id",
            "game_date",
            "season",
            "days_rest",
            "back_to_back",
            "games_last_7",
            "games_last_14",
            "home_team_id",
            "arena_lat",
            "arena_lon",
            "arena_tz_offset",
            "prev_game_id",
            "prev_game_date",
            "prev_home_team_id",
            "travel_miles_since_last",
            "time_zones_crossed_since_last",
            "travel_miles_last_3_days",
            "travel_miles_last_7_days",
            "time_zones_crossed_last_3_days",
            "time_zones_crossed_last_7_days",
        ]
    ]


def persist_referee_load_features(conn: sqlite3.Connection, features: pd.DataFrame) -> int:
    """Write referee load features to SQLite."""
    conn.execute("DELETE FROM referee_load_features")
    if features.empty:
        conn.commit()
        return 0

    clean = features.copy()
    clean["days_rest"] = clean["days_rest"].where(clean["days_rest"].notna(), None)
    clean = clean.where(pd.notna(clean), None)
    rows = clean.to_dict("records")
    conn.executemany(
        """
        INSERT OR REPLACE INTO referee_load_features (
            game_id, official_id, game_date, season, days_rest,
            back_to_back, games_last_7, games_last_14, home_team_id,
            arena_lat, arena_lon, arena_tz_offset, prev_game_id,
            prev_game_date, prev_home_team_id, travel_miles_since_last,
            time_zones_crossed_since_last, travel_miles_last_3_days,
            travel_miles_last_7_days, time_zones_crossed_last_3_days,
            time_zones_crossed_last_7_days
        )
        VALUES (
            :game_id, :official_id, :game_date, :season, :days_rest,
            :back_to_back, :games_last_7, :games_last_14, :home_team_id,
            :arena_lat, :arena_lon, :arena_tz_offset, :prev_game_id,
            :prev_game_date, :prev_home_team_id, :travel_miles_since_last,
            :time_zones_crossed_since_last, :travel_miles_last_3_days,
            :travel_miles_last_7_days, :time_zones_crossed_last_3_days,
            :time_zones_crossed_last_7_days
        )
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def add_arena_metadata(assignments: pd.DataFrame) -> pd.DataFrame:
    """Attach arena coordinates and time-zone offsets based on home team."""
    enriched = assignments.copy()
    enriched["home_team_id"] = enriched["home_team_id"].astype(int)
    enriched["arena_lat"] = enriched["home_team_id"].map(
        lambda team_id: ARENA_LOCATIONS_BY_TEAM_ID[team_id].latitude
    )
    enriched["arena_lon"] = enriched["home_team_id"].map(
        lambda team_id: ARENA_LOCATIONS_BY_TEAM_ID[team_id].longitude
    )
    enriched["arena_tz_offset"] = enriched["home_team_id"].map(
        lambda team_id: ARENA_LOCATIONS_BY_TEAM_ID[team_id].utc_offset
    )
    return enriched


def haversine_miles(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Great-circle distance between two lat/lon points."""
    radius_miles = 3958.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius_miles * math.atan2(math.sqrt(a), math.sqrt(1 - a))

