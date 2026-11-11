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
