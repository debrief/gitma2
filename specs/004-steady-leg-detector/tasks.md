# Tasks: steady-leg detector and Gate D (spec 004)

Ordered by dependency; [P] marks tasks that can run in parallel with the previous one. Each task
names its files and the requirement it serves.

## Phase 1: Gate 1 prerequisites (US1, US2)

- [x] T001 Schema 0.20.0: `head_activation`, `min_improvement`, `CheckpointMeta.weights_digest`,
  `JobRecord.git_dirty`, `PredictionHeader.weights_digest`, `ExperimentManifest.amendments`,
  `DetectorConfig`, `ControlSettings`, `DetectionRecord`, `GateDDecision`; regenerate types; tests
  (FR-001–FR-008, data-model)
- [x] T002 `models/heads.py`: head MLPs with relu | tanh; liveness diagnostics (alive share, output
  sd); `gate1.py` uses it (relu kept for Gate 1's weights; a test re-loads them) (FR-001)
- [x] T003 Liveness and learnability test: a tiny model trained a few hundred steps on varying
  labels passes; a zeroed-head model fails (FR-002, SC-002)
- [x] T004 `train.py`: `min_improvement`; `git_dirty` in job records; `weights_digest` in
  checkpoint meta; liveness figures logged per epoch (FR-003, FR-005)
- [x] T005 `predict.py` and prediction headers: `weights_digest`; no fallback to non-best weights in
  gate use; `tma2-g1` and the new gate check the digest; manifests list amendments (FR-004, FR-006)
- [x] T006 One median convention in reported efficiencies; one convergence definition in gross
  counting with gross rows by cause (`eval/g1.py`, `eval/metrics.py`) (FR-007, FR-008)

## Phase 2: Data and references (US3, US4)

- [x] T007 Validation split seed 304 (100,000; f32pack) and its digest
- [x] T008 `tma2-tune --criterion g5` and the G5 grid of R7; run on seed 304 from a clean tree;
  commit the tune record (FR-026)
- [x] T009 IMM: expose μ_CT per row (`references/imm.py`), with a conformance test that the
  estimates are unchanged (FR-024)

## Phase 3: Detector (US3)

- [x] T010 `models/detector_labels.py`: now, boundary (±60 s triangular) and kind targets; held and
  settled flags; tests on fixture spans (FR-011, R3)
- [x] T011 `models/detector.py`: 13-channel encoder (spec 003 design), p_change, pairwise w_change
  and p_kind heads (tanh, zero-initialised outputs), causal and time-late variants; untrained
  outputs give no knots; tests (FR-012, FR-013, FR-015, R2)
- [x] T012 Soft segmentation → physics inputs (R4) and knot export (local maxima above the
  threshold, top 8, kinds); tests against the oracle's inputs on fixture spans (FR-014)
- [x] T013 `models/detector_loss.py`: classification losses with held-leg weighting; downstream
  CRB-normalised loss through the physics layer (implicit); classification-only mode; finite
  gradients test (FR-016–FR-018, R5)
- [x] T014 Training integration: detector configurations in plans, two downstream rows, one noise
  draw, K = 50 training solve; resume equality test; local throughput measured (FR-019–FR-021)
- [x] T015 `tma2-detect`: per-timestep outputs with weights digest (contracts/cli.md)

## Phase 4: Controls and metrics (US4, US5)

- [x] T016 `detect/controls.py`: CUSUM on least-squares innovations, linearised GLR (W = 30),
  IMM μ_CT; `tma2-controls tune|run`; tests on synthetic manoeuvres (FR-022–FR-024, R6)
- [x] T017 `detect/matching.py`: alarms, detection, delays, misses, unresolved, held-leg false
  alarms (G5 fraction and per hour), kind accuracy, F1, ECE; tests (FR-028, R8)
- [x] T018 `detect/downstream.py`: exported knots and kinds → physics layer with trivial weights at
  G5 rows; reported beside batch LS, IMM, EKF, oracle (FR-027, FR-028)
- [x] T019 `eval/gd.py` + `tma2-gd`: bindings and refusals, Gate D checks with 97.5% clustered
  bootstraps, validation rule, record and verdict; tests (FR-029–FR-031)

## Phase 5: Export (US7)

- [x] T020 `models/detector_export.py`: ONNX, safetensors, manifest, golden batch; three legs;
  WASM time per window under one second; CI step (FR-033)

## Phase 6: Pre-registration, training and the gate (US5, US6)

- [x] T021 Runner throughput (bench) for the detector configuration; adjust per R5 within the
  plan's rules before registration (SC-003)
- [x] T022 `configs/gate-d/plan.json` and the decision record with FR-035's architecture check;
  commit before training (FR-032, FR-034, FR-035)
- [x] T023 Train (`train/gd-a`); validation workflow: detector outputs, control tuning (amendment by
  digest), validation report with the carried rule and the validation rule
- [x] T024 Gate workflow on seed 305 if the validation rule is met; `tma2-gd`; agent panel;
  `review.md`; `decided_by` (validation rule not met: no test; the panel reviewed the validation
  stop, round 2, `experiments/20261102-gd-a-val/review.md`)
- [x] T025 Site: detector algorithm note, glossary, Gate D write-up; AGENTS status (FR-036)
