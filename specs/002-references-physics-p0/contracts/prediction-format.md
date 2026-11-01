# Contract: prediction files (shared with gitma)

Format: `specs/001-iteration-0-pipeline/contracts/file-formats.md` in gitma; types
`PredictionHeader`, `Prediction`, `PredictionRow` in `schema/tma.yaml`.

- Line 1: `{"dataset_digest": "<sha256 of truth file>", "estimator": "<name>", "mode":
  "final"|"per_timestep", "record": "header", "schema_version": "<x.y.z>"}`.
- Then one `Prediction` per scenario, in the truth file's order:
  `{"estimator", "mode", "record": "prediction", "rows": [...], "scenario_index"}`.
- `rows`: per-timestep files carry one row per sample from `zig_index + 1` to the end; final
  files one row at the last sample. Row fields: `timestamp_s`, `range_m`, `course_rad`,
  `speed_mps`, `x_m`, `y_m` (all float32-rounded), `converged`, `iterations`; optional
  `p_manoeuvre`, `log_range_sd`, `vx_sd_mps`, `vy_sd_mps`.
- Non-converged rows carry placeholders (gitma: the EKF keeps its state, the IMM and classical
  write zeros or the implausible solution); readers score them as +∞ regardless.
- Readers check the schema version (same rules as datasets) and the digest against the truth
  file when both are given.
