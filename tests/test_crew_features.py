"""Tests for crew chief features and L2M joins."""

from __future__ import annotations

import sqlite3

import pandas as pd

from referee_fatigue.crew_features import (
    assign_experience_tier,
    assign_familiarity_bucket,
    compute_game_crew_features,
    games_with_three_officials,
    is_playoff_game_id,
    l2m_assignment_coverage,
    load_assignments_long,
    trio_key,
)


def test_is_playoff_game_id() -> None:
    assert is_playoff_game_id("0042300401") is True
    assert is_playoff_game_id("0022300001") is False


def test_trio_key_sorted() -> None:
    assert trio_key(3, 1, 2) == "[1, 2, 3]"
    assert trio_key(None, 1, 2) is None


def test_experience_tiers() -> None:
    assert assign_experience_tier(0) == "tier_1_lt75_chief_games"
    assert assign_experience_tier(74) == "tier_1_lt75_chief_games"
    assert assign_experience_tier(75) == "tier_2_75_299_chief_games"
    assert assign_experience_tier(299) == "tier_2_75_299_chief_games"
    assert assign_experience_tier(300) == "tier_3_ge300_chief_games"


def test_familiarity_buckets() -> None:
    assert assign_familiarity_bucket(0) == "first_time_trio"
    assert assign_familiarity_bucket(3) == "low_1_to_5"
    assert assign_familiarity_bucket(6) == "high_ge6"


def test_compute_game_crew_features_sequential() -> None:
    games = pd.DataFrame(
        {
            "game_id": ["g1", "g2", "g3"],
            "game_date": ["2023-10-01", "2023-10-02", "2023-10-03"],
            "season": ["2023-24"] * 3,
            "season_type": ["Regular Season"] * 3,
            "chief_rows": [1, 1, 1],
            "r2_rows": [1, 1, 1],
            "r3_rows": [1, 1, 1],
            "crew_chief_id": [10, 10, 20],
            "crew_chief_name": ["A", "A", "B"],
            "official_2_id": [11, 11, 21],
            "official_3_id": [12, 12, 22],
            "is_playoff": [0, 0, 0],
        }
    )
    games["game_date_parsed"] = pd.to_datetime(games["game_date"])
    games["trio_key"] = games.apply(
        lambda r: trio_key(r["crew_chief_id"], r["official_2_id"], r["official_3_id"]),
        axis=1,
    )
    out = compute_game_crew_features(games)
    assert list(out["chief_games_before"]) == [0, 1, 0]
    assert list(out["prior_same_trio_career"]) == [0, 1, 0]
    assert list(out["prior_same_trio_season"]) == [0, 1, 0]


def test_games_with_three_officials_sql(tmp_path) -> None:
    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE referee_assignments (
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
            PRIMARY KEY (game_id, official_id)
        )
        """
    )
    rows = [
        ("g1", "2023-10-01", "2023-24", "Regular Season", "002", 10, "A", "crew_chief"),
        ("g1", "2023-10-01", "2023-24", "Regular Season", "002", 11, "B", "official_2"),
        ("g1", "2023-10-01", "2023-24", "Regular Season", "002", 12, "C", "official_3"),
    ]
    conn.executemany(
        """
        INSERT INTO referee_assignments (
            game_id, game_date, season, season_type, jersey_num,
            official_id, official_name, role
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    df = games_with_three_officials(conn)
    assert len(df) == 1
    assert int(df.iloc[0]["crew_chief_id"]) == 10
    conn.close()


def test_load_assignments_long_empty(tmp_path) -> None:
    db = tmp_path / "e.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE referee_assignments (game_id TEXT, game_date TEXT, season TEXT, "
        "season_type TEXT, official_id INTEGER, role TEXT, official_name TEXT)"
    )
    conn.commit()
    df = load_assignments_long(conn)
    assert df.empty
    conn.close()


def test_l2m_assignment_coverage_counts(tmp_path) -> None:
    db = tmp_path / "cov.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE l2m_reports (
            game_id TEXT PRIMARY KEY,
            season TEXT NOT NULL,
            event_count INTEGER NOT NULL,
            incorrect_count INTEGER NOT NULL,
            has_report INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE referee_assignments (
            game_id TEXT NOT NULL,
            game_date TEXT,
            season TEXT NOT NULL,
            season_type TEXT NOT NULL DEFAULT 'Regular Season',
            official_id INTEGER NOT NULL,
            official_name TEXT NOT NULL,
            role TEXT NOT NULL,
            PRIMARY KEY (game_id, official_id)
        )
        """
    )
    conn.executemany(
        "INSERT INTO l2m_reports (game_id, season, event_count, incorrect_count, has_report) VALUES (?,?,?,?,?)",
        [
            ("0022300001", "2023-24", 10, 1, 1),
            ("0022300002", "2023-24", 5, 0, 1),
            ("0042300401", "2023-24", 8, 0, 1),
        ],
    )
    trio = [
        ("0022300001", "2023-10-01", "2023-24", 10, "A", "crew_chief"),
        ("0022300001", "2023-10-01", "2023-24", 11, "B", "official_2"),
        ("0022300001", "2023-10-01", "2023-24", 12, "C", "official_3"),
        ("0042300401", "2023-05-01", "2023-24", 20, "D", "crew_chief"),
        ("0042300401", "2023-05-01", "2023-24", 21, "E", "official_2"),
        ("0042300401", "2023-05-01", "2023-24", 22, "F", "official_3"),
    ]
    conn.executemany(
        """
        INSERT INTO referee_assignments (
            game_id, game_date, season, official_id, official_name, role
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        trio,
    )
    conn.commit()

    tables = l2m_assignment_coverage(conn)
    conn.close()

    by_season = tables["by_season"]
    assert len(by_season) == 1
    assert int(by_season.iloc[0]["l2m_games"]) == 3
    assert int(by_season.iloc[0]["full_trio"]) == 2

    sp = tables["by_season_playoff"]
    rs = sp[sp["bracket"] == "regular_season"].iloc[0]
    po = sp[sp["bracket"] == "playoffs"].iloc[0]
    assert int(rs["l2m_games"]) == 2 and int(rs["full_trio"]) == 1
    assert int(po["l2m_games"]) == 1 and int(po["full_trio"]) == 1

    gaps = tables["gaps"]
    assert len(gaps) == 1
    assert gaps.iloc[0]["game_id"] == "0022300002"
