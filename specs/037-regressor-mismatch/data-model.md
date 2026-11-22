# Data model: spec 037

- **MismatchCondition** (schema): adds `white_t_df` (> 2) and `sigma_step_factor` (≥ 1).
  A condition using either records overlay version 0.8.0; others stay 0.7.0.
- **TrainingMix** (`configs/regress/ft-mix.json`): `clean_share`, per kind `p_on` and the
  severity ranges; `stream` number. Digest bound in the plan.
- **RegressorConfig**: adds `mix` (path, empty = spec 012's clean stream) and `init_from`
  (a results branch and folder, with the checkpoint's digest). Omitted from the JSON at their
  defaults so spec 012's and 016's digests do not move.
- **Regressor prediction row**: adds `range_lo_m`, `range_hi_m`, `speed_lo_mps`,
  `speed_hi_mps`, `course_arc_rad` (absent = undetermined), `sd_course_rad`; header adds
  `interval_scale` (three numbers) and `init_weights_sha256`.
- **rmis plan** (`configs/rmis/<name>.json`): seed, count, ordinals, shard size, conditions
  (ids; files they come from), classical runs, checkpoints (name, branch, folder, digest),
  IMM and EKF names, `split`, `decision` (validation and test), `interval_scale` file,
  `hybrid` settings.
- **Reading record** (`reading.json`): per condition and reading: n scenarios, geometric
  mean, interval, median, shares, outcome; coverage tables; per-seed and pooled.
- **Decision record**: plan digests, code digest, readings and thresholds, forecasts, seeds
  (369 stream, 370 validation, 371 test), the ledger's total at registration.
