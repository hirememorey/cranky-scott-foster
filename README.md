# Cranky Scott Foster

NBA officiating analytics experiments focused on identifying structural contexts that make late-game referee decisions more error-prone.

## What This Contains

- L2M report collection from NBA official JSON endpoints.
- Coach challenge extraction from NBA game play-by-play pages.
- Referee workload features: rest, assignment density, travel miles, and time-zone crossings.
- Pace/load features from NBA play-by-play and team box-score data.
- Event-level L2M context analysis and post-event bad-call risk modeling.

## Current Finding

The strongest signal is not broad fatigue, travel, or pace. It is event structure:

- timing/count judgments
- possession-boundary adjudication
- selected violations and stoppages
- non-calls compared with calls

The post-event risk model ranks structurally high-risk L2M events well across seasons. In rolling season holdouts from 2018-19 through 2024-25, the top-10% risk bucket shows roughly a 3.5x lift over baseline on average.

## Research Direction

The current best path is an MIT Sloan-style paper on structural officiating risk:

> NBA late-game officiating errors are structurally predictable from decision context. Errors concentrate in timing/count, possession-boundary, and off-ball monitoring decisions rather than being broadly driven by referee fatigue, travel, or game pace.

Read the next-developer handoff before extending the project:

- [`docs/SLOAN_RESEARCH_HANDOFF.md`](docs/SLOAN_RESEARCH_HANDOFF.md)
- [`docs/CRITIQUE_RESPONSE_GUIDE.md`](docs/CRITIQUE_RESPONSE_GUIDE.md)

For a short public-facing draft, see:

- [`docs/ATTENTION_LOAD_BLOG_DRAFT.md`](docs/ATTENTION_LOAD_BLOG_DRAFT.md)

## Reproduce Core Reports

```bash
python scripts/collect_l2m_reports.py --all-seasons
python scripts/compute_referee_load.py
python scripts/compute_pace_features.py --all-seasons
python scripts/compute_l2m_event_context.py --all-seasons
python analysis/call_context_l2m.py
python analysis/post_event_risk_model.py --mode rolling
python analysis/model_baselines.py
python analysis/sori_export.py
```

Generated API caches and the local SQLite database are intentionally ignored by git.

