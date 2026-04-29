"""Game-level crew chief and trio familiarity features for L2M joins.

Joins rely on `referee_assignments`: crew chief is `role == 'crew_chief'`.
Experience is measured as prior games worked as crew chief in this database
(regular season and playoffs when collected). Familiarity is how often the same
three-person crew appeared together before the game (season-to-date or career).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from referee_fatigue.taxonomy import classify


def is_playoff_game_id(game_id: str | None) -> bool:
    """NBA playoff game IDs use the 004 prefix (10-digit GAME_ID)."""
    return bool(game_id) and str(game_id).startswith("004")


def trio_key(
    a: int | None,
    b: int | None,
    c: int | None,
) -> str | None:
    """Canonical sorted triple of official IDs for trio stability."""
    ids = [x for x in (a, b, c) if x is not None]
    if len(ids) != 3:
        return None
    return json.dumps(sorted(int(x) for x in ids))


def assign_experience_tier(chief_games_before: float | int | None) -> str | None:
    """Pre-defined tiers by cumulative crew-chief games before this game."""
    if chief_games_before is None or pd.isna(chief_games_before):
        return None
    g = int(chief_games_before)
    if g < 75:
        return "tier_1_lt75_chief_games"
    if g < 300:
        return "tier_2_75_299_chief_games"
    return "tier_3_ge300_chief_games"


def assign_familiarity_bucket(prior_same_trio_games: float | int | None) -> str | None:
    """Bucket prior co-appearances for reporting."""
    if prior_same_trio_games is None or pd.isna(prior_same_trio_games):
        return None
    n = int(prior_same_trio_games)
    if n == 0:
        return "first_time_trio"
    if n <= 5:
        return "low_1_to_5"
    return "high_ge6"


def load_assignments_long(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load referee_assignments as a tidy frame sorted by time."""
    df = pd.read_sql_query(
        """
        SELECT
            game_id,
            game_date,
            season,
            season_type,
            official_id,
            role,
            official_name
        FROM referee_assignments
        ORDER BY game_date, game_id
        """,
        conn,
    )
    df["game_date_parsed"] = pd.to_datetime(df["game_date"], errors="coerce")
    return df


def games_with_three_officials(conn: sqlite3.Connection) -> pd.DataFrame:
    """One row per game_id with chief id and trio key when three refs exist."""
    df = pd.read_sql_query(
        """
        SELECT
            game_id,
            MAX(game_date) AS game_date,
            MAX(season) AS season,
            MAX(season_type) AS season_type,
            SUM(CASE WHEN role = 'crew_chief' THEN 1 ELSE 0 END) AS chief_rows,
            SUM(CASE WHEN role = 'official_2' THEN 1 ELSE 0 END) AS r2_rows,
            SUM(CASE WHEN role = 'official_3' THEN 1 ELSE 0 END) AS r3_rows,
            MAX(CASE WHEN role = 'crew_chief' THEN official_id END) AS crew_chief_id,
            MAX(CASE WHEN role = 'crew_chief' THEN official_name END) AS crew_chief_name,
            MAX(CASE WHEN role = 'official_2' THEN official_id END) AS official_2_id,
            MAX(CASE WHEN role = 'official_3' THEN official_id END) AS official_3_id
        FROM referee_assignments
        GROUP BY game_id
        HAVING chief_rows = 1 AND r2_rows = 1 AND r3_rows = 1
        """,
        conn,
    )
    df["game_date_parsed"] = pd.to_datetime(df["game_date"], errors="coerce")
    df["is_playoff"] = df["game_id"].map(is_playoff_game_id).astype(int)
    df["trio_key"] = df.apply(
        lambda r: trio_key(r["crew_chief_id"], r["official_2_id"], r["official_3_id"]),
        axis=1,
    )
    df = df.sort_values(["game_date_parsed", "game_id"], kind="mergesort").reset_index(drop=True)
    return df


def compute_game_crew_features(games_df: pd.DataFrame) -> pd.DataFrame:
    """Add chief_games_before, trio prior counts (season and career), tenure."""
    out = games_df.copy()
    chief_counts: dict[int, int] = {}
    trio_counts_season: dict[tuple[str, str], int] = {}
    trio_counts_career: dict[str, int] = {}
    chief_first_seen: dict[int, pd.Timestamp] = {}

    chief_before: list[int] = []
    trio_s_before: list[int] = []
    trio_c_before: list[int] = []
    chief_years: list[float] = []

    for _, row in out.iterrows():
        cid = int(row["crew_chief_id"]) if pd.notna(row["crew_chief_id"]) else None
        trio = row["trio_key"]
        season = str(row["season"]) if pd.notna(row["season"]) else ""
        gd = row["game_date_parsed"]

        if cid is not None:
            chief_before.append(chief_counts.get(cid, 0))
            if cid not in chief_first_seen and pd.notna(gd):
                chief_first_seen[cid] = gd  # type: ignore[assignment]
            if cid in chief_first_seen and pd.notna(gd):
                delta_days = (gd - chief_first_seen[cid]).days
                chief_years.append(max(0.0, delta_days / 365.25))
            else:
                chief_years.append(float("nan"))
            chief_counts[cid] = chief_counts.get(cid, 0) + 1
        else:
            chief_before.append(0)
            chief_years.append(float("nan"))

        if trio:
            sk = (season, trio)
            trio_s_before.append(trio_counts_season.get(sk, 0))
            trio_counts_season[sk] = trio_counts_season.get(sk, 0) + 1

            trio_c_before.append(trio_counts_career.get(trio, 0))
            trio_counts_career[trio] = trio_counts_career.get(trio, 0) + 1
        else:
            trio_s_before.append(0)
            trio_c_before.append(0)

    out["chief_games_before"] = chief_before
    out["chief_season_games_before"] = chief_before  # alias: games as chief before this row
    out["prior_same_trio_season"] = trio_s_before
    out["prior_same_trio_career"] = trio_c_before
    out["years_since_first_chief_game"] = chief_years
    out["experience_tier"] = out["chief_games_before"].map(assign_experience_tier)
    out["familiarity_bucket_season"] = out["prior_same_trio_season"].map(assign_familiarity_bucket)
    return out


def assignment_coverage_by_l2m(conn: sqlite3.Connection) -> pd.DataFrame:
    """Summarize how many L2M games have crew assignments."""
    return pd.read_sql_query(
        """
        SELECT
            r.season,
            SUM(CASE WHEN ra.game_id IS NOT NULL THEN 1 ELSE 0 END) AS games_with_chief,
            COUNT(*) AS l2m_games
        FROM (SELECT DISTINCT game_id, season FROM l2m_reports WHERE has_report = 1) r
        LEFT JOIN (
            SELECT DISTINCT game_id FROM referee_assignments WHERE role = 'crew_chief'
        ) ra ON r.game_id = ra.game_id
        GROUP BY r.season
        ORDER BY r.season
        """,
        conn,
    )


def l2m_assignment_coverage(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    """Summarize L2M ↔ ``referee_assignments`` join quality for QA.

    Returns dict keys:

    - ``by_season``: counts per L2M season (distinct games with ``has_report``).
    - ``by_season_playoff``: same split into regular season vs playoffs (``004`` prefix).
    - ``gaps``: L2M games with no rows or without exactly one chief + official_2 + official_3.
    """
    by_season = pd.read_sql_query(
        """
        WITH l2m AS (
            SELECT DISTINCT game_id, season FROM l2m_reports WHERE has_report = 1
        ),
        agg AS (
            SELECT
                game_id,
                SUM(CASE WHEN role = 'crew_chief' THEN 1 ELSE 0 END) AS n_chief,
                SUM(CASE WHEN role = 'official_2' THEN 1 ELSE 0 END) AS n_o2,
                SUM(CASE WHEN role = 'official_3' THEN 1 ELSE 0 END) AS n_o3
            FROM referee_assignments
            GROUP BY game_id
        )
        SELECT
            l.season AS season,
            COUNT(*) AS l2m_games,
            SUM(CASE WHEN a.game_id IS NOT NULL THEN 1 ELSE 0 END) AS with_any_assignment,
            SUM(CASE WHEN COALESCE(a.n_chief, 0) >= 1 THEN 1 ELSE 0 END) AS with_chief_row,
            SUM(
                CASE
                    WHEN COALESCE(a.n_chief, 0) = 1
                        AND COALESCE(a.n_o2, 0) = 1
                        AND COALESCE(a.n_o3, 0) = 1
                    THEN 1 ELSE 0
                END
            ) AS full_trio
        FROM l2m l
        LEFT JOIN agg a ON l.game_id = a.game_id
        GROUP BY l.season
        ORDER BY l.season
        """,
        conn,
    )
    by_season_playoff = pd.read_sql_query(
        """
        WITH l2m AS (
            SELECT DISTINCT game_id, season FROM l2m_reports WHERE has_report = 1
        ),
        agg AS (
            SELECT
                game_id,
                SUM(CASE WHEN role = 'crew_chief' THEN 1 ELSE 0 END) AS n_chief,
                SUM(CASE WHEN role = 'official_2' THEN 1 ELSE 0 END) AS n_o2,
                SUM(CASE WHEN role = 'official_3' THEN 1 ELSE 0 END) AS n_o3
            FROM referee_assignments
            GROUP BY game_id
        )
        SELECT
            l.season AS season,
            CASE
                WHEN substr(l.game_id, 1, 3) = '004' THEN 'playoffs'
                ELSE 'regular_season'
            END AS bracket,
            COUNT(*) AS l2m_games,
            SUM(
                CASE
                    WHEN COALESCE(a.n_chief, 0) = 1
                        AND COALESCE(a.n_o2, 0) = 1
                        AND COALESCE(a.n_o3, 0) = 1
                    THEN 1 ELSE 0
                END
            ) AS full_trio
        FROM l2m l
        LEFT JOIN agg a ON l.game_id = a.game_id
        GROUP BY l.season, bracket
        ORDER BY l.season, bracket
        """,
        conn,
    )
    gaps = pd.read_sql_query(
        """
        WITH l2m AS (
            SELECT DISTINCT game_id, season FROM l2m_reports WHERE has_report = 1
        ),
        agg AS (
            SELECT
                game_id,
                SUM(CASE WHEN role = 'crew_chief' THEN 1 ELSE 0 END) AS n_chief,
                SUM(CASE WHEN role = 'official_2' THEN 1 ELSE 0 END) AS n_o2,
                SUM(CASE WHEN role = 'official_3' THEN 1 ELSE 0 END) AS n_o3
            FROM referee_assignments
            GROUP BY game_id
        )
        SELECT
            l.game_id AS game_id,
            l.season AS season,
            a.n_chief AS n_chief,
            a.n_o2 AS n_o2,
            a.n_o3 AS n_o3
        FROM l2m l
        LEFT JOIN agg a ON l.game_id = a.game_id
        WHERE a.game_id IS NULL
            OR NOT (
                COALESCE(a.n_chief, 0) = 1
                AND COALESCE(a.n_o2, 0) = 1
                AND COALESCE(a.n_o3, 0) = 1
            )
        ORDER BY l.season, l.game_id
        """,
        conn,
    )

    def _pct(num: pd.Series, den: pd.Series) -> pd.Series:
        return (100.0 * num.astype(float) / den.astype(float).replace(0, np.nan)).round(1)

    if not by_season.empty:
        by_season = by_season.copy()
        by_season["pct_full_trio"] = _pct(by_season["full_trio"], by_season["l2m_games"])
        by_season["pct_with_chief"] = _pct(by_season["with_chief_row"], by_season["l2m_games"])
    if not by_season_playoff.empty:
        by_season_playoff = by_season_playoff.copy()
        by_season_playoff["pct_full_trio"] = _pct(by_season_playoff["full_trio"], by_season_playoff["l2m_games"])

    return {
        "by_season": by_season,
        "by_season_playoff": by_season_playoff,
        "gaps": gaps,
    }


def load_l2m_events_with_crew_features(
    conn: sqlite3.Connection,
    crew_games: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """L2M events joined to per-game crew features (taxonomy included)."""
    if crew_games is None:
        base = games_with_three_officials(conn)
        crew_games = compute_game_crew_features(base)

    events = pd.read_sql_query(
        """
        SELECT
            e.game_id,
            e.event_index,
            e.season,
            e.period,
            e.game_clock,
            e.call_type,
            e.review_decision,
            e.incorrect
        FROM l2m_events e
        WHERE e.review_decision IN ('CC', 'CNC', 'IC', 'INC')
        """,
        conn,
    )
    merged = events.merge(crew_games, on="game_id", how="left")
    merged["monitoring_type"] = merged.apply(
        lambda row: classify(row["call_type"], row["review_decision"]),
        axis=1,
    )
    merged["is_playoff"] = merged["game_id"].map(lambda g: int(is_playoff_game_id(g)))
    merged["decision_kind"] = merged["review_decision"].map(
        {"CC": "call", "IC": "call", "CNC": "non_call", "INC": "non_call"}
    )
    merged["ic"] = merged["review_decision"].eq("IC").astype(int)
    merged["inc"] = merged["review_decision"].eq("INC").astype(int)
    merged["correct_or_ok"] = merged["incorrect"].eq(0).astype(int)
    return merged


def chief_tier_counts_latest_season(crew_games: pd.DataFrame, season: str) -> pd.DataFrame:
    """Distinct crew chiefs in season with tier at last game row."""
    sub = crew_games[crew_games["season"] == season].copy()
    if sub.empty:
        return pd.DataFrame()
    last = sub.sort_values(["crew_chief_id", "game_date_parsed"]).groupby("crew_chief_id").tail(1)
    return (
        last.groupby("experience_tier", dropna=False)
        .agg(chiefs=("crew_chief_id", "count"))
        .reset_index()
    )


def build_demographics_summary(crew_games: pd.DataFrame) -> pd.DataFrame:
    """Season-level tier counts for most recent seasons."""
    seasons = sorted(crew_games["season"].dropna().unique())[-5:]
    parts = []
    for s in seasons:
        ct = chief_tier_counts_latest_season(crew_games, str(s))
        if ct.empty:
            continue
        ct.insert(0, "season", str(s))
        parts.append(ct)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def save_crew_game_table(path: Path, crew_games: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    crew_games.to_csv(path, index=False)
