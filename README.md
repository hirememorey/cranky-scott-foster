# The Attention Load: Structural Predictability in NBA Officiating

NBA officiating analytics experiments focused on identifying the structural contexts that make late-game referee decisions more error-prone.

## Executive Summary: Why NBA Refs Miss Certain Calls

NBA officiating mistakes are not random. They cluster around decisions that ask humans to track too much at once—a phenomenon we call **Attention Load**.

We analyzed **51,130** NBA Last Two Minute (L2M) report events from the 2018-19 through 2024-25 seasons. The strongest finding is that officiating "badness" is not broadly driven by referee fatigue, travel, or game pace. Instead, it is **structurally predictable** from the type of decision being made.

### The Findings
Using a taxonomy grounded in **Wickens’ Multiple Resource Theory (MRT)**, we identified that error rates are significantly higher in categories that require divided attention or continuous state tracking:

- **Ordinary Contact Fouls** (Primary action): ~4% error.
- **Continuous Off-Ball Monitoring** (Lane timing, off-ball fouls): ~10% error.
- **Possession, Boundary, and Gather** (Traveling, Out-of-bounds): ~16% error.
- **Timing and Count** (Defensive 3s, shot clock): **~20% error.**

### The Model: 3.5x Lift
Our post-event risk model (L2-regularized logistic regression) identifies the highest-risk officiating contexts with significant accuracy. In rolling season holdouts, the top 10% highest-risk events were **3.5 times** more likely to be ruled incorrect than the baseline.

| holdout_season | baseline_error_rate | top_10_lift |
| -------------- | ------------------- | ----------- |
| 2021-22        | 7.7%                | 3.45x       |
| 2022-23        | 6.2%                | 3.93x       |
| 2023-24        | 6.0%                | 3.92x       |
| 2024-25        | 4.5%                | 4.00x       |

## Project Status & Methodology

**Note:** This is an ongoing evening/weekend research project exploring human factors engineering in professional sports.

### Where things stand
The main empirical result is unchanged: late-game error risk is **best explained by decision context** (MRT-aligned taxonomy), not broad fatigue, travel, or pace. **Referee assignment rows** are now collected for L2M-backed games from **www.nba.com** embedded game-page data (`__NEXT_DATA__`), not the Stats API. Some older games return HTTP errors on canonical URLs (`/game/{game_id}/…`); the collector falls back to **team subsite** URLs (`/cavaliers/game/{game_id}/…`, etc.) using home/away team IDs stored with each L2M game. Coverage QA and crew exports are documented under [`docs/FUTURE_RESEARCH_DIRECTIONS.md`](docs/FUTURE_RESEARCH_DIRECTIONS.md).

Event counts: the headline **51,130** reviewed L2M events (2018–19 through 2024–25) matches the primary modeling tables (`call_context`, post-event risk model). Analyses that join **playoff** L2M events and assignments use a larger row count (see `results/crew_chief_pipeline_report.md`).

### Research Direction
The goal of this project is to develop a formal framework for **Structural Officiating Risk**. By understanding which calls are neurologically "hardest" for human officials, teams can optimize challenge strategy and the league can design better process supports (e.g., automation for counts, replay-assist for boundaries).

For more in-depth research notes, see:
- [`docs/FUTURE_RESEARCH_DIRECTIONS.md`](docs/FUTURE_RESEARCH_DIRECTIONS.md)
- [`docs/MODEL_LIMITATIONS_AND_ROBUSTNESS.md`](docs/MODEL_LIMITATIONS_AND_ROBUSTNESS.md)
- [`docs/TAXONOMY.md`](docs/TAXONOMY.md)

### Reproduce Results
This project uses a Python-based pipeline for L2M collection and modeling.

```bash
# Core pipeline
python scripts/collect_l2m_reports.py --all-seasons
python analysis/post_event_risk_model.py --mode rolling
python analysis/challenge_alignment.py

# Referee assignments (HTML game pages; use after L2M rows exist)
python scripts/collect_officials.py --from-l2m-reports

# L2M ↔ assignment coverage QA + crew / trio features (CSV + markdown reports)
python scripts/report_l2m_assignment_coverage.py
python analysis/crew_chief_pipeline_analysis.py
```

Generated API caches and the local SQLite database are intentionally ignored by git.
