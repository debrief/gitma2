# Data model: spec 010

## MismatchCondition
- `id` (for example `off`, `corr-central`, `all-central`), `primary: bool`
- `correlated`: `tau_s`, `share` (0.5) or absent
- `bias`: `sd_rad`, `tau_s` or absent
- `sigma`: `k` or absent
- `outliers`: `rate`, `spread` (10) or absent
- Rule: `off` has none of the four; exactly one condition is primary.

## MismatchTruth (side file `<split>.mismatch.npz`, read by ceilings only)
- header: condition, digest of the split it belongs to, generator version and commit
- per engagement: `sigma_true_rad`, `sigma_w_rad`, `sigma_c_rad`, `tau_c_s`, `sigma_b_rad`,
  `tau_b_s`, `outlier_rate`, `outlier_spread`
- per sample: `e_white`, `e_corr`, `e_bias`, `outlier` (bool), `e_outlier`
- Rule: the pack's bearing equals the wrapped float32 of b plus the components' sum on valid
  samples. The pack header's σ stays the nominal value.

## Predictions
- Existing `PredictionRow`; model names `ceiling-attainable`, `ceiling-realisation`, `robust`,
  `robust-huber`, `robust-sigma`, `robust-whiten`, each with suffix `@truth` or `@c` for the
  segmentation used. Headers record the condition and, for ceilings, the truth file's digest.

## GateHPlan (`configs/gateh/gh-a.json`)
- conditions file and digest; primary condition; seeds; scenario counts
- robust control's settings; references by frozen name
- criteria: H-a band, H-b tolerance 1.02, H-c threshold 0.10; bootstrap settings

## HeadroomRecord (`headroom.json`, per condition)
- `R` with interval, for range; the same for course and speed
- on C's segmentation: the gap, the part the control closes, the remainder, the mismatch-off value
- operational table: metres, degrees, knots, share settled by 5, 10, 15, 20 min
- rows counted, rows every estimator answers
