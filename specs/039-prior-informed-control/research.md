# Research: spec 039

## R1 What the control must be

The regressor minimises an error under the simulator's distribution; C″ and the solve told the
true times return the mode of a likelihood. A Gaussian prior on range added to that solve
(spec 012's control, spec 037's static prior, spec 038's ownship-only prior) moves a mode very
little when the likelihood's valley is long and skewed, and the mode is not the estimate that
minimises a median relative error anyway. **Decision**: integrate along the valley. Profile the
cost over range at the row, weight by the prior, report the posterior median.
**Alternatives**: a particle filter under the simulator's prior (a large build; the structure
prior is the hard part and is part 3); a Laplace mean (the valley is not Gaussian).

## R2 The profile

- One unconstrained robust solve fixes the whiteners (Huber weights, fitted error model). Each
  grid point is a refit with the range at the row held to 0.2% by one prior row
  (`HybridLayer`), under those whiteners; its cost is the whitened bearing χ².
- Grid: 20 points, 1 to 80 km, geometric, plus nine points about the mode at ±0.5 to ±2.5 sds of
  the mode's own covariance, so a tight posterior is resolved.
- Weight: exp(−½ Δχ² ÷ T) × the table's density of ln range × a soft indicator of the speed at
  the row lying in the generator's support. T = 1, or the variance inflation the fitted error
  model implies for a mean (`temper: effective`).
- Read-out: the median of that density over ln range (trapezoid rule on the uneven grid); the
  velocity interpolated linearly between the two neighbouring refits; the position along the
  nearer refit's line of sight.
- **A profile is not a marginal**: the volume of the other parameters is ignored. Stated in the
  record; the flat-prior variant measures what "median of the profile against its mode" does
  without any prior.
- **First look** (three engagements of spent seed 321 under the primary condition): the read-out
  moved the range by 0.01 to 0.45 in ln on every row, with errors both much better and much
  worse than the mode's. It moves the solve; whether it helps is the development run's question.

## R3 The prior table

`configs/pic/prior-man2.json`: ln range at the scored rows over 15,921 engagements of spent seed
321 under MAN2's ranges (5% / 50% / 95%: 4.2 / 17.3 / 39.1 km), 40 bins; speed support from the
ranges file. The table must be smoother than the grid (a window narrower than the grid's spacing
is read as flat; found by a test). Seed 321's own engagements are development data for other
readings; the development run uses seed 370 and the test 373, so the table is never scored on
the engagements it was built from.

## R4 Choice rule (FR-010)

On the true segmentation, seed 370: the variant (tempered or not) with the larger pooled log
range ratio plain ÷ prior-informed over clean and primary. Moves-the-solve check (FR-011): the
share of rows with |Δ ln range| > 0.1, by thirds of the bound.

## R5 Estimands and thresholds

As spec FR-020 to FR-023, with spec 038's panel's lessons: every share is given as a mean, a
ratio of medians and trimmed at both ends; pooled over the conditions the choice rule pooled;
split differences with yardstick ÷ reference and reference ÷ system beside. Lines are set after
the development run and checked over bootstrap seeds.

## R6 The cut evidence search (part 3)

`timelate` solves a period (t, ownship, bearings, validity, σ). A prefix [0, k] is a period; the
control `ctl` (spec 016) run on it and read at its last moment is a causal estimator told Annex
B's manoeuvre prior. To measure on 50 development engagements at the last scored row: accuracy
beside the same rows' C″-robust, told-truth solve and regressor, and seconds per estimate.
Registered only if 300 engagements × 4 rows fit the CI budget.
