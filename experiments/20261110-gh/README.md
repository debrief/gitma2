# Gate H test record (spec 010 T022)

Run 42799040276 (`headroom/gh-test`, plan `configs/headroom/gh-test.json`), commit eb028df, clean
tree, every job exit 0. Scoring CPUs (each `run.json`): AMD EPYC 9V45 for the primary condition,
EPYC 7763 and an Intel Xeon for others; the prediction shards' CPUs were not recorded. Seed 322, count 13,000, generated in the run after the
validation record (`experiments/20261110-gh-val/`). Bound by `experiments/20261110-gh-decision/`
(plan `26d8e898…`). Primary condition: every σ = 1° scenario of the `train` split, 5,203
scenarios, 20,473 G5 rows. Five further conditions: the first 1,000 scenarios, 3,927 rows each.
Intervals 97.5%, paired, scenario-clustered, 2,000 resamples. Each condition's `headroom.json`,
`run.json` and data digests are here; errors and predictions are on
`results/headroom-gh-test-<condition>-plan-42799040276`. `gate.json` holds the computed checks.

## H-c, the verdict: headroom is not material

R, the robust control's median range error over the attainable ceiling's, minus 1, on the
primary condition, every estimator on the true segmentation:

**R = −0.4% [−2.4, +1.4].** The interval lies wholly below the 10% threshold.

| | Median relative range error | In metres |
| --- | --- | --- |
| Plain solve (the oracle) | 0.1341 | 2,110 m |
| Classical robust control | 0.1183 | 1,880 m |
| Attainable ceiling | 0.1188 | 1,885 m |
| Realisation ceiling | 0.1179 | |
| One leg / IMM / EKF | 0.596 / 0.652 / 0.582 | |

- Course: R −0.6% [−2.5, +1.6]. Speed: R +2.1% [−0.1, +4.5].
- On the 14,351 rows every estimator answers: R +1.5% [−0.9, +3.4].
- The plain solve is 12.9% [9.2, 16.2] above the ceiling. The robust control closes that gap:
  103% [90, 123] of it.
- By time since the zig (5, 10, 15, 20 min): R −0.4%, −1.3%, +1.6%, +1.4%. Settled rows −0.2%,
  unsettled −2.2%. The control beats the ceiling on 50.8% of rows.

### By true range (added after panel round 1; post hoc, not gated)

| True range | Rows | Plain solve | Robust control | Attainable ceiling | R: control over ceiling | Plain over ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| under 10.7 km | 5,118 | 0.0922 | 0.0776 | 0.0740 | +4.9% [+1.8, +8.2] | +24.7% [+18.1, +31.6] |
| 10.7–17.2 km | 5,118 | 0.1248 | 0.1053 | 0.1022 | +3.0% [−0.2, +7.1] | +22.1% [+15.3, +28.6] |
| 17.2–25.3 km | 5,118 | 0.1487 | 0.1297 | 0.1332 | −2.6% [−5.7, +0.7] | +11.6% [+5.2, +17.4] |
| over 25.3 km | 5,119 | 0.1792 | 0.1711 | 0.1805 | −5.2% [−8.3, −2.1] | −0.7% [−5.8, +5.3] |

The pooled R near zero is a short-range deficit and a long-range surplus cancelling. At short
range knowing the error model is worth about 5%; at long range the error-model-informed fit is
*worse* than the robust control and no better than the plain solve. The statistics reviewer
found two finer post-hoc slices whose intervals cross 10% (under 11 km and settled:
+7.2% [+3.6, +11.6]; under 11 km at 15 min or later: +8.6% [+2.7, +12.9]); no point exceeds 10%.

### Other statistics (panel, recomputed from `errors.npz`; rows both answer)

Geometric mean +0.9% [−0.7, +2.6]; 10% trimmed mean +0.3% [−0.8, +1.3]; P90 +1.7% [+0.1, +3.0];
P95 +1.8% [−0.4, +3.7]. The median is the most favourable to the control; none comes near 10%.
The control is slightly worse in the tail. Row by row the two fits differ by a factor of up to
3.3 either way (5–95%): they are equal in distribution, not per row. The "rows every estimator
answers" figure above conditions on the IMM, the EKF and one leg answering, which drops 30% of
rows; on the rows the two fits both answer (20,426), R is −0.5% [−2.4, +1.4].

Soundness on the test seed, for information (it is applied on validation): H-a efficiency 1.26,
pass; H-b clean-data cost +1.9% [−0.8, +4.8], pass.

## The other conditions (1,000 scenarios each)

| Condition | Plain solve | Robust control | Attainable ceiling | Ceiling efficiency | R: control over ceiling | Plain over ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| off | 0.0574 | 0.0584 | 0.0574 | 1.59 | +1.9% [−0.8, +4.8] | 0 |
| corr-central | 0.1104 | 0.1062 | 0.1030 | 1.29 | +3.1% [−1.5, +6.7] | +7.2% [+0.7, +11.9] |
| bias-central | 0.0738 | 0.0748 | 0.0740 | 1.39 | +1.2% [−2.9, +5.0] | −0.2% [−4.9, +3.3] |
| sigma-central | 0.0589 | 0.0587 | 0.0584 | 1.59 | +0.4% [−2.2, +2.8] | +0.8% [−3.3, +4.1] |
| out-central | 0.0821 | 0.0597 | 0.0573 | 1.63 | +4.2% [+0.8, +7.8] | +43.3% [+32.2, +54.0] |

No condition's interval reaches 10%.

## Operational units, primary condition

| | Plain solve | Robust control | Attainable ceiling |
| --- | --- | --- | --- |
| Median range error | 2,110 m | 1,880 m | 1,885 m |
| Median course error | 13.3° | 11.2° | 11.3° |
| Median speed error | 1.82 kt | 1.50 kt | 1.47 kt |
| Settled by zig + 5 min | 13% | 17% | 18% |
| Settled by zig + 10 min | 22% | 26% | 27% |
| Settled by zig + 20 min | 42% | 45% | 46% |

## Forecasts against results

| Check | Forecast | Result |
| --- | --- | --- |
| H-a | about 1.25, pass (0.90) | 1.29 on validation, pass |
| H-b | about +3%, pass (0.75) | +0.7% on validation, pass |
| H-c | about +1.5%, [−1, +4], not material (0.85) | −0.4% [−2.4, +1.4], not material |

## Critical reading (revised after panel round 1)

- **What the result says, in the narrowest honest words.** On the true segmentation, under the
  declared stationary Gaussian-plus-outlier bearing-error family at the stated severities,
  knowing the true error model is worth no more than about 1.5% in median range error (about 3%
  at P90) to the piecewise-constant-velocity least-squares solve, over a textbook robust fit.
- **"Nothing to win" is true only pooled.** By range it is +4.9% under 10.7 km and −5.2% over
  25.3 km (table above). A component that used the error model at short range and the robust fit
  at long range would gain a few percent. That is far below 10%, and it is a rule, not learning.
- **The reference is not a ceiling.** It sits at 1.26 times the known-manoeuvre Cramér–Rao bound
  on settled rows (1.59 on clean data), and the control beats it at long range. **Why the solve
  is that far from the bound is not established.** Earlier versions of this record said "because
  the solve fits each manoeuvre by a chord". The estimation reviewer tested that on the tuning
  seed: on noise-free bearings the plain solve's median range error is 2.0%, which in quadrature
  explains an efficiency of about 1.16, not 1.61. The rest is unexplained; one untested candidate
  is that the layer fits 4 + 2 × knots parameters (median 12) under weak priors against the
  bound's 8. The robust control itself is at about 1.25 times the bound. That 25% is not
  error-model headroom (it is larger with no mismatch at all), and the bound is not attainable
  (it knows the manoeuvre times and the outlier flags). But it is room that a better motion
  model or an end-to-end estimator could claim, and this gate says nothing about it.
- **The true segmentation defines away the likeliest operational cost.** Correlated error and a
  wandering bias can look like target manoeuvres, and C nominates with the nominal σ. Whether
  C's segmentation degrades under mismatch was a registered comparison (research R6, FR-033)
  that had not been run when the verdict was computed. It is being run on the validation seed
  (`configs/headroom/gh-val-c2.json`) and is reported in `experiments/20261110-gh-c2/`.
- **The simulated mismatch is the control's own model family.** The control's correlation model
  (white plus first-order) was chosen in implementation because first-order alone could not
  represent the declared error. The errors are stationary, independent of geometry, with
  zero-mean independent outliers: Huber's best case. Untested and more likely to matter: a bias
  that steps or lags at the ownship zig; bursty or one-sided outliers; σ that varies within an
  engagement with signal-to-noise or relative bearing.
- **The severity grid came close to fixing the outcome in advance.** The estimation reviewer's
  linearised calculation on the tuning seed: for the Gaussian part of the primary condition, the
  plain solve's range sd over the exact generalised-least-squares sd is 1.028 (median; P90
  1.06). Stretching the grid on the same geometry gives 1.085 at a 180 s correlation time, 1.12
  with 90% of the variance correlated, 1.06 at 1° of bias. Within this error family only
  outliers could reach 10%, and Huber weights remove those. The verdict holds for this grid.
- **"An untold σ costs nothing" is true by construction**, not a finding: one scale per
  engagement cannot move a least-squares point estimate.
- **The control was tuned on the gated condition and statistic** (seed 320, the primary
  condition, median range error). The test data are fresh, so the test is valid, but R is the
  control's best case. Outliers alone left +4.2% [+0.8, +7.8] here and harsh outliers
  +6.3% [+2.6, +11.6] on validation.
- **The gate was confirmatory.** The forecast gave "not material" 0.85 from the tuning seed.
- **The trackers are not credible as tuned references** on these rows (IMM 0.652, EKF 0.582
  against 0.118; a quarter of rows unanswered). They take no part in the verdict. No naive
  baseline was scored: nothing is trained, so there is no training-set mean to report.
- **Process.** Validation and test ran from the pull request's branch before the SRD row was
  merged: the owner said in the session on 2026-11-10 "merged, go ahead with validation and
  test" while PR 25 was in fact still open. The criteria were committed (a814ac5) before either
  seed was generated; the panel's process reviewer regenerated seed 322 and reproduced every
  digest and R exactly.
- **Not tested:** target-motion mismatch; other error families and severities; a classical bias
  state; real data.
