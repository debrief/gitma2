---

description: "Task list for spec 001: types and generator (foundations, part 1)"
---

# Tasks: Types and Generator (foundations, part 1)

**Input**: Design documents from `/specs/001-types-generator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by the constitution (golden-file tests per package; the conformance test is
the P0 check), so test tasks are included and written before or with the code they cover.

**Organization**: by user story, after a shared setup and foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1 conformance, US2 types, US3 CLI, US4 batches, US5 repository and site

## Phase 1: Setup

- [x] T001 Create the `uv` project: `pyproject.toml` (package `tma2`, scripts entry
  `tma2-generate`, runtime deps numpy, numba, pydantic; dev group linkml 1.12, pytest, ruff,
  mypy), `.python-version` 3.12, `uv.lock`, `src/tma2/__init__.py`, `tests/__init__.py`,
  `.gitignore`, `README.md` pointer to the quickstart
- [x] T002 [P] Configure `ruff` (line length 100, isort), `mypy --strict` (`[tool.mypy]`, numba
  stub `typings/numba/__init__.pyi` with `njit`, `prange`, `uint32`, `uint64`, `int64`,
  `float64`, `boolean`), `pytest` (`testpaths`, `-ra`) in `pyproject.toml`
- [x] T003 [P] Copy `schema/tma.yaml` from gitma `d0aec60` unchanged; add `schema/README.md`
  (one paragraph: source of truth, how to regenerate)

## Phase 2: Foundational

- [x] T004 `scripts/gen_types.py`: run `gen-pydantic` and `gen-json-schema` into
  `src/tma2/types/generated/` (`tma.py`, `tma.schema.json`), post-process models to
  `extra="forbid"` and `model_config` for exclude-none dumps; `--check` mode regenerates to a
  temp dir and diffs (exit 1 naming stale files). Commit the generated output.
- [x] T005 `src/tma2/types/__init__.py`: re-export models, `SCHEMA_VERSION` read from the schema
  file at import of the generated module (constant written by `gen_types.py`), `parse_record`
  helper that raises `RecordError(file, where, reason)`
- [x] T006 [P] `src/tma2/data/canonical.py`: canonical JSON with JavaScript number formatting
  (research R4); `tests/unit/test_canonical.py` with the threshold cases and a property test over
  random float32 values comparing with a reference implementation of `Number::toString` rules
- [x] T007 [P] `src/tma2/sim/prng.py`: SplitMix64 (`splitmix64_at`, `derive_seed`,
  `parse_seed`), xoshiro128** (`create_rng`, `next_u32`, `uniform01`, `uniform`, `log_uniform`,
  `gaussian`, `uniform_int`) as numba `njit` functions over a `uint32[4]` state array;
  `tests/unit/test_prng.py` with known-answer vectors produced from gitma (first 8 `uniform01` of
  seeds 0, 1, 2^64−1 and the `createRng` words; vectors generated once with a Node one-liner in
  the gitma checkout and committed as `tests/fixtures/prng-vectors.json`)
- [x] T008 [P] `src/tma2/sim/geometry.py`: `f32`, `f32_angle`, `wrap2pi`, `wrap_pi`,
  `bearing_of`, `arc_position`, `js_round`, `turn_rows`, unit constants; `tests/unit/test_geometry.py`
  (−0 → +0, 2π wrap to 0, `js_round` half-up on negatives)
- [x] T009 `src/tma2/sim/ranges.py`: `ParameterRanges` → `RangesStruct` (numba-friendly numeric
  record with presence flags and padded σ list / weight list), validation with gitma's error
  messages (across_los needs los_offset; count weights need angle/rate/after/margin/spacing and
  speed ranges when fraction > 0; weights and fraction exclusive); `DEFAULT_RANGES`,
  `HELDOUT_RANGES`, `noise_free()`; `rows_for()`

## Phase 3: User Story 1, reproduce gitma's scenarios (P1) 🎯 MVP

**Goal**: `generate_scenario(seed, index, ranges)` equals gitma's output for every fixture.

**Independent Test**: `uv run pytest tests/conformance -q -rA` passes for the three fixtures.

- [x] T010 [US1] Fixtures: `scripts/make_fixtures.sh` generating, from the gitma checkout at
  `d0aec60`, `tests/fixtures/gitma/phase4-seed777/` and `tests/fixtures/gitma/iter4-seed777/`
  (`--seed 777 --count 100 --format both`, keep the four `.f32pack`, `test.ndjson`,
  `digests.json`, `ranges.json`, `heldout-ranges.json`, `COMMIT`), and copy gitma's
  `packages/data/test/golden/seed1-count10-test.ndjson` + `digests.json` to
  `tests/fixtures/gitma/iter1-seed1/` with `ranges.json`/`heldout-ranges.json` materialising
  `DEFAULT_RANGES`/`HELDOUT_RANGES`. Run it; commit the fixtures.
- [x] T011 [US1] `src/tma2/sim/scenario.py`: the 0.5.0 algorithm as numba kernels:
  `draw_manoeuvre_count`, `draw_scenario` (parameters + fit), `plan_manoeuvres` (0.3.0),
  `plan_target_manoeuvre` (0.4.0), `plan_target_manoeuvres` (0.5.0), `simulate_two_legs`,
  `ownship_zig2`, `target_manoeuvre`, `target_manoeuvres`, `simulate_truth`, `ranges_of_truth`,
  `observe`, and `generate_into(seed, index, ranges_struct, out arrays…) -> redraws`, writing
  truth, observations, parameters and indices into preallocated arrays. Docstring table mapping
  each function to its gitma source lines.
- [x] T012 [US1] `src/tma2/sim/generate.py`: `generate_scenario(seed, index, ranges, noise_free)
  -> GeneratedScenario` building the Pydantic `Scenario` (metadata with optional keys only when
  present, float32 values, `seed` as decimal string) from the kernel's arrays;
  `GENERATOR_VERSION` in `src/tma2/sim/version.py`; `warm_up()`
- [x] T013 [US1] `src/tma2/data/ndjson.py` and `src/tma2/data/f32pack.py` readers (writers in
  US3): parse header, check versions (`src/tma2/data/versions.py`: schema compatibility and
  readable generator versions {0.1.0, 0.2.0, 0.3.0, 0.4.0, 0.5.0}), iterate scenarios with
  gitma's error messages; `tests/unit/test_formats.py` reading every fixture file
- [x] T014 [US1] `tests/conformance/test_gitma.py`: for each fixture, for each split, generate the
  same indices with gitma2 and compare scenario by scenario: integers, flags, strings equal;
  floats equal after float32 rounding or within one ulp (counted per field and printed in the
  summary); header fields equal except `created_by`, `generator_git_commit`,
  `generator_git_dirty` (printed); fail on any other difference naming the scenario index and
  field. Also re-serialise gitma's `test.ndjson` records through `canonical.py` and compare the
  text byte for byte.
- [x] T015 [US1] Iterate on T011/T012 until T014 passes for all three fixtures; record the
  residual counts in `specs/001-types-generator/quickstart.md` (section 3) and any
  decision-boundary case in `research.md` R3.

**Checkpoint**: conformance passes; the P0 first check is met.

## Phase 4: User Story 2, one schema, generated types (P1)

- [x] T016 [US2] `tests/unit/test_types.py`: every fixture record validates; an unknown key is
  rejected; `model_dump` omits absent optional keys; round-trip to identical canonical text
- [x] T017 [P] [US2] `tests/unit/test_versions.py`: schema major mismatch rejected, newer minor
  rejected, older minor accepted; unknown generator version rejected with both versions in the
  message
- [x] T018 [P] [US2] CI step `schema-check` running `scripts/gen_types.py --check` (in `ci.yml`,
  T027)

## Phase 5: User Story 3, generate datasets from the command line (P2)

- [x] T019 [US3] `src/tma2/data/io.py` (atomic file: tmp + rename, abort), `ndjson.py` and
  `f32pack.py` writers with header-first, count checks, offset-table patching
- [x] T020 [US3] `src/tma2/data/provenance.py`: git commit and dirty state read once from the
  package's checkout; `generator_provenance(allow_dirty)` with gitma's refusal messages
- [x] T021 [US3] `src/tma2/data/dataset.py`: `plan_splits`, `generate_dataset(options)` (count
  redraws first so the header is exact, then write all requested formats per split, then
  `digests.json`), `created_by` with `sha256:` ranges digests
- [x] T022 [US3] `src/tma2/cli/generate.py` (`tma2-generate`): argparse with the contract's
  options, exit codes and JSON summary; refuse manoeuvre ranges without held-out ranges
- [x] T023 [US3] `tests/golden/test_data_golden.py`: seed 1 count 10 with `DEFAULT_RANGES` and
  the fixed test provenance; digests of the eight files compared with gitma's `digests.json`
  (byte-identical files prove canonical JSON and the pack layout); `UPDATE_GOLDEN=1` path;
  `tests/unit/test_cli.py`: dirty-tree refusal (monkeypatched provenance), noise-free header,
  bad seed and format errors, two runs byte-identical

## Phase 6: User Story 4, batches without files (P2)

- [x] T024 [US4] `src/tma2/features/batch.py`: `Batch` dataclass of arrays (data-model.md),
  `generate_batch(seed, batch_index, batch_size, ranges, start, end, noise_free, workers)` using a
  `prange` wrapper over `generate_into`, per-timestep labels (manoeuvring, last_kind, since_zig_s,
  since_manoeuvre_end_s), padded spans
- [x] T025 [US4] `tests/unit/test_determinism.py`: batch sizes 1/64/1024 and workers 1/4 identical;
  a batch's rows equal the decoded file rows for the same indices; `tests/perf/test_throughput.py`:
  prints and asserts ≥ 1,000 scenarios/s (file path, phase-4 ranges, 2,000 scenarios) and
  < 0.5 s per 256-scenario batch after warm-up

## Phase 7: User Story 5, repository and site (P3)

- [x] T026 [P] [US5] `site/`: Docusaurus 3 skeleton (`package.json` without `"type": "module"`,
  `docusaurus.config.js`, `sidebars.js`, `docs/index.md` welcome with the project question and
  gate ladder, `docs/glossary.md` with gitma's terms plus physics layer, oracle ceiling,
  efficiency, steady leg, settled row), `scripts/data_dictionary.py` producing
  `site/docs/data-dictionary.md` (gen-markdown-datadict + units table, gitma's post-processing),
  `site/scripts/prebuild.mjs` calling it
- [x] T027 [US5] `.github/workflows/ci.yml` with separate jobs `lint`, `typecheck`, `test`,
  `schema-check`, `site` on `ubuntu-latest` using `astral-sh/setup-uv` and `actions/setup-node`;
  numba cache warmed in `test`
- [x] T028 [P] [US5] `AGENTS.md`: add the repository layout and the commands (`uv sync`,
  `uv run pytest`, `uv run tma2-generate …`, `scripts/gen_types.py --check`, site build) and the
  conformance-fixture rule (never regenerate without stating why)

## Phase 8: Polish

- [x] T029 Run `quickstart.md` end to end on a clean clone; fix anything that does not match
- [x] T030 PR description: constitution check, site pages, the agent decisions stated
  (001/002 split; fixture choice; 3.12 pin), conformance residual counts

## Dependencies

- Phase 1 → Phase 2 → US1; US2 needs T004–T005; US3 needs US1 (T012) and T006; US4 needs T011;
  US5 is independent of US1–US4 except T028 (after everything).
- T010 (fixtures) can run at any time after T001; it needs only the gitma checkout.

## Parallel opportunities

- T002, T003 together; T006, T007, T008 together; T016–T018 together; T026 and T027 alongside
  US3/US4.

## Implementation strategy

MVP is US1: T001–T015 give a conformance-proven generator with readers only. US3 adds writers
and the CLI (the golden test then proves byte-identical files). US4 adds batches. US5 wraps the
repository. One PR for the whole spec, as its acceptance test is the conformance test.
