# Critique Response Guide

Use this document to respond to feedback on the public blog draft, Sloan-style paper framing, or **SSAC-style research competition** review. It translates the strongest critique into claim boundaries, current evidence, and next analyses.

## Current Evidence Snapshot

The defensible JSON-era L2M dataset is `2018-19` through `2024-25`.

- L2M reports: 2,514
- L2M reviewed events: **51,130** (aligned with `results/call_context_l2m_report.md` and rolling model tables)
- Incorrect reviewed decisions: 3,214
- Baseline reviewed-event error rate: about **6.3%**

Structural category error rates from `results/call_context_l2m_report.md` (codes from `classify()` in `src/referee_fatigue/taxonomy.py`, **MRT-grounded**; definitions and legacy name pairs in `docs/TAXONOMY.md`):

- `focal_discrete` (primary-action contact): **4.4%**
- `ambient_continuous` (off-ball / spatial monitoring): **9.6%**
- `focal_continuous` (boundary / gather / travel family): **16.1%**
- `temporal_discrete` (clock / count): **19.8%**
- `administrative_process`: **6.1%**

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

Challenge alignment from `results/challenge_alignment_report.md` (same MRT codes as L2M; regenerate with `analysis/challenge_alignment.py` after taxonomy or DB changes):

- Challenge events analyzed: **4,519** from `2019-20` through `2024-25`.
- `2020-21` challenge coverage is partial; cached pages cover **39.4%** of expected games.
- **`focal_continuous`** (boundary / gather / last-touch family): **43.4%** of mapped challenges, **91.1%** overturn rate (n=1,963)—high L2M error rate and high replay success when challenged.
- **`focal_discrete`** (primary-action contact): **44.1%** of mapped challenges, **37.6%** overturn rate (n=1,991)—challenged often, overturned far less often than `focal_continuous`.
- **`temporal_discrete`** (clock / count): **0.3%** of mapped challenges (n=14), **85.7%** overturn when challenged—rare as a challenge target despite high L2M incorrect rates for that class.

Post-event risk model transparency (run `analysis/post_event_risk_model.py --mode rolling`; final-holdout block trains through `2023-24`, tests `2024-25`):

- `results/model_coefficients.csv` — one-hot feature names, logistic coefficients, odds ratios.
- `results/model_calibration.csv` — binned mean predicted probability vs. observed incorrect rate on the 2024-25 holdout.

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

- **`focal_continuous`** is high incorrect rate in L2M and the strongest mapped full-game challenge target by overturn rate.
- **`focal_discrete`** is challenged about as often but overturned much less often—consistent with replay being a weaker lever for that class.
- **`temporal_discrete`** stays high-risk in L2M but almost never appears as a challenge row—league/process and live-visibility story, not a team replay story.

Do not write:

> Coaches can improve challenge success just by using the L2M risk model.

Write:

> Challenge data suggests a split between team-addressable risks, especially **`focal_continuous`** replay, and league-addressable risks, especially **`temporal_discrete`** and **`ambient_continuous`** (plus anything rarely challengeable).

Also disclose that the challenge sample is full-game, not L2M-only, and `2020-21` coverage is partial.

### "Player behavior and play design claims may overreach"

Agree. The data shows referee-reviewed error risk by decision context. It does not prove that player ambiguity causes those errors or that cleaner player behavior reduces errors.

Safer player-facing framing:

> Teams can reduce exposure to structurally high-risk officiating contexts by emphasizing clarity near boundaries, gathers, lane timing, and off-ball contact late in games.

Avoid implying that ordinary footwork drills are a novel insight or that players can prevent all high-attention officiating errors.

### "Use 'shows' where the data shows"

Use direct language for descriptive rates and model validation:

- The data shows **`temporal_discrete`** (~timing/count) incorrect about **20%** of the time among L2M-reviewed events.
- The data shows **`focal_discrete`** (~primary-action contact) incorrect about **4%** of the time among L2M-reviewed events.
- Rolling season holdouts show high-risk events remain elevated out of sample.
- Robustness checks show the signal weakens but remains above baseline after excluding defensive three seconds and traveling.
- Challenge data shows **`focal_continuous`** rulings are the highest-overturn mapped challenge targets (with selection bias noted elsewhere).

Use softer language for applications that have not been directly tested:

- Teams could use these classes as a review-attention checklist.
- Targeted replay support may be more efficient than universal replay expansion.
- Challengeability and full-game opportunity denominators remain open tests.

## Suggested Blog Draft Edits

Most of the checklist below is now folded into `docs/ATTENTION_LOAD_BLOG_DRAFT.md` (method stack, null workload results, rolling holdout language, challenge caveats, L2M grading confound, SSAC/paper scope pointer). Use this section as a **checklist** when refreshing the public draft after new runs.

- Methodology: model family (regularized logistic regression), feature families, and pointer to `results/model_coefficients.csv` / `model_calibration.csv`.
- Null workload: travel, B2B, rest, time zones, pace.
- Rolling holdout: six future-season evaluations, ~3.5x mean top-decile lift.
- Archetype: **`temporal_discrete`** / **`focal_continuous`** vs **`focal_discrete`** in the same reviewed window (plain language: timing/count, boundary/gather, ordinary contact).
- Challenge framing: **`focal_continuous`** as strongest **mapped** replay opportunity; **`temporal_discrete`** as league/process; **selection bias** caveat explicit.
- League-design bullets: timing/count automation; possession/boundary replay assist; off-ball crew mechanics/training; targeted replay vs universal expansion.

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

## SSAC-Style Competition Review (External Critique)

The following maps a **research competition**–style assessment (novelty, rigor, impact, community interest) to how we answer it **today** vs. what still belongs on a paper roadmap.

### Strengths we lean into

- **Novel angle vs. bias literature:** Reframing from “who do refs favor?” to decision structure / attention design differentiates from home-court, star, and discrimination-focused L2M work.
- **Actionable prescriptions:** Challenge alignment plus layered league vs. team fixes matches what operations-facing venues reward.
- **Public data + scale:** Large multi-season L2M sample; SSAC-style venues increasingly expect **open replication**—this repo is the natural home for that requirement.
- **Temporal validation:** Rolling forward season holdouts and robustness to dropping obvious high-rate call types support “signal not just overfitting” narratives.

### Methodological pushback — how we answer now

| Concern | Response now | Still needed for a finalist-grade paper |
| -------- | ------------ | ---------------------------------------- |
| **Taxonomy feels post-hoc / gerrymandered** | Taxonomy is **rule-based**, versioned in code, and now **explicitly tied to MRT** (focal/ambient, discrete/continuous) *before* citing category error rates in `docs/TAXONOMY.md`. | Pre-registration narrative, **alternate groupings** (split-merge sensitivity), optional manual attention labels on a stratified sample. |
| **Model underspecified** | **Logistic regression** pipeline documented in `analysis/post_event_risk_model.py`; rolling **ROC AUC / average precision** in `results/post_event_risk_model_report.md`; **coefficients + calibration CSVs** for a 2024-25 holdout. | Full coefficient table in paper, formal calibration plots, richer feature ablations in text. |
| **“Cognitive load” is asserted, not measured** | We describe results as **consistent with** divided-attention / process-design hypotheses; fatigue and pace nulls **narrow** but do not eliminate confounds. | Explicit discussion of rule ambiguity, observability, grading strictness; optional instruments or natural experiments if available. |
| **L2M grading confound (video / stopwatch / brackets)** | Must be stated in limitations: league criteria for “incorrect” are not neutral across call families. | Dedicated subsection + sensitivity where bracket language appears in source data, if feasible. |
| **Challenge outcomes ≠ causal replay effectiveness** | Coaches **select** challenges; high overturn on a category mixes **replay clarity** with **selection**. | Denominator on challengeable opportunities; overturn conditional on challenge. |
| **Blog vs. paper** | Blog draft now points readers here and to `docs/SLOAN_RESEARCH_HANDOFF.md` for paper scope. | Formal IMRAD structure, literature review, citations, robustness appendix. |

### Open-source expectation

Venues such as SSAC ask for repository links supporting the work. Treat this GitHub repo as the canonical place for scripts, regenerated `results/`, and frozen taxonomy—**not** only a narrative PDF.

## Do Not Claim

- Do not claim the model measures all NBA officiating decisions.
- Do not claim individual referees are predictably bad.
- Do not claim coaches can win more challenges from the L2M model alone.
- Do not claim player footwork causes the officiating errors.
- Do not claim fatigue never matters; say broad fatigue proxies did not explain L2M error risk in this dataset.
- Do not ignore challenge selection bias; challenge outcomes are chosen by teams and are not a neutral sample of all officiating decisions.
- Do not equate L2M “incorrect” with raw referee error independent of **league review rules** (conclusive video, bracketed/stopwatch-dependent notes).
