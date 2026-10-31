# Data model: References, Physics Layer and Gate P0

Persisted types are gitma's schema classes; this spec bumps the schema to 0.17.0 with additive,
optional fields only.

## Schema changes (0.16.0 → 0.17.0)

| Class | Added slot | Meaning |
| --- | --- | --- |
| `MetricsRecord` | `crb_range_rel_median`, `crb_course_deg_median`, `crb_speed_kt_median` | median Cramér–Rao bound over the slice's rows, in the metric's units |
| `MetricsRecord` | `efficiency_range`, `efficiency_course`, `efficiency_speed` | median error ÷ median bound (≥ 1 for an unbiased estimator in expectation) |
| `MetricsRecord` | `crb_singular_rate` | fraction of rows where the bound is undefined |
| `CurvePoint` | `efficiency_range`, `efficiency_speed` | the same along time since zig |
| `ExperimentManifest` | `python_version`, `torch_version` | provenance of the Python stack (optional) |
| `GateId` | `P0` | the gitma2 pipeline gate |

## Entities used (unchanged from gitma)

`PredictionHeader` (record, schema_version, estimator, mode, dataset_digest), `Prediction`
(scenario_index, estimator, mode, rows), `PredictionRow` (timestamp_s, range_m, course_rad,
speed_mps, x_m, y_m, converged, iterations, optional p_manoeuvre / sd fields), `MetricsRecord`,
`CurvePoint`, `GateCheck`, `GateVerdict`, `ExperimentManifest`, `DatasetRef`, `EstimatorRef`,
`NaiveMeans`, `NaiveModel`.

## In-memory records

| Record | Content |
| --- | --- |
| `BearingData` | per scenario: t, own_x, own_y, bearing, valid (float64 / uint8 arrays) |
| `Solution` | θ (4), converged, iterations, cost |
| `EkfState` | t, x (4), P (4×4) |
| `ImmState` | t, two Gaussians (5, 5×5), μ (2), nis |
| `CrbRow` | per scenario row: I (4×4), singular flag, sd_range_rel, sd_course_deg, sd_speed_kt (full-window and per-leg variants) |
| `PhysicsInputs` (torch) | bearings [B,R], valid [B,R], own [B,R,2], t [B,R], sigma [B], k [B] (current row), changepoint weights [B,R], speed weights [B,R], bearing log-weights [B,R], initial state [B,4] |
| `PhysicsOutputs` (torch) | state at k [B,4] (x, y, vx, vy), covariance [B,4,4], cost [B], plausible [B] (bool), range/course/speed [B] |
| `RowError` | t_since_zig_s, range_rel, course_deg, speed_kt, position_m, gross, converged (+ crb fields) |
| `G5Row` | scenario, k, minutes, settled, cluster |

## Invariants

- A prediction file's `dataset_digest` equals the SHA-256 of the truth file it was scored
  against; `tma2-eval` refuses a mismatch (gitma behaviour).
- Estimator names are gitma's strings, with JavaScript number formatting.
- Physics layer with trivial inputs and the classical grid start equals the LM solution; with
  all changepoint weights 1 and no priors it is an unregularised per-row velocity fit
  (ill-posed, used only in tests to check the extreme).
- The CRB is undefined (singular) before the first leg-2 bearing; efficiency is omitted there.
