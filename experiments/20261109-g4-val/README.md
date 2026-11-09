# Gate 4 validation (spec 009 T015): stopped at validation

Seed 314 validation, scoring ordinals 500–1499 (1,000 scenarios, 3,934 σ = 1° G5 rows). Decision
record `experiments/20261108-g4-decision/` (plan `configs/gate4/g4-a.json`, `e357f8a7…`).

- **Training:** CI run 42536874618 (`results/g4-g4-a-42536874618`, commit 7270104, clean): three
  head seeds (best epochs 29, 30, 37) and the shuffled control (best epoch 1, last 6); the
  temperature's β per quantity is 0.7 (log range), 0.9 (course), 0.4 (speed).
- **Stated files:** `tma2-g4predict` at 74834aa (clean worktree) on E's validation file
  (`results/g2predict-g3-base-val-42471500526`) and the validation feature cache;
  `results/g4predict-g4-a-val` (each header names its model, weights, plan digest and commit).
  3,895 of 3,934 rows are stated; the other 39 have no usable covariance and state nothing.
- **Scoring:** CI run 42537069261 (`results/score-g4-a-val-42537069261`, commit 74834aa, AMD EPYC
  9V74), reference estimators reused from the Gate 4 baseline (`experiments/20261108-g4-base-val/`).
- **Verdict:** `tma2-g4 --split validation` at 74834aa (clean; Intel Xeon), `validation.json`
  (SHA-256 `05219c86…`). `by-head/` holds the same checks with the other seeds and the
  temperature in the head's role, for information only: they decide nothing.

## The carried seed and the checks

Carried rule (median validation standardised summed score): st-s1 2.773, st-s2 2.764,
**st-s3 2.765** → st-s3 (best epoch). Intervals 97.5%, 2,000 scenario-clustered resamples.

| Check | Value [interval] | Band | Verdict |
| --- | --- | --- | --- |
| G4-a coverage95 log range | 0.940 [0.926, 0.950] | [0.92, 0.98] | pass |
| G4-a coverage95 speed | 0.929 [0.915, 0.941] | [0.92, 0.98] | inconclusive |
| G4-b hit − P overall | −0.002 [−0.024, +0.021] | ±0.03 | pass |
| G4-b five bins of P (stated / hit) | 0.475/0.471, 0.631/0.587, 0.648/0.633, 0.657/0.657, **0.675/0.729** | ±0.05 each (point) | **fail** (top bin +0.054) |
| G4-c course log gain over uniform | +1.011 [0.922, 1.099] | > 0 | pass |
| G4-c mean P | 0.617 | ≥ 0.5 | pass |
| G4-d head − temperature (summed score) | −0.235 [−0.355, −0.137] | < 0 | pass |
| G4-d shuffled − temperature | best +0.164 [+0.037, +0.259]; last +0.370 [+0.200, +0.545] | rule: not wholly < 0 | rule passes |
| G4-e points identical | exact | — | pass |

**Validation rule** (every check's point within its band or limit): not met. G4-b's top bin is
0.054 above its stated P (limit 0.05); the head is *under*-confident on the rows it is most sure
of. Seed 320 is not generated (still unused).

## The other seeds and the temperature (information, not decision)

| Statement | Summed score | G4-a speed | G4-b bins (hit − P) | G4-c gain | Mean P | Would meet the validation rule |
| --- | --- | --- | --- | --- | --- | --- |
| st-s1-best | 2.773 | 0.932 [0.918, 0.944] | −0.033, −0.012, 0.000, +0.007, +0.040 | 1.010 | 0.625 | yes |
| st-s2-best | 2.764 | 0.935 [0.921, 0.947] | −0.014, −0.027, −0.021, +0.031, +0.022 | 1.009 | 0.617 | yes |
| st-s3-best (carried) | 2.765 | 0.929 [0.915, 0.941] | −0.004, −0.044, −0.016, 0.000, **+0.054** | 1.011 | 0.617 | no |
| temperature (sd^β) | 3.000 | 0.943 [0.931, 0.954] | +0.001, +0.001, +0.002, +0.031, −0.005 | 0.967 | 0.594 | a–c yes; d is itself |
| shuffled best / last | 3.164 / 3.370 | 0.922 / 0.934 | — | 0.954 / 0.858 | 0.619 / 0.612 | — |
| E raw (baseline) | 9.021 | 0.647 | −0.09 … −0.49 | −2.587 | 0.904 | no |

The stop is narrow and seed-dependent: two of three seeds meet every point, and the carried one
misses one per-bin point by 0.004 (787 rows per bin, sampling sd about 0.016). The rule was fixed
before any result and is applied as written; choosing another seed now would be choosing on
scoring rows.

## Reading

- **Learning shown, for the first time on uncertainty.** All three seeds beat the sd^β
  temperature by 0.23–0.24 standardised units, in every component (course log score 0.827 against
  0.871; range interval score 1.99 against 2.18; speed 11.86 against 13.12 m/s units), and the
  shuffled head is worse than the temperature at both epochs, so the gain is per-row information,
  not a better constant. Gate 3's head showed none.
- **The statement is usable.** E's raw sds claim P 0.90 and are right half the time (log gain
  −2.6); the stated E claims 0.62 within ±22° and is right 0.62 of the time, with a course
  statement 1.0 nat per row better than "unknown", and 95% intervals that cover 0.93–0.94.
- **What failed is the top of P's isotonic map:** fitted on 1,971 tuning rows with 10 knots, its
  last knot under-states the best rows for seed 3. A per-bin check at ±0.05 on 787 rows is
  sensitive to that; the overall reliability is −0.002.
- **Speed coverage sits at 0.93**, inside the band by point but not wholly: the interval-score
  minimiser on the training stream lands slightly low on validation for every head seed (0.929–
  0.935), while the temperature, fitted on the tuning rows of the same seed, lands at 0.943.

Files: `validation.json`, `by-head/*.json`, `calibration.json` (every measure by slice),
`metrics.json`, `report.md`, `inputs.json`, `plan.json`, `run.json`. `errors.npz` stays on the
results branch.
