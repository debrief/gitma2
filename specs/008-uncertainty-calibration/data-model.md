# Data model: spec 008

All types are defined once in `schema/tma.yaml` (constitution I) and generated. Additions are
optional fields or new classes, so existing files stay valid. The schema bumps from 0.25.0 to
0.26.0.

## PredictionRow (extended)

| Field | Type | Meaning |
| --- | --- | --- |
| `cov_xyvv` | float[10] | Upper triangle, row-major, of the 4 × 4 covariance of (x, y, vx, vy) at the row (m², m²/s, m²/s²) |
| `log_range_sd` | float | existing optional field; now also physics-layer and tracker rows (R2) |
| `course_sd_rad` | float | first-order standard deviation of course |
| `speed_sd_mps` | float | first-order standard deviation of speed |
| `cov_ok` | boolean | the covariance is usable (finite, positive definite, range > 1 m) |
| `cov_scale_log` | float | calibrated rows only: the head's or temperature's s (calibrated covariance = e^{2s} · raw) |

Validation rules:
- all of these are absent or present together;
- `cov_xyvv` gives a symmetric, positive-definite matrix when `cov_ok`;
- the point fields are unchanged.

## EPredictionHeader (extended)

- `model_settings`: the plan entry of the model that made the file (veto window, fade, kind…)
  (R10).
- `segmentation_sha256`: the C segmentation file read, when one was read.
- `calibration` (optional): `{kind: head|temperature|none, weights_sha256, plan_sha256}`.

## CalibrationRecord (per estimator, per slice)

- `n_rows`, `no_estimate_share`;
- `coverage68`, `coverage95` per quantity (log range, course, speed): value, lo, hi;
- `coverage95_answered` per quantity: on the rows the estimator answers;
- `nees_median_ratio` (median NEES / 3.357): value, lo, hi;
- `nees_within95` (share below 9.488);
- `interval_score95` per quantity: mean, lo, hi;
- `sharpness95` per quantity: the median width.

Slices: overall; G5 time (4); open-at-k (2); range band (as Gate 2); detectability band (as
Gate S); settled (2); gross (2).

## CalibrationHeadConfig

`width` (32), `layers` (2), `bound` (2.0), `beta` (0.5), `cap` (100), `learning_rate`,
`batch_rows`, `max_epochs`, `patience`, `min_improvement`, `seed`, `shuffled`, `features`
(`["h_k", "log_sd_raw", "code_k"]`).

## TemperatureConfig

`slices`: a list of slice names (default: G5 time × open-at-k); `beta`, `cap` as the head's.

## Feature cache (`.npz`, per shard)

`ordinal[N]`, `k[N]`, `h[N, 64]`, `cov_raw[N, 10]`, `state[N, 4]`, `truth[N, 4]`, `own_k[N, 2]`,
`code_k[N]`, `cov_ok[N]`, `plausible[N]`, `slice keys`. The header binds:
- the plan and E's weights digest;
- the dataset digest;
- the commit and the dirty flag.

## Gate3Decision

As Gate2Decision, plus:
- `criteria` (G3-a…G3-d with their bands);
- `score_of_record` (interval score, log range);
- `temperature_slices`;
- `head_plan_digest`;
- `carried_e` (e-s3, `a5485318…`);
- `test_seed` 320;
- `forecast`.

## Gate3Record / verdict

`g3a` (per quantity), `g3b`, `g3c` (head − temperature, interval score; shuffled rule), `g3d`
(G2-a…G2-d re-checked), each with point, interval and outcome; `decided_by`.
