#!/usr/bin/env python3
"""Crew chief experience, trio familiarity, and MRT taxonomy (Dowsett pipeline hook)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from referee_fatigue.crew_features import (
    build_demographics_summary,
    compute_game_crew_features,
    games_with_three_officials,
    load_l2m_events_with_crew_features,
    l2m_assignment_coverage,
    save_crew_game_table,
)
from referee_fatigue.db import connect, create_referee_tables
from referee_fatigue.taxonomy import (
    ADMINISTRATIVE_PROCESS,
    AMBIENT_CONTINUOUS,
    FOCAL_CONTINUOUS,
    FOCAL_DISCRETE,
    TEMPORAL_DISCRETE,
)

try:
    import statsmodels.formula.api as smf
except ImportError:  # pragma: no cover
    smf = None


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Markdown table without optional tabulate dependency."""
    if df.empty:
        return "_No rows._"
    formatted = df.copy()
    for column in formatted.columns:
        if column.endswith("rate") or column.endswith("_rate"):
            formatted[column] = formatted[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.1%}"
            )
        elif column in {"wilson_low", "wilson_high", "coverage_pct"}:
            formatted[column] = formatted[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.4f}"
            )
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
    parser = argparse.ArgumentParser(description="Crew chief pipeline + L2M taxonomy analysis")
    parser.add_argument("--db-path", default="data/nba_stats.db")
    parser.add_argument("--output", default="results/crew_chief_pipeline_report.md")
    parser.add_argument("--game-features-csv", default="results/crew_chief_game_features.csv")
    parser.add_argument("--events-csv", default="results/crew_chief_pipeline_events.csv")
    return parser.parse_args()


def rate_table(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    g = df.groupby(group_cols, dropna=False)
    out = g.agg(n=("incorrect", "count"), incorrect=("incorrect", "sum"))
    out["error_rate"] = out["incorrect"] / out["n"].replace(0, np.nan)
    out = out.reset_index().sort_values(group_cols)
    return out


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def add_precision_columns(tbl: pd.DataFrame, success_col: str = "incorrect", n_col: str = "n") -> pd.DataFrame:
    """Append Wilson lower/upper for binomial proportion."""
    lows = []
    highs = []
    for _, row in tbl.iterrows():
        lo, hi = wilson_interval(int(row[success_col]), int(row[n_col]))
        lows.append(lo)
        highs.append(hi)
    out = tbl.copy()
    out["wilson_low"] = lows
    out["wilson_high"] = highs
    return out


def safe_logit(formula: str, data: pd.DataFrame):
    if smf is None:
        return None, "statsmodels not installed"
    try:
        # Default Newton-Raphson; interaction models can warn on convergence—exploratory only.
        return smf.logit(formula, data=data).fit(disp=False), None
    except Exception as exc:  # pragma: no cover - singular designs
        return None, str(exc)


def main() -> None:
    args = parse_args()
    conn = connect(PROJECT_ROOT / args.db_path)
    create_referee_tables(conn)

    games = games_with_three_officials(conn)
    crew_games = compute_game_crew_features(games)
    save_crew_game_table(PROJECT_ROOT / args.game_features_csv, crew_games)

    df = load_l2m_events_with_crew_features(conn, crew_games)
    df.to_csv(PROJECT_ROOT / args.events_csv, index=False)

    coverage_tables = l2m_assignment_coverage(conn)
    demo_rows = build_demographics_summary(crew_games)

    lines: list[str] = [
        "# Crew Chief Pipeline vs. Structural Officiating Risk (L2M)",
        "",
        "This report joins **crew chief tenure** (games as chief before this game in our assignment DB), "
        "**trio familiarity** (prior games with the same three officials), and the **MRT taxonomy** "
        "(`monitoring_type`) for Last Two Minute events.",
        "",
        "## Data limits",
        "",
        "- L2M is a **league audit subset** (close games, reviewed events), not all whistles.",
        "- Crew chief identity comes from **assignment scrape order** (crew chief listed first). "
        "See `scripts/collect_officials.py`.",
        "- Experience is **games as crew chief observed in this database** (RS + playoffs when collected), "
        "not league-internal tenure.",
        "- **Selection**: senior chiefs receive harder assignments; interpret heterogeneity as descriptive.",
        "",
        "## Assignment coverage vs. L2M games",
        "",
        "Full crew pipeline requires exactly one row each for `crew_chief`, `official_2`, and `official_3`. "
        "See also `scripts/report_l2m_assignment_coverage.py` for gap CSV.",
        "",
    ]

    cov_season = coverage_tables["by_season"]
    if not cov_season.empty:
        lines.append(dataframe_to_markdown(cov_season))
        lines.append("")
    else:
        lines.append("_No L2M rows in database._")
        lines.append("")

    cov_sp = coverage_tables["by_season_playoff"]
    lines.extend(
        [
            "### Regular season vs playoffs (L2M games)",
            "",
        ]
    )
    if not cov_sp.empty:
        lines.append(dataframe_to_markdown(cov_sp))
        lines.append("")
    else:
        lines.append("_No rows._")
        lines.append("")

    gaps = coverage_tables["gaps"]
    lines.append(f"- L2M games **without** a complete trio in assignments: **{len(gaps):,}**")
    lines.append("")

    joined = df[df["experience_tier"].notna()].copy()
    missing_tier = int(len(df) - len(joined))
    lines.append(f"- Events with assigned experience tier: **{len(joined):,}** (dropped {missing_tier:,} without full crew join).")
    lines.append("")

    tax_order = [
        FOCAL_DISCRETE,
        AMBIENT_CONTINUOUS,
        FOCAL_CONTINUOUS,
        TEMPORAL_DISCRETE,
        ADMINISTRATIVE_PROCESS,
    ]

    lines.extend(
        [
            "## Experience tier × taxonomy (error rates)",
            "",
            "Pre-defined tiers: `<75` chief games, `75–299`, `≥300` prior games as crew chief.",
            "",
        ]
    )
    if len(joined) > 0:
        tier_tax = rate_table(joined, ["experience_tier", "monitoring_type"])
        tier_tax = tier_tax[tier_tax["monitoring_type"].isin(tax_order)].copy()
        tier_tax["monitoring_type"] = pd.Categorical(tier_tax["monitoring_type"], tax_order, ordered=True)
        tier_tax = tier_tax.sort_values(["experience_tier", "monitoring_type"])
        tier_tax = add_precision_columns(tier_tax)
        lines.append(dataframe_to_markdown(tier_tax))
        lines.append("")
    else:
        lines.append("_No joined rows._")
        lines.append("")

    lines.extend(["## Familiarity (season-to-date trio count) × taxonomy", ""])
    fam = df[df["familiarity_bucket_season"].notna()].copy()
    if len(fam) > 0:
        ft = rate_table(fam, ["familiarity_bucket_season", "monitoring_type"])
        ft = ft[ft["monitoring_type"].isin(tax_order)].copy()
        ft["monitoring_type"] = pd.Categorical(ft["monitoring_type"], tax_order, ordered=True)
        ft = ft.sort_values(["familiarity_bucket_season", "monitoring_type"])
        ft = add_precision_columns(ft)
        lines.append(dataframe_to_markdown(ft))
        lines.append("")
    else:
        lines.append("_No familiarity buckets._")
        lines.append("")

    lines.extend(["## Regular season vs. playoffs", ""])
    rs_po = rate_table(df, ["is_playoff", "monitoring_type"])
    if not rs_po.empty:
        rs_po = rs_po[rs_po["monitoring_type"].isin(tax_order)].copy()
        rs_po["monitoring_type"] = pd.Categorical(rs_po["monitoring_type"], tax_order, ordered=True)
        rs_po = rs_po.sort_values(["is_playoff", "monitoring_type"])
        rs_po = add_precision_columns(rs_po)
        lines.append(dataframe_to_markdown(rs_po))
        lines.append("")
        rs_n = len(df[df["is_playoff"] == 0])
        po_n = len(df[df["is_playoff"] == 1])
        lines.append(f"- Events (RS vs playoff): **{rs_n:,}** vs **{po_n:,}** (playoff requires `--include-playoffs` L2M + assignments).")
        lines.append("")
    else:
        lines.append("_Empty._")
        lines.append("")

    lines.extend(
        [
            "## Logistic models (exploratory)",
            "",
            "Reference category: focal/discrete × tier 1. Clustering by game not shown (MLE only).",
            "",
        ]
    )
    if len(joined) > 100 and smf is not None:
        # Numeric tier for simpler convergence
        tier_map = {
            "tier_1_lt75_chief_games": 1,
            "tier_2_75_299_chief_games": 2,
            "tier_3_ge300_chief_games": 3,
        }
        j = joined[joined["monitoring_type"].isin(tax_order)].copy()
        j["tier_num"] = j["experience_tier"].map(tier_map)
        j = j[j["tier_num"].notna()]
        m1, e1 = safe_logit("incorrect ~ C(monitoring_type) + C(experience_tier)", j)
        m2, e2 = safe_logit("incorrect ~ C(monitoring_type) * C(experience_tier)", j)
        lines.append(f"- Main effects: `{e1}`" if e1 else "")
        if m1 is not None:
            lines.append("```")
            lines.append(m1.summary().as_text())
            lines.append("```")
            lines.append("")
        lines.append(f"- Interaction model: `{e2}`" if e2 else "")
        if m2 is not None:
            lines.append("```")
            lines.append(m2.summary().as_text())
            lines.append("```")
            lines.append("")
            if m1 is not None:
                try:
                    lr = float(2 * (m2.llf - m1.llf))
                    df_diff = m2.df_model - m1.df_model
                    lines.append(f"- LR test interaction vs main (approx): chi^2 = {lr:.2f}, df = {df_diff:.0f}")
                    lines.append("")
                except Exception:
                    pass

        fam_j = df[df["familiarity_bucket_season"].notna()].copy()
        fam_j = fam_j[fam_j["monitoring_type"].isin(tax_order)]
        if len(fam_j) > 100:
            m3, e3 = safe_logit(
                "incorrect ~ C(monitoring_type) * C(familiarity_bucket_season)",
                fam_j,
            )
            lines.append(f"- Familiarity interaction: `{e3}`" if e3 else "")
            if m3 is not None:
                lines.append("```")
                lines.append(m3.summary().as_text())
                lines.append("```")
                lines.append("")
    else:
        lines.append("_Insufficient rows or statsmodels missing._")
        lines.append("")

    lines.extend(
        [
            "## IC vs INC asymmetry (exploratory)",
            "",
            "Among **calls** (CC/IC): IC rate; among **non-calls** (CNC/INC): INC rate. "
            "League grading difficulty differs by play type—interpret cautiously.",
            "",
        ]
    )
    calls = joined[joined["review_decision"].isin(["CC", "IC"])].copy()
    ncalls = joined[joined["review_decision"].isin(["CNC", "INC"])].copy()
    if len(calls) > 20:
        ic_tbl = calls.groupby("experience_tier", dropna=False).agg(
            ic=("ic", "sum"),
            n_calls=("ic", "count"),
        )
        ic_tbl["ic_rate_given_call"] = ic_tbl["ic"] / ic_tbl["n_calls"]
        lines.append("### Calls (CC + IC)")
        lines.append(dataframe_to_markdown(ic_tbl.reset_index()))
        lines.append("")
    if len(ncalls) > 20:
        inc_tbl = ncalls.groupby("experience_tier", dropna=False).agg(
            inc=("inc", "sum"),
            n_nc=("inc", "count"),
        )
        inc_tbl["inc_rate_given_noncall_review"] = inc_tbl["inc"] / inc_tbl["n_nc"]
        lines.append("### Non-calls (CNC + INC)")
        lines.append(dataframe_to_markdown(inc_tbl.reset_index()))
        lines.append("")

    lines.extend(["## Pipeline demographics (tier counts by season)", ""])
    if not demo_rows.empty:
        lines.append(dataframe_to_markdown(demo_rows))
        lines.append("")
    else:
        lines.append("_No demographics table._")
        lines.append("")

    lines.extend(
        [
            "## Interpretation notes",
            "",
            "- **Positive interaction** between high attention-load taxonomy buckets and lower experience "
            "would align with the Dowsett \"pipeline\" narrative; nulls are informative given selection bias.",
            "- Use **Wilson** intervals when comparing small playoff slices.",
            "",
        ]
    )

    out_path = PROJECT_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
