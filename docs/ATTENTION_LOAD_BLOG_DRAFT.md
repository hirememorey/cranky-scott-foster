# Why NBA Refs Miss Certain Calls

## The Short Version

NBA officiating mistakes are not random. They cluster around the kinds of decisions that ask humans to track too much at once.

We analyzed more than 51,000 NBA Last Two Minute report events from the 2018-19 through 2024-25 seasons. The league marked about 6% of those reviewed decisions as incorrect. But that average hides a big pattern.

Ordinary contact fouls were incorrect about 4% of the time. Timing and count decisions were incorrect about 20% of the time. Possession and boundary decisions were incorrect about 16% of the time. Continuous off-ball monitoring decisions were incorrect about 10% of the time.

The strongest finding is not that NBA referees are bad. It is that some decisions overload human attention more than others, and those decision types are predictable enough to design around.

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

That matters because the model does not know the league's final judgment in advance. It uses call type, structural category, game clock, period, call vs non-call, and related contextual features. The strongest predictors are call structure, not referee workload.

In plain English: the hard calls are partly predictable before we know whether they were missed.

We also tested referee travel miles, back-to-backs, rest days, time-zone crossings, and game pace. None meaningfully predicted error risk in the broad models.

## What This Means For Coaches

The coaching edge is not yelling at refs more. It is allocating late-game attention better.

If certain decision types are structurally higher risk, teams can train staff to watch those situations more deliberately in the final two minutes:

- boundary and last-touch plays
- travels and gather-step ambiguity
- lane violations and other timing/count situations
- defensive three seconds
- off-ball contact away from the ball
- loose-ball and scramble situations

This could plausibly change how benches support challenge decisions, but that part still needs to be tested directly against challenge data. Instead of treating every close call as equally worth reviewing, a team could build a late-game "risk watchlist" around the types of decisions most likely to be wrong.

The theoretical edge is an attention-arbitrage edge. Officials have limited live attention. Coaches have a bench, video staff, and role specialization. If teams know where officiating attention is most likely to break down, they can assign their own attention more efficiently.

## How A Team Could Use It

A practical version might look like this:

- One assistant tracks possession and boundary risk.
- One staffer watches off-ball and lane-count situations.
- Video staff prioritize high-risk rule classes before ordinary contact fouls.
- Players are coached to create clarity in situations where ambiguity and attention load are highest: sidelines, baselines, gathers, lane timing, and off-ball contact.
- Challenge decisions weigh not just importance, but structural miss probability and challengeability.

This does not mean challenging more. It means challenging smarter.

## What This Means For The League

For the league, the takeaway is design-oriented. The problem may not be "more replay for everything." The problem is knowing which kinds of calls need support.

Different high-risk categories point to different fixes:

- timing/count decisions: automation, table-supported count tracking, clock support, or clearer responsibility
- possession and boundary decisions: faster replay assist for last touch, stepped-out, and possession-control plays
- off-ball monitoring: positioning, crew mechanics, or targeted training modules
- ordinary contact fouls: less evidence that broad process intervention is needed

The most interesting cases are high attention load and low support. Those are the moments where elite human officials are being asked to do something that may be predictably difficult.

## What This Does Not Claim

This analysis is based on NBA Last Two Minute reports, not every officiating decision in every game.

It does not show that individual referees are bad. It does not estimate the error rate of all NBA calls. It does not prove fatigue never matters.

The claim is narrower and, hopefully, more useful:

> Among reviewed late-game NBA decisions, some rule contexts overload human attention more than others, and those risks are predictable enough for coaches and the league to design around.
