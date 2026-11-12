# Spec 012 panel control: C″ combined with a range prior (nothing trained)

Asked for by the panel (`../20261111-r-test/review.md`): if combining C″'s range with the
simulator's range prior closes most of the regressor's margin over C″ (−0.039), the margin is
shrinkage toward the prior, not anything learnt from the bearings.

## Registration (written before the rule touched the test seed)

Script: `scripts/research/r_prior_control.py`. Per scored row after a manoeuvre, on rows C″
answers: ln range = precision-weighted mean of C″'s ln range (sd = T × its stated
`log_range_sd`, floored at 0.02) and a prior on ln range. Two priors:

- **static**: one mean and sd of ln range for every row;
- **own**: the ownship-only regressor's ln range and stated sd (spec 012's `reg-own`; what
  range is usual given the ownship's track alone).

Fitted on validation seed 327 only (`results/rscore-r-a-val-man2-43083186284`, 3,890 rows,
999 engagements; `validation-fit.json`): the static prior's mean 9.676 and sd 0.668 of ln
range, and T from the grid 1 to 16 minimising the median relative range error: **T = 1.0
(static), T = 1.5 (own)**. On validation: C″ 0.104; C″ + static prior 0.104 (difference
+0.001 [−0.002, +0.003]); C″ + own prior 0.100 (−0.003 [−0.007, +0.001]); regressor seed 1
0.064, still −0.036 [−0.046, −0.030] ahead of the better control.

Applied to test seed 328 unchanged (`--apply validation-fit.json`) on
`results/rscore-r-a-test-man2-43125383838`. Reading, fixed here: the control **explains the
margin** if it closes at least half of regressor − C″ on the test seed (control − C″ at most
−0.019 with its interval below zero); it **does not** if it closes under a quarter (control −
C″ above −0.010); otherwise partial. Forecast from validation: does not.

Limits, known beforehand: one temperature for every row. C″'s stated sd is overconfident
exactly where it has missed a manoeuvre, so a precision weighting cannot shrink where
shrinkage would matter most; a "no" here rules out this simple rule, not every use of the
prior. The hedged-C″ control the panel also asked for is not built.
