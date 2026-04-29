"""Tests for referee assignment parsing helpers."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import collect_officials as co  # noqa: E402


def test_tag_season_type_playoff() -> None:
    rows = [{"season_type": "Regular Season"} for _ in range(3)]
    co._tag_season_type(rows, "0042300401")
    assert all(r["season_type"] == "Playoffs" for r in rows)


def test_tag_season_type_regular() -> None:
    rows = [{"season_type": "Playoffs"} for _ in range(3)]
    co._tag_season_type(rows, "0022300001")
    assert all(r["season_type"] == "Regular Season" for r in rows)


def test_season_from_game_id() -> None:
    assert co._season_from_game_id("0022300123") == "2023-24"
    assert co._season_from_game_id("0042300401") == "2023-24"
