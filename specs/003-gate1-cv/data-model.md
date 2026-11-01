# Data model: Gate 1 (schema 0.18.0)

Every persisted type is a LinkML class in `schema/tma.yaml`, generated to Pydantic and validated
on read and write (constitution I). New classes:

## PhysicsModelConfig

One model's hyperparameters (FR-010); carried in its manifest.

| Field | Type | Notes |
| --- | --- | --- |
| id | string | estimator name in predictions |
| head | enum PhysicsHead: physics, direct | direct = control (a), never carried |
| causal | boolean | false = time-late control (d) |
| width, layers, heads, feedforward | integer | encoder (R3: 64, 2, 4, 128) |
| weight_bound, scale_bound | float | log-weight and covariance log-scale bounds (2, 2) |
| iterations | integer | physics layer K (100) |
| loss_init_weight, loss_nll_weight, nll_beta, loss_cap | float | 0.1, 1, 0.5, 100 |
| rows_per_scenario, noise_draws | integer | 4, 2 |
| batch_scenarios | integer | 64 |
| learning_rate, weight_decay | float | Adam |
| epochs, patience | integer | stop rule |
| seed | integer | training seed (initialisation and row sampling) |
| shuffle_labels | boolean | control (c) |
| threads | integer | pinned |

## TrainingPlan

A plan branch's content.

| Field | Type | Notes |
| --- | --- | --- |
| id | string | plan id (`g1-a`) |
| ranges | ParameterRanges | the CV ranges (iteration-4 fixture's) |
| train_seed | integer | 310 |
| scenarios_per_epoch | integer | 10⁵ |
| validation | DatasetRef | seed 302, with digest |
| models | PhysicsModelConfig, multivalued | carried seeds and controls |
| decision | string | path of the decision record it implements |

## CheckpointMeta

| Field | Type | Notes |
| --- | --- | --- |
| model_id, plan_id | string | |
| epoch | integer | last completed |
| best_epoch, best_val_loss | integer, float | |
| complete | boolean | stop rule met |
| rng_state | string | serialised generator state |
| lineage | string | commit, plan digest |
| jobs | JobRecord, multivalued | start, end, seconds, cpu_model, threads, epochs |

## PhysicsModelManifest

The exported artefact's manifest (FR-022): config, schema and generator versions, training commit,
plan id, data digests, weights SHA-256, ONNX SHA-256, window rows, iterations, inputs and outputs
with shapes and dtypes, conformance results.

## Gate1Decision

The pre-registered record (FR-016, FR-021): plan id and digest, model ids (three carried seeds,
three controls), the carried rule, the test seed (303) and split size, gate rows, criterion,
forecast, follow-on if failed, EKF/IMM frozen settings, created commit.

## Relationships

TrainingPlan → PhysicsModelConfig (many) → CheckpointMeta (one per model) → PhysicsModelManifest
(per carried model). Gate1Decision → TrainingPlan; the gate's ExperimentManifest names the
decision, the plan, the models' weight digests and the datasets.
