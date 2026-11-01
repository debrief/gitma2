# Contract: evaluation outputs and the experiment folder

Identical to gitma's layouts (`packages/eval/src/csv.ts`, `experiment.ts`) plus efficiency.

## `metrics.csv` / `metrics.json`

Columns, in order: `estimator, slice, point, n, excluded, range_rel_median, range_rel_p90,
course_deg_median, course_deg_p90, speed_kt_median, speed_kt_p90, gross_error_rate,
non_converged_rate, position_m_mean, position_window_m_median, position_window_m_p90,
crb_range_rel_median, crb_course_deg_median, crb_speed_kt_median, efficiency_range,
efficiency_course, efficiency_speed, crb_singular_rate`. Empty cells for absent values. JSON is a
list of `MetricsRecord`.

## `curves.csv`

`estimator, t_since_zig_s, n, range_rel_median, range_rel_p90, course_deg_median,
speed_kt_median, gross_error_rate, non_converged_rate, efficiency_range, efficiency_speed`.

## `bootstrap.json`

gitma's `BootstrapReport` shape: per estimator/point/slice, median intervals for
`range_rel`, `course_deg`, `speed_kt` and paired ratio intervals against a named reference;
clustered variants carry `clusters` and `level`.

## `experiments/<id>/`

```
manifest.json   ExperimentManifest (+ python_version, torch_version)
metrics.json    the checks' numbers
checks.csv      one row per P0 check: name, result, value, threshold, detail
verdict.json    GateVerdict { gate: "P0", result, checks[], decided_by }
review.md       panel rounds (added by the panel step)
```

## Prediction NDJSON

Line 1 `PredictionHeader` (`dataset_digest` = SHA-256 of the truth file); then one `Prediction`
per scenario in truth order. Canonical JSON. Readable by gitma's `tma-eval`.
