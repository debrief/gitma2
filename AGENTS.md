# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

**gitma2: TMA via ML, second attempt.** Can a learned component, trained end to end with explicit
bearing geometry, match batch least squares wherever the constant-velocity model holds and beat a
tuned IMM wherever it does not? It starts from [debrief/Gitma](https://github.com/debrief/Gitma).

- Principles: `.specify/memory/constitution.md` (v1.3.0). Plans MUST pass its checks.
- Research and the owner's decisions: `docs/research/` (notes 01–05; decisions in 04 §6).
- Requirements: `docs/SRD.md` (draft), `docs/SRD-annex-A.md` (steady-leg detector, Gate D; §A.9 Gate S) and `docs/SRD-annex-B.md` (the owner's requirements for ownship and target manoeuvres and steady-leg segmentation, 2026-11-04). Read them before planning any feature; where this file and the SRD disagree, the SRD wins.

## Spec-driven workflow (GitHub Spec Kit)

Spec Kit is installed (`.specify/`, skills in `.claude/skills/speckit-*`). Feature work follows
`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement` → `/speckit-report-slides` → PR.
`/speckit-specify` ends with `/speckit-report-kickoff` (hooks in `.specify/extensions.yml`; see
Reporting below). Specs live under `specs/<NNN-feature>/` and cite the SRD section(s) they implement. Done: 001 (types and
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
005 (steady-leg segmentation, Gate S; Annex A §A.9, owner merges): implemented and scored. Components O
(ownship), C (classical target segmenter, the reference) and L (learned, starts equal to C); fresh
test seed from 312. Planned (`specs/005-steady-leg-segmentation/plan.md`): measured on validation,
an additive leg search is far weaker than GLR + confirm (F1 0.65 vs 0.79), so C confirms
nominations from both by the coupled physics-layer cost on each nomination's own prefix. Owner
decision 2026-11-04 (Annex B, SRD §9): the simulation changes to the owner's manoeuvre model
rather than the thresholds to the simulation. Generator 0.6.0 (MAN2: target legs 10–40 min, bell
shaped; 40–120 min windows, 720 rows; wander; slower turns; scoping in `docs/research/09`) is
spec 006 (`specs/006-generator-man2/`) and precedes Gate S: implemented (PR 13); **G0-MAN2
passed** (panel round 2, `experiments/20261104-g0-man2-r2/`, CLI `tma2-g0-man2`; two owner
amendments after results: check-4 coverage and the throughput method). Seeds: 314 validation
(`data/man2-val`, digests in `experiments/20261104-g0-man2/dataset-digests/`), 315 test (Gate S;
generated at a38f61b after the decision record; now used), 316 noise-free, 317 L's training
stream; 312/313 unused; the next fresh seed is 318. IMM/EKF re-tune on 314: `tune/**` branches
run `.github/workflows/tune.yml` (results to `results/man2-tune-<run id>`); frozen
`imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`, EKF `ekf-sa0.00003-p4-r0.03125`
(`experiments/20261104-man2-refs/`). Gate S: decision `experiments/20261104-gs-decision/` (plan
`configs/segment/gs-plan.json`; carried L = seed 3, `carried.json`), L training on CI
(`segtrain/**` → `.github/workflows/segtrain.yml`, validation `experiments/20261105-segL-val/`),
test segmentations on CI (`segment.yml` plans `configs/segment/gs-test-*.json`;
`glr-confirm/**` for the reference), scoring `tma2-gs ... --decision --plan --split test`.
**Gate S scored** (record r2 `experiments/20261105-gs-r2/`, after panel round 1 rejected r1 for a
causality bug in C's open-transition start, fixed in 7fe8874; decided by panel round 2): S1–S3 pass,
S4 inconclusive (L − C gap recovered +0.0012 [−0.0031, +0.0049]); C recovers 0.898 of the
one-leg-to-oracle gap (0.838 on the rows every estimator answers: one leg and the IMM fail on a
quarter), GLR + confirm 0.143. Follow-on (FR-072; inconclusive counts as not
passed): C is Gate 2's segmenter and control; learning recorded as not shown. Scoring runs on CI
(`score/**` → `.github/workflows/score.yml`, plans `configs/score/`). Before Gate 2 (C fixes done on the branch after PR 15: monotone cost tables, no overlap
through open transitions, `open_handover` parameter, `code_sha256` in headers; schema 0.24.0;
the open-transition convention is chosen on validation): fix the
search's cost-table fit failures (`segment/search.py` warm starts; check monotonicity on the
validation tables), bind the segmenter's code commit in segmentation headers (the digest binds
parameters only), fix one open-transition hand-over convention (the main lever: C recovers 0.66 of the gap on
rows open at k against 0.91 elsewhere, and S4's whole L − C difference sits on those rows), stop
transitions overlapping through open ones (`_free` treats an open transition as [s, s + 1]), and
take a fresh test seed. Owner decision 2026-11-05: a learned nominator, or evidence trained
through confirmation, is tested within Gate 2, not as a separate gate. Write-up:
`site/blog/2026-11-05-gate-s.md`.
007 (Gate 2 on MAN2, `specs/007-gate2-man2/`; SRD amendment G2-d in PR 16, merged by the owner):
E = E-s (spec 005's evidence shifting C's confirmation threshold, trained on decision tables,
`tma2-dtables`) then E-w (per-bearing weights and a start correction on C's hand-over, physics
layer with 12 knots); `tma2-g2train {tables,train,es}`, `tma2-g2predict`, `tma2-g2` (tma2-gs
scoring with `--predictions`, `--knots 12`). Workflows: `segment/**`, `dtables/**`, `g2train/**`,
`g2predict/**`, `score/**` (kind `g2`). C frozen at code `4d2c084f…` (parameters `60e6ee63…`,
hand-over `knot_at_k`); decision `experiments/20261107-g2-decision/` (plan `configs/gate2/g2-a.json`
`6092c364…`, never edited). Training run 42352638177; validation `experiments/20261107-g2-val/`
(carried e-s3, `carried.json`); **test record `experiments/20261107-g2/`: G2-a to G2-d pass, E − C
+0.025 [+0.018, +0.031]** (seed 319, 4,983 scenarios). Panel round 1: two majors (E-s ≈ a zig veto,
E-w ≈ a fading memory), answered by pre-registered classical controls C′, fade and C″
(`experiments/20261107-g2-veto/`, model kind `veto` in `tma2-g2predict`, plans
`configs/gate2/g2-a-{veto,fade}.json`). **Decided by the panel, round 2: G2-a to G2-d pass**;
on test the classical C″ (zig veto + fixed fade, nothing learned) − C is +0.018 and E − C″ +0.007
[+0.001, +0.012] (learning beyond the rules, small; E-s adds nothing shown beyond the veto).
Write-up `site/blog/2026-11-08-gate-2.md`; recommended follow-on: carry E, keep C″ as a standing
control, spec 008 uncertainty calibration with the panel's follow-ons (`specs/007-gate2-man2/tasks.md`).
`scripts/research/g2_paired_gaps.py` gives paired gap differences between any two scored
estimators. Seeds: 318 training stream, 319 test (used); the next fresh seed is 320.
008 (uncertainty calibration, Gate 3, `specs/008-uncertainty-calibration/`; done; time-late E-w:
no gain over causal, `experiments/20261108-g3-timelate/`): every
prediction row states its covariance (`cov_xyvv`, `cov_ok`, sds of log range, course and speed;
schema 0.27.0), the scorer measures coverage, NEES, interval score and sharpness
(`calibration.json`, `cal_<name>` in `errors.npz`), and `--reuse <errors.npz>` skips re-solving.
A calibration head (`src/tma2/calib/`, `tma2-g3train`, `tma2-g3predict`) scales E's covariance by
e^(2s) on cached features (`tma2-g2predict --features`); control: a per-slice temperature. Gate 3
criteria in `tma2-g3` (proposed in an SRD amendment; plan `configs/gate3/g3-a.json`, draft until
the decision binds it). Time-late E-w: `configs/gate2/g3-timelate.json`. **Gate 3 stopped at
validation** (decision `experiments/20261108-g3-decision/`, plan `fdf7987e…`; record and panel
round 2 `experiments/20261108-g3-val/`): G3-a inconclusive (course coverage largely vacuous: the
95% course interval is the whole circle on half the rows), G3-b 0.835 against 0.92 (kept
near-singular correlations; linearised training errors), G3-c head worse than the temperature,
no per-row learning shown; seed 320 not generated (still unused). E's raw covariance is
overconfident (95% coverage 0.60) and must not be shown as an uncertainty. Follow-on (write-up
`site/blog/2026-11-08-gate-3.md`, spec 009): circular or undetermined course, observability gating
by a causal proxy, correlation shrinkage, training on exact errors. The next fresh seed is 320.
009 (usable uncertainty, Gate 4, `specs/009-usable-uncertainty/`; owner chose the probabilistic
course): E's rows state course as an arc ±X (≤ 45°) with probability P (von Mises + uniform
mixture, P through an isotonic map) and range/speed 95% half-widths (schema 0.30.0 fields
`course_arc_rad`, `course_arc_prob`, `course_conc`, `course_mix_p`, `range_ratio_q95`,
`speed_q95_mps`). Code: `calib/statement.py`, `calib/statement_fit.py` (head and the sd^β
temperature, β per quantity from a grid), `tma2-g3train statement|statement-temperature` (CI
`g4train/**`), `tma2-g4predict`, scorer statement columns 9–14 in `eval/calibration.py` (9-wide
arrays widened on `--reuse`), criteria `calib/gate4.py` and `tma2-g4`. Baseline
`experiments/20261108-g4-base-val/`; decision `experiments/20261108-g4-decision/` (plan
`configs/gate4/g4-a.json` `e357f8a7…`). **Gate 4 stopped at validation**
(`experiments/20261109-g4-val/`, panel round 2): carried st-s3 missed G4-b's top bin (+0.054
against 0.05; the isotonic map caps P at 0.677); G4-c, G4-d (head − temperature −0.235) and G4-e
pass, G4-a speed inconclusive. P is honest on average but not on unsettled rows (stated 0.62, hit
0.30), and 72% of the head's margin is reproducible by a quadratic rule in E's three log sds.
Write-up `site/blog/2026-11-09-gate-4.md`; follow-on spec 010 (one self-consistent course
probability, slice-gated reliability with a causal unsettled proxy, interval-based bin checks,
cross-sd and encoder-only controls registered first). Seed 320 still unused.

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
  detect/                  Gate D: CUSUM/GLR controls, confirmation, matching, downstream (spec 004)
  segment/                 Gate S: O, C (nominate + confirm), L (evidence, crf, train, export), score, gate
  report/                  progress figures: track plots and error curves with provenance sidecars (tma2-plot)
  cli/                     tma2-generate, -solve, -track, -naive, -crb, -eval, -oracle, -p0, -train, -predict, -tune, -plan,
                           -gd, -g0-man2, -segment, -segtrain, -gs, -plot
conformance/onnx/          browser (WASM, Playwright) and Java legs of the export check
scripts/                   gen_types.py, data_dictionary.py, make_fixtures.sh, research/
tests/                     unit, golden, conformance (gitma fixtures), perf; fixtures/gitma/<name>/
specs/                     Spec Kit features
docs/                      SRD, Annex A, research notes
site/                      Docusaurus (welcome, glossary, generated data dictionary, process page, blog;
                           blog/_templates: kickoff and slides posts; static/slides/<post>/: reveal.js decks;
                           static/img/<post>/: committed figures with .json sidecars)
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
uv run tma2-plot track --truth <split> --predictions <pred>... --labels a,b --scenario <i> --at 3600,5400 --out fig.svg   # also: errors
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

## Reporting (constitution 1.3.0, owner decision 2026-11-08)

Two blog posts per task, where a task is a Spec Kit feature or a gate run. The practice page is
`site/docs/process/reporting.md`; templates are `site/blog/_templates/{kickoff,slides}.md` and
`site/static/slides/_template/index.html`.

- **Kickoff post** (`/speckit-report-kickoff`, run by `/speckit-specify`'s after-hook): written
  before implementation, from the spec. Where we are (the last gate's verdict, what is carried,
  what is open), where this task moves to (the SRD section, the criteria or acceptance, the plan
  in a few steps, the risks and what would make us stop) and how progress will be shown (which
  figures the slides post will carry). Smaller changes between tasks (fixes, CI repairs) append
  a dated paragraph to the current kickoff post rather than a post of their own.
- **Slides post** (`/speckit-report-slides`, run by `/speckit-implement`'s after-hook; a gate run
  does it after the panel decides): built *before the PR is opened*, so the PR carries it. A
  reveal.js deck at `site/static/slides/<date-slug>/index.html` (copy the template; reveal.js is
  loaded from cdnjs, pinned) embedded in the post with `<Slides slug="..." />`. Contents: an
  overview of the capability or fix, illustrated (a diagram or a figure per idea); a demonstration
  of progress with charts and track plots; what was not achieved; what comes next. A gate's
  slides post is the illustrated companion of its critical write-up and links to it.
- **Figures** are SVG under `site/static/img/<date-slug>/`, each next to the `.json` sidecar that
  `tma2-plot` writes (truth and prediction digests, scenario, command, code commit). A figure made
  by a script instead names the script and its commit in the post. Track plots: ownship blue,
  target red, each estimator's trail from the zig with its marker and 1-σ ellipse at the named
  times; rows before the zig are hidden because the layer's pre-zig states are undetermined.
  Keep each figure under about 200 KB; no raster images.
- **Data for figures** is seeded and regenerable: the demo split in a post names its seed, count
  and ranges file, or the committed experiment it came from. Never hand-edit a figure.
- A PR for a task without its slides post is not ready for review.

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
- Generator 0.6.0 (spec 006): `GenerateOptions.generator_version` defaults to 0.6.0; anything that
  regenerates a 0.5.0 fixture must pass the fixture's version (P0's `check_generator` did not, and
  `tma2-p0` was broken from PR 13 until the G0-MAN2 run found it). Pack headers carry no
  timestamp, so data regenerated at the generating commit (a `git worktree` at
  `generator_git_commit`) reproduce byte for byte; at any other commit only the header differs.
- The toy model's ONNX digest does not change with its golden inputs: conformance legs must also
  record `inputs_sha256` (SHA-256 over `in_*.bin` in name order), or stale results pass.
- To time a gate check while a long job runs, pause that job (`kill -STOP` its processes, then
  `kill -CONT`); stopping a `run_in_background` job's processes ends its wrapper shell (exit 147),
  but the job continues after `CONT` and writes its own outputs.
- MAN2 zig legs: ~40% of engagements have no usable zig leg (zig inside a target change, or the
  leg ends within 5 min); single-leg fits on MAN2 data must use `eval.rows.zig_leg` and mask or
  cut the rows before it, or the one-leg solve runs away (range 1e11 m).
- Docusaurus MDX: no `{...}` in prose (it is a JS expression); `scripts/data_dictionary.py`
  escapes `<` and braces outside code spans.
- Provenance is read before any output is written: a CLI that checks `git status` after writing
  into an untracked experiment folder always records `git_dirty: true` (`tma2-gs` did, fixed in
  e648f8b). Workflows must keep downloaded tables and checkpoints outside the checkout
  (`RUNNER_TEMP`), or every job records a dirty tree.
- Container restarts kill local background jobs (several per hour on 5 Nov): run anything over a
  few minutes on CI (`score.yml`, `segment.yml`, `glr-confirm.yml`), not in the session.
- A segmentation is not a function of its scenario alone: the physics-layer batch is padded to
  the longest scenario in the chunk (`r_max`, CHUNK = 16 in `cli/segment.py`), and last-bit cost
  changes can flip a near-threshold acceptance (Gate S panel round 2: ordinal 25 alone differs
  from 25–26). Reproduce a CI segmentation with the plan's ordinals and shards.
- Never edit or commit in the checkout while a gate run reads it: provenance is read once at
  launch and modules load lazily, so a mid-run change goes unrecorded. Run long scorings from a
  `git worktree` at the commit (pass absolute data paths).
- An open transition's state is decided at acceptance: anything a later close refines (C's
  start polish) must not reach prefixes before the close (FR-002; `Transition.start_at`).
- onnxruntime has no double `Conv`: the evidence network exports each convolution as a MatMul
  per tap (`segment/evidence_export.py`, `MatMulNet`), checked against torch.
- Training with torch on 4-core runners: `set_num_threads(1)` per worker is faster for L's
  per-prefix CRF loss (24 ms per prefix) than 4 threads.
- Semi-Markov truth paths: several lattice paths can agree equally with the truth codes; take the
  lexicographic maximum on (agreement, zero-evidence score), or the CRF loss starts near 2,000
  nats from an arbitrary path (`segment/crf.py`, `truth_path`).
- Gate 2 (spec 007): untrained E must equal C end to end. Write E's prediction rows in double:
  float32 rows put a 1e-7 bias into G2-d's paired E − C comparison.
- Decision tables bind a digest of the Gate 2 plan's `c` block, not the whole plan, because the
  plan names the tables' results branch (a circular digest otherwise).
- `tma2-dtables` and `tma2-g2predict` re-run C in `tma2-segment`'s chunks (16, padded to the
  longest) so they reproduce its segmentation file; `c_mismatch_rows` in the tables' header
  records any difference.
- C's GLR nominations divide by σ: noise-free (σ = 0) data needs search-only parameters.
- The full test suite takes about 10 minutes (C on fixture scenarios in the Gate 2 tests).
- Run `uv run ruff check .` (the whole repo, as CI does), not just `src tests`: `scripts/research`
  is linted too.
- E-s's learned evidence is mostly a veto at the ownship zig and E-w's weights mostly a recency
  profile (Gate 2 panel): test any learned component against the classical rule it might be
  before claiming learning, and register that control before its result exists.
- Early stopping that keeps epoch 0 makes a shuffled control equal to the untrained model, so its
  rule cannot fail: score the last-epoch shuffled weights too (Gate 2 panel).
- The scorer (`tma2-gs`/`tma2-g2`) re-solves C, one leg, the oracle and GLR + confirm, so a
  re-score on another CPU family is not byte-identical (Gate 2: C up to 6e-4 relative, 21 one-leg
  rows switch finite/runaway; G2-d moved 1.4e-5). Compare estimators within one scoring run's
  `errors.npz` (`scripts/research/g2_paired_gaps.py`), or re-score on the gate's CPU family.
- Calibration (spec 008): what gets scaled must not read the truth. The feature cache's `usable`
  rows need a finite NEES (truth) for training; `tma2-g3predict` and the export scale by
  `scalable` (plausible, `cov_ok`, finite sds) instead.
- `setup-uv` downloads uv from GitHub releases on every job; a wide matrix can hit 504s. Re-run
  the failed jobs (`rerun_failed_jobs`) once the run completes; nothing in the code is wrong.
- `.gitignore`'s `data/` also matched `src/tma2/data/` (now excepted): after adding a file, check
  `git status --ignored` before trusting a green local run.
- Calibration lessons (Gate 3 panel): choose design settings on tuning ordinals only, never on
  scoring rows; train on the errors the gate scores (a linearised course error cannot see a
  course flip); a scale-only calibration keeps the solve's near-singular correlations; a Gaussian
  sd for course above ~90° is a vacuous statement; the `settled` slice is defined from the truth.
- Gate 4 panel: a shuffled control that permutes errors but keeps the sds tests a null the
  temperature already rejects; register a richer classical rule (a function of all the sds) and an
  encoder-only shuffle before claiming learning. A per-bin reliability point band of ±0.05 on
  about 800 rows is about 2.5 sampling sd: use an interval or a slope test. A 10-knot PAV map on
  2,000 rows caps P by noise at its top knot. Recalibrating P but not the density makes the
  statement contradict itself.
- 20 concurrent CI jobs: a 32-job prediction run blocks every other workflow's merge job until
  it drains; queue long runs one at a time when a result is waited on.
