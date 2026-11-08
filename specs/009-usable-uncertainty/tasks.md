# Tasks: Usable uncertainty for the carried estimator (Gate 4)

**Input**: `specs/009-usable-uncertainty/` (spec, plan, research, data-model, contracts, quickstart)

**Tests**: requested by the spec (each user story's independent test; the constitution's gate rules).

## Phase 1: Setup

- [x] T001 Add the statement fields to `PredictionRow` and the configs `StatementHeadConfig`,
  `StatementTemperatureConfig`, `Gate4Criteria`, `Gate4Decision` in `schema/tma.yaml` (schema
  0.30.0; all row fields optional); regenerate types (`scripts/gen_types.py`); bump
  `tests/unit/test_types.py`.
- [x] T002 [P] Add `scripts/research/g4_tuning.py` reproducing research R1–R3 on tuning ordinals
  0–499 of a validation feature cache (no SciPy).

## Phase 2: Foundational

- [x] T003 Add `src/tma2/calib/statement.py`: the course mixture (von Mises κ = 1/(a·sd)², weight p,
  uniform remainder), the arc X = min(Xmax, 1.96·a·sd), its probability P, the circular log score,
  the interval half-widths q = c·sd and the interval score, and a monotone isotonic map (pool
  adjacent violators) for P. Unit tests in `tests/unit/test_statement.py`: P equals the numerical
  integral of the mixture over ±X; p = 0 gives P = X/π; the interval-score loss is minimised at the
  95% quantile; the isotonic map is monotone and identity on calibrated data.
- [x] T004 Extend `src/tma2/calib/data.py` with the exact errors per row (wrapped course, log range
  ratio, speed) and the raw sds; no linearised error in this path.
- [x] T005 Extend `src/tma2/eval/calibration.py`: per-row statement columns and the measures:
  reliability (hit − P overall, and in five bins of P), mean P, mean X, the course log score and its
  difference from the uniform's, range and speed coverage95 and interval scores. Tests in
  `tests/unit/test_calibration_metrics.py`.

## Phase 3: User Story 1 & 2 - The statement (P1)

**Goal**: every scored row states course (X, P) and range and speed 95% intervals; points unchanged.

**Independent test**: on synthetic rows with known errors the statement is reliable; on 4 validation
scenarios the fields are present and the points equal Gate 2's.

- [x] T006 [US1] Temperature form: `statement-temperature` in `src/tma2/cli/g3train.py` fits (a, p,
  c_range, c_speed) per slice (G5 minute × open) by the summed proper loss on tuning ordinals, then
  the isotonic map for P; writes `temperature.json`.
- [x] T007 [US1] `tma2-g3predict` writes the statement fields (`calib/predict.py`); the header records
  its own commit and dirty flag, read before writing (FR-040).
- [x] T008 [US2] The scorer (`cli/gs.py`) computes the statement measures for every estimator with
  statement fields, and for the raw E from its Gaussian sds (arc capped at Xmax).
- [x] T009 [US1] Baseline record `experiments/<date>-g4-base-val/`: E raw and references on scoring
  ordinals 500–1499 (`--reuse` the Gate 3 baseline's `errors.npz`); no calibrated estimator scored.

## Phase 4: User Story 4 - The gate (P2)

- [x] T010 [US4] SRD amendment: §5 Gate 4 row (R7 defaults), §9 record, and the Gate 3 row's form
  corrected (FR-043). The owner merges.
- [x] T011 [US4] `src/tma2/calib/gate.py` Gate 4 criteria and `src/tma2/cli/g4.py` (records name the
  producing commit and CPU, FR-042); tests in `tests/unit/test_gate4.py`.
- [x] T012 [US4] Plan `configs/gate4/g4-a.json` and decision record `experiments/<date>-g4-decision/`
  (binds the plan, the settings and their tuning evidence, the forecast) before any training.

## Phase 5: User Story 3 - Learning against a rule (P2)

- [x] T013 [US3] The statement head (`calib/statement_fit.py`): outputs
  (a, logit p, c_range, c_speed), zero-initialised to the temperature's global values; loss the
  standardised sum of the course log score and the two interval scores; early stopping on tuning
  ordinals; shuffled control writes distinct model ids for best and last (FR-041). Tests in
  `tests/unit/test_calib.py`.
- [ ] T014 [US3] (CI) `g3train/g4-a`: three seeds, shuffled, temperature.
- [ ] T015 [US3] Calibrated validation files (`tma2-g3predict`), validation scoring (`score/g4-a-val`,
  `--reuse`), `tma2-g4 --split validation`, carried rule, `carried.json` or the validation stop.

## Phase 6: Test and panel (P2)

- [ ] T016 [US4] (only if validation passes) seed 320 and the test scoring; `tma2-g4 --split test`.
- [ ] T017 [US4] Panel: five specialities, in rounds; `review.md`.

## Phase 7: Polish

- [ ] T018 [P] Slides post (reliability diagram, coverage charts, track plots with course arcs) and
  the gate write-up.
- [ ] T019 [P] AGENTS.md: spec 009 status, seeds, gotchas; site glossary (circular log score,
  reliability).
- [ ] T020 Run `quickstart.md` end to end.

## Dependencies

- T001 → T003–T005 → US1/US2 (T006–T009) → T010–T012 → T013–T015 → T016–T017 → T018–T020.
- T002 in parallel with T001. T010 can open as soon as the baseline (T009) exists.

## Implementation strategy

MVP is US1 + US2: a classical statement (the temperature form) that is reliable and informative is
already usable by an operator, whatever the learning claim.
