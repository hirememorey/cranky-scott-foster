# Why NBA Refs Miss Certain Calls

## The Short Version

NBA officiating mistakes are not random. They cluster around decisions that ask humans to track too much at once.

We analyzed more than 51,000 NBA Last Two Minute report events from the 2018-19 through 2024-25 seasons. The league marked about 6% of those reviewed decisions as incorrect. But that average hides a big pattern.

Ordinary contact fouls were incorrect about 4% of the time. Timing and count decisions were incorrect about 20% of the time. Possession and boundary decisions were incorrect about 16% of the time. Continuous off-ball monitoring decisions were incorrect about 10% of the time.

The strongest finding is not that NBA referees are bad. It is that different calls place different loads on human attention, and those risks are predictable enough to design around.

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

In the strictest current test, we trained on prior seasons and tested on the next season. Across six future-season holdouts, the top 10% highest-risk events were about 3.5 times more likely to be ruled incorrect than the average reviewed event.

The model uses call type, structural category, game clock, period, call vs non-call, and related contextual features. The strongest predictors are call structure, not referee workload.

The signal is not just one weird rule. It gets weaker when defensive three seconds and traveling are removed, but it does not disappear: in that stricter check, the top-risk decile still ran about 2.4 times baseline.

We also tested referee travel miles, back-to-backs, rest days, time-zone crossings, and game pace. None meaningfully predicted error risk in the broad models.

In plain English: the hard calls are partly predictable before we know whether they were missed.

## What Challenge Data Adds

Coach challenges show that not all high-risk calls are equally usable by teams.

Across 4,519 challenge events from the 2019-20 through 2024-25 seasons, possession and boundary plays were the clearest replay opportunity. They made up about 43% of challenges and were overturned about 91% of the time.

Ordinary contact fouls were challenged just as often, about 44% of the sample, but were overturned only about 38% of the time.

Timing and count decisions are different. They are high-risk in Last Two Minute reports, but they were almost absent from the challenge sample. That suggests many of those mistakes are hard to see live, hard to challenge, or not cleanly packaged as replay opportunities.

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

This analysis is based on NBA Last Two Minute reports, not every officiating decision in every game.

The challenge sample is full-game, not just Last Two Minute plays. Coverage is strong for most seasons, but 2020-21 is partial in the current collection.

It does not show that individual referees are bad. It does not estimate the error rate of all NBA calls. It does not prove fatigue never matters.

The claim is narrower and, hopefully, more useful:

> Among reviewed late-game NBA decisions, some rule contexts overload human attention more than others. Some of those risks are addressable by team challenge discipline, while others require better league-side support systems.
