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

The rule was fixed before any result and is applied as written; choosing another seed now would
be choosing on scoring rows. The panel (round 1, `review.md`) corrected this record's first reading
that the stop was "narrow and seed-dependent": re-binning under resampling, some bin misses ±0.05
in 87% of resamples for st-s3 and in 47% and 43% for st-s1 and st-s2, and the top bin is
under-stated for every seed (+0.055, +0.040, +0.022). The per-bin check is a point check whose
clustered sampling sd is about 0.018–0.023 per bin, so ±0.05 is about 2.5 sd; the temperature
itself would miss it in 28% of resamples. That is a design flaw in G4-b (recorded for the
follow-on), not a reason to read the stop as luck.

## Reading (as corrected by the panel, round 1)

- **The top-bin miss is the isotonic map's, not the head's.** In the top bin the raw head states
  0.761 against a hit rate of 0.730 (slightly over-confident); the map, fitted on 1,971 tuning
  rows with 10 knots (about 197 rows each, sampling sd about 0.034), pooled its top two knots to
  0.677, so no row can state more than 0.677 and 13.8% of rows sit at that ceiling. The map is
  needed overall (raw P 0.655 against a hit rate of 0.622) but its top is noise-driven. The
  temperature's map pools 7 of 10 knots to 0.583: about 80% of its rows state the same P, so its
  per-bin pass rests on ties.
- **P carries little per-row information.** The carried head's P runs 0.46–0.68 (5th–95th
  percentile); its AUC for a hit is about 0.60 (temperature 0.53). Most of the course log gain
  (+1.0 nat) is the arc's overall concentration; the head adds 0.044 nats over the temperature.
- **P is not conditionally reliable.** On rows not settled after a target manoeuvre (1,001 of
  3,934; "settled" is defined from the truth, so no statement can read it) P is 0.617 and the hit
  rate 0.30; on settled rows 0.626 against 0.73. The temperature does the same. Overall
  reliability (−0.002) averages a −0.31 and a +0.10. On open transitions the statement widens the
  arc (21° to 38°) at the same P, and is reliable there (−0.015).
- **The course statement contradicts itself.** P goes through the isotonic map; the stated density
  (`course_conc`, `course_mix_p`), which G4-c's log score scores, does not, so a row's density
  mass on ±X differs from its P by 0.037 on average and up to 0.20 (temperature up to 0.33). The
  normal approximation to the von Mises in P adds up to 0.12 on single rows (a·sd reaches about
  35° at the 95th percentile; the cap limits X, not a·sd).
- **Learning: the head beats the sd^β temperature by 0.235 standardised units, in every component**
  (course log score 0.827 against 0.871; range interval score 1.99 against 2.18; speed 11.86
  against 13.12), so the claim does not depend on G4-d's weights. But the registered shuffled
  control permutes errors while keeping the sds, which breaks the error–sd link the temperature
  itself uses; it being worse than the temperature does not show per-row information beyond the
  sd. An unregistered check by the panel (on the scoring rows, so evidence, not a result): a
  temperature refitted on the head's 39,054 stream rows scores 2.995, and a classical rule of 10
  deciles of sd × 8 cells per quantity fitted on the stream scores 2.907 against the heads'
  2.744–2.747, so about two-thirds of the gain lies beyond any function of sd and cell.
- **Plain-language widths.** The 95% range interval is a factor of 1.74 either way at the median
  (3.77 at the 95th percentile: at 20 km, 11–35 km); the speed half-width is 3.4 m/s (6.7 kn) at the
  median, 6.4 m/s at the 95th percentile. Honest, but wide. Coverage falls short at minute 5
  (range 0.916, speed 0.903) and beyond 30 km (range 0.907, speed 0.867), slices the gate reports
  but does not gate. `sharpness95_*` in `calibration.json` measures E's raw sds, not the stated
  intervals.
- **Comparison with the references is not like for like.** The baseline gives the oracle and the
  IMM statements from their raw sds, against E's fitted one; a fair ceiling would fit the same
  temperature to the oracle on the tuning rows.

Files: `validation.json`, `by-head/*.json`, `calibration.json` (every measure by slice),
`metrics.json`, `report.md`, `inputs.json`, `plan.json`, `run.json`. `errors.npz` stays on the
results branch.
