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

The post-event risk model ranks structurally high-risk L2M events well, with a held-out top-10% risk bucket showing roughly a 4x lift over baseline in the current 2024-25 sample.

## Reproduce Core Reports

```bash
python scripts/collect_l2m_reports.py --season 2024-25
python scripts/compute_referee_load.py
python scripts/compute_pace_features.py --season 2024-25
python analysis/call_context_l2m.py
python analysis/post_event_risk_model.py
```

Generated API caches and the local SQLite database are intentionally ignored by git.

