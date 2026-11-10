# Tasks: spec 012, the scaled end-to-end regressor control

## Phase 1: CPU build

- [x] T001 `regress/frame.py` (canonical frame, targets, inverse) + invariance test
- [x] T002 `regress/data.py` (on-the-fly stream, repeat block for the tenth-of-data control)
- [x] T003 `regress/model.py` (folded rows, causal transformer, β-NLL) + causality test
- [x] T004 `regress/train.py`, `tma2-rtrain` (time limit, checkpoints, resume, run record) + toy run test
- [x] T005 `regress/predict.py`, `tma2-rpredict` (rows at the scorer's prefixes)
- [x] T006 Score a toy model's predictions with the existing scorer on a small split (proves the path)
- [ ] T007 `regress/reading.py`, `tma2-rread` (held-course efficiency by geometry band; manoeuvring differences) + tests
- [ ] T008 Schema: `RegressorConfig`, `RegressorRunRecord`, `RegressorDecision`; the prediction header as a schema type

## Phase 2: GPU plumbing (no secrets needed)

- [ ] T010 `scripts/modal_train.py` (image, volume, one function, hard timeout), checked against Modal's current documentation; `modal` in an optional dependency group
- [ ] T011 `.github/workflows/gputrain.yml` (ledger check, modal run, chained segments, results branch); never on fork pull requests
- [ ] T012 Dry run: the app's function executed locally on CPU with `configs/regress/toy.json`

## Phase 3: registration

- [ ] T020 `configs/regress/pilot.json`, `r-a.json`; decision record (configuration, budget, readings, controls, forecasts, reduction rule)
- [ ] T021 Owner: Modal account, spending limit, `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` (owner-only; wait)

## Phase 4: runs

- [ ] T030 Pilot (at most 8 T4-hours): throughput first, then learning curves; apply the reduction rule
- [ ] T031 Three seeds; the ownship-only and tenth-of-data controls
- [ ] T032 Predict and score on validation seed 327; then test seed 328 once per trained seed (C″, references, bound on CI)
- [ ] T033 Readings; panel review; write-up; slides post (FR-031); AGENTS.md
