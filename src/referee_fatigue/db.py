"""SQLite schema helpers for the referee fatigue MVP."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: str | Path = "data/nba_stats.db") -> sqlite3.Connection:
    """Open the local analysis database."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def create_referee_tables(conn: sqlite3.Connection) -> None:
    """Create the tables used by the referee fatigue MVP."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS referee_assignments (
            game_id TEXT NOT NULL,
            game_date TEXT,
            season TEXT NOT NULL,
            season_type TEXT NOT NULL DEFAULT 'Regular Season',
            arena_city TEXT,
            home_team_id INTEGER,
            away_team_id INTEGER,
            official_id INTEGER NOT NULL,
            official_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            jersey_num TEXT,
            role TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (game_id, official_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ref_assignments_official_date
        ON referee_assignments(official_id, game_date)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ref_assignments_game
        ON referee_assignments(game_id)
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS challenge_events (
            game_id TEXT NOT NULL,
            event_num INTEGER NOT NULL,
            season TEXT NOT NULL,
            season_type TEXT NOT NULL DEFAULT 'Regular Season',
            period INTEGER,
            game_clock TEXT,
            description TEXT NOT NULL,
            original_ruling TEXT,
            final_ruling TEXT,
            overturned INTEGER NOT NULL,
            crew_chief_id INTEGER,
            challenging_team TEXT,
            event_msg_type INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (game_id, event_num)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_challenge_events_game
        ON challenge_events(game_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_challenge_events_crew_chief
        ON challenge_events(crew_chief_id)
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS referee_load_features (
            game_id TEXT NOT NULL,
            official_id INTEGER NOT NULL,
            game_date TEXT NOT NULL,
            season TEXT NOT NULL,
            days_rest INTEGER,
            back_to_back INTEGER NOT NULL,
            games_last_7 INTEGER NOT NULL,
            games_last_14 INTEGER NOT NULL,
            home_team_id INTEGER,
            arena_lat REAL,
            arena_lon REAL,
            arena_tz_offset INTEGER,
            prev_game_id TEXT,
            prev_game_date TEXT,
            prev_home_team_id INTEGER,
            travel_miles_since_last REAL,
            time_zones_crossed_since_last INTEGER,
            travel_miles_last_3_days REAL,
            travel_miles_last_7_days REAL,
            time_zones_crossed_last_3_days INTEGER,
            time_zones_crossed_last_7_days INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (game_id, official_id)
        )
        """
    )
    _ensure_columns(
        conn,
        "referee_load_features",
        {
            "home_team_id": "INTEGER",
            "arena_lat": "REAL",
            "arena_lon": "REAL",
            "arena_tz_offset": "INTEGER",
            "prev_game_id": "TEXT",
            "prev_game_date": "TEXT",
            "prev_home_team_id": "INTEGER",
            "travel_miles_since_last": "REAL",
            "time_zones_crossed_since_last": "INTEGER",
            "travel_miles_last_3_days": "REAL",
            "travel_miles_last_7_days": "REAL",
            "time_zones_crossed_last_3_days": "INTEGER",
            "time_zones_crossed_last_7_days": "INTEGER",
        },
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ref_load_official_date
        ON referee_load_features(official_id, game_date)
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2m_reports (
            game_id TEXT PRIMARY KEY,
            season TEXT NOT NULL,
            game_date TEXT,
            home_team_id INTEGER,
            away_team_id INTEGER,
            home_team TEXT,
            away_team TEXT,
            home_score INTEGER,
            away_score INTEGER,
            event_count INTEGER NOT NULL,
            incorrect_count INTEGER NOT NULL,
            has_report INTEGER NOT NULL,
            comments TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_l2m_reports_season
        ON l2m_reports(season)
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l2m_events (
            game_id TEXT NOT NULL,
            event_index INTEGER NOT NULL,
            season TEXT NOT NULL,
            period TEXT,
            game_clock TEXT,
            call_type TEXT,
            review_decision TEXT,
            incorrect INTEGER NOT NULL,
            committing_player TEXT,
            disadvantaged_player TEXT,
            comment TEXT,
            difficulty TEXT,
            possession_id INTEGER,
            possession_start TEXT,
            possession_end TEXT,
            team_id_in_favor INTEGER,
            error_in_favor TEXT,
            video_event_num TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (game_id, event_index)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_l2m_events_game
        ON l2m_events(game_id)
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS game_pace_features (
            game_id TEXT PRIMARY KEY,
            season TEXT NOT NULL,
            game_minutes REAL,
            estimated_possessions REAL,
            estimated_pace REAL,
            total_actions INTEGER NOT NULL,
            actions_per_minute REAL,
            q4_actions INTEGER NOT NULL,
            q4_actions_per_minute REAL,
            q4_pre_l2m_actions INTEGER NOT NULL,
            q4_pre_l2m_actions_per_minute REAL,
            l2m_actions INTEGER NOT NULL,
            l2m_actions_per_minute REAL,
            q4_shots INTEGER NOT NULL,
            q4_fouls INTEGER NOT NULL,
            q4_turnovers INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_game_pace_features_season
        ON game_pace_features(season)
        """
    )
    conn.commit()


def _ensure_columns(
    conn: sqlite3.Connection,
    table_name: str,
    columns: dict[str, str],
) -> None:
    """Add columns to an existing SQLite table without rebuilding it."""
    existing = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, column_type in columns.items():
        if column_name not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

