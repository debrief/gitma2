---
title: Uncertainty calibration
---

# Uncertainty calibration (spec 008)

Sources:

- `src/tma2/physics/uncertainty.py` (the covariance a row states);
- `src/tma2/eval/calibration.py` (the measures);
- `src/tma2/calib/` (head, loss, training, temperature, calibrated files, Gate 3's criteria);
- the CLIs `tma2-g3train`, `tma2-g3predict` and `tma2-g3`.

Requirements: SRD §7 step 5 (first item) and spec 008.

## What a row states

The physics layer's damped solve ends with a Gauss–Newton covariance of the state at the scored
row, P = σ²(JᵀJ)⁻¹ in (x, y, vx, vy). Every prediction row now carries it: the ten entries of its
upper triangle (`cov_xyvv`), a usable flag (`cov_ok`: finite, symmetric, positive definite) and
three standard deviations derived by the delta method:

- log range, from the gradient of ½ log((x − ox)² + (y − oy)²);
- course, from the gradient of atan2(vx, vy);
- speed, from the gradient of √(vx² + vy²).

C, E, the classical controls, the IMM and the EKF (its 4×4 block; for the IMM, the mixed
estimate's) all write the same fields. Points are unchanged.

E-w and the fading memory rescale the bearings' weights, so their P is not on C's scale until
it is calibrated. This is why the calibration is measured per estimator and not assumed.

## Measures

Each row is scored against the truth state at that row. All intervals are the scorer's
scenario-clustered bootstrap (97.5%, 2,000 resamples).

| Measure | Definition | Calibrated value |
| --- | --- | --- |
| Coverage | share of rows whose error lies within z·sd, z = 1 and 1.95996 (missing rows count as not covered) | 0.683, 0.95 |
| NEES ratio | median of eᵀP⁻¹e over the χ²₄ median 3.3567 | 1 |
| NEES in 95% | share of rows with eᵀP⁻¹e below 9.4877 | 0.95 |
| Interval score | Gneiting–Raftery 95% score: width + (2/0.05)·miss; a missing row is charged the 99th percentile | lower is better |
| Sharpness | median stated sd | — |

The interval score rewards calibration and sharpness together, so it is the score of record for
learning (G3-c): an estimator cannot win it by stating huge intervals.

## The calibration head

A small network reads E's encoder state at the row, the log raw sds and C's code at the row, and
outputs one scale s = 2·tanh(·). The calibrated covariance is e^(2s)·P. The state is never
changed (FR-020), so Gate 2's results hold for the calibrated E by construction.

The output layer starts at zero, so the untrained head is the identity.

The loss is β-NLL (β = 0.5): ½e^(−2s)q + 4s, with q = eᵀP⁻¹e the raw NEES, each row weighted by
the stop-gradient of e^(2sβ) and q capped at 100. Training uses E's frozen features cached over
stream seed 318; early stopping uses validation ordinals 0–499. Three seeds and a shuffled-label
control are trained. The shuffled control is scored at its best and its last epoch.

## The classical control

A per-slice temperature: one scale per cell of (minutes since the zig × open at k), fitted by the
same loss on validation ordinals 0–499. It is what a careful engineer would do without learning,
so the head must beat it (G3-c) before any calibration is credited to learning.

## Gate 3

The criteria are fixed by the SRD (§5) and the decision record before any training result:

| Criterion | Test |
| --- | --- |
| G3-a | 95% coverage of log range, course and speed: interval wholly in [0.92, 0.98] |
| G3-b | share of rows with NEES within the χ²₄ 95% point (missing rows outside): interval wholly in [0.92, 0.98] (owner, 2026-11-08) |
| G3-c | head − temperature, mean interval score in log range: wholly below 0; void if the shuffled control also beats the temperature on validation |
| G3-d | the calibrated E's point errors equal E's on every row |

`tma2-g3` reads a finished scoring run's stored arrays (`errors.npz`), so nothing is re-solved
and the verdict does not depend on the CPU family.
