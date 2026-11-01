---
description: "Task list for spec 003: Gate 1 on constant-velocity data"
---

# Tasks: Gate 1, a learned model on constant-velocity data

**Input**: `specs/003-gate1-cv/` (spec, plan, research, data model, contracts, quickstart)

**Tests**: required (constitution): golden and unit tests, the implicit-gradient check, resume
equality, export conformance.

## Phase 1: Entry conditions from P0 (US6)

- [x] T001 `cov_ok` also false when the solved track passes within 1 m of ownship at any valid
  sample ≤ k, or a Jacobi-scaled pivot is within 1e3 × COV_RIDGE; test at K = 100 on the collapse
  rows (phase4 train scenarios 15 and 50)
- [x] T002 `check_physics_equals_ls`: fail on a non-finite covariance (only range ≤ 1 m is
  degenerate); bound the states of lower-cost rows in sd units; negative test with a crippled
  layer (K = 5)
- [x] T003 `Experiment` refuses folders outside `experiments/`; tests for an edit outside the
  folder and a commit during a run (in a temporary clone)
- [x] T004 At-scale check asserts gitma's IMM header estimator and the gitma pack's generator
  commit; P0 records the data and conformance commands

## Phase 2: Types (all stories)

- [x] T005 Schema 0.18.0: `PhysicsHead`, `PhysicsModelConfig`, `TrainingPlan`, `JobRecord`,
  `CheckpointMeta`, `PhysicsModelManifest`, `Gate1Decision`, `GateId.G1`; regenerate; data
  dictionary

## Phase 3: Model (US1)

- [x] T006 Physics layer implicit mode (exact-Hessian Newton step) and zero knots (research R1)
- [x] T007 `models/rows.py`: re-noising, scored rows, grid start, CRB state covariance (R5)
- [x] T008 `models/features.py`, `models/encoder.py` (causal transformer, fast path off),
  `models/gate1.py` (heads, physics layer, direct-head control, time-late variant)
- [x] T009 `models/loss.py`: CRB-normalised squared errors, β-NLL, auxiliary init loss, cap
- [x] T010 Tests: untrained model equals batch LS (FR-009); finite gradients on every parameter;
  implicit gradient equals central differences of the converged solve (1e-3 relative on
  determined rows); determinism of a training step

## Phase 4: Training (US1, US2)

- [x] T011 `models/train.py` + `tma2-train`: epochs over on-the-fly data, validation loss, stop
  rule, checkpoints with optimiser and RNG state, resume, wall-clock cap; resume test (two runs of
  one epoch each equal one run of two)
- [x] T012 Throughput: one epoch on 10⁴ scenarios locally at 4 threads, extrapolated to 10⁵ and
  recorded (FR-014); adjust rows per scenario only before the decision record
- [x] T013 `models/predict.py` + `tma2-predict`: per-timestep predictions at every post-zig row in
  gitma's prediction format

## Phase 5: Data and references (US3)

- [x] T014 Validation split (seed 302) and its digest; `tma2-tune` with research R6's grids;
  `experiments/<date>-g1-tune/` committed with the frozen EKF and IMM

## Phase 6: Export (US5)

- [x] T015 Physics iteration body as a scripted tensor function shared by eager and export
  paths, bit-identical to the current layer; Loop export of the full model at K = 100
- [x] T016 `models/export.py`: ONNX, safetensors, manifest, golden batch; Python, WASM and Java
  legs to 1e-5; load time under a minute; CI job

## Phase 7: Runs (US2)

- [x] T017 `.github/workflows/train.yml`: plan branches, matrix over models, chained ≤ 345-min jobs (four),
  checkpoint branches, results branches, job records; a short plan exercised end to end

## Phase 8: Pre-registration and training (US4)

- [x] T018 `configs/gate1/plan.json` (three seeds of the carried configuration; controls a, c, d)
  and `experiments/<date>-g1-decision/decision.json` with forecast; commit before training
- [ ] T019 Push `train/g1-a`; monitor; collect results; validation report with the carried rule
  applied, controls checked (shuffled no better than batch LS, amendment 1; time-late ≥ causal)

## Phase 9: Gate (US3)

- [ ] T020 `eval/g1.py` + `tma2-g1`: decision and seed checks, same-rows scoring of every
  reference, clustered ratios and gross-error difference, efficiency per slice, verdict
- [ ] T021 Test split (seed 303), predictions, `tma2-g1`, the agent panel (rounds), `review.md`,
  `decided_by`

## Phase 10: Site (US7)

- [ ] T022 `site/docs/algorithms/gate1-model.md`; glossary; the Gate 1 write-up with the numbers;
  README, AGENTS and welcome status
