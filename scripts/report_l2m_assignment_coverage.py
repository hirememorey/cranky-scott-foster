#!/usr/bin/env python3
"""Step 1 QA: L2M games vs referee_assignments coverage (season + RS/playoff + gaps)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.crew_features import l2m_assignment_coverage
from referee_fatigue.db import connect, create_referee_tables


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Markdown table without optional tabulate dependency."""
    if df.empty:
        return "_No rows._"
    formatted = df.astype(object).where(pd.notna(df), "")
    headers = list(formatted.columns)
    rows = formatted.astype(str).values.tolist()
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report L2M ↔ referee assignment coverage")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/l2m_assignment_coverage.md")
    parser.add_argument(
        "--gaps-csv",
        default="results/l2m_assignment_coverage_gaps.csv",
        help="Games missing a complete trio (chief + official_2 + official_3).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)
    tables = l2m_assignment_coverage(conn)

    by_season = tables["by_season"]
    by_sp = tables["by_season_playoff"]
    gaps = tables["gaps"]

    lines = [
        "# L2M ↔ referee assignment coverage",
        "",
        "Distinct **L2M games** (`l2m_reports.has_report = 1`) compared to "
        "**`referee_assignments`** rows needed for the crew pipeline "
        "(exactly one `crew_chief`, `official_2`, and `official_3` per game).",
        "",
        "## By season",
        "",
        dataframe_to_markdown(by_season),
        "",
        "## Regular season vs playoffs",
        "",
        dataframe_to_markdown(by_sp),
        "",
        "## Gaps",
        "",
        f"- L2M games **without** a full trio: **{len(gaps):,}**",
        "",
    ]
    if len(gaps) > 0:
        out_gaps = PROJECT_ROOT / args.gaps_csv
        out_gaps.parent.mkdir(parents=True, exist_ok=True)
        gaps.to_csv(out_gaps, index=False)
        lines.append(f"- Detail: `{args.gaps_csv}`")
        lines.append("")
    else:
        lines.append("_No gaps — every L2M game has a complete trio._")
        lines.append("")

    out_md = PROJECT_ROOT / args.output
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")
    if len(gaps) > 0:
        print(f"Wrote {PROJECT_ROOT / args.gaps_csv} ({len(gaps)} rows)")


if __name__ == "__main__":
    main()
