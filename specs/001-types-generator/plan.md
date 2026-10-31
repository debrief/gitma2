# Implementation Plan: Types and Generator (foundations, part 1)

**Branch**: `001-types-generator` (work is pushed on the session branch `claude/inspiring-curie-j192v9`) | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-types-generator/spec.md`

## Summary

Port gitma's data layer to Python so that gitma2 generates the same scenarios from the same seeds:
carry `schema/tma.yaml` and generate Pydantic models, JSON Schema and the data dictionary from
it; implement gitma's generator 0.5.0 as a per-scenario scalar kernel compiled with numba and run
in parallel over scenario indices (each scenario is a pure function of seed, index and ranges, so
batch size and worker count cannot change the output); write gitma's NDJSON and Float32-pack
formats with canonical JSON that matches JavaScript's number formatting; prove conformance against
committed gitma fixtures; give training an in-memory batch interface; and set up the `uv`
project, CI and the Docusaurus site skeleton.

## Technical Context

**Language/Version**: Python 3.12 (pinned in `.python-version`; numba's supported range is the
constraint, see research R7)

**Primary Dependencies**: numpy, numba, pydantic 2, linkml 1.12 (dev, for generation),
typer or argparse for the CLI (argparse: no dependency, mirrors gitma's `parseArgs`), pytest,
ruff, mypy; Node 22 + Docusaurus for `site/` only

**Storage**: files: NDJSON (inspection) and Float32-pack (compact) with a digests file; no
database

**Testing**: pytest; golden files under `tests/golden/`; conformance fixtures under
`tests/fixtures/gitma/`

**Target Platform**: Linux (GitHub `ubuntu-latest`, 4 cores) and developer laptops; no GPU

**Project Type**: library + CLI (single Python package `tma2`) with a static site

**Performance Goals**: ≥ 1,000 scenarios/s to files; a 256-scenario batch in < 0.5 s on 4 cores
(spec SC-003)

**Constraints**: byte-equal integers/flags/strings and float32-equal floats against gitma
(1 ulp residual reported, not failed); output independent of batch size, worker count and order;
seeded PRNG only; stored floats float32 with −0 → +0

**Scale/Scope**: datasets of 10^5–10^6 scenarios (files); on-the-fly batches for training;
schema of ~30 classes carried unchanged

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
| --- | --- | --- |
| I Types once in LinkML | Schema carried unchanged; Pydantic, JSON Schema, data dictionary generated; staleness check in CI; every file read validated; gitma files remain readable | pass (FR-001..004) |
| II Determinism | gitma's SplitMix64 + xoshiro128** per scenario; output a pure function of (seed, index, ranges); float32 rounding and −0 → +0; versions and digests in every header; golden tests per package; evaluation splits as files with digests; on-the-fly batches are seeded | pass (FR-005..008, 014, 016, 017) |
| III Physics layer | Not applicable to this spec (no model); `sim` stays plain functions over arrays with no hidden state (FR-021) | pass |
| IV Honest measurement | Not applicable (no results reported); the conformance test is itself a measurement with a stated tolerance | pass |
| V Gates | This spec delivers P0's first check and trains nothing | pass |
| VI Portable artefact | Not applicable (no model artefact); Python stack as decided | pass |
| Technical constraints | Python 3.12+, `uv`, numpy/numba, LinkML, pytest, ruff, mypy --strict; free 4-core runners; frame and units as gitma; public repo, mock data | pass |
| Development workflow | PR against main; CI runs lint, typing, tests, schema check, site build; site pages (data dictionary, glossary) added with the concept | pass |

No violations; Complexity Tracking is empty.

**Post-design re-check (after Phase 1)**: unchanged. The numba kernel is a plain function over
scalars and arrays (III); the batch interface returns arrays and indices only; the JavaScript
number formatter is pure. The one design choice that could have violated II, a vectorised NumPy
generator with per-scenario RNG state arrays, was rejected in research R2 precisely because
redraws make stream consumption data-dependent per scenario.

## Project Structure

### Documentation (this feature)

```text
specs/001-types-generator/
├── plan.md              # This file
├── research.md          # Phase 0: algorithm, vectorisation, formats, tooling decisions
├── data-model.md        # Phase 1: entities (from the schema) and the batch arrays
├── quickstart.md        # Phase 1: how to prove the feature works
├── contracts/
│   ├── cli-tma2-generate.md   # command-line contract
│   ├── file-formats.md        # NDJSON, Float32-pack, digests, canonical JSON
│   └── batch-interface.md     # in-memory batch arrays and labels
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
pyproject.toml            # uv project: package tma2, dev groups (linkml, lint, test)
.python-version           # 3.12
uv.lock
schema/
└── tma.yaml              # carried from gitma (0.16.0), the single source of truth
src/tma2/
├── __init__.py
├── types/
│   ├── __init__.py       # re-exports, SCHEMA_VERSION
│   └── generated/        # gen-pydantic output (committed; CI checks staleness)
│       ├── tma.py
│       └── tma.schema.json
├── sim/
│   ├── __init__.py
│   ├── prng.py           # SplitMix64, xoshiro128**, uniform/logUniform/gaussian/uniformInt (numba)
│   ├── geometry.py       # f32, f32_angle, wrap2pi, bearing_of, arc_position, js_round
│   ├── ranges.py         # ParameterRanges → flat numeric struct for the kernel; DEFAULT/HELDOUT
│   ├── scenario.py       # the 0.5.0 algorithm: draw, plan, simulate, observe (numba kernel)
│   ├── generate.py       # generate_scenario(seed, index, ranges) → Scenario; batches (prange)
│   └── version.py        # GENERATOR_VERSION = "0.5.0"
├── data/
│   ├── __init__.py
│   ├── canonical.py      # canonical JSON with JavaScript number formatting
│   ├── ndjson.py         # writer/reader with header, atomic write
│   ├── f32pack.py        # writer/reader of the TMAPACK format
│   ├── dataset.py        # planSplits, generate_dataset, digests.json
│   ├── provenance.py     # git commit / dirty, refusal without --allow-dirty
│   └── versions.py       # schema and generator compatibility checks
├── features/
│   └── batch.py          # Batch dataclass of arrays; per-timestep labels; rows_for(ranges)
└── cli/
    └── generate.py       # tma2-generate
scripts/
├── gen_types.py          # schema → Pydantic + JSON Schema (+ staleness check mode)
├── data_dictionary.py    # schema → site/docs/data-dictionary.md (gen-markdown-datadict + units)
└── make_fixtures.sh      # how the gitma fixtures were produced (pinned commit, commands)
tests/
├── unit/                 # prng, geometry, canonical json, formats, provenance, versions
├── golden/               # seed-fixed byte-identical outputs per package (+ UPDATE_GOLDEN=1)
├── conformance/          # gitma fixtures vs tma2 output (the P0 check 1)
├── fixtures/gitma/       # committed gitma outputs: iter1 seed1 count10; phase4 seed777 count100;
│                         # iter4 seed777 count100 (f32pack all splits, test.ndjson, digests, ranges, COMMIT)
└── perf/                 # throughput measurements printed and asserted (SC-003)
site/                     # Docusaurus: welcome, glossary, generated data dictionary
.github/workflows/ci.yml  # lint, typecheck, tests, schema staleness, site build (separate steps)
```

**Structure Decision**: a single Python package with sub-packages mirroring gitma's `types`,
`sim`, `data`, `features` boundaries, so that spec 002 (references, physics layer) and later
specs add `references/`, `physics/`, `models/`, `eval/`, `export/` beside them. The site is a
separate Node project as in gitma, built only in CI and for releases.

## Complexity Tracking

None. No constitution violations to justify.
