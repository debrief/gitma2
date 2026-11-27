# Tasks: spec 038, where the regressor's gain comes from

Order matters where a task names an earlier one. `[P]` can run beside its neighbours.

## Phase 1: code (no result)

- [x] T001 `src/tma2/headroom/edit.py`: wild-bearing editing and an effective sd for the data C
  sees, causal at the scored rows; tests `tests/unit/test_headroom_edit.py` (R2).
- [x] T002 `tma2-hpredict --edit`, `--segments-cache`; the header's `segmenter_settings`
  carries the edit; C's digests unchanged (`test_segment_robust.py::test_c_is_frozen`).
- [x] T003 [P] `src/tma2/regress/decomp.py`, `tma2-rdecomp`; tests
  `tests/unit/test_regress_decomp.py` (R5).
- [x] T004 [P] `tests/unit/test_ownship_only.py`: which bearings reach the ownship-only model
  (FR-010, R3).
- [x] T005 `headroom.yml`: plan keys `ranges`, `heldout`, `segments_cache`, `runs[].edit`,
  `decomp`; `scripts/gd_read.sh`. The command builder emulated against the real plan.
- [x] T006 `configs/gd/protocol.json`, `configs/gd/shift-ranges.json` (generated locally on a
  spent seed: rows at the scored prefixes exist on all three splits), `scripts/research/gd_plan.py`.
- [ ] T007 Smoke: every run kind of the development plan on three engagements, locally; a
  cache hit reproduces the uncached rows.

## Phase 2: development on spent seeds

- [ ] T010 Run A (seed 321, in distribution, 300 engagements, clean and primary): threshold
  grid, edit variants, own-prior weight grid. Record `experiments/<date>-gd-dev-a/`.
- [ ] T011 Choose by the rules of research R1 to R3; write `chosen` into the protocol; extend a
  grid whose best value is at its edge.
- [ ] T012 Run B (seed 370, three splits): the chosen settings and their neighbours; every
  reading end to end; the stop rule (FR-042) read here. Record `experiments/<date>-gd-dev-b/`.
- [ ] T013 `scripts/research/gd_tables.py` (tables from `decomp.json`; split differences from
  `decomp-logs.npz`), tested on run B.
- [ ] T014 Thresholds checked over bootstrap seeds on run B (R7).

## Phase 3: registration and test

- [ ] T020 Decision record `experiments/<date>-gd-decision/`: protocol digest, code digest,
  estimands, thresholds, forecasts with their basis, what is reported beside.
- [ ] T021 Test: seed 372, three plans, scored once. Record `experiments/<date>-gd/`.
- [ ] T022 Three reviewers (fidelity, statistics, critical); `review.md`; corrections.

## Phase 4: reporting

- [ ] T030 `scripts/research/gd_charts.py`; figures under `site/static/img/<date>-gain-decomposition/`.
- [ ] T031 Write-up and slides post; deck.
- [ ] T032 AGENTS.md; what was promised and not run; PR.
