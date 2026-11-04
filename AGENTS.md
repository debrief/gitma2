# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

**gitma2: TMA via ML, second attempt.** Can a learned component, trained end to end with explicit
bearing geometry, match batch least squares wherever the constant-velocity model holds and beat a
tuned IMM wherever it does not? It starts from [debrief/Gitma](https://github.com/debrief/Gitma).

- Principles: `.specify/memory/constitution.md` (v1.2.0). Plans MUST pass its checks.
- Research and the owner's decisions: `docs/research/` (notes 01–05; decisions in 04 §6).
- Requirements: `docs/SRD.md` (draft), `docs/SRD-annex-A.md` (steady-leg detector, Gate D; §A.9 Gate S) and `docs/SRD-annex-B.md` (the owner's requirements for ownship and target manoeuvres and steady-leg segmentation, 2026-11-04). Read them before planning any feature; where this file and the SRD disagree, the SRD wins.

## Spec-driven workflow (GitHub Spec Kit)

Spec Kit is installed (`.specify/`, skills in `.claude/skills/speckit-*`). Feature work follows
`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`. Specs live under
`specs/<NNN-feature>/` and cite the SRD section(s) they implement. Done: 001 (types and
generator), 002 (references, physics layer, ONNX harness, P0; **P0 passed**, panel round 3,
`experiments/20261101-p0-r4/`). 003 (Gate 1, constant velocity): **Gate 1 passed** (panel round 2,
`experiments/20261101-g1-a-g1/`), but only because the model reduces to batch least squares: the
heads died in training, so learning is untested until Gate 2 (prerequisites in
`specs/003-gate1-cv/tasks.md`). Workflows: `train/<plan>`, `validate/<run>`, `gate/<plan>`,
`report/<gate run>`. 004 (steady-leg detector, Annex A): **Gate D stopped at validation**
(panel round 2, `experiments/20261102-gd-a-val/`). The detector raised no alarm: its p_change
reads only time since the zig. Downstream it scored 0.95× batch least squares but 1.21× the IMM,
and the time-late variant failed. Test seed 305 is unscored and reserved. Annex A §A.6 applies:
publish, and Gate 2 uses the CUSUM/GLR segmenter at an operating point its spec declares
(recommended: GLR at a 5% held-leg false-alarm rate). Write-up: `site/blog/2026-11-02-gate-d.md`.
Detector workflows: `train/gd-a`, `validate-gd/<run>`. Research note 08 (leg-detection spike,
validation only) recommends GLR + physics-layer confirmation as the interim Gate 2 segmenter.
005 (steady-leg segmentation, Gate S; Annex A §A.9, owner merges): specified. Components O
(ownship), C (classical target segmenter, the reference) and L (learned, starts equal to C); fresh
test seed from 312. Planned (`specs/005-steady-leg-segmentation/plan.md`): measured on validation,
an additive leg search is far weaker than GLR + confirm (F1 0.65 vs 0.79), so C confirms
nominations from both by the coupled physics-layer cost on each nomination's own prefix. Owner
decision 2026-11-04 (Annex B, SRD §9): the simulation changes to the owner's manoeuvre model
rather than the thresholds to the simulation. Generator 0.6.0 (MAN2: target legs 10–40 min, bell
shaped; wander; slower turns; scoping in `docs/research/09`) is the next spec and precedes
Gate S.

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
  references/              lsq, classical, naive, ekf, imm (ports of gitma's), crb (Fisher information)
  physics/                 reference.py (NumPy, documentation of record), layer.py (torch, exportable), segmentation
  eval/                    errors, slices, stats, metrics (+ efficiency), bootstrap, rows (settled, G5), predictions, experiment
  export/                  toy model and ONNX export (f64 conformance artefact, f32 reported)
  models/                  Gate 1: rows, model (encoder, heads, physics layer), loss, train, predict, export
  cli/                     tma2-generate, -solve, -track, -naive, -crb, -eval, -oracle, -p0, -train, -predict, -tune, -plan
conformance/onnx/          browser (WASM, Playwright) and Java legs of the export check
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
uv run tma2-solve --in <split> --out <pred.ndjson> [--per-timestep]
uv run tma2-track --in <split> --out <pred.ndjson> --filter imm --sigma-cv 0.01 --sigma-ct 0.03 --sigma-omega 0.01 --switch 0.001 --p0-scale 4 --r-scale 8
uv run tma2-crb --in <split> --out <crb.ndjson> [--model full_window|known_manoeuvres|per_leg]
uv run tma2-eval --truth <split> --predictions <pred>... [--crb <crb.ndjson>] [--points 300,600] --out <dir>
uv run tma2-oracle --truth <split> --out <pred.ndjson> [--speed-prior] [--trivial] [--mask-turns]
uv run tma2-p0 --experiment experiments/<id> [--oracle-data <dir with validation.f32pack>] [--gitma-imm <gitma tma-track output>]   # exit 3: gate not passed
uv run python -m tma2.export.onnx_export --out conformance/onnx/export
(cd conformance/onnx && npm ci && node wasm_leg.mjs --dir export/f64) ; uv run python conformance/onnx/java_leg.py conformance/onnx/export/f64
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

## Gotchas (learned in specs 001–002)

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
- The reference ports keep gitma's arithmetic order, including explicit 4×4/5×5 loop products
  instead of BLAS (`@` on small matrices changes the last bits and the iteration path) and the
  IMM's finite-difference Jacobians. Agreement with gitma is 1e-7 typical, 1e-5 worst, flags exact.
- Export size: the Gauss–Jordan solve is one masked whole-matrix update per pivot; a row-by-row
  form made ~3,000 nodes per solve and onnxruntime took over 10 minutes to load the graph.
  Iterations are unrolled, so the conformance export uses 8; a deployable model needs an ONNX
  `Loop` over the iteration (spec 003).
- Physics layer export rules: no `torch.diagonal`/`diag_embed`/in-place slice writes (they export
  `If` or unsupported ops); no `torch.cos` or `torch.atan` in double (onnxruntime-web has no
  float64 kernels for them: use `cos_export`/`atan2_export`); no `Solve`/`Inverse` (unrolled
  Jacobi-scaled Gauss–Jordan instead); keep onnxruntime versions aligned across Python, web and
  Java (1.20's FusedMatMul is float-only).
- The physics layer must run in double: in float32 the damped solve's accept/reject decisions flip
  between runtimes (~1e-3 disagreement). The f32 export is reported, never the conformance artefact.
- Knot predecessors for the speed-continuity prior are counted among active knots only; an inert
  candidate between a turn's start and end knots must not become the end knot's predecessor.
- Physics layer gradients: never `sqrt` a quantity that can be exactly 0 and carries a gradient
  (masked rows, inert knots); use `safe_sqrt`. A single NaN there poisons every parameter of a
  model on the first backward pass (P0 panel round 1). Tests assert finite gradients everywhere.
- The layer tries several damping values per iteration (gitma's inner retry, side by side); with
  one trial per iteration it stops short on flat-valley rows. Compare it with *cold-start* batch
  least squares (`solve_batch` at row k): per-timestep rows are warm-started and can sit in a
  different minimum.
- Before the zig the layer returns finite, "plausible" states with range sd ≫ range: training
  and scoring must exclude or down-weight rows whose covariance says they are undetermined.
- Prediction caches in `tma2-p0 --work` are keyed by commit and reused only from a clean tree;
  `results.json` from the conformance legs must name the fresh export's SHA-256.
- Cramér–Rao bounds: `full_window` for held course, `known_manoeuvres` (times and kinds known) on
  manoeuvring data; `per_leg` is a diagnostic only. Efficiency is median(|e|/σ)/0.6745 per row.
- Model export (spec 003): the physics iterations are one ONNX `Loop` because the eager layer calls
  a TorchScript-scripted `iterate` while tracing. Inside the loop body, ONNX shape inference fails
  on zero-size tensors (no knots) and on lost ranks, so the CV path has no knot tensors and shapes
  are explicit. Write attention out (PyTorch's encoder layer casts masks to double, which the
  exporter refuses); no GELU (onnxruntime has no double `Erf`). Set the default dtype to the
  model's for `torch.onnx.export`: the scripted loop's scalar constants follow it.
- Experiments from a worktree: do not symlink `data` into it (`data/` in .gitignore matches
  directories, not a symlink, so the tree records as dirty); pass absolute data paths.
- Never time anything while another CPU-heavy job runs: torch's OpenMP threads oversubscribed by
  a parallel tune ran the physics layer 50–100× slower (48 s against 0.55 s per call; spec 004).
- Within one process, a second training run can differ from the first in the last bits
  (allocator state; 1e-16 in layer-norm weights); separate processes are byte-identical, so
  determinism and resume tests run each job in a fresh interpreter (`test_detector_train.py`).
- The known-manoeuvres Cramér–Rao bound has a numba port (`crb_known_manoeuvres_fast`, 0.4 ms
  per scenario against 8 ms) for the training loss; `Batch.tm` carries the generator's table.
- Docusaurus MDX: no `{...}` in prose (it is a JS expression); `scripts/data_dictionary.py`
  escapes `<` and braces outside code spans.
