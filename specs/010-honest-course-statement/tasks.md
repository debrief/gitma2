# Tasks: An honest course statement (Gate 5)

**Input**: `specs/010-honest-course-statement/` (spec, plan, research, data-model, contracts, quickstart)

**Tests**: requested by the spec (each story's independent test; SC-003's synthetic check).

## Phase 1: Setup

- [ ] T001 Schema 0.31.0 in `schema/tma.yaml`. All new fields are optional.
  - New `PredictionRow` fields: `course_kappa`, `course_form`, `unsettled_score`, `unsettled_flag`.
  - New configs: `StatementConfig5` (with `shuffle: none|errors|encoder`), `ClassicalRuleConfig`,
    `TemperatureConfig5`, `ProxyDefinition`.
  - New gate classes: `Gate5Criteria`, `Gate5Decision`.
  - Regenerate the types and bump `tests/unit/test_types.py`.
- [ ] T002 [P] Add `scripts/research/g5_tuning.py`, reproducing research R1–R4 on tuning ordinals
  0–499: the proxy AUCs, the held-out logistic, exact against normal mass, the Platt slopes and the
  share of course errors beyond 150°.

## Phase 2: Foundational

- [ ] T003 Extend `src/tma2/calib/statement.py` with the truncated form.
  - The exact von Mises mass on ±X (numerical, `np.i0e`).
  - The truncated density and its log score, in NumPy and torch.
  - The Platt map.
  - Tests in `tests/unit/test_statement5.py`: the density integrates to 1; the arc mass equals P to
    1e-9; the log score is proper (its expectation is maximised at the true P); the torch and NumPy
    versions agree.
- [ ] T004 Add `src/tma2/calib/proxy.py` and `src/tma2/cli/g5proxy.py`: the R1 features per row
  (residual bias 6/12/30, χ² 60, C open, minutes since C's last closed transition) and the proxy
  cache with digests.
  - Tests in `tests/unit/test_proxy.py`: changing bearings after row k leaves the features at k
    unchanged; synthetic CV data gives bias ≈ 0; refusal on a missing segmentation.
- [ ] T005 Extend `src/tma2/eval/calibration.py`.
  - Columns for κ, the form, and the proxy score and flag.
  - The truncated log score, by form.
  - Per-slice reliability, the calibration slope and the AUC of P.
  - Tests in `tests/unit/test_calibration_metrics.py`.
- [ ] T006 Add `src/tma2/calib/gate5.py`: the G5 criteria (R7).
  - Tests in `tests/unit/test_gate5.py`, including SC-003's synthetic check: a calibrated statement
    passes G5-b in ≥ 90% of 200 resampled datasets; one miscalibrated by 0.15 on a slice fails it in
    ≥ 90%.
  - If the proposed bands fail this check, revise them here, before the amendment.

## Phase 3: User Stories 1 and 2 - one consistent probability that drops after a suspected manoeuvre (P1)

- [ ] T007 [US1] Add `tma2-g3train proxy5` (fits the proxy definition on tuning rows; R1) and
  `temperature5` (the truncated temperature per cell with the β grid and the Platt map; R6.1;
  `--errors-of` for the references).
- [ ] T008 [US2] Add `tma2-g3train classical5` (the classical rule on the stream; R6.2) and
  `statement5`.
  - `statement5` trains the head in the truncated form, with the P features plus the encoder
    state, on the exact errors.
  - Each model can take `shuffle: encoder`, which permutes only the encoder state each epoch (R6.3).
  - In `src/tma2/calib/statement_fit.py`.
- [ ] T009 [US1] Extend `tma2-g4predict` for the truncated form: the classical rule, the
  temperature and the head, with the proxy fields. The header records the digests and provenance.
- [ ] T010 [US3] Extend the scorer (`cli/gs.py`) to read the new columns and report the per-slice
  table, the slope, the AUC, and the proxy-state and truth-settled splits.

## Phase 4: User Story 3 - the gate (P1)

- [ ] T011 [US3] Run the proxy caches: validation 0–1499 in the session; the stream (seed 318) on CI
  with a `g5proxy.yml` workflow.
- [ ] T012 [US3] Baseline record `experiments/<date>-g5-base-val/`.
  - Scored on ordinals 500–1499 with `--reuse` of the Gate 4 validation scoring.
  - It contains: raw E; Gate 4's st-s3 and temperature, expressed in their own form; and the
    references raw.
  - No spec 010 statement is scored.
- [ ] T013 [US3] Write the SRD amendment: the §5 Gate 5 row (R7, after T006's check) and a §9
  record. The owner merges.
- [ ] T014 [US3] Write the plan `configs/gate5/g5-a.json` and the decision record
  `experiments/<date>-g5-decision/`.
  - The decision record binds the plan, the proxy definition, the controls and the forecast.
  - It discloses the R1–R3 fits.

## Phase 5: User Stories 4 and 5 - learning and fair references (P2)

- [ ] T015 [US4] CI training with `g5train/g5-a`.
  - Three head seeds, the encoder-only shuffle, the classical rule and the temperature.
  - The reference temperatures for the oracle and the IMM.
- [ ] T016 [US4] Validation.
  - Write the stated files and the reference files, and push them to a results branch.
  - Run `score/g5-a-val`.
  - Run `tma2-g5 --split validation`; the validation record is `experiments/<date>-g5-val/`.
  - Write `carried.json`, or record the stop.

## Phase 6: Test and panel (P2)

- [ ] T017 (only if the validation rule is met) Seed 320 on CI: data, E features, C segmentation,
  the proxy, the scoring, then `tma2-g5 --split test`.
- [ ] T018 Panel: five specialities, in rounds; `review.md`.

## Phase 7: Polish

- [ ] T019 [P] The write-up and the slides post (reliability diagram, P and hit rate by proxy and
  truth slice, plain-language widths).
- [ ] T020 [P] Update AGENTS.md (status, seeds, gotchas) and the glossary (calibration slope,
  truncated statement).
- [ ] T021 Run `quickstart.md` end to end.

## Dependencies

T001 → T003–T006 → T007–T010 → T011–T014 → T015–T016 → T017–T018 → T019–T021. T002 runs in
parallel with T001. T006's synthetic check gates T013.
