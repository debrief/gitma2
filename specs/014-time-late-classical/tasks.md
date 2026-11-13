# Tasks: Time-late, the classical follow-on to Gate T (spec 014)

**Input**: `specs/014-time-late-classical/` (spec, plan, research R1–R10, data-model, contracts/cli.md, quickstart)

Tests are part of each task (plan, Testing). Nothing is trained; no GPU.

## Phase 1: Setup

- [x] T001 Pin Gate T: write `tests/fixtures/timelate/gt-fixture.json` (two periods of tuning seed 329: candidates' evidence, spans, tracks from the registered search) and a test in `tests/unit/test_timelate2.py` that the working tree reproduces it to 1e-4 (the evidence moves 2e-7 between CPU families) with default settings (R1)
- [x] T002 Schema 0.36.0 in `schema/tma.yaml`: `TimeLateStudyCriteria` (class threshold 3, match tolerance 120 s, materiality 1.10, soundness band [0.8, 1.3], convergence minimum 0.90, forecasts); `TimeLateShardHeader` fields `prior_version`, `prior_kind`, `thinning`, `condition`, `split`; regenerate types (`scripts/gen_types.py`), update `tests/unit/test_types.py`

## Phase 2: Foundational (blocks every story)

- [x] T003 Run time per period and system on the runner: `scripts/research/tl2_runtime.py` and a `timelate/tl-c-smoke` CI run; record in `experiments/<date>-tl2-runtime/`; apply R10's sizing rule to `plan.md` if needed
- [x] T004 [P] `src/tma2/timelate/counts.py`: matched, missed, false, timing error at 60, 120, 240 s; manoeuvres cut by the period's edges excluded; tests
- [x] T005 [P] Scorer in `src/tma2/cli/tlscore.py` and `src/tma2/timelate/gate.py`: `--errors` writes `errors.npz` (per scored row and system: errors, bound, period ordinal, split keys); beside every ratio of medians the geometric mean paired ratio, share of periods each side better, share over twice as bad (FR-014); splits by ownship manoeuvres, leg position, range tercile, true count, with `bound_applies` per system (FR-015); tests
- [x] T006 Period records in `src/tma2/timelate/run.py` and `src/tma2/cli/tlsolve.py`: spans and kinds of every system that states manoeuvres; run time per system; `--systems` selection; defaults reproduce Gate T (T001 still passes)
- [x] T007 Corrected prior (FR-002, R2): `ManoeuvrePrior.version` 2 in `src/tma2/timelate/prior.py` (leg curvature once; uniform-direction volume; leg normal renormalised above its minimum); test that the leg density integrates to 1; system `search2`; `--prior-version`
- [x] T008 Effect of the correction on tuning seed 333 (150 Annex B periods): `search` beside `search2`, track error, counts, calibration; record `experiments/<date>-tl2-prior/`; from here `search2` is this spec's search

## Phase 3: User Story 1 - where the gain comes from (P1)

**Independent test**: one scoring run gives C″, `c2-refit`, `search-flat`, `search2` and the reference on the same periods with paired ratios and the refit's share of the gain.

- [x] T009 [P] [US1] `src/tma2/timelate/controls.py`: `c2_refit` (C″ transitions as spans, `choose_kinds`, one joint fit to the posterior with times free from C″'s states and the neutral starts, best evidence; no add, remove or re-kind); test that it never calls `evidence_search`
- [x] T010 [P] [US1] `src/tma2/timelate/flat.py`: uniform densities over the solver's box for turn, speed change, times and kinds; state prior and Occam volumes kept; system `search-flat`; test that the history prior is constant inside the box
- [x] T011 [US1] `src/tma2/timelate/study.py`: gain share = log gain (C″ → `c2-refit`) ÷ log gain (C″ → `search2`) per period pooled with a period bootstrap, overall and by whether `search2`'s first candidate is right (FR-005); tests on synthetic errors
- [x] T012 [US1] Tuning seed 333: the five systems on 150 Annex B and 60 shifted periods; record `experiments/<date>-tl2-controls/`

## Phase 4: User Story 2 - how often the bearings cannot decide (P1)

**Independent test**: class shares with intervals and both headroom figures from one scoring run.

- [x] T013 [US2] `src/tma2/timelate/classify.py`: fit the true history's structure to the posterior from the neutral starts and from `search2`'s best track (never the true states); convergence flag; Δ against the first candidate; classes at thresholds 1, 3, 5 and tolerances 60, 120, 240 s; `--classify` in `tlsolve`; test antisymmetry and that no true state is read
- [x] T014 [US2] Composites `ident-search`, `ident-all` and the headroom statistic (geometric mean paired ratio, period bootstrap; ratio of medians beside; material / not material / inconclusive at 1.10) in `src/tma2/timelate/study.py`; truth-in-first-three by class (FR-008); tests
- [x] T015 [US2] Tuning seed 333: class shares, headroom, and a check that the statistic is not degenerate; record in `experiments/<date>-tl2-controls/`; if degenerate, change the statistic in `research.md` R4 before registration and say so

## Phase 5: User Story 3 - a target that never manoeuvres (P1)

**Independent test**: false-manoeuvre rate and track error of `search2`, C″ and one leg on a held-course split.

- [x] T016 [US3] `configs/timelate/tl-quiet-ranges.json` (Gate T's ranges, no target manoeuvres); generate locally first; `timelate.yml` accepts a ranges file per split
- [x] T017 [US3] False-manoeuvre rate with a Wilson interval and track error against one leg in `src/tma2/timelate/study.py`; undetermined periods scored for false manoeuvres only (FR-010); tests
- [x] T018 [US3] Tuning seed 333, 100 held-course periods; record `experiments/<date>-tl2-quiet/`

## Phase 6: User Story 4 - thinning (P2)

**Independent test**: track error and run time of each form against the full data on the same periods, and the rule's outcome.

- [x] T019 [US4] `src/tma2/timelate/thin.py`: `drop:N`, `fixed:N`, `adaptive:TOL[:robust]` on the arc problem's bearings (variance σ²/n; scoring rows unchanged); `--thin`; test that N = 1 equals the full data
- [x] T020 [US4] `scripts/research/tl2_thin.py` on 100 tuning periods, clean and with outliers, N in 2, 4, 6, 12; apply R6's adoption rule; record `experiments/<date>-tl2-thin/`; set the registered runs' `thinning` accordingly

## Phase 7: User Story 5 - beyond Gate T's conditions (P2)

- [x] T021 [P] [US5] `src/tma2/timelate/smooth.py`: Rauch–Tung–Striebel smoother over the frozen EKF, system `ekf-rts`; test that it equals the filter at the last row
- [x] T022 [US5] Mismatch conditions in the time-late runs: check the overlay's correlation time units at 5 seconds; `condition` in run files and `timelate.yml`; whole engagements as split `whole`; local generation of each first
- [x] T023 [US5] CI smoke `timelate/tl-c-smoke` with every split and condition (3 periods each); emulate the workflow's command builder through bash against the run file before pushing

## Phase 8: Registration and the fresh seeds

- [x] T024 Plan `configs/timelate/tl-c.json`, run files `configs/timelate/runs/tl-c-{val,test}.json`, decision record `experiments/<date>-tl2-decision/` (digests, criteria, forecasts for FR-005, FR-007, FR-010, the recommendation rule, the soundness stop); SRD §9 line (owner merges)
- [x] T025 Validation seed 334 (`timelate/tl-c-val`); soundness stop; record `experiments/<date>-tl2-val/`; failure check 20 minutes after launch
- [x] T026 Test seed 335 once (`timelate/tl-c-test`); record `experiments/<date>-tl2/` with `errors.npz`, the list of anything not run (FR-022), and the recommendation by the registered rule
- [x] T027 Panel review (five reviewers; critical); `review.md`; corrections

## Phase 9: User Story 6 - prior robustness (P3; first to be cut)

- [ ] T028 [US6] Mismatch diagnostic (detection on shifted periods at a false-alarm rate fixed on Annex B tuning periods) and a broadened prior (`--prior broad`) in `src/tma2/timelate/prior.py`; scored on both splits; reported only

## Phase 10: Polish

- [x] T029 Write-up `site/blog/<date>-time-late-classical.md`, slides post and deck (`/speckit-report-slides`), figures by a script reading committed records
- [x] T030 `AGENTS.md` (status, gotchas), kickoff post updates, PR description

## Dependencies

T001–T002 → T003–T008 → US1 (T009–T012) → US2 (T013–T015, needs `search2` and the scorer). US3 (T016–T018) and US4 (T019–T020) depend on Phase 2 only and can run beside US1. US5 depends on Phase 2. T024 needs T008, T012, T015, T018, T020, T023. US6 is independent of registration.

Parallel: T004, T005; T009, T010; T021 with anything.

## Strategy

MVP: phases 1 to 4 on the tuning seed answer the owner's main question in draft (where the gain comes from; how much is attainable). Each later phase adds a reading without changing those. One long CI run at a time.

## Notes (2026-11-12)

- T001: the fixture is the synthetic case of `test_timelate.py`, not two seed-329 periods (C″ on real periods costs minutes a test); tolerance 1e-4 for another CPU family.
- T003, T008, T012, T015, T018: one tuning run, `experiments/20261112-tl2-tuning/`. Run time is no constraint (R10 not invoked). The headroom statistic is not degenerate.
- T023: no separate smoke run; the tuning run exercised the workflow, and the thinning runs exercise `thinning`, `systems` and `condition`.
- T028 (User Story 6): not built (cut, as the spec allowed); only the mixed prior, a narrower thing. Recorded in the test README.
- Panel round 1 (2026-11-13): two defects in the registered code (duration volume; edge manoeuvres in classing) recorded, not repaired: a repair is a new registration.
