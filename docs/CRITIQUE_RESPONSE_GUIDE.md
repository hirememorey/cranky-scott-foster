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

Negative result from `results/l2m_error_workload_report.md` and `results/pace_l2m_error_report.md`:

- Travel miles, immediate previous-game miles, time-zone crossings, and back-to-backs do not meaningfully explain L2M error rates in the broad workload models.
- Full-game pace, Q4 pre-L2M action density, and L2M action density do not meaningfully explain L2M error rates.

## How To Answer The Main Critique

### "The 3.5x lift is weaker than the old 4.2x"

Agree and clarify. The old 4.2x was from the original 2024-25-only split. The current `3.5x` is the stronger number for publication because it is averaged across rolling future-season holdouts.

Recommended wording:

> The original 2024-25-only model showed about 4x lift, but the better test is cross-season validation. Training on prior seasons and testing on future seasons, the top-risk decile is 3.5x more likely to be incorrect on average. When trained on `2018-19` through `2023-24` and tested on `2024-25`, the top decile is 4.0x baseline.

### "The coaching challenge section is plausible but not proven"

Agree. The current project shows that some L2M decision classes are structurally higher risk. It does **not yet** show that coach challenges are miscalibrated or that challenges in those classes are more likely to succeed.

Use hypothesis language until challenge alignment is added:

> This could plausibly improve challenge discipline, but the next analysis should test whether current challenges target the same high-risk classes and whether overturn rates track structural risk.

Do not write:

> Coaches can improve challenge success by using these classes.

Write:

> Coaches may be able to allocate live review attention more efficiently if challengeable high-risk classes are under-recognized.

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

Use softer language for applications that have not been directly tested:

- Coaches could plausibly use these classes as a review-attention checklist.
- Targeted replay support may be more efficient than universal replay expansion.
- Challenge alignment remains an open test.

## Suggested Blog Draft Edits

Add one methodology sentence:

> The model uses call type, structural taxonomy, game clock, period, call vs non-call, and contextual features. The strongest predictors are call structure, not referee workload.

Add one null-result sentence:

> We also tested referee travel miles, back-to-backs, rest days, time-zone crossings, and game pace. None meaningfully predicted error risk in the broad models.

Make the split explicit:

> In the strictest current test, the model is trained on prior seasons and tested on the next season. Across six future-season holdouts, the top-risk decile is 3.5x baseline on average.

Add one concrete archetype:

> A timing/count or possession-boundary event in the last two minutes is several times more likely to be judged incorrect than an ordinary shooting or personal foul in the same reviewed window.

Soften the coaching section:

- Replace "teams can improve challenge discipline" with "teams could test whether a high-risk decision checklist improves challenge discipline."
- Replace "players are coached to avoid self-inflicted late-game risk" with "teams can emphasize clarity in situations where ambiguity and attention load are highest."
- Keep the "attention allocation" theory; it is the strongest coaching idea.

Expand the league-design section:

- Timing/count: automated or table-supported count/clock tracking.
- Possession/boundary: faster replay assist for last touch, stepped-out, and possession-control plays.
- Off-ball monitoring: crew responsibility changes, positioning review, and training modules.
- Replay policy: targeted support for high-load classes, not universal expansion.

## Highest-Value Follow-Up Analysis

### Challenge Alignment

Purpose: convert the coaching-edge hypothesis into evidence.

Questions:

- Which structural classes are challenged most often?
- Which structural classes have the highest overturn rates?
- Are high-risk L2M classes under-challenged because they are not visible live or not challengeable?
- Do overturned challenges concentrate in possession/boundary classes while L2M incorrect non-calls concentrate in timing/count or off-ball monitoring?

Expected output:

- `results/challenge_alignment_report.md`
- challenge count by taxonomy category
- overturn rate by taxonomy category
- challengeability notes by class
- comparison against L2M incorrect rate by category

### Rare-Type Robustness

Purpose: defend against "this is just defensive three seconds and traveling."

Tests:

- Exclude `Foul: Defense 3 Second`.
- Exclude `Turnover: Traveling`.
- Exclude all call types with fewer than 100 events.
- Re-run rolling holdouts.

Expected claim:

> The signal weakens but remains directionally present if the result is structural rather than one-call-type driven.

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

> Among reviewed late-game NBA decisions, errors are not evenly distributed. They concentrate in rule contexts that overload human attention: timing and count judgments, possession and boundary adjudication, and continuous off-ball monitoring. These risks are predictable across seasons, which means coaches and the league can design review attention, training, and replay support around them.

## Do Not Claim

- Do not claim the model measures all NBA officiating decisions.
- Do not claim individual referees are predictably bad.
- Do not claim coaches can already win more challenges from this alone.
- Do not claim player footwork causes the officiating errors.
- Do not claim fatigue never matters; say broad fatigue proxies did not explain L2M error risk in this dataset.
