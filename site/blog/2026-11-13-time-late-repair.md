---
title: "Time-late, repaired and re-registered: the numbers hold, the rule says no, and the reference turns out to matter most"
date: 2026-11-13
tags: [write-up, spec-015]
---

Spec 014's panel found two defects in registered code: the evidence gave a manoeuvre's
duration far too much volume, and the classing counted manoeuvres cut by a period's edge. It
also found the true-history reference drifting into other histories. The owner chose to
repair and re-register. Spec 015 fixed the three, decided the same five quantities on fresh
seeds (336 validation, 337 test) and trained nothing. The registered figures reproduce, and
the registered rule again says no GPU budget. The panel approved with findings, and its main
one is that the headroom figure now depends most on the thing we repaired last: how the
reference is fitted. The illustrated companion is
[the slides post](/blog/2026/11/13/time-late-repair-slides).

<!-- truncate -->

## What was repaired

- **The evidence** (prior version 3). Every factor of the prior that has no Gaussian
  residual now gets a Laplace volume equal to one over its density at the fit, so a density
  and its volume cancel when the bearings say nothing. Spec 014's version kept about 600 s
  of volume for a duration whose density is tens of seconds wide.
- **One edge rule** (`timelate/match.py`). A manoeuvre cut by the period's start or end is
  neither required nor counted against a history, wherever two histories are compared.
- **The reference.** If the true-history fit moves a manoeuvre more than 120 s from the
  truth it is refitted with the times held, and the period is flagged.
- **Tables** are generated from `summary.json` by a script; a test checks them.

## What was decided (test seed 337, Annex B data, 364 scored periods)

| | Quantity | Spec 014 (seed 335) | Spec 015 (seed 337) |
| --- | --- | --- | --- |
| D1 | Share of the search's gain obtained by refitting C″'s own manoeuvre times | 0.43 [0.28, 0.58] | 0.33 [0.20, 0.45] |
| D2 | First candidate right | about 0.60 edge-aware | 0.64 [0.59, 0.69] |
| D2 | Wrong histories: ambiguous / search failure / evidence failure | 0.57 / 0.11 / 0.33 edge-aware | 0.44 / 0.13 / 0.43 |
| D3 | Headroom with a perfect search | 1.04 | 1.06 [1.01, 1.11], inconclusive |
| D3 | Headroom with a perfect evidence as well | 1.10 [1.04, 1.18] | 1.17 [1.10, 1.25], inconclusive (lower limit 1.099) |
| D4 | Held-course periods given a manoeuvre: search | 0.76 | 0.53 [0.48, 0.58] |
| D4 | ... C″ / flat prior / mixed prior | 0.02 / 0.01 / 0.03 | 0.02 / 0.01 / 0.00 |
| D5 | A learned whole-period model | no GPU budget by the rule | no GPU budget by the rule |

C″ read as a track against the repaired search is 2.10 [1.82, 2.44] paired per period (0.083
against 0.039 in median period range error); the true history with the prior is at 0.028.
Soundness on both fresh seeds passed.

## What the panel made of it

Five reviewers, all approve with findings, one round (`experiments/20261113-tl3/review.md`).
They recomputed every decided number from the per-row errors and found no bug that changes
one. What they changed is what the numbers mean.

**The headroom figure rests on the repaired reference.** In the composite that stands for "a
perfect evidence", 73 of 364 periods are replaced by the true-history fit. Nineteen of those
fits were held to the true times, and they carry a third of the gain. A fit told when the
target manoeuvred knows more than which history is right. By reference convention the figure
runs from 1.11 to 1.19, and only "times held everywhere" clears the line. Ten periods carry
over half of it; several are runaways of the search that a guard might remove. So the first
record's "between 10% and 30% to win, most likely 17%" is withdrawn: an oracle is 8% to 30%
ahead depending on convention, and what a real identifier would obtain is less and unmeasured.

**The rule says no, and the first record tried to soften that.** The lower limit missed the
10% line by a thousandth, and the record called the decision "a judgement, and the owner's".
The panel: the rule was written so that inconclusive counts as not material; an override is
a departure from it, not a reading of it. It also notes that a rule we forecast as a coin's
toss should not have been registered as a decision instrument: at 364 periods it could
barely decide.

**The repair of the evidence is real and not finished.** On held course the false-manoeuvre
rate fell from 0.80 (spec 014's search on the same periods) to 0.53, and under 30 minutes
from 0.50 to 0.09. A reviewer integrated the evidence numerically on 34 periods: the
remaining rate is the prior's (Annex B says a target probably manoeuvres within the hour),
not approximation error. But the same integration shows the low rate on short periods is
not what a correct evidence gives either: summed over where a manoeuvre might be, the prior
favours "some manoeuvre" almost everywhere, because the bearings are silent about it. And
the new pairing fails at the edges of the prior's support, where most invented manoeuvres
sit (1 to 3.5 nats). That is the fifth error of this family.

**The repair is not free.** The repaired search calls a one-manoeuvre target quiet in 13% of
cases against 4% before. Those are not suppressed manoeuvres: integrated numerically they
are within a nat of undecidable. A mixed prior with a stated half chance of a quiet target
removes the false manoeuvres (0.00) and raises the misses to 20%; re-ranked at a 1% chance
it gives 0.09 and 14%. The right setting is a small one, and no split here has a mixed
population to tune it on.

**D1 is "between a third and a half"** and mostly restates how often C″ has the history
right: there the refit obtains all of the search's gain, elsewhere a quarter.

**D2's split between "ambiguous" and "evidence failure" is the threshold's.** At thresholds
1, 3 and 5 the ambiguous share is 0.11, 0.44 and 0.66. Only "search failure is the smallest
class" survives.

## What was not delivered

- The effect of each repair on each decided quantity on the same periods: only D4 and the
  first candidate were shown, and the repairs were not separated. The panel separated them
  for the first candidate (edge rule +0.10, evidence +0.04 to +0.05).
- D2 at every registered sensitivity (the panel supplied it).
- Unit tests for the code that computes the decided statistics.
- The refit's fall-back, built to catch runaway refits, caught one of seven.
- The forecasts held in five of seven rows, but they restated a development run made
  minutes earlier; the one forecast of a quantity known to move, D1, missed.

## Where this leaves a learned model

Nothing here shows that learning cannot help, nor that it would. Where the simulator's
assumptions hold (Annex B statistics, independent Gaussian errors) an oracle is 10% to 20%
ahead of the search and 400 periods cannot decide a 10% line. Where they fail the gaps are
large: the search is 1.7 times the oracle under a shifted prior, 1.4 under correlated errors,
1.5 with outliers. No classical remedy has been tried on any of the three, so a learned win
there today could not be told from a missing Huber cost or a broader prior. This project has
been caught that way three times.

The panel's order, for the owner to choose from:

1. A hedged track from the stored candidates and a declaration margin: cheap, classical.
2. A robust likelihood, a correlated-error likelihood and a prior that can be wrong, scored
   on the shifted, correlated and outlier splits at more than one severity.
3. Then a learned whole-period model, registered against 1 and 2 on those splits.
4. No fourth Annex B identification study.

No GPU run starts without the owner.

## Records

`experiments/20261113-tl3-decision/` (registration), `-dev/`, `-val/`,
`experiments/20261113-tl3/` (test record, `tables.md`, `review.md`). Seeds 336 and 337 are
used; the next fresh seed is 338.
