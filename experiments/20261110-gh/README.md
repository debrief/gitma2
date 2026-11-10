# Gate H test record (spec 010 T022)

Run 42799040276 (`headroom/gh-test`, plan `configs/headroom/gh-test.json`), commit eb028df, clean
tree, every job exit 0, AMD EPYC 9V45. Seed 322, count 13,000, generated in the run after the
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

## Critical reading

- **What the result says.** Under correlated, biased, mis-scaled and outlier-ridden bearing
  errors of the declared severities, a least-squares fit of the piecewise-constant-velocity
  model with textbook robust weighting is as accurate as the same fit told the true error
  model. A learner of the *error model*, feeding this solve, has nothing measurable to win.
- **What it does not say.** It does not say this estimator is near the best possible. The
  ceiling sits at 1.26 times the Cramér–Rao bound on settled rows (1.59 on clean data), because
  the solve fits each manoeuvre by a chord. That gap is model error in the *target's motion*,
  which this gate did not test and no error-model learner could close.
- **"Ceiling" overstates the reference.** On validation the control beat both ceilings in point
  value (−4.0%). On test, at five times the size, the three are within half a percent and the
  realisation ceiling is 0.8% [0.1, 1.8] below the attainable one, as it should be. The
  validation gap looks like noise, but the reference is a model-based fit, not an optimum: R
  measures "what knowing the error model is worth to this fit", and should be read that way.
- **Where the mismatch hurts.** Outliers alone raise the plain solve's error by 43%, and Huber
  weights remove nearly all of it. Correlated error raises everyone's error and leaves the
  largest residual (+3.1%, interval to +6.7%). Bias and an untold σ cost almost nothing.
- **The speed component is the closest to showing anything** (+2.1% [−0.1, +4.5]): far below
  the threshold, but the one place the control is visibly behind.
- **The trackers are not competitive here** (IMM 0.652, EKF 0.582 against 0.118), and fail to
  answer a quarter of rows. They take no part in the verdict.
- **Not tested:** target-motion mismatch; other severities (harsh outliers left +6.3%
  [+2.6, +11.6] on validation); a classical bias state; the same comparison on C's
  segmentation, which was planned as a reported extra and not run; real data.
