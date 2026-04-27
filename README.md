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
```

Generated API caches and the local SQLite database are intentionally ignored by git.
