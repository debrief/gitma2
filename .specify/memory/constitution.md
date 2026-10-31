# gitma2 Constitution

gitma2 is the second attempt at target motion analysis (TMA) from bearings alone with machine
learning. It inherits the question, the measurement discipline and the gate process of
[debrief/Gitma](https://github.com/debrief/Gitma) (constitution 1.3.0), and changes the stack and
the model philosophy as set out in `docs/research/` (notes 01–05) and the owner's decisions of
2026-10-31 recorded there.

## Core Principles

### I. Single Source of Truth for Types (NON-NEGOTIABLE)

- Every exchanged data type (scenario, track, observation, prediction, manifest, metrics record,
  decision record) MUST be defined once in LinkML under `schema/`, carried over from gitma's
  `schema/tma.yaml` and extended there.
- Pydantic models, JSON Schema and the data dictionary MUST be generated from that schema;
  hand-written equivalents are forbidden. Generated output is committed; CI MUST fail if stale.
- Every file read at runtime MUST be validated with the generated models.
- Files that gitma wrote (scenarios, predictions, manifests) MUST remain readable by gitma2 for
  every schema version gitma2 still supports; a breaking change bumps the schema's major version.

Rationale: gitma's committed scenarios, weights and results are gitma2's conformance oracle and
its baselines; the two repositories must keep exchanging files.

### II. Determinism and Reproducibility (NON-NEGOTIABLE)

- All randomness MUST come from seeded, counter-based or per-scenario PRNG streams keyed by a
  64-bit seed; unseeded randomness is forbidden. The same seed MUST reproduce the same scenario,
  and the same batch regardless of batch order or worker count.
- Stored floats MUST be float32-rounded at generation; −0 is stored as +0.
- Every dataset file and model artefact MUST carry the schema version, generator version, the
  generating commit and a content digest; mismatches are rejected.
- Training reproducibility is **statistical, verified by re-scoring**: every run records seeds,
  library versions, device, thread count and data digests in its manifest; the committed weights
  are the artefact of record; a verdict is reproduced by re-scoring the frozen weights (digest
  bound), never by re-training. Scoring MUST be deterministic given the weights and the data.
- Every package MUST have a golden-file test: fixed seed in, byte-identical output out. The
  generator's golden files include scenarios regenerated from gitma's committed files, equal
  after float32 rounding.
- Training data MAY be generated on the fly from a seed; evaluation splits (validation, test,
  held-out) MUST exist as files with committed digests.

Rationale: a go/no-go verdict is worthless if the experiment behind it cannot be re-run, and
GPU-class training is not byte-reproducible, so the proof moves to the frozen artefact.

### III. Physics Does the Numerics, Learning Does the Judgement

- The estimate reported by a gitma2 model MUST come from a declared, differentiable physics layer
  (a batch or recursive bearings-only estimator written in ordinary tensor operations, with a
  fixed number of iterations and no data-dependent control flow), whose equations its algorithm
  note states exactly. A learned component supplies the inputs that physics cannot know:
  segmentation (when the target manoeuvred), measurement weights, initialisation, priors and
  calibration.
- A model whose output is a direct regression from a network MAY be trained only as a declared
  control, never as a carried model.
- The physics layer alone, with oracle inputs, MUST be scored as the ceiling of every design, and
  with trivial inputs (no segmentation, uniform weights) MUST reproduce batch least squares to
  float32 precision. These two references sit beside every model result.
- Models use standard operators only (dense, attention, normalisation, elementwise maths,
  matrix products, `atan2`), so the whole model, physics layer included, exports to one portable
  graph (principle VI).

Rationale: gitma showed that a recurrent regressor learns TMA judgement but stalls about 3 × the
Cramér–Rao bound on numerics; batch least squares is at the bound and knows nothing. The open
question is whether a learned component can close the gap to the oracle, not whether a network
can reinvent least squares.

### IV. Honest Measurement

- No model result MAY be reported without, on the same rows: the naive baseline, batch least
  squares, the re-tuned tracking filter reference (IMM and EKF, tuned on validation with declared
  grids and frozen), and the physics layer's oracle ceiling.
- Metrics MUST be medians and 90th percentiles with gross-error rates, overall and sliced by
  range band, zig angle, noise σ, time since zig and time since the last manoeuvre; and
  **statistical efficiency** (error relative to the per-scenario Cramér–Rao bound) MUST be
  reported per slice, so an approximation floor is visible as a flat efficiency.
- Intervals are paired, scenario-clustered bootstraps; a gate passes only when the whole interval
  and the point meet the limit, fails when the interval lies wholly beyond it, and is otherwise
  inconclusive (one re-score on a larger fresh seed, then final).
- Every carried configuration is trained with at least three seeds; the spread is reported and
  the carried weights are named in advance by rule (for example the median seed on validation).
- Normalisation statistics MUST be computed from inputs only; a shuffled-label control MUST score
  at naive level; a time-late variant MUST score at least as well as its causal counterpart.
- What is scored on a test split is declared, with a forecast, in a decision record committed
  before training; test seeds are fresh for every look; a validation rule stops a phase before
  the test split is touched. Exploration on validation is otherwise unrestricted and recorded.

Rationale: TMA failure modes are heavy-tailed, the main risk is a model that learns the
generator's priors, and gitma's single-seed, one-lever-at-a-time record could not separate a
lever's effect from initialisation noise.

### V. Fail Fast Through Gates

- Work proceeds through gates defined in `docs/SRD.md`: a pipeline gate (the Python generator and
  references reproduce gitma's committed outputs; the physics layer recovers noise-free truth)
  before any training; **Gate 1** on the constant-velocity problem (within 1.1 × batch least
  squares on every metric and below its gross-error rate); **Gate 2** on the manoeuvring problem
  (below the re-tuned IMM overall, within 1.1 × batch least squares on settled rows, and at least
  half of the gap from plain least squares to the oracle ceiling recovered).
- No training MAY begin until the pipeline gate passes. A gate's follow-on for each outcome is
  fixed in its annex before the result is known.
- Gate verdicts are taken by the agent review panel (Governance), never by a casting vote.

Rationale: the project exists to answer one question cheaply, not to build a product.

### VI. Portable Artefact, Not Portable Stack

- The training stack is Python (PyTorch for models, NumPy/numba for the generator and reference
  estimators); it need not port.
- Every carried model MUST export to a single ONNX graph (fixed window length, dynamic batch,
  standard operators only, no custom ops) plus safetensors weights and a JSON architecture
  manifest, and the algorithm note MUST state the physics layer's equations so that a port can be
  written by hand.
- CI MUST run a conformance test on a golden batch across ONNX Runtime for Python, the browser
  (WASM) and Java, agreeing with the training framework to 1e-5; a model that does not pass is
  not carried.
- Browser demos run the exported graph in ONNX Runtime Web; WebGPU is an optimisation, never a
  requirement.

Rationale: the owner's requirement is that trained structure and weights transfer across diverse
technologies; gitma's one-codebase approach bought that at a tenfold cost in training throughput
and tied the model family to tfjs's operator support.

## Technical Constraints

- Python 3.12+, `uv`-managed; PyTorch 2.x; NumPy and numba; LinkML for schema generation;
  `pytest` with golden-file tests; `ruff` and `mypy --strict` clean; no untyped public functions.
- Training runs on free GitHub-hosted 4-core CPU runners (owner decision 2026-10-31): models
  stay small enough for one epoch over 10^5 scenarios in well under an hour; chained ≤ 6 h jobs
  with per-epoch checkpoints; a plan branch (`train/<id>`) names the dataset seed, generator
  version, digests and configuration, and results go to `results/<plan>-<run>` branches. Nothing
  merges automatically.
- Frame and units as gitma: flat-earth Cartesian, x east, y north, metres; bearings true,
  clockwise from north, radians internally; speeds m/s, knots only for reporting; the generator
  implements gitma's generator 0.3.0 (constant-velocity target, three legs) and 0.5.0
  (0–3 course changes, one speed change) semantics before any new realism.
- Scope: single target, Gaussian bearing noise and dropouts, ownship navigation exact; anything
  beyond `docs/SRD.md` §1 requires an SRD amendment first.
- Each pipeline stage is a separate CLI reading and writing files; `sim` and reference estimators
  are plain functions over arrays.
- The repository is public: nothing above OFFICIAL, mock data only, no real-world provenance.

## Development Workflow

- Every change lands via a PR against `main`; no direct pushes.
- CI on each PR MUST run lint, type check, unit and golden-file tests, schema regeneration check,
  ONNX conformance (when a model exists) and the site build; all MUST pass before merge.
- A PR that adds a concept, data type, algorithm or result MUST add or update the matching page
  under `site/` (glossary, data dictionary regeneration, algorithm note or blog post). Reviewers
  may block on a missing page.
- Each gate produces an `experiments/<id>/` folder (manifest, seeds, metrics, verdict,
  `review.md`) and a blog post that reads its own result critically.
- Feature work follows the Spec Kit flow (specify → plan → tasks → implement); each spec MUST
  cite the SRD section(s) it implements and MUST pass the constitution check in its plan.

## Governance

- This constitution governs development practice; `docs/SRD.md` governs requirements. Where
  they conflict, raise it and amend one of them; never silently pick.
- Amendments are made by PR that updates this file, states the version bump and its rationale,
  and updates `AGENTS.md` if agent guidance changes. Versioning is semantic: MAJOR for removing
  or redefining a principle, MINOR for adding a principle or materially expanding guidance, PATCH
  for clarifications.
- Every PR review MUST check compliance with the principles above; any justified exception is
  recorded in the PR description.
- Gate verdicts are taken by an **agent review panel**, not by humans: at least five independent
  AI reviewers with distinct specialities (TMA geometry, estimation and numerics, evaluation
  statistics, reproducibility, red team) review the gate evidence and return approve,
  approve-with-findings or reject with severity-tagged findings. Every blocker and major finding
  MUST be fixed or answered with evidence, and the panel is re-invited until no reviewer rejects
  and no blocker or major finding stays open. The record is committed as
  `experiments/<id>/review.md`, and the verdict's `decided_by` names the panel round.
- Owner decisions that change the plan (compute, stack, first target, schema, process) are
  recorded in `docs/research/04-proposal.md` §6 or a later decision record before work follows
  from them.
- **The owner is not a blocker** (amended 1.1.0, 2026-10-31). Agents proceed from the documents:
  stated defaults are adopted and recorded; undocumented choices are made, stated in the PR and
  left to review; gate verdicts come from the panel; a follow-on the SRD leaves to the owner is
  proposed with a recommended default and adopted if unopposed by the next spec. Only the
  owner-only list in `AGENTS.md` (spending or new accounts, SRD §1 scope, classification, gate
  criteria after a result, deleting committed records, publishing elsewhere) waits for the owner.
  An agent may merge its own PR when CI is green and a review agent or the panel has approved;
  SRD, annex and constitution amendments are merged by the owner, or by the agent after two
  working days without objection.
- Runtime guidance for agents lives in `AGENTS.md`.

**Version**: 1.1.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31
