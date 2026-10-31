# Feature Specification: References, Physics Layer and Gate P0 (foundations, part 2)

**Feature Branch**: `002-references-physics-p0`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Spec 002, foundations part 2: reference estimators (naive, batch
least squares, EKF, IMM) ported from gitma and checked against its outputs; the per-scenario
Fisher information and Cramér–Rao bound; the physics layer (a differentiable
piecewise-constant-velocity bearings-only batch solve with fixed iterations) that equals batch
least squares with trivial inputs and is the oracle ceiling with truth segmentation; ONNX export
and cross-runtime conformance; evaluation basics (metrics, slices, efficiency, clustered
bootstrap, settled rows, G5 rows); gate P0 with its experiment record and panel; algorithm notes."

**SRD traceability**: SRD §4 (model requirements: physics layer, loss inputs), §5 (references,
metrics, efficiency, statistics, gate P0), §6 (architecture), §7 step 1–2; constitution III
(physics does the numerics), IV (honest measurement), V (gates), VI (portable artefact).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - gitma's references, reproduced (Priority: P1)

A researcher runs the gitma2 batch least-squares solver, EKF and IMM on a gitma dataset and gets
the same per-timestep estimates gitma's tools produce, so every later comparison with gitma's
reference numbers (classical at the Cramér–Rao bound; the frozen phase-4 IMM) is on identical
estimators.

**Why this priority**: The whole measurement discipline rests on the references; a drifted port
would make gitma2's ratios incomparable with gitma's record.

**Independent Test**: Run the three estimators on the seed-777 fixtures and compare row by row
with prediction files produced by gitma's `tma-solve --per-timestep`, `tma-track --filter ekf`
and `tma-track --filter imm` (frozen phase-4 settings) on the same files; all rows equal under
the one-ulp float32 rule, including the `converged` flags and the re-initialisation points.

**Acceptance Scenarios**:

1. **Given** the phase-4 seed-777 test split and gitma's per-timestep least-squares prediction
   file, **When** gitma2's solver runs in per-timestep mode, **Then** every row's range, course,
   speed, position and converged flag equals gitma's under the conformance rule.
2. **Given** the same split and gitma's EKF and IMM prediction files at the frozen reference
   settings, **When** gitma2's trackers run, **Then** every row equals gitma's under the
   conformance rule, including rows after a divergence re-initialisation.
3. **Given** a noise-free dataset, **When** the final-mode solver runs, **Then** range is
   recovered to within 0.1% on every scenario (gitma's G0 check 1).
4. **Given** a prediction file written by gitma2, **When** gitma's evaluation tooling reads it,
   **Then** it parses and scores it (format interchangeable).

---

### User Story 2 - The physics layer is least squares, and the oracle ceiling (Priority: P1)

A researcher calls the physics layer with "trivial" inputs (no changepoints, uniform bearing
weights, the classical grid start) and gets batch least squares' answer; calls it with the true
manoeuvre spans and kinds and gets the oracle-ceiling estimate measured in the research note; and
can differentiate its output with respect to every learned input.

**Why this priority**: Constitution III makes the physics layer the source of every estimate;
proving it equals least squares and reproduces the oracle ceiling is what makes Gates 1 and 2
meaningful.

**Independent Test**: Trivial-input equality with the ported solver to float32 on the fixtures;
oracle-ceiling ratios against the frozen IMM on a 10^5 MAN validation split within the research
note's intervals; finite-difference gradient checks on changepoint weights, bearing weights and
initial state agree with autograd.

**Acceptance Scenarios**:

1. **Given** any fixture scenario and row, **When** the physics layer runs with trivial inputs
   and the same number of iterations as the solver took, **Then** its state equals the ported
   solver's to float32 precision, and its covariance equals σ²(JᵀJ)⁻¹.
2. **Given** a 10^5-scenario MAN validation split (seed from 301, digest pinned), **When** the
   layer runs with truth segmentation and with the speed-continuity prior, **Then** the median
   range ratio to the frozen IMM over G5 rows lies within [0.486, 0.574] and the settled-row ratio
   within [0.450, 0.557] (the research note's 97.5% intervals), and without the speed prior
   within [0.595, 0.687] and [0.508, 0.628].
3. **Given** soft changepoint weights strictly between 0 and 1, **When** the output is
   differentiated with respect to them, the bearing log-weights and the initial state, **Then**
   autograd gradients match central finite differences to 1e-4 relative.
4. **Given** a batch of scenarios of different lengths, **When** the layer runs, **Then** every
   scenario's result is identical to running it alone (masking is exact).

---

### User Story 3 - Portable artefact proven before any model exists (Priority: P2)

A developer exports the physics layer with a toy encoder to the portable graph format and runs
the same golden batch in the Python runtime, the browser runtime and the Java runtime; all agree
with the training framework.

**Why this priority**: Constitution VI; discovering an export gap after training would waste the
owner's compute and the project's time.

**Independent Test**: CI job exports the toy model, runs it under the three runtimes on a committed
golden batch, and asserts agreement to 1e-5; the Java leg is skipped with a visible reason if its
runtime cannot be installed on the runner.

**Acceptance Scenarios**:

1. **Given** the toy model and a golden batch of 8 scenarios, **When** exported and run in the
   Python runtime, **Then** outputs agree with the framework to 1e-5.
2. **Given** the exported graph, **When** run in the browser runtime (WASM) under an automated
   browser, **Then** outputs agree to 1e-5 and the run completes in under 10 s.
3. **Given** the exported graph, **When** run in the Java runtime, **Then** outputs agree to 1e-5,
   or the job reports "Java leg deferred: <reason>" and the harness remains in place.
4. **Given** the export, **When** its operator set is listed, **Then** it contains only standard
   operators (no custom ops, no data-dependent loops).

---

### User Story 4 - Score estimators the gitma way, plus efficiency (Priority: P2)

A researcher scores any prediction file against truth and gets gitma's metrics (median and P90 of
range, course and speed error, gross-error rate), sliced by range band, zig angle, noise σ, time
since zig and time since the last manoeuvre, plus **efficiency** (error relative to the Cramér–Rao
bound), with scenario-clustered paired bootstrap intervals; settled and G5 rows follow gitma's
definitions.

**Why this priority**: Every gate from here on uses these numbers; efficiency is the diagnostic
gitma lacked.

**Independent Test**: Score gitma's fixture prediction files with gitma2 and compare the medians
and P90s with gitma's `tma-eval` output on the same files; efficiency of batch least squares on
settled rows at σ = 1° lies near 1 (0.8–1.3) on a noise-only dataset.

**Acceptance Scenarios**:

1. **Given** gitma's prediction files and truth for the fixtures, **When** scored, **Then** the
   overall and sliced medians/P90s equal gitma's to 1e-9 relative.
2. **Given** the per-scenario Cramér–Rao bound, **When** least squares is scored on settled rows,
   **Then** its efficiency on speed is between 0.8 and 1.3 at σ = 1° (it is "at the bound").
3. **Given** two estimators' rows, **When** the paired clustered bootstrap runs with seed
   20261011 and 2,000 resamples, **Then** the interval is reproducible and matches gitma's
   bootstrap on the same inputs.

---

### User Story 5 - Gate P0 decided and recorded (Priority: P1)

The agent review panel receives an experiment record showing: generator conformance (spec 001),
reference reproduction, physics layer equals least squares, noise-free truth recovery, and the
oracle ceiling reproduced; it returns a verdict that is committed with `decided_by` naming the
round.

**Why this priority**: Constitution V: no training before P0 passes.

**Independent Test**: `experiments/<date>-p0/` contains manifest, metrics, verdict with
`decided_by`, and `review.md` with at least five reviewers' rounds; `tma2-p0` reproduces the
metrics from the manifest.

**Acceptance Scenarios**:

1. **Given** the implemented checks, **When** `tma2-p0` runs, **Then** it writes the experiment
   folder and a verdict that passes only if every check passes.
2. **Given** the record, **When** the panel reviews, **Then** every blocker and major finding is
   fixed or answered and the final round approves.

---

### User Story 6 - Documented algorithms (Priority: P3)

A reader finds on the site an algorithm note for the physics layer (its exact equations, inputs,
iteration, covariance), for batch least squares, the EKF/IMM and the Cramér–Rao bound, and
glossary entries for the new terms.

**Independent Test**: The site builds with four algorithm notes linked from the glossary; the
physics-layer note's equations match the NumPy reference implementation used in the golden test.

---

### Edge Cases

- A scenario where least squares does not converge or hits the plausibility bound: the physics
  layer with trivial inputs must report the same `converged = false` semantics (a flag, not a
  silent answer).
- Changepoint weights of exactly 0 or 1 must reduce to "no knot" and "hard knot" respectively,
  with the ridge prior disappearing or binding fully.
- A knot in the last few samples (a leg too young to observe): the ridge prior must keep the
  solution finite; the covariance must reflect the unobservability (large, not NaN).
- Zero valid bearings in the window prefix (all dropouts): no estimate, flagged.
- The Cramér–Rao bound is singular before the zig (one leg): efficiency is undefined there and
  must be reported as such, not as 0 or ∞.
- Prediction files from gitma with `p_manoeuvre` or Gaussian columns (schema 0.14–0.16): must
  read and score; the extra columns are ignored.
- The IMM's re-initialisation after divergence depends on the batch solution at that sample;
  conformance must cover scenarios where it fires.

## Requirements *(mandatory)*

### Functional Requirements

**References**

- **FR-001**: The system MUST provide the naive baseline (training-set means of log range,
  course vector and speed) and batch least squares (Levenberg–Marquardt on a constant-velocity
  target, 12 × 8 × 3 grid start, 50 iterations, 1e-12 relative stop, plausibility bounds 25 m/s
  and 100 km, final and per-timestep modes with warm starts and gitma's restart rule) that
  reproduce gitma's prediction files under the conformance rule.
- **FR-002**: The system MUST provide the Cartesian EKF (white-noise acceleration) and the IMM
  (CV + coordinated turn, Markov switching, wrapped innovation, Joseph-form update, batch-solution
  initialisation at `zig_index`, divergence re-initialisation, `p0_scale` and `r_scale`) with the
  same parameters as gitma's `tma-track`, reproducing gitma's prediction files.
- **FR-003**: Estimators MUST write and read prediction files in gitma's format
  (`PredictionHeader` with `dataset_digest`, one `Prediction` per scenario with `rows`), so files
  are interchangeable in both directions.
- **FR-004**: CLIs `tma2-naive`, `tma2-solve` and `tma2-track` MUST mirror gitma's options and
  exit codes.

**Cramér–Rao bound**

- **FR-005**: The system MUST compute, per scenario and per scored timestep, the Fisher
  information of the constant-velocity state from the valid bearings up to that timestep at the
  true trajectory and σ, and the resulting bounds on range, course and speed error (delta
  method), reporting singular cases explicitly.

**Physics layer**

- **FR-006**: The physics layer MUST solve the piecewise-constant-velocity bearings-only problem
  over bearings 0..k: parameters = position at window start and one velocity per segment;
  residuals = wrapped bearing differences divided by σ, weighted by per-bearing weights; a ridge
  prior between consecutive segment velocities whose strength is the segment's changepoint
  weight; a soft speed-continuity prior across segments whose strength is a per-knot weight; a
  fixed number of damped Gauss-Newton iterations from a given initial state; no data-dependent
  control flow.
- **FR-007**: With trivial inputs (changepoint weights 0, uniform bearing weights, the classical
  grid start) it MUST equal the ported batch least squares started from the same grid at the same
  row on every scored fixture row: the plausibility flags agree; the layer's cost is never above
  the solver's by more than 1e-9 relative where the solver converged; where the costs agree and
  both are plausible, the state agrees to 1e-4 relative on determined rows (range sd < half the
  range) and to 1e-2 of the row's own standard deviation on every row; and its covariance MUST
  equal σ²(JᵀJ)⁻¹. *Amended in P0 panel round 1* (the SRD criterion, "equals batch LS", is
  unchanged): the earlier wording, float32 on every row against the warm-started per-timestep
  rows with "the solver's iteration count", cannot hold for any two correct solvers on
  undetermined rows, which stop at different points of equal cost along a flat direction, and the
  machine check had tested 1e-4 on a sample of 59 rows. The owner may overrule.
- **FR-008**: With truth segmentation (knots at span starts and ends, kinds from the spans) it
  MUST reproduce the oracle-ceiling ratios of `docs/research/05` within their intervals on a
  10^5 MAN validation split.
- **FR-009**: The layer MUST be differentiable with respect to changepoint weights, speed
  weights, bearing weights and the initial state (gradient checks), and exact under masking.
- **FR-010**: A NumPy reference implementation of the same equations MUST exist and agree with
  the tensor implementation to 1e-6; the algorithm note states the equations it implements.
- **FR-011**: The layer MUST output a `converged`/plausibility flag with gitma's semantics.

**Portable artefact**

- **FR-012**: The physics layer with a toy encoder MUST export to a single standard-operator
  graph (fixed window, dynamic batch, no custom ops), and a CI job MUST compare the Python,
  browser (WASM) and Java runtimes against the framework on a committed golden batch to 1e-5; the
  Java leg MAY be deferred with a stated reason if its runtime cannot be installed.

**Evaluation**

- **FR-013**: The system MUST compute gitma's metrics record (median and P90 of relative range
  error, course error in degrees, speed error in knots; gross-error rate = range error > 50% or
  no estimate) overall and sliced by range band, zig angle, σ, time since zig and time since the
  last manoeuvre end, and MUST add efficiency per slice (median error / median CRB).
- **FR-014**: The system MUST implement the scenario-clustered paired bootstrap (2,000 resamples,
  seed 20261011, configurable level) and gitma's settled-row and G5-row definitions.
- **FR-015**: `tma2-eval` MUST score any prediction file against truth and write metrics as CSV
  and JSON in gitma's layout.

**Gate P0**

- **FR-016**: `tma2-p0` MUST run every P0 check (generator conformance digests, reference
  reproduction, physics layer equals least squares, noise-free recovery, oracle ceiling) and write
  `experiments/<id>/` with manifest (commit, digests, seeds, versions), metrics and a verdict
  whose `decided_by` is set by the panel round.
- **FR-017**: The P0 record MUST be reviewed by the agent panel (five specialities) and the
  review committed as `review.md`.

**Site**

- **FR-018**: Algorithm notes for the physics layer, batch least squares, EKF/IMM and the
  Cramér–Rao bound, and glossary entries (changepoint weight, ridge prior, speed-continuity
  prior, efficiency, Fisher information, G5 rows) MUST be added.

### Key Entities

- **Prediction / PredictionHeader / PredictionRow**: gitma's schema types; one file per
  estimator per split, `dataset_digest` binding it to the truth file.
- **Fisher information record**: per scenario, per row: the 4 × 4 information matrix and the
  derived bounds (range, course, speed), plus a singular flag.
- **Physics-layer inputs**: bearings, validity, ownship positions, σ; changepoint weights
  (per row), speed-continuity weights (per row), bearing log-weights (per row), initial state;
  **outputs**: state at row k, covariance, converged flag.
- **MetricsRecord / CurvePoint / GateVerdict / ExperimentManifest**: gitma's schema types,
  extended with an `efficiency` field (schema minor bump, generated types regenerated).
- **P0 experiment**: `experiments/<date>-p0/` with manifest, metrics, verdict, review.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Batch least squares, EKF and IMM rows equal gitma's prediction files on the seed-777
  fixtures under the conformance rule, with the count of one-ulp residuals reported. At scale
  (added in P0 panel round 1, when gitma's `tma-track` output on the P0 split is supplied) the
  IMM's flags are identical and at most 0.1% of rows differ by more than 1e-4.
- **SC-002**: The physics layer with trivial inputs equals the ported solver on every fixture row
  as FR-007 defines it; its NumPy reference agrees to 1e-6; gradient checks pass to 1e-4; every
  gradient is finite, including on masked rows.
- **SC-003**: Oracle-ceiling ratios on the 10^5 split fall inside the research note's intervals
  for all four range checks (with and without the speed prior, all and settled rows).
- **SC-004**: Exported graph outputs agree across Python and browser runtimes to 1e-5 on the
  golden batch; Java agrees or is deferred with a stated reason.
- **SC-005**: Metrics on gitma's fixture predictions equal gitma's to 1e-9 relative; least
  squares' settled-row speed efficiency at σ = 1° is within 0.8–1.3.
- **SC-006**: `experiments/<date>-p0/verdict.json` is `pass` with `decided_by` naming a panel
  round, and `review.md` records the rounds.

## Assumptions

- gitma's prediction files for the fixtures are produced once from the local gitma checkout at
  `d0aec60` (`tma-solve --per-timestep`, `tma-track --filter ekf --sigma-a 0.03 --p0-scale 4
  --r-scale 8`, `tma-track --filter imm --sigma-cv 0.01 --sigma-ct 0.03 --sigma-omega 0.01
  --switch 0.001 --p0-scale 4 --r-scale 8`) and committed as fixtures.
- The oracle check's validation split is 10^5 scenarios at a fresh seed from 301 (not 10^6), to
  fit CI; generated once, digest pinned; the frozen IMM is run on it in CI (minutes, numba).
- PyTorch (CPU) enters the dependency set here for the physics layer only; models come in spec
  003. The physics layer's NumPy reference stays the documentation of record.
- Schema bump 0.16.0 → 0.17.0 adds `efficiency` (and the CRB fields) to the metrics record;
  gitma files remain readable (minor bump).
- The ONNX Java leg uses Temurin from the standard setup action; if the runtime package cannot be
  fetched the job prints the reason and the leg is deferred, recorded in the P0 record.
- Agent decisions under AGENTS.md (Autonomy): the above, plus keeping gitma's restart rule and
  plausibility bounds verbatim rather than "improving" them, so that the reference stays gitma's.
- No owner-only item is touched.
