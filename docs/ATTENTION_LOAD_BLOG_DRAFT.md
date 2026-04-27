# Why NBA Refs Miss Certain Calls

## The Short Version

NBA officiating mistakes are not random. They cluster around decisions that ask humans to track too much at once.

We analyzed **51,130** NBA Last Two Minute report events from the 2018-19 through 2024-25 seasons. The league marked about **6.3%** of those reviewed decisions as incorrect. But that average hides a big pattern.

For exposition we group decisions into four intuitive buckets; in the research code these map to a **pre-specified taxonomy** grounded in **Wickens-style multiple resource theory** (focal vs. ambient monitoring, discrete vs. continuous state), not tuned to error rates:

- **Ordinary contact fouls** (primary-action fouls): incorrect about **4%** of the time.
- **Timing and count** decisions: incorrect about **20%** of the time.
- **Possession, boundary, and gather** judgments (traveling, out of bounds, similar): incorrect about **16%** of the time.
- **Continuous off-ball monitoring** (e.g., lane timing, many off-ball fouls): incorrect about **10%** of the time.

The strongest finding is not that NBA referees are bad. It is that different calls place different demands on attention and parallel tracking, and those risks are predictable enough to design around—while staying clear that we are **not** measuring cognitive load directly.

## Why This Makes Sense

A shooting foul usually happens near the ball. Everyone is watching the same action.

But many high-risk calls ask officials to monitor several things at once:

- Is a defender in the lane for too long?
- Did the ball handler gather before or after the pivot foot moved?
- Who touched the ball last near the sideline?
- Did a player step out before regaining possession?
- Did an off-ball player create illegal contact away from the main action?

These are not just "judgment calls." They are attention-load calls. They require officials to track position, time, possession, player movement, and sometimes off-ball action at the same time.

## What The Model Found

In the strictest current test, we trained on prior seasons and tested on the next season. Across six future-season holdouts, the top 10% highest-risk events were about **3.5 times** more likely to be ruled incorrect than the average reviewed event.

The estimator is **L2-regularized logistic regression** on one-hot-encoded categoricals (including call type / family, MRT structural bucket, period and clock buckets, decision kind, score and possession proxies, sequence context) plus scaled numeric context; see `analysis/post_event_risk_model.py`. Rolling holdouts report **ROC AUC** roughly **0.66–0.73** by season (full table in `results/post_event_risk_model_report.md`). For a fixed **2024-25** holdout, the repo also writes **`results/model_coefficients.csv`** (coefficients and odds ratios) and **`results/model_calibration.csv`** (binned predicted vs. observed incorrect rates) for transparency.

The strongest predictors are **call structure and context**, not referee workload proxies.

The signal is not just one weird rule. It gets weaker when defensive three seconds and traveling are removed, but it does not disappear: in that stricter check, the top-risk decile still ran about 2.4 times baseline.

We also tested referee travel miles, back-to-backs, rest days, time-zone crossings, and game pace. None meaningfully predicted error risk in the broad models.

In plain English: the hard calls are partly predictable before we know whether they were missed.

## What Challenge Data Adds

Coach challenges show that not all high-risk calls are equally usable by teams.

Across **4,519** coach challenge events from the 2019-20 through 2024-25 seasons (full game, not L2M-only), **possession/boundary-style** plays were the clearest replay opportunity in our mapping: about **43%** of challenges and overturned about **91%** of the time.

**Ordinary contact** fouls were challenged about as often (~**44%**) but overturned only about **38%** of the time.

**Timing/count** decisions are different: high incorrect rates in L2M, but they were almost absent from the challenge sample. That pattern is consistent with mistakes that are hard to see live, hard to challenge, or not cleanly packaged as replay opportunities.

**Selection caveat:** coaches choose what to challenge; high overturn rates on a category do not by themselves prove replay “fixes” that call type—they also reflect which disputes teams bother to mount.

## What This Means For Teams

The edge is not yelling at refs more. It is allocating attention better.

Teams already scout opponents, lineups, shot profiles, and late-game tendencies. They should also scout officiating risk: which actions create boundary ambiguity, gather-step confusion, off-ball contact, lane timing, or scramble situations.

A practical version might look like this:

- One assistant tracks possession, last-touch, and boundary risk.
- One staffer watches off-ball and timing/count situations.
- Video staff prioritize possession and boundary reviews before emotional contact challenges.
- Players are coached to create clarity near sidelines, baselines, gathers, lane timing, and off-ball contact.
- Challenge decisions weigh importance, structural miss probability, and challengeability.

This does not mean challenging more. It means knowing which mistakes replay can actually fix.

## What This Means For The League

For the league, the takeaway is design-oriented. The problem may not be "more replay for everything." The problem is matching the support to the type of decision.

Different high-risk categories point to different fixes:

- possession and boundary decisions: faster replay assist for last touch, stepped-out, and possession-control plays
- timing/count decisions: automation, table-supported count tracking, clock support, or clearer responsibility
- off-ball monitoring: positioning, crew mechanics, or targeted training modules
- ordinary contact fouls: less evidence that broad process intervention is needed

Some errors are replay-solvable. Some are attention-design problems. Some are ordinary judgment calls. Treating them as one big "refs missed it" bucket is less useful than asking what kind of decision broke down.

## What This Does Not Claim

This analysis is based on **NBA Last Two Minute (L2M) reports**, not every officiating decision in every game. L2M uses the league’s own review standard: among other things, the NBA requires **clear and conclusive video** to mark a play incorrectly officiated, and may bracket or treat differently events that depend heavily on **stopwatch, zoom, or other technical support**. That means category-level “error” rates mix **officiating difficulty** with **how the league grades each call family**—an important confound for any paper, not something this blog post can fully disentangle.

The challenge sample is **full-game**, not L2M-only, so merging it with L2M is descriptive alignment, not a causal link. Coverage is strong for most seasons, but **2020-21** is partial in the current challenge collection.

We do **not** observe cognitive load, eye tracking, or brain activity. Higher incorrect rates in some call families are **consistent with** attention-load and divided-attention stories, but **observational** alternatives remain: rule ambiguity, observability and camera geometry, harsher league grading for some play types, and different baselines for how “marginal” calls are.

It does not show that individual referees are bad. It does not estimate the error rate of all NBA calls. Broad **fatigue / travel / pace** proxies did not explain much in our models; that is **not** the same as proving fatigue never matters in any form.

The claim is narrower and, hopefully, more useful:

> Among reviewed late-game NBA decisions, some rule contexts are disproportionately likely to be graded incorrect—and that pattern is stable enough across seasons to be useful for process design, challenge strategy, and honest limits on what replay can fix.

For SSAC-style competition, this draft is still a **popular summary**, not a full paper: a submission would need formal literature review, methods detail, robustness to alternate taxonomies, explicit handling of L2M grading rules, and open replication artifacts (see `docs/CRITIQUE_RESPONSE_GUIDE.md` and `docs/SLOAN_RESEARCH_HANDOFF.md`).
