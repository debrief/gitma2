# Spec 012: validation scoring (seed 327)

Scored by `rscore.yml`; one folder per scoring run. Validation, not a result of the experiment:
the readings that count are on test seed 328.

## `own/`: the ownship-only control and the baselines (run 43017737740, code 410f9fe)

The first 1,000 σ = 1° engagements of the MAN2 split and of the held-course split. The
regressor here is the control given the ownship track only
(`results/gputrain-r-a-own-42990062999`: 25,000 updates, 6.4 million scenarios, 2.6 T4-hours).

### Held course (994 engagements, 3,904 settled rows with no target change)

Efficiency (error over the Cramér–Rao bound), 95% scenario-clustered intervals:

| System | Range | Course | Speed | Reading |
| --- | --- | --- | --- | --- |
| Plain least squares (the check) | 1.02 [0.95, 1.07] | 1.02 [0.96, 1.07] | 0.99 [0.94, 1.05] | reaches |
| Ownship-only control | 11.1 [10.5, 11.7] | 26.6 [23.7, 29.5] | 15.3 [14.4, 16.4] | floor |

- The rows and the bound are sound: the check reads 1.0 with intervals wholly below 1.25.
- The control's efficiency worsens from the worst to the best geometry quartile (range 6.2 to
  35): its error does not shrink where the information grows. This is what a floor looks like.

### After manoeuvres (MAN2 split, 1,000 engagements, 3,929 rows; every row has a change begun)

| System | Median relative range error | Course (°) | Speed (kt) | Rows answered |
| --- | --- | --- | --- | --- |
| True manoeuvre times, plain solve | 0.063 | 7.3 | 0.95 | 1.00 |
| C″ | 0.105 | 13.0 | 1.50 | 0.99 |
| C at three times its threshold | 0.123 | 16.5 | 1.72 | 0.98 |
| Ownship-only control | 0.333 | 58.2 | 6.36 | 1.00 |
| IMM | 0.561 | 53.6 | 5.87 | 0.77 |
| EKF | 0.574 | 63.4 | 5.56 | 0.80 |
| One leg | 0.587 | 67.4 | 6.10 | 0.75 |

- Ownship-only − C″: +0.228 [+0.207, +0.250]. The prior alone beats the IMM's median (the IMM
  fails on a quarter of rows) and is three times C″'s error.
- **C at three times its threshold is worse than C″ on this fresh seed**: +0.018
  [+0.010, +0.026] with the plain final solve. Spec 011's tuning seed had hinted the opposite
  on clean data (no interval excluded zero, and the final solve there was the robust one). The
  hint does not survive; C″ stays the classical system to beat, and the raised-threshold line
  is kept only as a reported row.
- C″ − true manoeuvre times: +0.043 [+0.035, +0.052].

## `seeds/`: the three trained seeds and the controls (run 43083186284, code a567163)

The same 1,000 + 1,000 engagements. Checkpoints as in `../20261111-r-runs/`.

### Held course (994 engagements, 3,904 rows): efficiency against the bound

| System | Range | Course | Speed | Reading |
| --- | --- | --- | --- | --- |
| Plain least squares (the check) | 1.01 [0.95, 1.07] | 1.02 [0.96, 1.07] | 0.99 [0.94, 1.05] | reaches |
| Regressor, seed 1 | 1.18 [1.13, 1.24] | 1.79 [1.70, 1.91] | 1.45 [1.36, 1.54] | partial |
| Regressor, seed 2 | 1.19 [1.13, 1.25] | 1.80 [1.70, 1.91] | 1.44 [1.35, 1.53] | partial |
| Regressor, seed 3 | 1.15 [1.10, 1.23] | 1.78 [1.69, 1.87] | 1.42 [1.34, 1.51] | partial |
| A tenth of the data | 1.30 [1.22, 1.37] | 1.95 [1.83, 2.09] | 1.56 [1.46, 1.67] | partial |
| Ownship only | 11.1 | 26.6 | 15.3 | floor |

- By geometry quartile (best to worst observed), seed 1: range 1.81, 1.17, 1.08, 0.89; speed
  2.83, 1.56, 1.32, 0.89. The shortfall is where the information is greatest; where it is
  least the regressor is below 1, which an estimator that knows the scenario ranges can be (the
  bound is for unbiased estimators).

### After manoeuvres (MAN2 split, 1,000 engagements, 3,929 rows)

| System | Median relative range error | P90 | Course (°) | Speed (kt) | Rows answered |
| --- | --- | --- | --- | --- | --- |
| True manoeuvre times, plain solve | 0.063 | 0.25 | 7.3 | 0.95 | 1.00 |
| Regressor, seeds 1 / 2 / 3 | 0.065 / 0.065 / 0.064 | 0.21 | 9.8 / 9.7 / 9.8 | 1.37 / 1.40 / 1.38 | 1.00 |
| A tenth of the data | 0.071 | 0.22 | 10.5 | 1.50 | 1.00 |
| C″ | 0.105 | 0.51 | 13.0 | 1.50 | 0.99 |
| C at three times its threshold | 0.123 | 0.62 | 16.5 | 1.72 | 0.98 |
| Ownship only | 0.333 | 1.16 | 58.2 | 6.36 | 1.00 |
| IMM | 0.561 | | 53.6 | 5.87 | 0.77 |

Regressor − C″ (seed 1; the others agree to 0.001), paired, 95%:

- range −0.042 [−0.051, −0.034]; on rows both answer −0.040 [−0.049, −0.033];
- course −3.3° [−4.6, −2.2]; speed −0.15 kt [−0.27, −0.02]; range error −723 m [−878, −569];
- by quartile of true range, near to far, regressor against C″: 0.058 / 0.074, 0.062 / 0.092,
  0.066 / 0.121, 0.073 / 0.139.

**On validation the regressor is better than C″ after manoeuvres, on every quantity, and
matches the plain solve on the true manoeuvre times in range.** The decision record forecast
the opposite ("worse than C″"); the forecast was wrong. Cautions before the test seed:

- This is validation. The registered reading is on test seed 328.
- The regressor has learnt the simulator's scenario ranges (it is below the bound where
  geometry is poor); the classical systems do not use them. How much of its margin is that
  prior is not measured here. The ownship-only control (the prior alone) is at 0.333, so the
  prior is not most of it, but the margin grows with range, where a prior would help most.
  A scoring on the held-out-ranges split is added to answer this (declared before its result).
- C″'s weakness on these rows is missed manoeuvres; the regressor needs no segmentation.
