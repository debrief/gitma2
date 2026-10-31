# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

**gitma2: TMA via ML, second attempt.** Can a learned component, trained end to end with explicit
bearing geometry, match batch least squares wherever the constant-velocity model holds and beat a
tuned IMM wherever it does not? It starts from [debrief/Gitma](https://github.com/debrief/Gitma).

- Principles: `.specify/memory/constitution.md` (v1.1.0). Plans MUST pass its checks.
- Research and the owner's decisions: `docs/research/` (notes 01–05; decisions in 04 §6).
- Requirements: `docs/SRD.md` (draft) and `docs/SRD-annex-A.md` (steady-leg detector, Gate D). Read them before planning any feature; where this file and the SRD disagree, the SRD wins.

## Spec-driven workflow (GitHub Spec Kit)

Spec Kit is installed (`.specify/`, skills in `.claude/skills/speckit-*`). Feature work follows
`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`. Specs live under
`specs/<NNN-feature>/` and cite the SRD section(s) they implement. Done: 001 (types and
generator). Next: 002 (references, physics layer, P0).

## Stack (owner decisions, 2026-10-31)

Python 3.12 throughout: PyTorch models (from spec 003), NumPy/numba generator and reference
estimators, LinkML → Pydantic types, `uv`, `pytest`, `ruff`, `mypy --strict`. Training on free
4-core GitHub runners. Models export to ONNX (standard ops, fixed window, dynamic batch) with a
cross-runtime conformance test. Site and process as gitma: Docusaurus site, pre-registered
decision records, fresh test seeds, agent review panel for every gate.

## Repository layout

```
schema/tma.yaml            LinkML source of truth (carried from gitma, 0.16.0); README explains regeneration
src/tma2/
  types/                   generated Pydantic models + JSON Schema (scripts/gen_types.py), parse_record
  sim/                     prng (SplitMix64, xoshiro128**), geometry, ranges, scenario (numba kernel), generate
  data/                    canonical JSON (JavaScript number formatting), ndjson, f32pack, dataset, provenance, versions
  features/                batch: in-memory padded batches with per-timestep labels (prange over scenarios)
  cli/                     tma2-generate
scripts/                   gen_types.py, data_dictionary.py, make_fixtures.sh, research/
tests/                     unit, golden, conformance (gitma fixtures), perf; fixtures/gitma/<name>/
specs/                     Spec Kit features
docs/                      SRD, Annex A, research notes
site/                      Docusaurus (welcome, glossary, generated data dictionary, blog)
```

## Commands

```
uv sync                                   # Python 3.12 env with dev tools
uv run pytest -q                          # unit, golden, conformance, perf (~15 s after numba warm-up)
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run python scripts/gen_types.py        # after editing schema/tma.yaml; --check is what CI runs
uv run python scripts/data_dictionary.py  # site/docs/data-dictionary.md
uv run tma2-generate --seed <uint64> --count <n> --out <dir> [--ranges f --heldout-ranges f] [--noise-free] [--allow-dirty] [--format both|ndjson|f32pack]
(cd site && npm ci && npm run build)      # site; prebuild regenerates the data dictionary
```

## Autonomy and owner input

The owner does not want to be the blocker. Agents make progress from the documents and ask only
where the documents say the decision is the owner's.

- **Decide and record.** Where the SRD, an annex or a decision record states a default (for
  example Annex A §A.8), adopt it, record it in the decision record or spec with a one-line
  reason, and proceed. Where no default exists, choose what a careful colleague would, state the
  choice and the alternatives in the PR description, and proceed; the owner can overrule on
  review.
- **Proceed between gates.** Specify → plan → tasks → implement → PR for every step of the SRD
  plan runs without asking. Gate verdicts come from the agent review panel, never from waiting
  on a human. A follow-on the SRD leaves to the owner is proposed in the write-up with a
  recommended default; if the owner has not objected by the time the next spec is written, the
  recommendation is adopted and recorded as such.
- **Merging.** An agent may merge its own PR once CI is green, a review agent (`/code-review`,
  or the panel for a gate PR) has approved, and the PR touches no owner-only item below. A PR
  that amends the SRD, an annex or the constitution is opened by the agent and merged by the
  owner; after two working days without objection the agent merges it and says so in the next
  write-up.
- **Owner-only** (ask, and wait): anything that spends money or needs a new account or secret
  (paid runners, cloud GPUs, external services); any change to the scope in SRD §1 or to the
  classification and mock-data rules; changing a gate's criteria after any result on that gate
  exists; deleting committed experiments, weights or result branches; publishing outside this
  repository and its site; anything the owner has said is theirs.
- **Ask well.** When input is needed, ask one multiple-choice question at a time with a
  recommended option first, do everything that does not depend on the answer beforehand, and
  never stop with nothing delivered.

## Hard rules

See the constitution. In short: types once in LinkML; seeded randomness only; the reported
estimate comes from a declared physics layer; no result without naive, batch least squares, the
tuned IMM/EKF and the oracle ceiling on the same rows; efficiency (error / CRB) per slice; three
seeds per carried configuration; nothing above OFFICIAL, mock data only.

## Gotchas (learned in spec 001)

- The generator is a line-for-line port of gitma's `scenario.ts`: every PRNG draw, in gitma's
  order, including draws that are consumed and discarded. Changing the order breaks conformance.
- JavaScript semantics matter: `Math.round` is half-up (`js_round`), `%` is `fmod`, `Math.fround`
  + 0 maps −0 to +0 (`f32`). `canonical_json` formats numbers as `Number::toString` (integral
  doubles without `.0`, exponent thresholds 1e-6 and 1e21).
- Conformance fixtures under `tests/fixtures/gitma/` are gitma's output; never regenerate them
  from gitma2. `scripts/make_fixtures.sh` documents how they were made.
- Numba compiles on first use (several seconds); tests warm it up in `conftest.py`; CI warms it
  explicitly. The compiled cache lives next to the sources (`__pycache__`) and is gitignored.
- Throughput: kernel ≈ 20k scenarios/s; f32pack ≈ 2k/s; NDJSON ≈ 400/s (Python float formatting).
  Use `--format f32pack` for large datasets; NDJSON is for inspection.
