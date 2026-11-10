# Data model: spec 012

## RegressorConfig (`configs/regress/*.json`, schema type)

`id`, `seed`, `patch_rows` (3), `layers`, `width`, `heads`, `feedforward`, `loss` (`beta_nll`),
`beta`, `batch_scenarios`, `learning_rate`, `warmup_updates`, `weight_decay`, `stream_seed`
(326), `stream_start`, `stream_repeat` (0, or the length of the repeated block for the
tenth-of-data control), `inputs` (`full` or `ownship_only`), `limit_gpu_seconds`,
`checkpoint_seconds`, `precision` (`amp` or `float32`).

## RegressorRunRecord (`run.json` on a results branch)

`config` and its digest, `git_commit`, `gpu` (type, count), `gpu_seconds`, `segments` (each:
start, end, updates, resumed-from digest), `scenarios_seen`, `scenarios_per_second`, `torch`,
`cuda`, `modal` versions, `checkpoint_sha256`, `validation` (loss and median errors by
checkpoint), `stopped` (`limit`, `complete` or `error`).

## RegressorDecision (`experiments/<date>-r-decision/decision.json`)

Plan digest, the carried configuration, the budget table, seeds (326, 327, 328), the readings'
thresholds (1.25, 2.0) and level, the two controls, forecasts, and the reduction rule (R3).

## Predictions

Existing prediction header and rows; `estimator` names the run (`reg-s1` …), `mode`
`per_timestep`; rows at the scorer's prefixes.

## Reading (`reading.json`)

Per trained seed and pooled: held-course efficiency with interval for the regressor and batch
least squares, by geometry band; the reading; paired differences after manoeuvres against C″ and
the IMM, by range quartile, in relative and operational units; rows counted.
