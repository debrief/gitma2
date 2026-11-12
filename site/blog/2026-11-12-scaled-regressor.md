---
title: "The scaled regressor: a learned control that beat the classical system, and what that does not show"
date: 2026-11-12
tags: [write-up, spec-012]
---

Spec 012 trained a direct sequence-to-state model on about twenty million simulated
engagements, on a rented GPU, as a control: what does a learned model with no physics layer
and no segmenter reach, and what does it not? On a fresh test seed it is partial against the
bound on a steady target and it beats the standing classical system after target manoeuvres.
The second result is the first time in this project that something learned has clearly beaten
the classical line. The review panel accepted the measurements and rejected most of what was
first said about them. This post reports both.

<!-- truncate -->

## What was built

A causal transformer (8 layers, width 256, 6.4 million parameters) reads the bearings and the
ownship's track and outputs range, course and speed with a stated spread for range and speed.
It never sees a physics layer. Training data are drawn on the fly from generator 0.6.0 (seed
326), a fifth of them with the target holding course. Three seeds, a model trained on a tenth
of the data, and a model that sees only the ownship's track were trained on Tesla T4s through
Modal: 38 GPU-hours, $25.81 of the owner's $50 budget. Two of the three seeds stopped at 91%
and 97% of their planned updates when their time limits ran out; this was disclosed before
scoring and not repaired.

Two readings were registered before any scored run, with thresholds
(`experiments/20261111-r-decision/`): efficiency against the Cramér–Rao bound where the target
holds course (reaches: below 1.25 in range, course and speed; floor: above 2.0), and paired
differences from the standing classical system C″ and the tuned IMM after manoeuvres.
Forecasts were written down too.

## The readings on test seed 328

**Held course: partial, as forecast.** Error as a multiple of the bound, 7,816 rows from
1,990 engagements:

| System | Range | Course | Speed |
| --- | --- | --- | --- |
| Least squares | 0.99 | 0.97 | 0.98 |
| Regressor, three seeds | 1.13 to 1.16 | 1.74 to 1.81 | 1.42 to 1.43 |
| A tenth of the data | 1.22 | 2.05 | 1.57 |
| Ownship only | 11.5 | 28.7 | 15.6 |

The pooled range figure flatters the model. By geometry quartile it runs 1.81, 1.20, 1.00
and 0.84 from best to worst: furthest from the bound where the bearings fix the target best,
and below the bound where they fix it worst. An unbiased estimator cannot be below the bound.
The model is biased toward what the simulator usually does, and where the bearings say
little that bias helps.

**After manoeuvres: the regressor beats C″, against the forecast.** Median relative range
error on rows both answer, with engagement-clustered 95% intervals:

| | Regressor (seed 1) | C″ | Difference |
| --- | --- | --- | --- |
| Range | 0.066 | 0.105 | −0.039 [−0.045, −0.033] |
| Range, metres | 1,008 | 1,665 | −657 [−765, −565] |
| Course | 9.6° | 12.7° | −3.1° [−4.0, −2.3] |
| Speed | 1.34 kt | 1.47 kt | −0.14 kt [−0.23, −0.05] |

Seeds 2 and 3 agree (range differences −0.038). The forecast was "worse than C″, better than
the IMM"; the first half was wrong on validation and wrong again on test.

Medians are not the whole picture. Against the bound on settled rows the regressor is better
than C″ in range (1.71 against 2.52), about level in speed (2.48 against 2.63) and **worse
in course** (3.40 against 3.19). The solve told the true manoeuvre times is at 1.65, 2.04
and 1.86.

## What the panel made of it

Three independent reviewers; all three approved with findings
(`experiments/20261111-r-test/review.md`). The measurements were checked against the raw
files and stand. Four claims in the first draft of the record do not:

1. **"The first clear result for learning" was too broad.** The model knows the simulator's
   ranges, speeds and manoeuvre statistics, and its loss targets the quantity that is scored.
   C″ uses none of that. The supportable statement is narrower: a prior-informed estimator
   trained to minimise the scored error beats a prior-free fit, in median range.
2. **"It holds on ranges the model never saw" was wrong.** The second test split differs only
   in initial range (20 to 30 km against 2 to 20 km); the manoeuvre statistics are the same
   and the realised ranges overlap training. On it the margin falls from −0.054 in the
   nearest quartile to −0.014 [−0.050, +0.025] in the farthest: it vanishes exactly where the
   model has to extrapolate. On the test seed the margin grows with range.
3. **The explanation offered was untested.** The draft said the model probably hedges between
   manoeuvre histories that the bearings cannot separate. That was carried over from spec
   013's tuning data, has not been tested on this model, and the far-range collapse is not
   what hedging predicts.
4. **"More data or a bigger model would not help" did not follow.** The tenth-of-data model
   varies data, not capacity, and on held course it is clearly worse.

## The control the panel asked for

If the margin were simply C″'s answer pulled toward the usual range, a classical rule could
reproduce it. We built that rule: C″'s range combined, by precision weighting, with a range
prior (either one fixed distribution or the ownship-only model's output). Its one setting was
fitted on the validation seed and committed before the rule touched the test seed
(`experiments/20261112-r-control/`).

| System | Median range error, test seed |
| --- | --- |
| C″ | 0.103 |
| C″ with a fixed range prior | 0.104 |
| C″ with the ownship-only prior | 0.102 |
| Regressor | 0.066 |

The control closes about 3% of the margin. **It is not simple shrinkage.** The rule has a
known weakness: C″'s stated uncertainty is overconfident exactly when it has missed a
manoeuvre, so a precision weighting cannot shrink where shrinking would matter. What the
control rules out is the easy explanation, not every use of prior knowledge.

## What this supports

- After manoeuvres, on this simulator, a model that has learnt the simulator is better in
  median range than the best classical system we have, by about 650 m at these ranges, and
  the gap is not explained by a range prior bolted onto the classical answer.
- It is still a control and is not carried. It states no usable uncertainty, gives no
  manoeuvre times, is 1.75 times the bound in course on a steady target (3.2 times in the
  best geometry), and is worse than C″ in course efficiency after manoeuvres.
- Nothing here supports a claim outside the simulator. The model's advantage may be made of
  knowing Annex B's statistics exactly, which no real target obeys.

## What was not achieved

- The source of the margin. The second control the panel asked for (C″ hedged between its
  histories by evidence) is not built.
- A naive estimator on the same rows, which the specification requires, is missing from
  this scorer's output.
- The seeds are reported singly, not pooled as registered.
- The larger-model run (an addendum to the decision record) was not run; the owner paused
  GPU work to turn to the time-late problem.

## What comes next

Spec 013 (time-late) is now building the classical estimator this result needs as its
proper comparison: a search over manoeuvre histories scored by evidence under the same
manoeuvre statistics the regressor learnt. A learned model that beats *that* would be a
result about learning. One that only beats a prior-free fit is a result about priors. The
remaining GPU budget, about $24, is held until that control exists.

Records: `experiments/20261111-r-decision/`, `20261111-r-runs/`, `20261111-r-val/`,
`20261111-r-test/` (with `review.md`), `20261112-r-control/`. Slides:
[the illustrated companion](/blog/2026/11/12/scaled-regressor-slides).
