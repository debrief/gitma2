# Tasks: spec 012, the scaled end-to-end regressor control

## Phase 1: CPU build

- [x] T001 `regress/frame.py` (canonical frame, targets, inverse) + invariance test
- [x] T002 `regress/data.py` (on-the-fly stream, repeat block for the tenth-of-data control)
- [x] T003 `regress/model.py` (folded rows, causal transformer, β-NLL) + causality test
- [x] T004 `regress/train.py`, `tma2-rtrain` (time limit, checkpoints, resume, run record) + toy run test
- [x] T005 `regress/predict.py`, `tma2-rpredict` (rows at the scorer's prefixes)
- [x] T006 Score a toy model's predictions with the existing scorer on a small split (proves the path)
- [x] T007 `regress/reading.py`, `tma2-rread` (held-course efficiency by geometry band; manoeuvring differences) + tests
- [x] T007a Held-course ranges and a held-course share of the stream (research R8) + test
- [ ] T008 Schema: `RegressorConfig`, `RegressorRunRecord`, `RegressorDecision`; the prediction header as a schema type

## Phase 2: GPU plumbing (no secrets needed)

- [x] T010 `scripts/modal_train.py` (image, volume, one function, hard timeout), written from Modal's documentation of 2026-11-10; not yet run with credentials; `modal` installed by the workflow only (`uv run --with modal`)
- [x] T011 `.github/workflows/gputrain.yml` (ledger check, modal run, chained segments, results branch); pushes only; `regress/ledger.py`
- [x] T012 Dry run: the provider-free segment runner (`regress/remote.py`) on CPU, two segments (test)

## Phase 3: registration

- [x] T020 Plans `configs/regress/{pilot-curve,r-a-s1..3,r-a-own,r-a-tenth}.json`; decision record `experiments/20261111-r-decision/`
- [x] T021 Owner: Modal account, limits ($15 spend limit; $50 budget), secrets (checked by `modal-check`)

## Phase 4: runs

- [x] T029 Scoring pipeline: `.github/workflows/rscore.yml`, `scripts/rscore_job.sh`, `scripts/rscore_push.sh`, plans `configs/rscore/`; smoke run 42976549223 (pilot checkpoint; pipeline check only)
- [ ] T030 Pilot (at most 8 T4-hours): throughput first, then learning curves; apply the reduction rule
- [ ] T031 Three seeds; the ownship-only and tenth-of-data controls
- [ ] T032 Predict and score on validation seed 327; then test seed 328 once per trained seed (C″, references, bound on CI)
- [ ] T033 Readings; panel review; write-up; slides post (FR-031); AGENTS.md
