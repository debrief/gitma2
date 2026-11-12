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

## Result on test seed 328 (`test.json`; 7,824 rows, 2,000 engagements; rule unchanged)

The script's own C″ row errors match the scorer's to 2.5e-7. One code change after
registration: the loader now accepts the fit file's wrapper (the first run stopped on a
`KeyError` before computing anything); the rule in `test.json` is asserted equal to the
registered one.

Median relative range error on rows C″ answers; differences with engagement-clustered 95%
intervals:

| System | Median | Difference from C″ | Regressor minus it |
| --- | --- | --- | --- |
| C″ | 0.103 | | −0.038 [−0.045, −0.033] |
| C″ + static range prior | 0.104 | +0.001 [−0.002, +0.002] | −0.038 [−0.044, −0.032] |
| C″ + ownship-only prior | 0.102 | −0.001 [−0.004, +0.001] | −0.036 [−0.043, −0.031] |
| Regressor, seed 1 | 0.066 | | |

By true-range quartile, C″ / C″ + ownship-only prior / regressor: 0.067 / 0.068 / 0.061;
0.097 / 0.095 / 0.063; 0.110 / 0.107 / 0.065; 0.154 / 0.157 / 0.075.

**Reading, as registered: the control does not explain the margin** (it closes about 3% of
it; the threshold for "does not" was under a quarter). Forecast correct.

What this rules out: that the regressor's advantage in median range is C″'s answer pulled
toward the usual range by a precision weighting with one temperature. What it does not rule
out: any use of the prior that knows *when* C″ is wrong. C″'s stated uncertainty does not
know (it is overconfident after a missed manoeuvre), so this rule cannot shrink where it
would matter. The regressor's stated sd, or evidence about the manoeuvre history, could.
The margin is therefore still unexplained: not simple shrinkage, and hedging between
histories remains untested (the hedged-C″ control is not built).
