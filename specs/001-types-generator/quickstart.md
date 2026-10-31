# Quickstart: Types and Generator (foundations, part 1)

How to prove the feature works end to end. Commands run from the repository root.

## Prerequisites

- Python 3.12 via `uv` (`uv python install 3.12` if needed); Node 22 for the site only.
- `uv sync` installs runtime and dev dependencies from `uv.lock`.

## 1. Types are generated from the schema and not stale

```bash
uv run python scripts/gen_types.py --check
```

Expected: exit 0, "generated types are up to date". Edit a description in `schema/tma.yaml`,
re-run: exit 1 naming the stale file. Revert.

## 2. gitma's files validate and round-trip

```bash
uv run pytest tests/unit/test_formats.py -q
```

Expected: every fixture file under `tests/fixtures/gitma/` parses with the generated models, and
NDJSON → Float32-pack → NDJSON is byte-identical.

## 3. Conformance with gitma (P0 check 1)

```bash
uv run pytest tests/conformance -q -rA
```

Expected: three fixtures (`iter1-seed1`, `phase4-seed777`, `iter4-seed777`) pass; the summary
prints the number of float values compared and the count of one-ulp residuals per field
(expected: a handful or zero). Any scenario-level mismatch fails with the index and the first
differing field.

## 4. Determinism across batch size and workers

```bash
uv run pytest tests/unit/test_determinism.py -q
```

Expected: identical arrays for batch sizes 1, 64, 1,024 and for 1 and 4 workers; identical
`digests.json` for two CLI runs.

## 5. Generate a dataset

```bash
uv run tma2-generate --seed 777 --count 1000 --out /tmp/tma2-777 \
  --ranges tests/fixtures/gitma/phase4-seed777/ranges.json \
  --heldout-ranges tests/fixtures/gitma/phase4-seed777/heldout-ranges.json --format both
```

Expected: JSON summary with four splits and `scenarios_per_s` ≥ 1000; `digests.json` present;
`head -c 400 /tmp/tma2-777/test.ndjson` shows the header with `generator_version` 0.5.0, the
commit and `generator_git_dirty: false` on a clean tree. Repeat the command into a second
directory: `diff <(cat /tmp/tma2-777/digests.json) <(cat /tmp/tma2-777b/digests.json)` is empty.

## 6. Throughput

```bash
uv run pytest tests/perf -q -s
```

Expected: prints scenarios/s for the file path and seconds per 256-scenario batch; asserts
≥ 1,000/s and < 0.5 s respectively (after warm-up).

## 7. CI and site

Open a PR: the `ci.yml` jobs `lint`, `typecheck`, `test`, `schema-check` and `site` run
separately. Locally:

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src scripts tests
uv run pytest -q
(cd site && npm ci && npm run build)
```

The site build runs `scripts/data_dictionary.py` first; the resulting `site/docs/data-dictionary.md`
lists every class in `schema/tma.yaml`, and `site/docs/glossary.md` contains the terms named in
spec FR-020.
