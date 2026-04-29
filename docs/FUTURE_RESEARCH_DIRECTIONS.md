# Sloan Research Handoff

This project started as a referee fatigue/travel investigation and pivoted after the data did not support that framing. The strongest current direction is an event-context model of NBA late-game officiating risk.

## Research North Star

**Goal:** identify what factors lead to NBA late-game officiating errors, especially in decisions that require continuous off-ball monitoring, timing/count judgment, or possession-boundary adjudication, rather than ordinary contact fouls.

Working thesis:

> NBA late-game officiating errors are structurally predictable from decision context. Errors concentrate in timing/count, possession-boundary, and off-ball monitoring decisions rather than being broadly driven by referee fatigue, travel, or game pace.

The structural buckets are implemented as an **a priori**, **MRT-aligned** taxonomy in `src/referee_fatigue/taxonomy.py` (`focal_discrete`, `focal_continuous`, `ambient_continuous`, `temporal_discrete`, `administrative_process`). See `docs/TAXONOMY.md` for definitions and mapping from legacy report labels.

**SSAC / competition angle:** the idea is competitive as a **novel framing** (design and attention load vs. bias economics) with **practical impact**, but a finalist-level submission still needs the methodological stack called out in `docs/MODEL_LIMITATIONS_AND_ROBUSTNESS.md` (critique / SSAC sections: alternate taxonomies, L2M grading confound, causal language discipline, full paper structure, open repo).

Possible paper title:

> Where NBA Referees Miss: Structural Error Risk in Late-Game Officiating Decisions

## Current Evidence

The current dataset is the JSON-era NBA Last Two Minute report archive from 2018-19 through 2024-25. Earlier centralized archive pages are unavailable or PDF-only in the current collection path.

Key results:

- L2M reports analyzed: 2,514
- L2M events analyzed: **51,130** (current modeling / call-context tables)
- Incorrect decisions: 3,214
- Baseline event error rate: 6.3%
- Rolling season holdouts evaluated: 6
- Mean top-10% predicted-risk lift over baseline: about 3.5x
- 2024-25 holdout: train on 2018-19 through 2023-24, test on 2024-25; top-decile lift about 4.0x
- Robustness: excluding both `Foul: Defense 3 Second` and `Turnover: Traveling` lowers mean top-decile lift to about 2.4x, but the signal remains above baseline.
- Challenge alignment: 4,519 coach challenge events from 2019-20 through 2024-25 are mapped to the structural taxonomy; 2020-21 coverage is partial.
- Possession-boundary challenges: 43.4% of mapped/full challenge events, 91.1% overturn rate.
- Ordinary contact challenges: 44.4% of challenge events, 38.0% overturn rate.
- Timing/count challenges: 0.3% of challenge events despite high L2M risk.

The strongest predictors are event-structure features (see `results/model_coefficients.csv` for a 2024-25 holdout coefficient dump):

- `Foul: Defense 3 Second`
- `Turnover: Traveling`
- `Stoppage: Out-of-Bounds` and related turnover/boundary families
- violation family
- `monitoring_type` MRT buckets (e.g. `ambient_continuous`, `temporal_discrete`)
- 61-90 second clock bucket
- non-call vs call

The fatigue/schedule angle has not shown support so far:

- Back-to-back rest: no meaningful L2M relationship.
- Travel miles: no meaningful L2M relationship.
- Time-zone crossings: no meaningful L2M relationship.
- Pace/action density: no meaningful L2M relationship.

Baseline model comparison adds an important nuance:

- Raw `call_type` is the strongest compact predictor.
- The frozen structural taxonomy is still valuable for interpretation and paper narrative.
- The best public claim is not that the five-category taxonomy captures everything, but that high-risk raw call types share attention-load properties: timing/count state, possession/boundary state, and continuous off-ball monitoring.
- Challenge data supports a practical split: possession/boundary risk is highly replay-addressable for teams, while timing/count and off-ball monitoring look more like league/process-support opportunities.

## What Not To Overclaim

Do **not** claim that referees miss 60% of all defensive three-second violations. The L2M data only includes reviewed calls and notable non-calls in qualifying close-game windows.

Safer claim:

> Among L2M-reviewed late-game events, certain rule categories are disproportionately likely to be judged incorrect by the league.

Also avoid claiming individual referees are predictably bad from this sample. The current signal is primarily decision-context risk, not referee identity.

## Referee assignments and crew pipeline

**Collection.** Crew lists are scraped from public **www.nba.com** game pages (embedded Next.js props). `stats.nba.com` is not used for officials in this workflow. Crew chief is operationalized as the **first official in the page list** (see `scripts/collect_officials.py`). Generic routes such as `/game/{game_id}/play-by-play` sometimes fail for real games; the client retries **team subsite** URLs built from `home_team_id` / `away_team_id` on each L2M row (`src/referee_fatigue/nba_com_team_slug.py`, `NBAStatsClient.get_nba_game_page_data`).

**Coverage.** For distinct L2M games (`l2m_reports.has_report = 1`), assignment QA shows **full trio** rows (exactly one `crew_chief`, `official_2`, `official_3`) aligned with every game in the current database; see `results/l2m_assignment_coverage.md` (from `scripts/report_l2m_assignment_coverage.py`).

**Outputs.** Per-game tenure and trio familiarity features: `results/crew_chief_game_features.csv`; L2M events joined for exploratory tables: `results/crew_chief_pipeline_events.csv`; narrative + diagnostics: `results/crew_chief_pipeline_report.md` (from `analysis/crew_chief_pipeline_analysis.py`). Row counts there include **playoff** L2M events when those games exist in `l2m_reports` and assignments (e.g. **55,490** events vs **51,130** regular-season-only style totals in the core risk-model tables—check each report’s header).

**Next analytical step.** Pre-specify hypotheses for **crew / chief / familiarity × taxonomy** interactions (heterogeneity and descriptive contrasts), not standalone referee quality rankings—consistent with the limitations section.

## Current Reports

- `results/call_context_l2m_report.md`
  - Context taxonomy and error-rate distribution.
- `results/post_event_risk_model_report.md`
  - Rolling season holdout post-event risk ranking model.
- `results/model_coefficients.csv` / `results/model_calibration.csv`
  - Final-holdout logistic coefficients / odds ratios and binned calibration (written by `post_event_risk_model.py` when 2024-25 test rows exist).
- `results/post_event_high_risk_events.csv`
  - Highest-risk scored events for inspection.
- `results/model_baselines_report.md`
  - Rolling holdout comparison of baseline, call type, taxonomy, clock, and context/workload variants.
- `results/sori_event_scores.csv`
  - Event-level Structural Officiating Risk Index scores.
- `results/sori_game_scores.csv`
  - Game-level SORI summaries.
- `results/sori_category_map.md`
  - Category-by-clock observed error-rate map.
- `results/l2m_error_workload_report.md`
  - Rest/travel/time-zone tests.
- `results/pace_l2m_error_report.md`
  - Pace and late-game load tests.
- `results/challenge_alignment_report.md`
  - Coach challenge behavior by structural category, raw action type, season, and coverage.
- `results/challenge_coverage_by_season.csv`
  - Challenge extraction coverage by season; `2020-21` remains partial.
- `results/l2m_robustness_report.md`
  - Rolling holdouts after excluding key high-risk labels, rare call types, and structural categories.
- `results/h1b_challenge_overturn_report.md`
  - Original challenge-overturn fatigue screen.
- `results/l2m_assignment_coverage.md`
  - L2M games vs full referee-assignment trio coverage by season and RS/playoffs.
- `results/crew_chief_pipeline_report.md`
  - Crew chief tenure, trio familiarity buckets, and exploratory taxonomy tables (see § Referee assignments and crew pipeline).
- `docs/MODEL_LIMITATIONS_AND_ROBUSTNESS.md`
  - Claim boundaries and response guidance for public/Sloan feedback (includes critique / SSAC framing).

## Best Next Steps

### 1. Close The Pre-2018 Data Question

The current code collects centralized JSON-era archive links from 2018-19 onward. The 2015-16 and 2016-17 centralized archive URLs return 404, and 2017-18 appears PDF-only in the NBA archive page.

Why this matters:

- A Sloan-quality paper needs a clean inclusion/exclusion rationale.
- Parsing 2017-18 PDFs may add one more season, but the current JSON-era dataset is already large enough for the main result.

Implementation notes:

- Either build a PDF parser for 2017-18 and earlier single-report PDFs, or explicitly define the dataset as the 2018-19 to 2024-25 JSON-era sample.
- Do not mix PDF-derived rows into the analysis without validating that fields match JSON-derived rows.

### 2. Freeze A Defensible Taxonomy

The taxonomy is **frozen in code** (`src/referee_fatigue/taxonomy.py`) and documented in `docs/TAXONOMY.md`.

Current top-level **MRT** categories (stable strings from `classify()`):

- `focal_discrete` — primary-action contact fouls.
- `ambient_continuous` — divided-attention / off-ball spatial monitoring (e.g. defensive three seconds, many screens, loose-ball positioning).
- `temporal_discrete` — clock/count administration intersecting discrete events.
- `focal_continuous` — boundary/gather/travel/out-of-bounds family requiring sustained spatial tracking.
- `administrative_process` — replay, timeouts, many technicals, clock/stoppage process.

Why this matters:

- Categories are defined by **stated cognitive demand**, not by error rates.
- A rigorous paper still needs **robustness to alternative groupings** and honest discussion of **L2M grading rules** that differ by call type (conclusive video, bracketed stopwatch plays).

### 3. Validate By Season

Use season-level holdouts:

- Train on seasons up to year N.
- Test on season N+1.
- Report top-decile lift and ROC AUC by season.

The key Sloan chart should be:

> Top-decile structural-risk events are X times more likely to be incorrect out of sample.

Benchmarks to include:

- Baseline error rate.
- Call type only.
- Call vs non-call only.
- Taxonomy only.
- Taxonomy + clock context.
- Taxonomy + referee/workload variables.

The current evidence suggests context-only will perform nearly as well as the fuller model. That is a strength, not a weakness.

### 4. Add A Practical Risk Index

Turn the model into a usable metric:

> Structural Officiating Risk Index (SORI)

Possible outputs:

- Event-level risk score: probability an L2M-reviewed decision is incorrect.
- Game-level structural risk: average/max expected risk across events in the last two minutes.
- Category-level risk map: which rule classes create the most audit risk.

This gives the paper an applied contribution beyond prediction.

### 5. Use Challenge Alignment As Secondary Applied Evidence

Current answers:

- Possession-boundary plays are both structurally risky in L2M and highly successful challenge targets.
- Ordinary contact fouls are challenged just as often, but have much lower overturn rates.
- Timing/count plays are high-risk in L2M but nearly absent from coach challenges.

Interpretation:

This connects L2M review, replay/challenges, and officiating process design. It supports a split between team-addressable risks, especially possession/boundary replay, and league-addressable risks, especially timing/count and off-ball monitoring.

Remaining caveat:

- Challenge events are full-game, not L2M-only.
- `2020-21` challenge coverage is partial in the current cache-backed collection.
- Challenge share is not denominator-matched to all challengeable opportunities.

### 6. Add Game Context

High-value additions:

- score margin at event time
- tied vs one-possession state
- trailing team possession
- final 30 seconds vs 31-60 vs 61-90 vs 91-120
- overtime
- rebound/scramble indicators from comments or play-by-play action types
- drive/shot/rebound/turnover sequence context

These should be treated as event-context variables, not referee-fatigue variables.

### 7. Keep Fatigue As A Negative Result

The project started with fatigue, but current tests suggest it is not the main effect.

Use it as a useful contrast:

> Broad schedule-load variables do not explain late-game error risk nearly as well as structural decision context.

That makes the paper more credible because it shows the analysis rejected the initial hypothesis.

## Suggested Paper Structure

1. Introduction
   - NBA officiating transparency via L2M reports.
   - Problem: aggregate accuracy hides structurally hard decision classes.

2. Data
   - L2M reports, calls/non-calls, reviewed event categories.
   - Coach challenges as secondary validation.
   - Referee schedule/travel and pace features as rejected/secondary hypotheses.

3. Taxonomy
   - Define structural monitoring categories with an explicit **MRT** (focal vs ambient, discrete vs continuous) mapping.
   - Explain cognitive demands: continuous state tracking, divided attention, boundary ambiguity—without claiming direct cognitive load measurement from L2M labels alone.

4. Descriptive Results
   - Error rates by category.
   - Non-call vs call asymmetry.
   - Clock/OT context.

5. Predictive Model
   - Held-out game/season split.
   - Risk deciles and lift over baseline.
   - Feature interpretation.

6. Robustness
   - Season holdouts.
   - Baselines.
   - Exclude rare categories and high-risk labels.
   - Compare with referee/workload variables.

7. Practical Implications
   - Replay support.
   - Training emphasis.
   - Rule/process design for high-risk categories.
   - Potential automated timing/count support.

8. Limitations
   - L2M selection bias.
   - Not a complete sample of all officiating decisions.
   - League audit criteria may vary; **grading standard differs** for plays requiring conclusive video or technical aids (stopwatch/zoom/bracket language in league guidance).
   - Challenge merge is descriptive (full-game challenges vs. L2M window); **coach selection** biases overturn rates.
   - Some event context inferred from text.

## Completed Developer Checklist

1. Add multi-season L2M archive discovery.
2. Freeze taxonomy in a dedicated module, not inside one analysis script.
3. Rebuild `post_event_risk_model.py` to support season holdout mode.
4. Produce a season-by-season lift table.
5. Add simple baselines and compare model variants.
6. Add a `SORI` score export for all L2M events.
7. Run challenge-alignment analysis by structural taxonomy and raw call type.
8. Add robustness checks excluding `Foul: Defense 3 Second`, `Turnover: Traveling`, rare call types, and structural categories.
9. Write public/methods guidance describing exactly what the model can and cannot claim.

## Current Next Developer Checklist

1. Pre-specify estimands for **crew / experience / trio familiarity × structural taxonomy** (interaction vs additive contrasts; game- or season-level validation)—step 3 of the internal roadmap.
2. Decide whether to parse pre-2018 PDFs or formally define the sample as JSON-era only.
3. Manually label 100-200 events for attention-load properties to support the conceptual thesis beyond NBA call labels.
4. Build a challengeability/opportunity denominator: which full-game events were actually challengeable, not just which were challenged.
5. Improve or explicitly bracket `2020-21` challenge coverage.
6. Tighten final Sloan paper language around L2M selection bias and full-game challenge selection bias.

**Recently completed (assignment pipeline):** full L2M-driven officials backfill with HTML-only collection and team-site URL fallbacks; automated `l2m_assignment_coverage` report; refreshed crew game features and pipeline markdown.

