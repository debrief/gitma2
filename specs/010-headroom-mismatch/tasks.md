# Tasks: Headroom under bearing-error mismatch (Gate H)

**Input**: `specs/010-headroom-mismatch/` (spec, plan, research, data-model, contracts, quickstart)

**Tests**: requested by the spec (each user story's independent test; the constitution's gate rules).

**Order of PRs**: PR 24 carries the spec, plan and these tasks and amends the SRD (owner merges).
Implementation follows in its own PR, with the slides post.

## Phase 1: Setup

- [x] T001 Add `MismatchCondition`, `MismatchTruth`, `GateHPlan`, `GateHCriteria`, `GateHDecision`
  and `HeadroomRecord` to `schema/tma.yaml` (schema 0.31.0); regenerate types
  (`scripts/gen_types.py`); bump `tests/unit/test_types.py`; regenerate the data dictionary.
- [x] T002 [P] Add `configs/gateh/conditions.json`: the 16 conditions of research R2 (owner
  accepted the grid, 2026-11-09), `all-central` primary.

## Phase 2: Data (US1)

- [x] T003 `src/tma2/sim/mismatch.py` (numba): the overlay of research R1 from its own stream
  (label `mismatch`), fixed draw order, draws for every sample whether dropped or not; returns the
  bearing and the truth arrays. The kernel must expose b and the white draw without changing its
  own draws.
- [x] T004 `src/tma2/sim/generate.py`, `cli/generate.py`: generator 0.7.0, `--mismatch FILE#id`,
  the side file `<split>.mismatch.npz` with the split's digest; `off` takes the 0.6.0 path and
  writes no side file. `GenerateOptions.generator_version` stays explicit for older fixtures.
- [x] T005 [P] `tests/unit/test_mismatch.py`: data bytes equal 0.6.0's for three seeds
  (SC-001); existing golden and conformance tests unchanged.
- [x] T006 [P] `tests/unit/test_mismatch.py`: per kind on 200 scenarios, lag
  autocorrelation, bias sd, σ range and outlier rate within sampling error; tracks, manoeuvres
  and dropouts equal the `off` split's (FR-003); determinism.
- [x] T007 [P] `tests/unit/test_mismatch.py`, `tests/unit/test_headroom.py`: no estimator entry point other than
  `tma2-hpredict ceiling` opens the side file; pack header σ is the nominal value (FR-005).
- [x] T008 Generate seed 320 (500 scenarios × 16 conditions) on CI; digests recorded per condition in
  `experiments/20261109-gh-tuning/<condition>/data-digests.json`.

## Phase 3: Ceilings and bound (US2)

- [x] T009 `src/tma2/headroom/cov.py`: Σ from the parameters on valid sample times, Cholesky
  whitening, prefix-causal (FR-014). Tests: against a dense reference; gaps; Σ = σ² I when off.
- [x] T010 `src/tma2/headroom/gls.py`: the whitened piecewise-CV solve through the physics
  layer's residuals and Jacobian (double); with no whitening the existing oracle path, untouched.
- [x] T011 `src/tma2/headroom/ceilings.py` and `tma2-hpredict ceiling`: realisation (exact) and
  attainable (mixture responsibilities, iteratively reweighted). `tests/unit/test_headroom.py`:
  both equal the existing oracle row for row with mismatch off (FR-013).
- [x] T012 `src/tma2/headroom/crb.py`: Jᵀ Σ⁻¹ J with known manoeuvres (research R4); test that it
  equals `known_manoeuvres` when off.
- [x] T013 Efficiency of both ceilings against the bound on seed 320, every condition; investigate
  any settled-slice value far from 1 before going on (US2 scenario 2). Record in
  `experiments/<date>-gh-tuning/`.

## Phase 4: Robust control and references (US3)

- [x] T014 `src/tma2/headroom/robust.py` and `tma2-hpredict robust`: Huber weights, σ̂ from the
  median absolute residual, ρ̂ whitening with the fallback rule; `--only` ablations;
  `--segmentation truth|FILE`. Tests: on clean data with wide Huber constant and no whitening it
  equals C″'s solve; finite outputs on short legs.
- [x] T015 Choose the control's settings on seed 320, primary condition, from the grid of research
  R5 (27 points), on CI; record the table and the choice.
- [x] T016 Re-tune the IMM and EKF on seed 320, primary condition (`tune/**`, the grids of
  `experiments/20261104-man2-refs/`); freeze by name.
- [x] T017 `src/tma2/headroom/gate.py`, `cli/gh.py` (`tma2-gh`): `tma2-gs` scoring with
  `--predictions`, the statistic R with its paired clustered interval, the segmentation part, the
  operational table (research R8), `headroom.json`; refusals of contracts/cli.md. Tests on fixture
  scenarios, including R's interval containing zero with mismatch off (US3 scenario 4).
- [x] T018 `.github/workflows/headroom.yml` (`headroom/**`; generation, predictions and scoring
  per condition and variant); plans under `configs/headroom/`.

## Phase 5: Gate H registered (US4)

- [x] T019 SRD §5 row for Gate H (criteria of research R7, with the true-segmentation denominator
  flagged for the owner) and a dated §9 line, in a PR the owner merges. No result on 321 or 322
  may exist.
- [x] T020 `configs/gateh/gh-a.json` and the decision record `experiments/<date>-gh-decision/`:
  conditions and digest, settings from T015, references from T016, the H-a band from T013, seeds,
  forecasts for R per condition, the validation rule. Committed before T021.

## Phase 6: Validation and test

- [x] T020a Shard `headroom.yml` (predictions per ordinal range, one scoring job) before the
  test run: about 5,200 scenarios exceed one job's time limit.
- [x] T021 Generate seed 321 (1,000 × 16) and score on CI, one run at a time; apply H-a and H-b
  only; record `experiments/<date>-gh-val/`. Stop only if a soundness check fails.
- [ ] T022 Generate seed 322 after the validation record (5,000 primary; 1,000 each for `off` and
  the four single kinds at central); score once from a worktree at the commit.
- [ ] T023 Panel review (five reviewers, rounds until decided); record `experiments/<date>-gh/`
  with `review.md`. Inconclusive: one re-score on seed 323, larger, then final.

## Phase 7: Reporting

- [ ] T024 `scripts/research/gh_charts.py`: bearings under each kind on one engagement; the
  headroom chart per condition; efficiency per slice. Track plots with `tma2-plot` (C″, robust
  control, attainable ceiling at zig + 10 and + 20 min). SVG with sidecars under
  `site/static/img/<date-slug>/`.
- [ ] T025 Write-up `site/blog/<date>-gate-h.md` (critical; states what was not tested: target
  motion mismatch, a classical bias state, other severities) and the slides post
  (`/speckit-report-slides`) before the PR.
- [ ] T026 `AGENTS.md` status, seeds and gotchas; glossary entries (headroom, attainable ceiling,
  whitening); quickstart corrected to the commands run.
- [ ] T027 Follow-on recorded per the verdict (FR-044), and the scaled regressor control named as
  the next spec with what the owner must set up (Modal account, spending limit, two repository
  secrets).

## Dependencies

- T001–T002 before all. T003–T004 before T005–T008. T008 before T013, T015, T016.
- T009–T012 before T013. T014 before T015. T017 needs T011, T012, T014.
- T019–T020 before T021; T021 before T022; T022 before T023; T023 before T025.
- [P] tasks touch different files and can run together.
