# Tasks: Uncertainty calibration of the Gate 2 estimator (Gate 3)

**Input**: design documents in `specs/008-uncertainty-calibration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

Tests are part of this spec: SC-001 to SC-003 and every follow-on in US5 need one. (CI) marks a
task that runs on GitHub Actions.

## Phase 1: Setup

- [ ] T001 Bump the schema to 0.26.0 in `schema/tma.yaml`. Add optional `PredictionRow` fields:
  `cov_xyvv` (float, multivalued, 10: "upper triangle, row-major, of the 4 × 4 covariance of (x,
  y, vx, vy)"), `course_sd_rad`, `speed_sd_mps`, `cov_ok` (boolean), `cov_scale_log`. Widen
  `log_range_sd`'s description to physics-layer and tracker rows. Add `EPredictionHeader`'s
  `model_settings`, `segmentation_sha256` and `calibration`. Add `CalibrationHeadConfig`,
  `TemperatureConfig`, `Gate3Decision`, `Gate3Record` and `CalibrationRecord`. Then run
  `uv run python scripts/gen_types.py` and `scripts/data_dictionary.py`.
- [ ] T002 [P] Create the package skeleton `src/tma2/calib/__init__.py`, with docstrings citing
  spec 008.

## Phase 2: Foundational

- [ ] T003 Write `src/tma2/physics/uncertainty.py`:
  - `pack_cov(P)` and `unpack_cov(v)`: the 10-entry upper triangle, row-major;
  - `derived_sds(state, P, own_xy)`: log-range, course and speed standard deviations by
    first-order propagation (research R2);
  - `cov_usable(P, state, own_xy)`: finite, positive definite, range > 1 m.
- [ ] T004 [P] Write `tests/unit/test_uncertainty.py`:
  - the propagated standard deviations match finite differences of sampled Gaussians, within 2%
    at small covariance;
  - pack and unpack round-trip;
  - non-positive-definite input gives `cov_usable` False.
- [ ] T005 Write `src/tma2/eval/calibration.py` (research R4):
  - per-row errors over standard deviations for log range, wrapped course and speed;
  - NEES;
  - the 95% interval score per quantity (log range, degrees, knots), with a missing estimate
    charged the estimator's own 99th-percentile finite score;
  - coverage at z = 1 and 1.96, where a missing or `cov_ok`-false row is not covered;
  - sharpness;
  - slice masks (G5 time, open-at-k, range band, detectability, settled, gross);
  - clustered bootstrap intervals with the scorer's resamples (`eval/bootstrap.py`).
- [ ] T006 [P] Write `tests/unit/test_calibration_metrics.py`. On synthetic Gaussians with known
  covariance, coverage at 68% and 95% must be within binomial error, the median NEES ratio near
  1, and the interval score equal to a hand computation. A missing row must count as not covered.

## Phase 3: User Story 1 — every estimate states its uncertainty (P1)

**Goal**: every physics-layer and tracker row carries its covariance; point fields unchanged.
**Independent test**: Gate 2's validation files re-made with covariances score identical point
errors.

- [ ] T007 [US1] In `src/tma2/gate2/predict.py` `_row` and `e_rows`, write `cov_xyvv`, the three
  standard deviations and `cov_ok` from the layer's or E's `cov`, in double. Point fields stay
  as now.
- [ ] T008 [US1] In `src/tma2/cli/g2predict.py`, have the header carry `model_settings` (the plan
  entry) and `segmentation_sha256` (FR-003). Update `tests/unit/test_gate2_predict.py`: covariance
  fields present on plausible rows; points equal the pre-change values on a fixture scenario.
- [ ] T009 [US1] In `src/tma2/segment/score.py` `layer_errors` and `tracker_errors`, return
  per-row calibration arrays: errors, standard deviations, NEES, `cov_ok`, plausible. In
  `src/tma2/cli/gs.py`, store them in `errors.npz` as `cal_<name>` [N, 9], with the existing
  arrays unchanged.
- [ ] T010 [P] [US1] In `src/tma2/references/imm.py` and `ekf.py`, add optional covariance
  out-arrays (the mixed 4 × 4 block for the IMM), as `nis_out`. f32 rows MUST be byte-identical:
  extend `tests/conformance/test_references.py` to assert it.
- [ ] T011 [US1] In `src/tma2/gate2/predict.py` `prediction_errors`, read E files' covariance into
  the same calibration arrays.
- [ ] T012 [US1] (CI) Re-make the Gate 2 validation prediction files with covariances:
  `configs/g2predict/g3-base-val.json` (models e-s3, ew-s3; the veto and fade plans' C″). Check
  that the point errors equal `results/score-g2-a-val-42392768062` and
  `results/score-g2-veto-val-42434645201` row for row, using a script in `scripts/research/`.

## Phase 4: User Story 2 — know how well calibrated they are (P1)

**Goal**: the validation calibration baseline for C, E, E-w, C″, the IMM, the EKF and the oracle.
**Independent test**: the record reproduces from its plan; figures recompute from per-row arrays.

- [ ] T013 [US2] Write `src/tma2/cli/g3.py` (`tma2-g3`, registered in `pyproject.toml`). It runs
  `tma2-g2`'s scoring with E files, then the calibration records per estimator and slice
  (`calibration.json`, `report.md`). Flags `--reuse` (T029) and gate mode (T027) are stubs
  until their tasks.
- [ ] T014 [US2] In `.github/workflows/score.yml`, add kind `g3` (as `g2`: `c`, `e`, `knots`,
  `gate`).
- [ ] T015 [US2] (CI) Run the baseline: `configs/score/g3-base-val.json` on seed 314 scoring
  ordinals 500–1499. Record `experiments/<date>-g3-base-val/` (README with the coverage, NEES,
  interval score and sharpness tables, overall and per slice).

## Phase 5: Gate 3 amendment and decision (before any calibration training)

- [ ] T016 Open the SRD amendment PR adding the Gate 3 row (docs/SRD.md §5) with the proposed
  bands from spec FR-030, informed by T015. The owner merges it. If two working days pass
  without objection, the agent merges and says so in the next write-up (AGENTS.md).
- [ ] T017 Write the head plan `configs/gate3/g3-a.json`:
  - head config and temperature slices;
  - models `cal-s1..s3` and `cal-shuffled`;
  - the feature caches by branch;
  - the carried E (e-s3, `a5485318…`);
  - the score of record.
- [ ] T018 Commit the decision record `experiments/<date>-g3-decision/decision.json` (Gate3Decision)
  and README, binding the plan digest, criteria, rules, seed 320 and the forecast, after the
  amendment is merged.

## Phase 6: User Story 3 — a learned calibration and a classical one (P2)

**Goal**: three head seeds, a shuffled control, a temperature control; the state is never changed.
**Independent test**: untrained = raw; points identical; validation scores improve over raw.

- [ ] T019 [P] [US3] Write `src/tma2/calib/head.py`: a 2-layer tanh MLP on [h_k, log sd_raw,
  code_k] → s = bound · tanh(·), with its last layer zero-initialised.
- [ ] T020 [P] [US3] Write `src/tma2/calib/loss.py`: β-NLL on the 4-state Gaussian with a
  stop-gradient weight e^{2sβ}, a cap (100), and `cov_ok`-false rows excluded and counted.
- [ ] T021 [US3] Write `src/tma2/gate2/predict.py` `--features` (via `cli/g2predict.py`): the
  cache arrays per data-model, with a header binding the plan, E weights, dataset and commit.
  Add a `.github/workflows/g2features.yml` branch family.
- [ ] T022 [US3] Write `src/tma2/calib/train.py` and `src/tma2/cli/g3train.py head`: seeded,
  resumable (as `gate2/train.py`), early stopping on tuning ordinals 0–499, saving `best` and
  `last` (FR-060). Add the workflow `.github/workflows/g3train.yml`.
- [ ] T023 [P] [US3] Write `src/tma2/calib/temperature.py` and `g3train temperature`: one
  log-scale per declared slice, fitted by the same loss on tuning ordinals.
- [ ] T024 [US3] Write `src/tma2/calib/predict.py` and `tma2-g3predict`: copy the rows, scale the
  covariance by e^{2s}, set `cov_scale_log`, and refuse mismatched rows.
- [ ] T025 [P] [US3] Write `tests/unit/test_calib_head.py`, `tests/unit/test_calib_identity.py`
  and `tests/unit/test_calib_train.py`:
  - zero head gives the raw covariance;
  - calibrated files' point fields are byte-identical to E's;
  - finite gradients;
  - resume determinism in a fresh interpreter;
  - the shuffled control saves its last epoch.
- [ ] T026 [US3] (CI) Run the feature caches (stream 318, validation 0–1499), the training
  (cal-s1..3, cal-shuffled), the temperature, `g3predict` on validation, and the validation
  scoring in gate mode. Apply the carried-seed, shuffled and validation rules. Record
  `experiments/<date>-g3-val/` and `carried.json` beside the decision (the shuffled outcome is
  read from `validation.json`, by digest).

## Phase 7: User Story 4 — the gate on a fresh seed (P2)

- [ ] T027 [US4] Implement `tma2-g3` gate mode in `src/tma2/calib/gate.py`:
  - G3-a…G3-d per the decision;
  - `verdict.json`, `manifest.json`;
  - refuse `start ≠ 0` or `count ≠ sigma1_scenarios` on test (FR-032);
  - read the shuffled rule from the validation record (FR-063).

  Add `tests/unit/test_gate3.py`.
- [ ] T028 [US4] (CI) Generate seed 320 after `carried.json` (`seed320-digests.json`,
  `test-digest.json`). Then run C's segmentation, the E predictions with features, `g3predict`
  (carried head and temperature) and the gate scoring. Record `experiments/<date>-g3/`.
- [ ] T029 [US4] Panel: five specialities, in rounds, `review.md`, `decided_by`.

## Phase 8: User Story 5 — the Gate 2 panel's follow-ons (P3)

- [ ] T030 [P] [US5] `--reuse <errors.npz>` in `src/tma2/cli/gs.py`: load the re-solved
  estimators when (ordinal, k) match exactly, and refuse otherwise (FR-062). Add
  `tests/unit/test_score_reuse.py`.
- [ ] T031 [P] [US5] Make the merge steps in `.github/workflows/g2predict.yml` and `segment.yml`
  assert every ordinal in [a, b) appears once (FR-061).
- [ ] T032 [P] [US5] Add a time-late E-w (research R9, as amended): `causal: false` in a plan; the encoder
  reads every row, the solve stays C's at k. Train one seed on CI (`g2train/<plan>`), score it on validation beside ew-s3,
  and record it in `experiments/<date>-g3-timelate/`.
- [x] T033 [P] [US5] Add `tests/unit/test_followons.py`: the coverage assertion, merge-count
  failure, shuffled-rule source and header settings.

## Phase 9: Polish

- [ ] T034 [P] Export: E-w's graph gains the head's calibrated covariance output
  (`src/tma2/gate2/export.py`), with three-runtime conformance in `ci.yml`.
- [ ] T035 [P] Site: an algorithm note `site/docs/algorithms/calibration.md`, glossary entries
  (NEES, coverage, interval score, sharpness) and the write-up `site/blog/<date>-gate-3.md`.
- [ ] T036 [P] Update `AGENTS.md`: spec 008 status, seeds (320 used; next 321), gotchas.
- [ ] T037 Run `quickstart.md` end to end.

## Dependencies

- T001 → T003, T005, T007–T011.
- **US1** (T007–T012) → **US2** (T013–T015) → **Phase 5** (T016–T018) → **US3** training (T026).
- US3's code (T019–T025) can proceed in parallel with US2 and Phase 5. **No training before
  T018.**
- T030 (`--reuse`) and T031 come before T028.
- **US4** after US3; T032 in parallel with US3 and US4.

## Parallel opportunities

- T004, T006, T010.
- T019, T020, T023 and T025.
- T030–T033.
- T034–T036.

## Implementation strategy

1. **MVP:** US1 and US2. Covariances everywhere and a measured baseline are useful on their own,
   since they say how far E's stated uncertainty can be trusted today.
2. **Then:** the amendment and decision, then US3.
3. **Then:** US4 with US5's follow-ons in place.
