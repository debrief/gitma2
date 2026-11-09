# Gate 5 validation baseline (spec 010 T012)

This record re-reports the Gate 4 validation scoring with spec 010's measures, on seed 314
validation scoring ordinals 500–1499 (1,000 scenarios, 3,934 σ = 1° G5 rows).

- **Run:** CI run 42705184463 (`results/score-g5-base-val-42705184463`, commit 1f633cd, Intel Xeon
  Platinum 8573C). The plan is `plan.json` (= `configs/score/g5-base-val.json`).
- **Reused, not re-solved:** every estimator comes from the Gate 4 validation scoring's
  `errors.npz` (run 42537069261). The run adds the calibration slope, the AUC of P and the slice
  labels.
- **Scope:** no spec 010 statement is scored. Not gate mode.

**Slope correction.** In this run's `calibration.json`, `statement_slope` diverged (to about
1e12) for raw E, C and the IMM. Their stated P is almost constant (0.95 at the capped arc), so the
logistic fit has no slope to find. The code now returns NaN when the fit does not converge or the
slope runs away; under the gate, a NaN slope does not pass. The slopes below were recomputed with
the fixed code from this run's stored arrays.

## Overall, and by the truth's settled split

Columns:
- **Hit − P:** reliability (0 when honest).
- **Slope:** the logistic calibration slope of the hit on logit P (1 when honest).
- **AUC:** how well P ranks hits.
- **Log gain:** course log score over "unknown".
- **Settled / not settled:** stated P / hit rate on rows settled or not by the truth (a target
  manoeuvre in progress, or one that ended under 5 min before).
- **Cov95:** range / speed coverage.

| Statement | Mean P | Hit − P | Slope | AUC | Log gain | Settled P / hit | Not settled P / hit | Cov95 range / speed |
|---|---|---|---|---|---|---|---|---|
| E raw sds | 0.904 | -0.396 | n/a | 0.448 | -2.59 | 0.91 / 0.60 | 0.89 / 0.25 | 0.598 / 0.647 |
| Gate 4 temperature (sd^β) | 0.594 | +0.006 | 0.74 | 0.544 | +0.97 | 0.59 / 0.71 | 0.59 / 0.28 | 0.942 / 0.943 |
| Gate 4 head st-s3 | 0.617 | -0.002 | 1.16 | 0.610 | +1.01 | 0.62 / 0.72 | 0.61 / 0.30 | 0.940 / 0.929 |
| Gate 4 shuffled (best) | 0.619 | +0.002 | 1.73 | 0.543 | +0.95 | 0.62 / 0.73 | 0.62 / 0.30 | 0.958 / 0.922 |
| oracle raw sds | 0.891 | -0.117 | 0.24 | 0.556 | +1.05 | 0.92 / 0.83 | 0.82 / 0.62 | 0.875 / 0.912 |
| IMM raw sds | 0.522 | -0.095 | n/a | 0.719 | -0.36 | 0.52 / 0.46 | 0.52 / 0.33 | 0.405 / 0.730 |

## Reading, against Gate 5's proposed bands

- **Gate 4's statements against G5-b and G5-c.**
  - The carried head would pass the overall reliability (±0.04), the slope ([0.75, 1.33]: 1.16)
    and the AUC (> 0.55: 0.61).
  - The temperature would miss the slope (0.74) and the AUC (0.544).
- **What G5-b's per-slice check catches.** Both Gate 4 statements fail on the truth-unsettled
  rows: about 0.6 stated against about 0.3 hit. That split is defined from the truth and is
  reported, not gated. Gate 5 gates the causal proxy's two states, which these files do not carry,
  since they predate spec 010.
- **The oracle's raw statement** is over-confident on settled rows too (0.92 stated against 0.83),
  and its slope is 0.24.
- **The IMM's AUC (0.72) is an artefact.** The IMM states nothing on 22.5% of rows. Those rows have
  P = 0 and never hit, which inflates the AUC.

Files: `calibration.json` (as run; see the slope correction above), `report.md`,
`inputs.json`, `plan.json`, `run.json`. `errors.npz` stays on the results branch.
