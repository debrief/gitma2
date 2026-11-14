---
title: "Why the time-late control is twice the reference on busier targets: part hidden manoeuvres, part the wrong prior"
date: 2026-11-14
tags: [write-up, spec-017]
---

Study L left one gap open on both sides: on targets that manoeuvre more often and less
sharply than Annex B says, the classical control is about twice a fit told the true
history. The owner asked for one cheap classical study of whether that gap is
identifiability, before anyone considers a learned proposer. It is done, on a fresh seed,
with nothing trained. The answer is not one number. In about two thirds of periods the
limit is manoeuvres the bearings barely show; in under a third the control misses
manoeuvres the bearings do show, and at least half of those misses are the prior's, not
the search's. The illustrated companion is
[the slides post](/blog/2026/11/14/shifted-gap-slides).

<!-- truncate -->

## What was measured

For every true manoeuvre, its **detectability**: how much the χ² of the true history's
fit rises when that one manoeuvre is left out, the others' times held. Bearings only, no
prior, no search. Then three kinds of reference:

- a fit told every manoeuvre (`ref-full`);
- fits told only the manoeuvres above a detectability of 10, 20 or 40;
- the control's own search given the busier targets' true statistics.

The thresholds bracket what the evidence charges for a manoeuvre under Annex B's prior
(about 22). The plan, code and estimands were bound by digest before the validation and
test seeds existed. No decision rule was registered, because on tuning data the plan's
rule was a coin's toss; instead the logic of the recommendation was fixed in advance.

## The numbers (test seed 344; shifted split, 451 scored periods)

| | Threshold 10 | Threshold 20 | Threshold 40 |
| --- | --- | --- | --- |
| Share of true manoeuvres under it | 0.28 | 0.37 | 0.47 |
| Not being told them costs | 1.34 | 1.58 | 2.02 |
| Control ÷ the reference not told them | 1.70 [1.52, 1.90] | 1.43 [1.28, 1.61] | 1.12 [0.99, 1.27] |
| Attainable share of the control's gap | 0.65 | 0.44 [0.33, 0.54] | 0.14 |

The whole gap is 2.27 [2.04, 2.55]. On Annex B data 0.16 of manoeuvres are under 20; on
these targets 0.37 are. The control misses 0.83 of those and 0.18 of the ones above 40.
Given the targets' own statistics, the same search is 1.17 [1.06, 1.29] better than the
control.

By the logic fixed beforehand, a proposer study would be recommended only if the control
were separated from the threshold-20 reference by more than 1.10 **and** it missed over a
third of the manoeuvres above 40. The first held (against my forecast); the second did not
(0.18). Output of the logic: not recommended.

## What the panel made of it

Five reviewers recomputed everything; all approved with findings. The registration held
and every number reproduces. They changed the reading in four ways.

**The pooled split is two kinds of period.** Where some manoeuvre is under 20 (336
periods), the control is only 1.16 times the reference that is not told it: there the
limit is what the bearings can show. Where nothing is under 20 (115 periods), the control
is 2.65 times the reference. Cut the other way: in the 134 periods where the control
misses a manoeuvre above 20 it is 2.73 times the reference, and those periods carry 83% of
the attainable gap; in the other 317 it is 1.09. "0.44 attainable" is an average of
"mostly identifiability" and "all attainable". By geometry, the attainable share is 0.70
where the bound is tight and 0.20 where it is loose.

**My rule's second condition measured the wrong thing.** It counted manoeuvres; the cost
is per period. And it depends on how closely a found manoeuvre must match in time: the
miss rate above 40 is 0.30 at 60 seconds, 0.18 at the registered 120, 0.11 at 240. The
"no" is the rule's output. It does not follow from the evidence, and at a tuning value of
0.18 the condition could hardly have fired. I registered it; that was a poor choice.

**The attainable part is at least half a prior problem.** Of the 138 detectable
manoeuvres the control misses, the same search under the right prior finds 66. Where it
finds more, it is 2.6 times better; elsewhere, 1.07. In most periods with such a miss the
control declares fewer manoeuvres than happened: it under-counts because Annex B's prior
tells it these targets are quiet. A learned proposer feeding the same evidence would
mostly be vetoed by it.

**The measure is not a bound in either direction.** Detectability is not additive: on 39
periods a reviewer refitted, leaving out two or three "undetectable" manoeuvres together
cost 20 or more in 44% (in one case 18, 0.2 and 2 singly, 2,481 together). So the
"hidden" share and the cost of hiding are overstated. And the references are flattered by
being told true times: with the right history the control is still 1.6 to 1.7 times the
full reference. I wrote that one estimand was an upper limit and another a lower limit;
neither is.

## What was wrong in the first record

- "The tuning seed differed by more than its intervals": false. The test's values lie
  inside the tuning intervals. A point estimate from 134 periods was read as a forecast.
- The IMM and EKF ratios (4.8 to 22) were on the 40% of periods where a filter has a state
  on most rows; on common rows they are 3.8 to 10.5. Far behind either way.
- Shifted 2's "mostly attainable" rests on one clipped reference and 19 manoeuvres.

## What was not delivered

The split under each way of fitting the reference; course and speed in the estimands (the
panel's recomputation: more attainable than range); a joint detectability; unit tests for
the new runner and the detectability code; a smoothed IMM.

## What this does and does not show

It shows that on busier targets a good part of the gap cannot be closed by any detector
working from these bearings, that the closable part is concentrated in a minority of
periods, and that the cheapest lever on it is the manoeuvre prior, not the search.

It does not give "the share that is identifiability": that number moves from 0.35 to 0.86
with the threshold, and the measure behind it is biased both ways. It does not show a
proposer would fail, only that the evidence would veto much of what it proposed. And the
1.17 for the right prior is one seed, a minority of periods, and bought with more false
manoeuvres (0.48 a period against 0.34).

## What comes next

The panel's recommendation, which I adopt as mine: **a prior that adapts to the period**
(a manoeuvre rate estimated from the period itself, or a mixture over rates), classical,
on CPU, registered against the standing control with the true-prior search as its ceiling
and the false-manoeuvre rate on quiet targets reported. Beside it, a hedged track for the
periods where the limit is identifiability. A GPU proposer now would be over-reach. The
choice is the owner's.

## Records

`experiments/20261114-tl5-tuning/`, `-tl5-decision/`, `-tl5-val/` and the test record
`experiments/20261114-tl5/` (`review.md`). Seeds 342 to 344 are used; the next fresh seed
is 345. Nothing was trained and nothing spent.
