# Critique Response Guide

Use this document to respond to feedback on the public blog draft or Sloan-style paper framing. It translates the strongest critique into claim boundaries, current evidence, and next analyses.

## Current Evidence Snapshot

The defensible JSON-era L2M dataset is `2018-19` through `2024-25`.

- L2M reports: 2,514
- L2M reviewed events: 51,384
- Incorrect reviewed decisions: 3,214
- Baseline reviewed-event error rate: about 6.3%

Structural category error rates from `results/call_context_l2m_report.md`:

- `ordinary_contact_foul`: 4.4%
- `continuous_off_ball_monitoring`: 9.6%
- `possession_boundary_adjudication`: 16.1%
- `timing_count_judgment`: 19.8%

Rolling season holdout from `results/post_event_risk_model_report.md`:

- Holdout seasons evaluated: 6
- Train on prior seasons, test on next season.
- Mean top-decile lift: 3.5x.
- 2024-25 holdout: train on `2018-19` through `2023-24`, test on `2024-25`; top-decile error rate 18.2% vs 4.5% baseline, 4.0x lift.

Baseline comparisons from `results/model_baselines_report.md`:

- `call_type_only`: strongest mean top-decile lift, 3.5x.
- `taxonomy_context_workload`: 2.9x.
- `taxonomy_clock`: 2.6x.
- `taxonomy_only`: 2.6x.
- `call_vs_non_call`: 1.1x.
- baseline error rate: about 1.0x.

Robustness checks from `results/l2m_robustness_report.md`:

- Full-sample mean top-decile lift: 3.5x.
- Excluding `Foul: Defense 3 Second`: 3.1x.
- Excluding `Turnover: Traveling`: 2.9x.
- Excluding both `Foul: Defense 3 Second` and `Turnover: Traveling`: 2.4x.
- Excluding raw call types with fewer than 100 events: 3.3x.

Challenge alignment from `results/challenge_alignment_report.md`:

- Challenge events analyzed: 4,519 from `2019-20` through `2024-25`.
- `2020-21` challenge coverage is partial; cached pages cover 39.4% of expected games.
- `possession_boundary_adjudication`: 43.4% of challenges, 91.1% overturn rate.
- `ordinary_contact_foul`: 44.4% of challenges, 38.0% overturn rate.
- `timing_count_judgment`: 0.3% of challenges despite high L2M risk.

Negative result from `results/l2m_error_workload_report.md` and `results/pace_l2m_error_report.md`:

- Travel miles, immediate previous-game miles, time-zone crossings, and back-to-backs do not meaningfully explain L2M error rates in the broad workload models.
- Full-game pace, Q4 pre-L2M action density, and L2M action density do not meaningfully explain L2M error rates.

## How To Answer The Main Critique

### "The 3.5x lift is weaker than the old 4.2x"

Agree and clarify. The old 4.2x was from the original 2024-25-only split. The current `3.5x` is the stronger number for publication because it is averaged across rolling future-season holdouts.

Recommended wording:

> The original 2024-25-only model showed about 4x lift, but the better test is cross-season validation. Training on prior seasons and testing on future seasons, the top-risk decile is 3.5x more likely to be incorrect on average. When trained on `2018-19` through `2023-24` and tested on `2024-25`, the top decile is 4.0x baseline.

### "The coaching challenge section now has evidence, but is still bounded"

Partly agree, then update. The project now has secondary challenge evidence, but it should be framed narrowly.

What the data supports:

- Possession/boundary decisions are both structurally high-risk in L2M and highly successful challenge targets.
- Ordinary contact fouls are challenged just as often, but overturn far less often.
- Timing/count decisions are high-risk in L2M but nearly absent from the challenge sample.

Do not write:

> Coaches can improve challenge success just by using the L2M risk model.

Write:

> Challenge data suggests a split between team-addressable risks, especially possession/boundary replay, and league-addressable risks, especially timing/count and off-ball monitoring.

Also disclose that the challenge sample is full-game, not L2M-only, and `2020-21` coverage is partial.

### "Player behavior and play design claims may overreach"

Agree. The data shows referee-reviewed error risk by decision context. It does not prove that player ambiguity causes those errors or that cleaner player behavior reduces errors.

Safer player-facing framing:

> Teams can reduce exposure to structurally high-risk officiating contexts by emphasizing clarity near boundaries, gathers, lane timing, and off-ball contact late in games.

Avoid implying that ordinary footwork drills are a novel insight or that players can prevent all high-attention officiating errors.

### "Use 'shows' where the data shows"

Use direct language for descriptive rates and model validation:

- The data shows timing/count decisions are incorrect about 20% of the time among L2M-reviewed events.
- The data shows ordinary contact fouls are incorrect about 4% of the time among L2M-reviewed events.
- Rolling season holdouts show high-risk events remain elevated out of sample.
- Robustness checks show the signal weakens but remains above baseline after excluding defensive three seconds and traveling.
- Challenge data shows possession/boundary rulings are high-overturn challenge targets.

Use softer language for applications that have not been directly tested:

- Teams could use these classes as a review-attention checklist.
- Targeted replay support may be more efficient than universal replay expansion.
- Challengeability and full-game opportunity denominators remain open tests.

## Suggested Blog Draft Edits

Add one methodology sentence:

> The model uses call type, structural taxonomy, game clock, period, call vs non-call, and contextual features. The strongest predictors are call structure, not referee workload.

Add one null-result sentence:

> We also tested referee travel miles, back-to-backs, rest days, time-zone crossings, and game pace. None meaningfully predicted error risk in the broad models.

Make the split explicit:

> In the strictest current test, the model is trained on prior seasons and tested on the next season. Across six future-season holdouts, the top-risk decile is 3.5x baseline on average.

Add one concrete archetype:

> A timing/count or possession-boundary event in the last two minutes is several times more likely to be judged incorrect than an ordinary shooting or personal foul in the same reviewed window.

Use current challenge framing:

- Possession/boundary is the strongest team-facing replay opportunity.
- Timing/count and off-ball monitoring are better framed as league/process-design opportunities.
- Keep the "attention allocation" theory; it remains the strongest coaching idea.

Expand the league-design section:

- Timing/count: automated or table-supported count/clock tracking.
- Possession/boundary: faster replay assist for last touch, stepped-out, and possession-control plays.
- Off-ball monitoring: crew responsibility changes, positioning review, and training modules.
- Replay policy: targeted support for high-load classes, not universal expansion.

## Highest-Value Follow-Up Analysis

### Challengeability And Opportunity Denominators

Purpose: move beyond "what was challenged" to "what could have been challenged."

Questions:

- Which full-game actions were challengeable?
- Within challengeable opportunities, which structural categories are challenged most often?
- Are possession/boundary challenges high-overturn because teams select only obvious winners, or because the category itself is structurally replay-friendly?
- Which L2M high-risk classes are not challengeable, only challengeable when called, or practically hard to detect live?

Expected output:

- challengeability map by taxonomy category and raw call type
- denominator-matched challenge rates by category
- overturn rate by category conditional on challengeability
- explicit league-side vs team-side opportunity split

### Manual Attention Labels

Purpose: move from call labels to the attention-design thesis.

Sample:

- 100 to 200 L2M events across high-risk and low-risk classes.

Labels:

- off-ball monitoring required
- timing/count state required
- boundary/possession state required
- simultaneous contact and possession judgment
- replay/challenge support available
- obvious live visibility vs divided-attention visibility

Expected claim:

> High-risk call types share attention-load properties that are visible beyond the raw NBA call label.

## Recommended Public Thesis

> Among reviewed late-game NBA decisions, errors are not evenly distributed. They concentrate in rule contexts that overload human attention: timing and count judgments, possession and boundary adjudication, and continuous off-ball monitoring. Some of those risks are addressable through team challenge discipline, especially possession/boundary replay, while others require league-side support systems.

## Do Not Claim

- Do not claim the model measures all NBA officiating decisions.
- Do not claim individual referees are predictably bad.
- Do not claim coaches can win more challenges from the L2M model alone.
- Do not claim player footwork causes the officiating errors.
- Do not claim fatigue never matters; say broad fatigue proxies did not explain L2M error risk in this dataset.
- Do not ignore challenge selection bias; challenge outcomes are chosen by teams and are not a neutral sample of all officiating decisions.
