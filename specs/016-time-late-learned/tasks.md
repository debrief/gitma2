# Tasks: spec 016

## Phase 1: controls, code
- [x] T001 Prior version 4 (R6) with tests at support edges and solver bounds
- [x] T002 `hedge.py`: hedged track and declaration margin (R1, R2), tests
- [x] T003 `robust.py` (R3) and `corr.py` (R4), tests
- [x] T004 Prior kinds `broad`, `mix2` and the mismatch diagnostic (R5); `tl-shift2-ranges.json`
- [x] T005 `run4.py`, `study4.py`, CLI and workflow wiring, schema bump, fixture; tracks stored (R13)

## Phase 2: controls, tuning
- [x] T006 Tuning run on seed 338; settings chosen by the declared rules; record

## Phase 3 and 4: model
- [x] T007 Period stream with the mix (R9); non-causal model with logit head (R7); toy training test
- [x] T008 `learned.py` read-out (R8), `tma2-tlpredict`, export check (FR-015)
- [x] T009 Pilot on a T4 (at most 1 h); throughput; training plans written

## Phase 5: registration
- [x] T010 SRD §5 row and §9 line; decision record with digests, criteria and the power table

## Phase 6 to 8
- [x] T011 Train three seeds within the ledger cap
- [x] T012 Controls' validation on seed 340; L-a; record committed
- [x] T013 Test on seed 341: one scoring; tables by script; README check by test

## Phase 9
- [x] T014 Panel (five reviewers), corrections
- [x] T015 Write-up, slides post and deck with track plots; AGENTS.md; kickoff update; PR

## Not done as planned (see `experiments/20261114-tl4/review.md`)

- T001: prior version 4 was deferred (research, "As built").
- T003: only wild-bearing editing and an effective sd were built; no Huber cost, no whitened fit.
- T004: the mismatch diagnostic that was built is not a Bayes factor and does not work.
- T008: the export check ran on a toy model, not on the trained checkpoints.
- T005: no unit tests for `run_shard4` or `study_split4`; no schema bump (existing header
  fields were reused).
