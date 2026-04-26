#!/usr/bin/env python3
"""Compute referee workload features from collected assignments."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.referee_load import (
    compute_referee_load_features,
    persist_referee_load_features,
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute referee load features")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "compute_referee_load.log"),
            logging.StreamHandler(),
        ],
    )
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    features = compute_referee_load_features(conn)
    row_count = persist_referee_load_features(conn, features)
    logger.info("Wrote %s referee load feature rows", row_count)


if __name__ == "__main__":
    main()

