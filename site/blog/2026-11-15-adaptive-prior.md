---
title: "A manoeuvre prior that adapts to the period: no gain, and why one period cannot choose its prior"
date: 2026-11-15
tags: [write-up, spec-018]
---

Spec 017 said the closable part of the gap on busier targets was largely the prior's. The
owner chose to try the classical remedy: a control that infers how the target manoeuvres
from the period itself, with a hedged track beside it. It is done, on a fresh seed, with
nothing trained. The adaptive control gains nothing on busier targets, so by the rule
registered beforehand the standing control stays. My forecast, written from the tuning
seed, said otherwise and was wrong. The illustrated companion is
[the slides post](/blog/2026/11/15/adaptive-prior-slides).

<!-- truncate -->

## What was built

**Two designs, both on the tuning seed.** The first ran a search under each of three
manoeuvre rates and let the period's evidence choose. It gained nothing: one period did
not identify the rate. The second, which was registered, uses a family of 30 priors (how
long the legs are, how regular, how large the turns), scores one shared set of candidate
histories under each, and declares under the member with the most evidence. Beside it, a
hedged track: the weighted mean of every member's candidates, with a stated spread in
range.

The plan, code and conditions were bound by digest before the validation and test seeds
existed. The conditions read paired period error and coverage, not counts: a lesson from
the last panel.

## The registered outcome (test seed 347, 1,250 periods)

Standing control ÷ system, in range (above 1: the system is better):

| Split (scored periods) | Adaptive, declared | Adaptive, hedged |
| --- | --- | --- |
| Shifted (355) | 1.00 [0.92, 1.08] | 1.00 [0.93, 1.08] |
| Shifted 2 (137) | 1.01 [0.92, 1.11] | 0.99 [0.89, 1.09] |
| Annex B (273) | 0.93 [0.85, 1.01] | 0.92 [0.84, 1.01] |
| Held course (172) | 1.05 [0.98, 1.13] | 1.02 [0.94, 1.12] |
| Outliers (93) | 0.95 [0.79, 1.16] | 0.94 [0.79, 1.11] |
| Correlated (93) | 0.85 [0.71, 1.00] | 0.89 [0.74, 1.06] |

No gain on either busier-target split for either output. The hedged track reads as harm
in course on two splits. Its stated spread covers 0.94 of rows on Annex B targets and 0.90
on shifted, at the edge of the registered band. **The standing control stays.**

On the tuning seed the same comparison was 1.10 and 1.16 on shifted targets. I forecast a
trade from that. The 60-period validation seed had already shown 0.95 and 1.04.

## What the panel made of it

Five reviewers recomputed all 36 cells and the registration; all approved with findings.
The outcome stands. Several of my secondary sentences did not.

**What the null means.** The evidence of one period does not rank these priors by how
accurate they are. Its preference among the 30 members is nearly flat (the favourite has
a probability of about 0.13), and on shifted targets a member's probability and its error
are uncorrelated. The member chosen is 1.9 times worse than the member that would have
been best in hindsight, and only 3 to 5% better than one sensible fixed member. The choice
avoids bad priors. It does not adapt. A period holds two to five manoeuvres: too few to
say what kind of target made them.

**How tight the null is.** The test could have detected a gain of 12%. Pooled over three
seeds the declared control is 1.01 [0.95, 1.08]: gains above about 8% are excluded, small
ones are not. I wrote that the tuning seed had flattered the design "by all of the
effect"; that overstates what one test shows.

**The cost on Annex B targets is real and is the design's.** Pooled over three seeds:
0.91 [0.84, 0.98]. The standing control searches under Annex B's own prior; my family did
not include it. Where the control's answer came from that prior the adaptive control is
0.89; elsewhere 1.05.

**The family was not blind.** I set its grid after the first tuning run had told me what
the first grid lacked, and it sits close to the test splits' own statistics. That favoured
it. It gained nothing all the same.

**The reference it was chasing is a tail.** The search told the true statistics is 1.10
here, 1.15 [1.07, 1.23] over three seeds. Ten shifted periods of 355 carry 87% of that
gain, and in 13% of periods it is over twice as bad as the control. I had called it a
ceiling. It is not one.

**The hedge is not worth having as built.** It costs about 10% in course on every split,
as a tail, and is level in range. Its spread cannot be stated by one factor: the factor
that gave 95% coverage on the tuning seed was 1.95 and on the test seed would be 2.68,
both set by about twenty periods. The spread is honest where the candidates disagree and
too narrow where the mixture is confident and wrong.

## What was wrong in the first record

- "The true statistics are worth less than spec 017 found": sampling. Three seeds agree.
- "The inferred rate barely moves": it moves, by about half the true difference, widely
  scattered per period.
- "It loses where the bearings say most": one seed's subgroup, a tail, not repeated.
- "None of the three is it": the members refit shared candidates and other parts of the
  prior were never varied.
- "Not honest by three parts in a thousand": shifted coverage is 0.897 [0.870, 0.923].

## What was not delivered

A family member with Annex B's own prior; a search under each member; unit tests of the
runner and the spread code; the tuned IMM and EKF on these periods; a spread for course
and speed; a per-period rule for choosing between declared and hedged output that does
anything.

## What this does and does not show

It shows that this evidence, on one period, cannot tell which of a family of manoeuvre
priors is the right one, and that a hedged mean of candidates is no better than the
declared history. On quiet targets the adaptive control invents fewer manoeuvres (3% of
periods against 8%), a gain not separated in error and reversed on the tuning seed.

It does not show that priors cannot be adapted: a longer history of the same target, a
different evidence, or a family that contained the truth's other dimensions were not
tested. It does not show a learned model would fail, though a model facing the same two
to five manoeuvres has the same information.

Across specs 013 to 018 the time-late picture is steady. The arc model and Annex B's
statistics brought a factor of two over the old system. Editing and an honest bearing sd
removed most of the damage from bad bearings. On targets unlike Annex B's, about two
thirds of the remaining gap is manoeuvres the bearings do not show, and the rest has now
resisted a learned model and a classical one.

## What comes next

The panel's recommendation, which I adopt as mine: **stop trying to identify the prior,
and write up the time-late track (specs 013 to 018) as a whole**, with the classical
control standing. The alternatives are in the question put to the owner. A learned
proposer or any GPU run would be over-reach.

## Records

`experiments/20261114-tl6-tuning/`, `experiments/20261115-tl6-tuning2/`, `-tl6-decision/`,
`-tl6-val/` and the test record `experiments/20261115-tl6/` (`review.md`). Seeds 345 to
347 are used; the next fresh seed is 348. Nothing was trained and nothing spent.
