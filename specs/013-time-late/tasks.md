# Tasks: spec 013, time-late TMA (Gate T)

## Phase 1: data and the solution format

- [x] T001 `configs/timelate/tl-ranges.json`, `tl-heldout.json` (MAN2 at 5 s); check the kernel at 1,440 rows (buffers, manoeuvre table, row-counted rules); existing data byte-identical (test)
- [x] T002 `timelate/periods.py`: the cut as a seeded in-memory transform (no new file format, no `tma2-period`; decided at build: simpler and existing data cannot change); tests
- [x] T003 `timelate/points.py`: fixed normal points (pairs for C); test (dropping, adaptive, robust: with T030)
- [x] T004 `timelate/track.py`: state at every row from `theta` and `knots`; test against the layer's last-row state
- [x] T005 `timelate/bound.py`: whole-period bound at every row; test against the prefix bound at the last row
- [ ] T006 Schema `TrackSolution`, `TrackRow`; regenerate types and the data dictionary

## Phase 2: systems and scoring on the tuning seed

- [ ] T010 `timelate/systems.py`: reference, C″ to the end (frozen C on pair points), one leg, IMM (causal); `tma2-tlsolve`
- [ ] T011 `timelate/score.py`, `tma2-tlscore`: whole-track errors, determined rows, strata, manoeuvre measures
- [ ] T012 `timelate.yml`, smoke plan; emulate the command builder locally before launching
- [x] T013 First checkpoint on seed 329 (local, 24 to 60 periods): **stopped by the rule.** The reference is at about twice its bound on cut periods and 4.5 times on whole engagements; the scoring is sound; the cause is the layer's manoeuvre model (`experiments/20261111-tl-diagnosis/`). Owner 2026-11-11: add the arc-model solve.
- [x] T014 `timelate/arc.py` (arc-model least squares, search over starts, kind selection; tests); measured on 60 tuning periods (`experiments/20261111-tl-arc/`): 1.2 to 1.4 × the bound on true times against the chord's 1.9; worse than the chord on C″'s own transitions. The reference is the arc solve on true times.
- [x] T015 `timelate/retest.py` (full-period re-test on the arc cost: refine times, add, remove); measured on the same 60 periods (`experiments/20261111-tl-retest/`): **no better than C″ read as a track**; it fits the bearings as well as the true-times fit (median cost difference 0) and is 3 to 4 times worse in range. The limit is identifiability, not the search: what separates structures is prior knowledge of manoeuvres. Owner 2026-11-11: classical prior first.
- [x] T016 `timelate/prior.py`, `retest.log_evidence`/`choose_kinds`/`ensemble` (tests); measured (`experiments/20261112-tl-prior/`): told only the basin, the fit reaches the bound (1.03, 1.00, 1.17) with times free; under Annex B's prior the true history is not more probable than the re-test's wrong one (ahead by over 3 in about 0.4 of the bad periods, behind by over 3 in about 0.4); a local evidence-weighted ensemble does not help. No single-history estimator reaches the reference. Owner's decision: a full sampler over histories, the learned full-period model, or write up.
- [x] T017 Correction: T016's evidence reading was an artefact (prior evaluated at a bearings-only fit). With the fit to the posterior, the true history is usually preferred and the re-test's history refitted with the prior halves C″'s error as a track (0.057 against 0.113). Decision back with the owner; next: a search over histories scored by evidence.

## Phase 3: the full-period system

- [ ] T020 Full-period re-test (`c2-full`): drop, add, iterate; tests (causality is not required; no truth read)
- [ ] T021 Settings on seed 329 by the declared rule (research R4); misses recovered; record

## Phase 4: compression study

- [ ] T030 `scripts/research/tl_compress.py`: the four forms, clean and outlier conditions, accuracy and run time; record; apply the adoption rule (research R7)

## Phase 5: Gate T

- [ ] T040 `timelate/gate.py`; schema `GateTCriteria`, `GateTDecision`
- [ ] T041 SRD §5 row and §9 line (owner merges); plan `configs/timelate/gt-a.json`; decision record with forecasts, before seeds 330 and 331 exist
- [ ] T042 Validation (seed 330): T-a; record
- [ ] T043 Test (seed 331), once; record; registered breakdowns; the reported regressor line
- [ ] T044 Panel review; verdict
- [ ] T045 Write-up, slides post (FR-050), AGENTS.md
- [x] T018 Owner 2026-11-12: continue classically. `timelate/search.py` (evidence-scored search, candidate tracks; test). Measured on 99 fresh tuning periods (`experiments/20261112-tl-search/`): 0.042 against C″'s 0.088 (2.12 [1.62, 2.96]). Probabilities not calibrated.
- [x] T019 `tma2-tlsolve`, `tma2-tlscore`, `timelate.yml` (smoke run 43200187567 green); schema 0.34.0 (`TimeLateShardHeader`, `GateTCriteria`); one leg, IMM, EKF as tracks.
- [ ] T020 (registered 2026-11-12, `experiments/20261112-gt-decision/`; validation launched) Register Gate T (SRD row for the owner; criteria incl. a prior-shift split and a calibration measure), decision record; validation 330; test 331; panel; write-up; slides.
- [x] T021 Validation seed 330 (`experiments/20261112-gt-val/`): **T-a failed (0.67); gate stopped; seed 331 not generated.** The reference starts at the truth (tested on tuning data). T-b to T-d would pass (C″ ÷ search 2.56). Owner to decide on re-registration.
- [x] T022 Owner 2026-11-12: re-register. `run.history_reference` (neutral starts; times held / free / with the prior), efficiency by bound band in `tma2-tlscore`, T-d-shift, schema 0.35.0; second decision record `experiments/20261112-gt2-decision/` (plan `tl-b.json`).
- [ ] T023 Smoke on CI, validation seed 332, test seed 331 if T-a passes, panel, write-up, slides.
