# Gate 3 validation baseline (spec 008 T015)

How far each estimator's stated uncertainty can be trusted today, before any calibration is
trained. Seed 314 validation, scoring ordinals 500–1499: 1,000 scenarios, 3,934 σ = 1° G5 rows.
Scoring run 42480880386 (`results/score-g3-base-val-42480880386`, commit f0416f4, Intel Xeon
6973P-C), plan `plan.json` (= `configs/score/g3-base-val.json`). Not gate mode.

Every row's covariance is that of (x, y, vx, vy) at the row as the estimator states it: the
physics solve's σ²(JᵀJ)⁻¹ for C, E, E-w, C″ and the oracle; the filters' own for the IMM (mixed
estimate) and the EKF; the solve's for one leg and GLR + confirm. A row with no usable covariance
counts as not covered (the "answered" coverages in `calibration.json` leave such rows out).
Intervals: 97.5%, 2,000 scenario-clustered resamples.

## Overall

Coverage should be 0.95 (95%) and 0.683 (68%); the NEES ratio (median 4-state NEES over the χ²₄
median, 3.357) and the share within the χ²₄ 95% point should be 1 and 0.95. Interval scores
(lower is better) charge a row without an estimate the 99th percentile.

| Estimator | Cov95 log range | Cov95 course | Cov95 speed | Cov68 log range | NEES ratio | NEES within 95% | No estimate |
|---|---|---|---|---|---|---|---|
| C | 0.607 [0.582, 0.632] | 0.551 | 0.635 | 0.368 | 7.34 [6.01, 9.35] | 0.363 | 0.006 |
| e-s3 | 0.598 [0.573, 0.624] | 0.532 | 0.647 | 0.364 | 6.65 [5.78, 8.11] | 0.330 | 0.010 |
| ew-s3 | 0.569 [0.543, 0.594] | 0.524 | 0.616 | 0.335 | 8.48 [6.78, 10.28] | 0.310 | 0.012 |
| veto-w6-fade | 0.613 [0.587, 0.637] | 0.546 | 0.636 | 0.357 | 6.41 [5.35, 7.91] | 0.351 | 0.006 |
| oracle | 0.875 [0.858, 0.892] | 0.813 | 0.912 | 0.615 | 1.32 [1.24, 1.42] | 0.747 | 0.000 |
| imm | 0.405 [0.376, 0.435] | 0.612 | 0.730 | 0.222 | 10.61 [7.42, 15.00] | 0.372 | 0.225 |
| ekf | 0.046 [0.037, 0.055] | 0.033 | 0.049 | 0.024 | 184884.64 [124738.63, 265897.25] | 0.001 | 0.188 |
| one_leg | 0.099 [0.085, 0.115] | 0.046 | 0.095 | 0.057 | 243627.06 [159131.77, 380786.06] | 0.007 | 0.232 |
| glr_confirm | 0.248 [0.224, 0.272] | 0.246 | 0.353 | 0.134 | 355.83 [276.02, 477.48] | 0.069 | 0.203 |

| Estimator | IS95 log range | IS95 course ° | IS95 speed kt | Sharpness log range | Sharpness course ° | Sharpness speed kt |
|---|---|---|---|---|---|---|
| C | 4.83 | 853 | 48.32 | 0.316 | 23.29 | 5.56 |
| e-s3 | 4.54 | 855 | 47.34 | 0.266 | 21.18 | 5.44 |
| ew-s3 | 5.18 | 893 | 51.84 | 0.266 | 20.87 | 5.16 |
| veto-w6-fade | 4.21 | 823 | 47.43 | 0.291 | 22.19 | 5.38 |
| oracle | 1.13 | 364 | 16.29 | 0.361 | 43.99 | 7.73 |
| imm | 23.85 | 1600 | 99.40 | 0.877 | 160.60 | 30.81 |
| ekf | 45.30 | 2987 | 336.89 | 0.032 | 1.37 | 0.26 |
| one_leg | 40.38 | 3178 | 343.52 | 0.125 | 3.62 | 0.76 |
| glr_confirm | 32.53 | 2390 | 285.05 | 0.330 | 19.31 | 5.89 |

## Slices (E = e-s3 and C)

**by_g5_minutes** (E e-s3 / C): coverage95 log range, NEES ratio
| slice | E cov95 log range | E NEES ratio | C cov95 log range | C NEES ratio |
|---|---|---|---|---|
| 5 | 0.591 | 9.21 | 0.589 | 15.67 |
| 10 | 0.632 | 5.57 | 0.636 | 5.06 |
| 15 | 0.598 | 6.35 | 0.613 | 6.59 |
| 20 | 0.570 | 6.70 | 0.590 | 7.35 |

**by_open_at_k** (E e-s3 / C): coverage95 log range, NEES ratio
| slice | E cov95 log range | E NEES ratio | C cov95 log range | C NEES ratio |
|---|---|---|---|---|
| open | 0.600 | 3.89 | 0.610 | 3.47 |
| not_open | 0.598 | 6.93 | 0.607 | 7.78 |

**by_settled** (E e-s3 / C): coverage95 log range, NEES ratio
| slice | E cov95 log range | E NEES ratio | C cov95 log range | C NEES ratio |
|---|---|---|---|---|
| settled | 0.610 | 4.07 | 0.615 | 3.56 |
| not_settled | 0.563 | 639.68 | 0.583 | 727.46 |

**by_range_band** (E e-s3 / C): coverage95 log range, NEES ratio
| slice | E cov95 log range | E NEES ratio | C cov95 log range | C NEES ratio |
|---|---|---|---|---|
| 0-2km | 0.788 | 2.27 | 0.827 | 1.52 |
| 10-20km | 0.603 | 5.77 | 0.606 | 7.25 |
| 2-5km | 0.721 | 2.56 | 0.758 | 1.83 |
| 20-30km | 0.580 | 11.07 | 0.604 | 12.81 |
| 30+km | 0.533 | 14.82 | 0.531 | 21.74 |
| 5-10km | 0.628 | 4.25 | 0.627 | 3.65 |

## Findings

1. **Every estimator is overconfident except the oracle.** E's 95% interval covers 0.60 of rows
   in log range, 0.53 in course and 0.65 in speed; its median NEES is 6.7× the χ²₄ median. C is
   alike (0.61, NEES 7.3×). The oracle, which has the true segmentation, is nearly calibrated
   (0.875 coverage, NEES 1.32×): most of E's and C's overconfidence comes from segmentation and
   model error that the solve's covariance does not know about, not from the solve itself.
2. **The overconfidence depends on the slice**, which is what a calibration must learn:
   - worst at zig + 5 min (E's NEES 9.2×) and at long range (30+ km: 14.8×; 0–2 km: 2.3×);
   - milder on rows with a transition open at k (3.9× against 6.9×) and on settled rows (4.1×);
   - unsettled rows carry the extreme NEES (median 640×): gross errors with tight stated
     covariance.
   A per-slice temperature over (minutes since the zig × open at k) can follow time and the open
   transition but not range; the head reads the raw sds (which grow with range) and E's encoder
   state, so G3-c tests whether that extra information is used.
3. **E-w's weights make the covariance tighter without making it better calibrated** (Gate 2
   panel R2-5): ew-s3 has the lowest coverage of the solve-based estimators (0.57) and the highest
   NEES (8.5×). E-s on top recovers part of it (e-s3 0.60, 6.7×).
4. **The trackers' covariances are not usable as uncertainty on MAN2.** The EKF covers 0.05 of
   rows (NEES 1.8 × 10⁵×), one leg 0.10; the IMM 0.41 with 22% of rows missing. GLR + confirm
   covers 0.25.
5. **Interval score in log range** (G3-c's score): C″ 4.21, E 4.54, C 4.83, E-w 5.18; the
   oracle 1.13. It is dominated by misses (narrow intervals around wrong estimates), so widening
   E's intervals where it is overconfident should lower it substantially.

## Prediction files (points unchanged)

The validation prediction files were re-made with covariances (schema 0.26.0+; runs 42471500526
and 42471502678) and checked against Gate 2's (`scripts/research/g3_points_check.py`): 3,934 rows
in each, none missing, no converged-flag flips. Rows differing by more than 1e-6 relative: e-s3
10 (4 at ranges under 1,000 km, at most 5.5e-6), ew-s3 21 (14, at most 9.5e-6), veto-w6-fade 4 (1,
2.2e-6). The rest are runaway rows (ranges over 10⁶ m). This is the CPU-family dependence AGENTS.md
records (Gate 2: up to 6e-4); the re-made files are scored here, so the comparison within this run
is exact.

## Files

- `calibration.json`: every measure, overall and by slice (G5 minutes, settled, open at k, range
  band, row band, gross), for every estimator, with intervals.
- `report.md`, `plan.json`, `inputs.json` (digests of every input, the truth's included),
  `run.json`. `errors.npz` stays on the results branch (2.8 MB).
