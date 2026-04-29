# Structural Officiating Risk Index Methods

The Structural Officiating Risk Index (SORI) is an event-level score for NBA Last Two Minute report decisions. It estimates the probability that an L2M-reviewed decision is later graded incorrect by the league, conditional on the structural context of the reviewed event.

## Inputs

The default SORI export uses the frozen taxonomy in `src/referee_fatigue/taxonomy.py` (MRT-aligned structural buckets; see `docs/TAXONOMY.md`), clock context, and period context. When multi-season validation is available, `analysis/sori_export.py` selects the variant with the strongest rolling-season top-decile lift and refits it on all available L2M events before scoring.

Optional enriched features are produced by `scripts/compute_l2m_event_context.py`:

- score margin at the nearest play-by-play action
- tied and one-possession state
- trailing-team action proxy
- final-30-second and overtime indicators
- rebound/scramble sequence indicators

## Outputs

- `results/sori_event_scores.csv`: event-level SORI probability.
- `results/sori_game_scores.csv`: game-level mean and max SORI across L2M-reviewed events.
- `results/sori_category_map.md`: observed error rates by taxonomy category and clock bucket.

## Claims Boundary

SORI ranks L2M-reviewed events by structural error risk. It does not estimate missed calls outside L2M reports, does not measure total referee accuracy, and should not be interpreted as an individual referee quality metric. The core claim is comparative: among reviewed late-game decisions, some structural contexts are more likely to be graded incorrect than others.

Per-game **crew chief / trio familiarity** features (`src/referee_fatigue/crew_features.py`, `analysis/crew_chief_pipeline_analysis.py`) are optional enrichment for heterogeneity analyses; they are not required to reproduce the default SORI CSV exports.

## Negative-Result Framing

Workload, travel, rest, and pace variables remain useful as contrast tests. Current evidence supports the narrower statement that broad schedule-load variables do not explain late-game error risk nearly as well as decision context in the available data.
