# Tasks: spec 011, a robust classical segmenter (Gate R)

Order is dependency order. [P] can run beside its neighbours.

## Phase 0: diagnosis (done unless marked)

- [x] T001 `diagnose.yml`, plans, run on seed 323 (150 engagements, 6 conditions)
- [x] T002 `scripts/research/gr_diagnosis.py`, `gr_kind_shares.py`; record `experiments/20261110-gr-diagnosis/`
- [x] T003 `tma2-hpredict --segments-from` (the clean split's segmentation applied to this split) and `--dump-segmentation`
- [x] T004 FR-003 on seed 323, primary and off: robust final solve on C's segmentation, on C's
      clean-data segmentation applied to the mismatched bearings, on the truth; add to the record
- [ ] T005 Which decisions over-accept: `Confirmed.decisions` under off and outliers by source,
      open or closed, drop against threshold (a research script; 60 engagements); add to the record

## Phase 1: C-r

- [x] T010 Schema 0.32.0 (header fields; gate types pending): `RobustConfirmSettings`, header `robust` block, `GateRCriteria`,
      `GateRDecision`; regenerate types and the data dictionary
- [x] T011 `segment/robust.py`: hypothesis-free scale and lag-1 estimate; Huber-cost driver over
      `confirm._confirm_one`; `segment_robust`; threshold factor
- [x] T012 `tma2-hpredict --segmentation c2r --robust-confirm` (header: settings, `robust_code_sha256`)
- [x] T013 Tests: C's digests unchanged; C-r at unit weights equals C; causality by truncation;
      finite costs with a 30 σ bearing; scale estimate on white noise
- [x] T014 Runs through `headroom.yml` (plans `configs/headroom/gr-*.json`); smoke runs
- [x] T015 Pilot (`experiments/20261110-gr-pilot/`) and the choice on 150 (`experiments/20261111-gr-choice/`):
      the robust test is not carried; by the rule C-r is C at three times its threshold

## Phase 2: Gate R

- [ ] T020 `segment/gate_r.py`, `tma2-gr` (share closed, remainder, R-a, R-b, breakdowns) + tests
- [ ] T021 SRD §5 row and §9 line (owner merges); `configs/gater/gr-a.json`; decision record
      with forecasts and the at-most yield, before seeds 324 and 325 exist
- [ ] T022 Validation (seed 324): R-a and pipeline soundness; record
- [ ] T023 Test (seed 325), once; record; registered breakdowns
- [ ] T024 Panel review; `review.md`; verdict
- [ ] T025 Write-up, slides post (FR-040), AGENTS.md; kickoff post dated paragraph

## Closed at tuning (owner, 2026-11-11)

- [x] T005 not run: the choice run's transition counts answered the design question
- [x] T020–T024 not run: no Gate R (the robust test was not carried; the owner chose to publish)
- [x] T025 Write-up `site/blog/2026-11-11-robust-segmenter.md`, slides post and deck, AGENTS.md, SRD §9
