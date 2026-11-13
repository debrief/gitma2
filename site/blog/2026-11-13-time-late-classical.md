---
title: "Time-late, the classical follow-on: what the search is worth, what it gets wrong, and two faults the panel found"
date: 2026-11-13
tags: [write-up, spec-014]
---

Gate T showed that a classical search over manoeuvre histories halves the track error of the
standing classical system, and its review panel showed that this did not yet say where the
gain comes from or how much is left. The owner chose classical work first. Spec 014 trained
nothing: it built the missing controls, tested the owner's bearing-rate thinning idea, looked
at targets that never manoeuvre, and registered a study on a fresh test seed. The numbers
reproduce. The panel found two defects in the registered code and narrowed most of what was
first said. This post reports both; the illustrated companion is
[the slides post](/blog/2026/11/13/time-late-classical-slides).

<!-- truncate -->

## What was asked

Four questions, with forecasts written before the fresh seeds existed
(`experiments/20261112-tl2-decision/`), and a rule fixed before any tuning result for the
fifth:

1. How much of the search's gain over C″ comes without a search, by refitting C″'s own
   manoeuvre times with the same arc model and prior?
2. When the search names the wrong history, is that the search's fault, the evidence's, or
   can the bearings not decide?
3. How much would a better identifier of histories gain?
4. How often is a manoeuvre declared on a target that made none?
5. Is a learned whole-period model worth the GPU budget? Only if the answer to 3 is material
   against 10%.

It was registered as a study, not a gate: nothing is carried or stopped by a threshold. The
panel's view is that the fifth question is in effect a gate with a failable line, and should
be read as a rule's output.

## The result on test seed 335

Four hundred periods on Annex B data, 300 under a shifted manoeuvre prior, 400 in which the
target holds course, 100 each with correlated and outlying bearing errors, and 60 whole
engagements.

| | Question | Forecast | Result |
| --- | --- | --- | --- |
| D1 | Share of the gain from refitting C″'s times | 0.75 | 0.43, interval 0.28 to 0.58 |
| D2 | Wrong histories: ambiguous, search failure, evidence failure | 0.45, 0.10, 0.45 | 0.53, 0.08, 0.39 |
| D3 | Headroom with a perfect search; with a perfect evidence as well | inconclusive; material | 1.04, not material; 1.10 (1.04 to 1.18), inconclusive |
| D4 | False manoeuvres on held course: search, C″, flat prior, mixed prior | 0.80, 0.03, 0.02, 0.10 | 0.76, 0.02, 0.01, 0.03 |
| D5 | Learned whole-period model | by the rule | no GPU budget |

Three of the decided forecasts were wrong, all in the direction one tuning seed of 134
periods had pointed.

![Every system on three splits](/img/2026-11-13-time-late-classical-slides/systems.svg)

The search's gain over C″ holds on a third seed: C″ ÷ search is 2.13 period by period
(1.88 to 2.43) on Annex B data, 1.53 under the shifted prior, and 4.09 on whole engagements.

## Two defects in the registered code

The panel's code reviewer found faults that move decided numbers. They are recorded, not
repaired: the code is registered, and a repair is a new registration.

**The evidence over-credits small, short manoeuvres.** The prior says a minimum-size change
lasts 20 to 120 seconds, but the volume the evidence allows for a manoeuvre's duration was
left at about 600 seconds. Each small manoeuvre gets a bonus it has not earned. The
manoeuvres the search invents on quiet targets are exactly of this kind: speed changes of
about a metre a second over twenty seconds. Re-ranking the stored candidates with a
corrected volume gives a false-manoeuvre rate of 0.47 to 0.57, not 0.76. This is the fourth
error of this family in the prior; the first three were found by Gate T's panel and fixed
here, and all three penalised an extra manoeuvre. The one left rewards it.

**The classing counted manoeuvres cut by the period's edge**, which the spec says to leave
out. Without them the wrong histories divide 0.57, 0.11, 0.33 and the search's first
candidate is right in about 60% of periods, not 51%.

A third weakness is not a bug but matters as much: the fit "told the true history" is free
to move its manoeuvre times, and in 13% of periods it moved them far enough to be a
different history. The composite used for headroom is therefore a noisy oracle, not an
upper limit.

## What the panel narrowed

**The search's share is about half.** The registered 0.43 depends on four refits that ran
away numerically; without them it is 0.52, and by other reasonable definitions 0.39 to
0.58. Over three seeds, 0.47. Gate T's panel said "mostly smoothing"; the fair statement is
"about half", and the refit is handicapped because it inherits C″'s missed manoeuvres. The
cleaner split was sitting in the results: a search told nothing of how targets manoeuvre
obtains 0.78 of the gain. Annex B's statistics are worth about a fifth.

![The decided quantities on three seeds](/img/2026-11-13-time-late-classical-slides/decided.svg)

**The headroom is on the line, not below it.** With a perfect evidence it is 1.10 at the
registered threshold, 1.18 and 1.05 at the other two thresholds registered as
sensitivities, 1.17 if the reference's times are held, and 1.25 if every wrong period is
counted. "Inconclusive" is robust. "Little left to win", which the first draft said, is not.

**"Ambiguous" does not mean the bearings cannot decide.** It means this approximate
evidence was within a factor of twenty, and the evidence's own noise is that large. On
those periods the search's track is still twice as bad as the fit told the history.

**The rule reads the easy case.** On Annex B data the search holds the simulator's own
motion model, prior and noise law, so little headroom is expected. Under the shifted prior,
correlated errors and outliers the same statistic is 1.5 to 1.6, and no remedy of any kind
was built: the prior-mismatch work in the spec was cut.

![Correlated and outlying bearing errors](/img/2026-11-13-time-late-classical-slides/conditions.svg)

## A target that never manoeuvres

![False manoeuvres on held course](/img/2026-11-13-time-late-classical-slides/quiet.svg)

On 400 held-course periods the informed search declares a manoeuvre in 76% and its track is
twice as bad as C″'s. Part of that is the defect above. Part is the prior: Annex B makes an
hour with no manoeuvre improbable, and over an hour the rate is 98 to 100%. But under thirty
minutes it is still 46%, and it happens on 4 of Annex B's own 11 quiet periods. A small
manoeuvre the bearings cannot rule out costs nothing net under this evidence.

A prior mixed half and half with "the target never manoeuvres" brings the rate to 3%. The
first draft said "at no cost". The panel showed the cost: it now calls a manoeuvring target
quiet in 7.8% of Annex B periods against 1.9%, and on targets that manoeuvre once, 20%
against 6%. The 3% also depends on the half. And the search with no manoeuvre statistics at
all already gives 1%.

## The thinning idea

The owner asked whether runs of bearings at a steady bearing rate could be replaced by fewer
observations (`experiments/20261112-tl2-thin/`, tuning seed only).

![Thinning forms](/img/2026-11-13-time-late-classical-slides/thinning.svg)

- Dropping bearings loses information and saves no time.
- Fixed normal points (one fitted bearing per bin) cost 1% to 9% and halve the search's run
  time, but the intervals reach 20% to 30%: not separated from free, nor from a real cost.
- Bins set by bearing-rate steadiness cost 25% to 50%. The panel showed why this says
  nothing about the idea: the rule that ends a bin was tripping on noise, so the bins were
  set by noise, not by the bearing rate.
- With 2% wild bearings, editing them out before forming points brought the search back to
  clean-data quality. The edit was not separated from the binning, and a robust cost in the
  fit was not tried.

By the rule written beforehand nothing was adopted. The rule needed more periods than were
run, and that was knowable. The idea is not tested yet.

## What this supports

On simulated data, with a fitting model that is the simulator's own:

- A whole-period search halves C″'s track error where targets manoeuvre as Annex B says, and
  about half of that is available without a search.
- With the evidence as it stands, faults included, the search is 5% to 25% from a fit told
  the history's structure, depending on convention.
- That evidence invents small manoeuvres on quiet targets.

It does not show that learning cannot help, that half of wrong histories are beyond any
identifier, or that 76% is what a sound evidence would do. It is silent on a model that
hedges across histories instead of naming one, which is what the spec 012 regressor did.

## The recommendation, read fairly

The registered rule says no GPU budget for a learned whole-period model, and it was applied
as written. What the evidence says is narrower. Where targets behave exactly as the
simulator says, a model trained to identify histories has about 10% to win, on the line.
Where the prior or the error model is wrong, the gap is 50% to 60%, and neither a classical
nor a learned remedy has been tried.

## What was not achieved

The prior-mismatch diagnostic and a broadened prior; an IMM smoother (the smoothed EKF that
was run is no use on manoeuvring targets); the wild-bearing edit on test data; a test of the
owner's thinning idea that is not confounded by noise; a posterior-weighted track from the
candidates. The per-row errors are on the results branch, not in the repository.

## What comes next

The panel's order: repair the evidence, the classing and the reference and run again under
a new registration; then the classical work against the real gaps (a robust likelihood in
the search, a correlated-error model, a prior that can be wrong); then a hedged track as the
classical control; and only then a learned model. The choice is the owner's.

Records: `experiments/20261112-tl2-decision/`, `20261112-tl2-tuning/`, `20261112-tl2-thin/`,
`20261112-tl2-val/`, `20261112-tl2/` (`review.md`).
