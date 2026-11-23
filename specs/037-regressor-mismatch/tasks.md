# Tasks: the scaled regressor under bearing-error mismatch (spec 037)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md)

Stories: US1 the unchanged regressors (step 1), US2 fine-tune with an uncertainty (step 2), US3
the hybrid (step 3), US4 spending. Tests are written with the code they check.

## Phase 1: Setup

- [x] T001 (condition fields only; the interval fields reuse spec 009's row fields, so no others were needed) Add the schema fields of data-model.md to `schema/tma.yaml` (condition fields `white_t_df` "> 2" and `sigma_step_factor` "≥ 1"; regressor row interval fields; header `interval_scale`, `init_weights_sha256`; rmis plan and reading records), schema 0.41.0; run `scripts/gen_types.py` and `scripts/data_dictionary.py`
- [x] T002 [P] Register `tma2-rmread` in `pyproject.toml` and add `src/tma2/cli/rmread.py` (argument parsing only)

## Phase 2: Foundational

- [x] T003 [P] `src/tma2/regress/intervals.py`: 95% intervals from the variance head (range; speed and course arc by a fixed 256-point quadrature; "undetermined" over a half circle), with `tests/unit/test_intervals.py` (a known Gaussian's coverage by simulation; the arc of a zero-mean velocity is undetermined)
- [x] T004 `src/tma2/regress/predict.py` and `src/tma2/cli/rpredict.py`: rows carry the intervals; `--scale FILE`; header fields; spec 012's existing row fields unchanged (test: old fields equal with and without the change)
- [x] T005 `src/tma2/regress/mread.py`: per-scenario medians, paired log ratios, scenario bootstrap, shares, pooled seeds, all rows and common rows with counts, coverage with normalised-error median, slices (research R6), with `tests/unit/test_mread.py` (a planted ratio is recovered; a true ratio of 1 is "not separated"; constructed ties are excluded and counted)
- [x] T006 `src/tma2/cli/rmread.py`: reads `errors.npz` and the truth (and the mismatch truth file), writes `reading.json`; exit 0 always

## Phase 3: User Story 1 - the unchanged regressors under mismatch (P1)

**Goal**: step 1's record on spent seed 321 and the rule's output.
**Independent test**: `reading.json` holds sixteen conditions, every system, the rule's inputs and output.

- [x] T007 [US1] (built as a hook in the existing `headroom.yml` with `scripts/rmis_regressors.sh` and `scripts/rmis_read.sh`, plans under `configs/headroom/rm-*.json`, instead of a new workflow) `.github/workflows/rmis.yml` (`rmis/**`) and `scripts/rmis_job.sh`: per condition, generate the split with `--mismatch`, classical shards by `tma2-hpredict` (C″ plain and robust final solve; the robust solve on the true segmentation), regressors by `tma2-rpredict`, `tma2-gh`, `tma2-rmread`; `set -o pipefail`, folders made before `tee`, everything outside the checkout, results on an orphan branch `results/rmis-<name>-<run id>`; `max-parallel` 16; a test plan refused without its decision record or when its results branch exists
- [x] T008 [US1] `configs/rmis/smoke.json` (two conditions, 20 engagements) and `configs/rmis/dev-321.json` (sixteen conditions, 300 engagements, the three `r-a` checkpoints with digests); emulate the workflow's command builder through bash against both plans before any push
- [x] T009 [US1] Commit the rule of research R5 in `experiments/<date>-rmis-dev/RULE.md` before the run; push `rmis/smoke`, check it 20 minutes after launch, then `rmis/dev-321`
- [x] T010 [US1] `scripts/research/rmis_tables.py` (tables from `reading.json` only) and the record `experiments/<date>-rmis-dev/` (README, tables, reading, digests); state the rule's output; update the kickoff post with a dated paragraph
- [x] T011 [US1] **Checkpoint**: "holds up" → stop before step 2 and ask the owner; otherwise continue

## Phase 4: User Story 4 - spending (P1)

- [x] T012 [US4] `configs/regress/ft-pilot.json`, `ft-s1..s3.json`, `ft-toy.json` with limits that sum inside the guard (research R4); check each with `python -m tma2.regress.ledger --cap-usd 49`; record the ledger's total in the decision record and after the runs

## Phase 5: User Story 2 - fine-tune with an uncertainty (P1)

**Goal**: M1 to M5 on test seed 371, scored once.
**Independent test**: one scoring run gives every reading; the decision record predates the three runs.

- [x] T013 [US2] `src/tma2/sim/mismatch.py`: `white_t_df` and `sigma_step_factor` from a second stream; `tests/unit/test_mismatch_kinds.py`: mismatch off and each of the sixteen conditions reproduce committed digests byte for byte; the new kinds have the stated sd and tails; `configs/rmis/heldout-conditions.json`
- [x] T014 [US2] `src/tma2/features/batch.py`: `generate_indices(..., mismatch=)` applies a condition per scenario and equals `tma2-generate --mismatch` on the same indices (test)
- [x] T015 [P] [US2] `src/tma2/regress/mixture.py` and `configs/regress/ft-mix.json`: a condition per scenario index from its own stream (research R3); the held-out kinds can never be drawn (test); `tests/unit/test_regress_mixture.py`
- [x] T016 [US2] `src/tma2/regress/model.py`, `data.py`, `train.py`, `scripts/modal_train.py`: config fields `mix` and `init_from` (omitted from the JSON at defaults: spec 012's and 016's digests asserted unchanged); training starts from a checkpoint whose digest is checked; a toy fine-tune on CPU in a fresh interpreter
- [x] T017 [US2] Pilot on Modal (`gputrain/ft-pilot`): throughput, the validation curve; one change of configuration allowed; stop and ask if nothing moves in the first hour; record `experiments/<date>-ft-pilot/`
- [x] T018 [US2] Read on tuning data that the held-out conditions hurt C″ at all (seed 321, 100 engagements); if not, strengthen once before registration
- [x] T019 [US2] Decision record `experiments/<date>-rmis-decision/`: plans and code by digest, readings M1–M5 and Y1–Y2 with thresholds, controls, forecasts labelled by their basis, seeds 369, 370, 371, the ledger's total; never edited afterwards
- [ ] T020 [US2] (**launched and cut off**: Modal disabled the workspace at about $45; see `experiments/20261123-ft-runs/`; blocked on the owner) Launch `gputrain/ft-s1..s3` a minute apart; failure check 20 minutes after each; run records to `experiments/<date>-ft-runs/` with checkpoint digests
- [ ] T021 [US2] Validation `rmis/val-370` (off, `all-central`, `ho-both`, one more): the interval scales, the temperature control, the hybrid's weight; addendum binding them; forecasts not rewritten
- [ ] T022 [US2] Test `rmis/test-371`, once; record `experiments/<date>-rmis/` with weights' digests, readings, tables, what was promised and not run

## Phase 6: User Story 3 - the hybrid (P2)

- [x] T023 [US3] `src/tma2/regress/hybrid.py`: a subclass of the physics layer with the three prior residuals and the regressor's start (research R7); `physics/layer.py` untouched and C's `code_sha256` asserted unchanged; `tests/unit/test_hybrid.py` (weight → 0 equals C″'s solve; a tight prior returns the regressor's range; finite gradients)
- [x] T024 [US3] `tma2-hpredict --kind hybrid --prior-from --prior-weight`; the static range-prior comparator; fall-back rows flagged; wired into `rmis.yml` before T021

## Phase 7: Polish

- [ ] T025 Panel review of the test record (`review.md`); narrow the write-up to what the panel supports
- [ ] T026 Write-up `site/blog/<date>-regressor-mismatch.md`; slides post by `/speckit-report-slides` with `scripts/research/rmis_charts.py`; SRD §9 line proposed (owner merges)
- [ ] T027 `AGENTS.md`: status, seeds, gotchas; `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q`

## Dependencies

T001–T006 → US1 (T007–T011) → checkpoint → T012 → US2 (T013–T022); US3's code (T023, T024)
before T021. T003, T005, T015 can run in parallel with their neighbours. MVP: US1 alone is a
complete, reportable record.

## Notes during implementation

- The Cramér–Rao bound under a held-out condition: the truth side file's per-engagement columns do not
  describe the two new kinds, so efficiency there is against the nominal bound and named so (to do in T021).
- Fine-tune plans (draft until T019): pilot $0.57, three seeds $2.27 each by the ledger's rate; $47.95 in all against the $49 guard.
