# Gate 4 validation baseline (spec 009 T009)

How usable each estimator's uncertainty statement is today, before any statement is fitted.
Seed 314 validation, scoring ordinals 500–1499 (1,000 scenarios, the σ = 1° G5 rows of the Gate 3
baseline). Scoring run 42533994834 (`results/score-g4-base-val-42533994834`, commit 7216105,
AMD EPYC 7763), plan `plan.json` (= `configs/score/g4-base-val.json`). Every estimator was reused
from the Gate 3 baseline's `errors.npz` (run 42480880386): no estimator was re-solved, and no
calibrated or stated estimator was scored. Not gate mode.

None of these estimators states a statement of its own, so each is given the one its Gaussian
sds imply (`eval.calibration.statement_from_sds`): course arc X = min(45°, 1.96 sd) with
P = the normal probability of ±X; range and speed half-widths 1.96 sd; the course log score of a
von Mises with that sd. A row with no usable covariance states nothing (P = 0, not covered, the
uniform's log score). Intervals: 97.5%, 2,000 scenario-clustered resamples.

## Overall

Reliability is hit rate minus mean stated P (0 when P is honest); the log gain is the mean course
log score minus the uniform's (above 0: more informative than "course unknown").

| Estimator | Mean P | Reliability | Mean X (°) | Course log gain | Cov95 log range | Cov95 speed | No estimate |
|---|---|---|---|---|---|---|---|
| C | 0.904 | -0.384 [-0.409, -0.360] | 17.428 | -2.617 [-2.948, -2.284] | 0.607 [0.582, 0.632] | 0.635 | 0.006 |
| e-s3 | 0.904 | -0.396 [-0.420, -0.370] | 16.579 | -2.587 [-2.923, -2.266] | 0.598 [0.573, 0.624] | 0.647 | 0.010 |
| ew-s3 | 0.904 | -0.405 [-0.430, -0.380] | 16.315 | -2.759 [-3.119, -2.430] | 0.569 [0.543, 0.594] | 0.616 | 0.012 |
| veto-w6-fade | 0.908 | -0.388 [-0.411, -0.364] | 16.818 | -2.527 [-2.855, -2.199] | 0.613 [0.587, 0.637] | 0.636 | 0.006 |
| oracle | 0.891 | -0.117 [-0.137, -0.098] | 24.152 | 1.046 [0.859, 1.228] | 0.875 [0.858, 0.892] | 0.912 | 0.000 |
| imm | 0.522 | -0.095 [-0.120, -0.070] | 32.057 | -0.356 [-0.513, -0.205] | 0.405 [0.376, 0.435] | 0.730 | 0.225 |
| ekf | 0.770 | -0.738 [-0.761, -0.712] | 1.567 | -10.088 [-10.441, -9.700] | 0.046 [0.037, 0.055] | 0.049 | 0.188 |
| one_leg | 0.726 | -0.682 [-0.707, -0.656] | 2.737 | -9.158 [-9.535, -8.754] | 0.099 [0.085, 0.115] | 0.095 | 0.232 |
| glr_confirm | 0.746 | -0.509 [-0.536, -0.484] | 11.315 | -5.035 [-5.381, -4.683] | 0.248 [0.224, 0.272] | 0.353 | 0.203 |

Reliability by five equal-count bins of P (stated / hit):

| Estimator | Bin 1 | Bin 2 | Bin 3 | Bin 4 | Bin 5 |
|---|---|---|---|---|---|
| e-s3 | 0.72 / 0.63 | 0.95 / 0.47 | 0.95 / 0.49 | 0.95 / 0.48 | 0.95 / 0.46 |
| oracle | 0.67 / 0.70 | 0.94 / 0.76 | 0.95 / 0.81 | 0.95 / 0.78 | 0.95 / 0.82 |
| imm | 0.00 / 0.00 | 0.24 / 0.37 | 0.58 / 0.61 | 0.83 / 0.64 | 0.95 / 0.51 |

## Reading

- E (e-s3) states its course within ±16.6° on average with P 0.90, and is right on 0.51 of rows:
  reliability −0.40, and its course statement is 2.6 nats worse per row than saying "unknown",
  because a confidently wrong course costs a large log loss. Its range and speed 95% intervals
  cover 0.60 and 0.65.
- Even the oracle (known manoeuvre times) is overconfident (−0.12, bins 0.94–0.95 stated against
  0.76–0.82 hit): manoeuvre lag is physical, so a statement has to give up P, not only widen.
- The IMM is the most honest raw statement (−0.10, mean P 0.52) because its course sds are wide,
  but it states nothing on 22.5% of rows and its log gain is still below zero.
- Every Gate 4 check (G4-a coverage, G4-b reliability, G4-c log gain and mean P) fails for raw E
  by a wide margin: the statement has to come from the fit, not from the solve's covariance.

Files: `calibration.json` (all measures, by slice, by gross), `report.md`, `inputs.json`,
`plan.json`, `run.json`. `errors.npz` stays on the results branch.
