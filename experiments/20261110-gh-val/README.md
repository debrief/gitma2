# Gate H validation (spec 010 T021)

Run 42774644963 (`headroom/gh-val`, plan `configs/headroom/gh-val.json`), commit e4d305f, clean
tree, every job exit 0. Seed 321, count 2,600, the `train` split's first 1,000 σ = 1° scenarios,
3,931 G5 rows per condition, all 16 conditions. Bound by `experiments/20261110-gh-decision/`
(plan `26d8e898…`). Intervals are 97.5%, paired, scenario-clustered, 2,000 resamples. Each
condition's `headroom.json`, `run.json` and data digests are here; the full records (errors,
predictions) are on `results/headroom-gh-val-<condition>-plan-42774644963`.

## The validation rule: both soundness checks pass

| Check | Result | Limit | |
| --- | --- | --- | --- |
| **H-a** ceiling's range efficiency, settled rows, primary | 1.29 | within [0.9, 1.6] | **pass** |
| H-a, second clause: ceiling no worse than the plain solve | 0.1190 against 0.1300 | | **pass** |
| **H-b** control's cost on clean data | +0.7% [−2.3, +2.8] | point ≤ 5%, interval not wholly above 2% | **pass** |

The gate goes on to the test seed. `validation.json` holds the computed checks.

## H-c on validation (reported; decided on the test seed only)

R on the primary condition: **−4.0% [−7.4, +1.6]**. The interval lies wholly below 10%, which on
the test seed would read "not material". On the rows every estimator answers: −0.7% [−6.0, +4.4].
Course +1.4% [−2.8, +6.7], speed +1.5% [−3.4, +7.3].

## Every condition (median relative range error, true segmentation)

| Condition | Plain solve | Robust control | Attainable ceiling | Realisation ceiling | Ceiling efficiency | R: control over ceiling | Plain over ceiling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| off | 0.0600 | 0.0604 | 0.0600 | 0.0600 | 1.62 | +0.7% [−2.3, +2.8] | 0 |
| corr-mild | 0.0922 | 0.0955 | 0.0924 | 0.0924 | 1.43 | +3.3% [−0.1, +6.0] | −0.2% [−4.9, +4.5] |
| corr-central | 0.1073 | 0.1062 | 0.1090 | 0.1090 | 1.34 | −2.6% [−6.1, +1.3] | −1.6% [−7.0, +4.1] |
| corr-harsh | 0.1214 | 0.1175 | 0.1213 | 0.1213 | 1.23 | −3.1% [−8.7, +2.3] | +0.1% [−6.7, +6.6] |
| bias-mild | 0.0645 | 0.0648 | 0.0644 | 0.0644 | 1.56 | +0.6% [−2.0, +3.8] | +0.2% [−1.8, +3.6] |
| bias-central | 0.0750 | 0.0750 | 0.0750 | 0.0750 | 1.46 | −0.0% [−3.7, +4.5] | −0.1% [−3.6, +4.3] |
| bias-harsh | 0.1039 | 0.1032 | 0.1028 | 0.1028 | 1.31 | +0.3% [−4.6, +6.7] | +1.0% [−4.3, +7.5] |
| sigma-mild | 0.0597 | 0.0604 | 0.0600 | 0.0600 | 1.62 | +0.7% [−1.7, +3.5] | −0.5% [−2.4, +2.1] |
| sigma-central | 0.0605 | 0.0602 | 0.0595 | 0.0595 | 1.64 | +1.3% [−1.1, +4.2] | +1.8% [−1.7, +4.5] |
| sigma-harsh | 0.0606 | 0.0609 | 0.0600 | 0.0600 | 1.66 | +1.5% [−0.9, +4.5] | +1.0% [−2.2, +6.4] |
| out-mild | 0.0653 | 0.0609 | 0.0604 | 0.0603 | 1.65 | +0.9% [−2.6, +3.3] | +8.3% [+3.2, +12.7] |
| out-central | 0.0859 | 0.0632 | 0.0612 | 0.0605 | 1.67 | +3.1% [−0.7, +7.3] | +40.3% [+29.6, +52.1] |
| out-harsh | 0.1134 | 0.0668 | 0.0628 | 0.0619 | 1.67 | +6.3% [+2.6, +11.6] | +80.5% [+67.4, +97.0] |
| all-mild | 0.0980 | 0.0961 | 0.0951 | 0.0944 | 1.39 | +1.1% [−1.3, +5.4] | +3.1% [−2.2, +10.2] |
| **all-central (primary)** | 0.1300 | 0.1143 | 0.1190 | 0.1167 | 1.29 | **−4.0% [−7.4, +1.6]** | +9.2% [+1.9, +19.0] |
| all-harsh | 0.1764 | 0.1448 | 0.1431 | 0.1432 | 1.17 | +1.2% [−4.8, +7.0] | +23.2% [+14.0, +33.3] |

Primary condition, references on the same rows: one leg 0.565, IMM 0.617, EKF 0.553.

## Operational units, primary condition

| | Plain solve | Robust control | Attainable ceiling |
| --- | --- | --- | --- |
| Median range error | 2,000 m | 1,710 m | 1,830 m |
| Median course error | 12.7° | 10.6° | 10.4° |
| Median speed error | 1.76 kt | 1.48 kt | 1.46 kt |
| Settled by zig + 5 min | 12% | 18% | 18% |
| Settled by zig + 10 min | 21% | 27% | 29% |
| Settled by zig + 20 min | 42% | 48% | 47% |

"Settled": range error within 10% at that time and every later scored time.

## Critical reading

- **The "ceiling" is beaten in point value on the primary condition.** The robust control's
  median range error (0.1143) is below the attainable ceiling's (0.1190) and below the
  realisation ceiling's (0.1167), which whitens by the exact covariance. The intervals include
  zero, so this is not established, but the same sign appears on both correlated conditions.
  The likely cause: the solve fits each manoeuvre by a chord, and where the model is wrong
  about the *target*, weighting by the true *error* covariance is not optimal, while Huber
  weights also discount the bearings the chord misfits. The decision record said the ceiling is
  the ceiling of this solve; this shows it is not even that, strictly. It bounds what knowing
  the error model is worth to a least-squares fit of this model. That is the gate's question,
  but the word "ceiling" overstates it and the write-up must say so.
- **It does not threaten the verdict's direction.** A control at or below the reference means
  no headroom of this kind is visible. It does mean R cannot be read as "distance from optimal".
- **The tuning seed's picture repeats on a fresh seed at twice the size**: outliers are the only
  kind the plain solve suffers from badly, and the control removes almost all of it (harsh
  outliers leave +6.3% [+2.6, +11.6], the one condition whose interval reaches the threshold);
  correlated error and bias cost every estimator alike; an untold σ costs nothing.
- **H-b passed more easily than forecast** (+0.7% against a forecast of about +3%). The tuning
  seed's +4.0% on 300 scenarios was noise.
- **The plain oracle is at 1.62 times the bound on clean data here**, just outside the band set
  from the tuning seed (1.57). H-a is defined on the primary condition (1.29), so it passes, but
  the band's upper edge was set with no margin.
