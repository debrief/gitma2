# Data model: steady-leg detector and Gate D (schema 0.20.0)

All types are LinkML classes in `schema/tma.yaml` (constitution I); generated Pydantic models
validate every file read.

## Changed

| Class | Change |
| --- | --- |
| `PhysicsModelConfig` | `head_activation` (relu \| tanh; absent = relu, Gate 1's weights), `min_improvement` (relative; absent = 0) |
| `CheckpointMeta` | `weights_digest` (SHA-256 of `best.safetensors`) |
| `JobRecord` | `git_dirty` |
| `PredictionHeader` | `weights_digest` (optional; required by gate commands for learned estimators) |
| `ExperimentManifest` | `amendments`: list of `ArtefactRef` (path, digest, role "amendment") |
| `TrainingPlan` | `detectors`: a list of `DetectorConfig` beside `models` (now optional) |

## New

**`DetectorConfig`**: id, variant (causal | time_late), encoder (width, layers, heads, feedforward),
`head_activation` (tanh), input channels (13), `now_window_s` (60), `tolerance_s` (60),
`held_leg_weight` (3), loss weights (`now`, `boundary`, `kind`, `downstream`; downstream 0 for the
classification-only control), `knots` (8), `train_iterations` (50), `iterations` (100),
`downstream_rows` (2), `noise_draws` (1), optimiser fields, `epochs`, `patience`,
`min_improvement`, `seed`, `threads`.

**`HeadLiveness`** (in `CheckpointMeta.liveness`): head, alive share, output sd.

**`DetectorOutputRow`** (per-timestep prediction record): timestamp_s, `p_change`, exported knots
(row, weight, p_kind) as of this row; header carries the detector id and weights digest.

**`ControlSettings`**: kind (cusum | glr | imm_mode), parameters (δ for CUSUM, W for GLR, the IMM
setting), the tuned threshold and the validation false-alarm fraction it matched.

**`DetectionRecord`** (per scenario and detector, written by `tma2-gd` and the validation report):
scenario index, spans with detection row or miss or unresolved, delays, held-leg alarm count and
held-leg seconds, alarms at held-leg G5 rows, kind correctness per detected span, matched knots.

**`GateDDecision`**: plan id and digest, carried variants and seeds, control models, carried rule,
D1 threshold and tolerance, D2 variants and level, D3 limit rule (5% or the IMM's lower rate on
validation), D4 seeds, held-leg weighting, knot export threshold, controls' tuning rule, the frozen
IMM and EKF settings, validation rule, follow-on (Annex A §A.6), forecast, test seed and count,
bootstrap level and resamples.

## Relationships

`TrainingPlan` → `DetectorConfig` (models) → `CheckpointMeta` (weights_digest) →
`PredictionHeader` (same digest) → `ExperimentManifest` (artefacts incl. digests; amendments) ←
`GateDDecision` (bound by digest; its commit an ancestor of every `JobRecord.git_commit`).
