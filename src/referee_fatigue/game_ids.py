"""Game ID loading helpers.

The target project owns the analysis code, while the existing
resilience_basketball checkout can be used as an optional source of raw NBA
season files.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


DEFAULT_SEASONS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]


def default_resilience_path(project_root: Path | None = None) -> Path:
    """Return the sibling resilience_basketball path when it exists."""
    root = project_root or Path.cwd()
    sibling = root.parent / "resilience_basketball"
    return sibling if sibling.exists() else Path("/Users/harrisgordon/Documents/Development/resilience_basketball")


def load_regular_season_game_ids(
    seasons: list[str],
    project_root: Path,
    resilience_path: Path | None = None,
) -> dict[str, list[str]]:
    """Load game IDs from local files first, then the resilience data folder."""
    data_roots = [project_root / "data"]
    candidate_resilience = resilience_path or default_resilience_path(project_root)
    if candidate_resilience.exists():
        data_roots.append(candidate_resilience / "data")

    return {
        season: _load_ids_for_season(season, data_roots)
        for season in seasons
    }


def season_from_game_id(game_id: str) -> str:
    """Convert an NBA game ID like 0022300001 to 2023-24."""
    start_year = 2000 + int(game_id[3:5])
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _load_ids_for_season(season: str, data_roots: list[Path]) -> list[str]:
    season_slug = season.replace("-", "_")

    for data_root in data_roots:
        json_path = data_root / f"{season_slug}_regular_games.json"
        if json_path.exists():
            with json_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            ids = payload.get("game_ids", [])
            if ids:
                return sorted(set(str(game_id) for game_id in ids))

    for data_root in data_roots:
        csv_path = data_root / f"rs_game_logs_{season}.csv"
        if csv_path.exists():
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                ids = {
                    row["GAME_ID"]
                    for row in reader
                    if row.get("GAME_ID") and str(row["GAME_ID"]).startswith("002")
                }
            if ids:
                return sorted(ids)

    return []

