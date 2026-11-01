# Feature Specification: Gate 1, a learned model on constant-velocity data

**Feature Branch**: `003-gate1-cv`

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "Spec 003: Gate 1 on constant-velocity data: the P0 entry conditions;
on-the-fly CV training data with several noise draws per truth, a validation split and a fresh
reserved test split; a small causal encoder whose heads give per-bearing weights, an initial state
and a covariance scale to the declared physics layer (no changepoints); CRB-normalised training
with implicit differentiation through the solve, sampled scored rows and a measured hour budget
per epoch; training on free GitHub runners with chained resumable jobs; three seeds and two
controls; Gate 1 scored exactly as SRD §5 against naive, batch least squares, the tuned EKF/IMM
and the oracle on the same rows; a pre-registered decision record and the agent panel; an ONNX
export of the trained model with cross-runtime conformance; site pages."

**SRD traceability**: SRD §3 (on-the-fly data, labels), §4 (encoder, heads, physics layer, loss,
controls, export, compute), §5 (references, metrics, statistics, Gate 1), §7 step 2, §8 (implicit
differentiation); constitution I–VI; spec-003 entry conditions in
`specs/002-references-physics-p0/tasks.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A model whose estimate comes from the physics layer, trained within budget (Priority: P1)

A researcher trains a model in which a small learned encoder decides how much to trust each
bearing and where to start the solve, and the declared physics layer computes the estimate. One
epoch over 10^5 scenarios fits in an hour on a free 4-core runner, so a full training run fits the
project's free compute.

**Why this priority**: Gate 1 is the first test of the project's thesis; without a model that
trains on the available compute there is nothing to gate.

**Independent Test**: Train for one epoch on 10^5 generated scenarios on a 4-core machine with
threads pinned; the epoch's wall time, peak memory and the loss before and after are recorded;
the estimate the model reports is the physics layer's output.

**Acceptance Scenarios**:

1. **Given** a model with untrained heads that output uniform weights and the classical grid
   start, **When** it predicts, **Then** its estimates equal the physics layer with trivial
   inputs (batch least squares) on the same rows.
2. **Given** the training configuration, **When** one epoch runs on a 4-core runner, **Then** it
   completes in under an hour and its duration and peak memory are recorded.
3. **Given** a batch, **When** the loss is differentiated, **Then** every learned parameter has a
   finite gradient, including through rows that are masked, invalid or degenerate.
4. **Given** the same seed and configuration, **When** training is repeated on the same CPU
   family, **Then** the weights are identical.

---

### User Story 2 - Training runs on free runners, resumably (Priority: P1)

A researcher pushes a plan branch; GitHub-hosted runners train each configuration in chained jobs
of at most six hours, checkpointing after every epoch with the optimiser state, resuming where the
last job stopped, and push the results to a results branch, without anyone watching.

**Why this priority**: Cloud sessions are reclaimed in hours; the owner chose free CPU runners;
training must survive both.

**Independent Test**: Push a short plan (two epochs, small data); the first job stops after one
epoch, the chained job resumes from the checkpoint, and the final weights equal those of an
uninterrupted run.

**Acceptance Scenarios**:

1. **Given** a plan branch, **When** it is pushed, **Then** training starts for every model in the
   plan and every job's duration is recorded.
2. **Given** a job that ends mid-run, **When** the next job starts, **Then** it resumes from the
   last epoch's checkpoint, and the result equals an uninterrupted run.
3. **Given** a finished plan, **When** results are pushed, **Then** they carry the dataset digests,
   the code commit and the run identity, and nothing merges automatically.

---

### User Story 3 - Gate 1 decided against the references on the same rows (Priority: P1)

A researcher scores the carried model on a fresh constant-velocity test split it has never seen,
beside naive, batch least squares, the tuned EKF and IMM and the oracle, on the same rows, and
the gate verdict follows the pre-registered criterion and is decided by the agent panel.

**Why this priority**: This is the gate; the SRD fixes its criterion and its consequence.

**Independent Test**: Run the Gate 1 command on the test split with the committed decision record;
the experiment record holds every estimator's metrics on the same rows, the scenario-clustered
intervals, the efficiency per slice and the machine verdict; the panel's rounds are recorded.

**Acceptance Scenarios**:

1. **Given** the committed decision record and the test split, **When** the gate runs, **Then** it
   refuses a test seed, plan or model that the record does not name.
2. **Given** σ = 1° test rows, **When** scored at zig + 5 min (range, course) and zig + 10 min
   (speed), **Then** the verdict is pass only if the model's median is within 1.1 × batch least
   squares on every metric with the scenario-clustered interval wholly below, its gross-error rate
   is at or below batch least squares', and its efficiency is at most 1.25 on the settled slices;
   fail if an interval is wholly beyond; otherwise inconclusive (one re-score on a larger fresh
   seed, then final).
3. **Given** the experiment, **When** it is written, **Then** naive, batch least squares, the EKF,
   the IMM and the oracle appear on the same rows, with efficiency per slice for every estimator.
4. **Given** the two controls, **When** scored on validation, **Then** they are reported beside the
   carried model and never carried.

---

### User Story 4 - Pre-registered before training (Priority: P1)

Before any training run, a decision record fixes the seeds, data, configurations, controls, the
rule that picks the carried weights among three training seeds, the gate rows and what happens if
the gate fails, so the result cannot shape the question.

**Why this priority**: Constitution V and the project's measurement discipline.

**Independent Test**: The decision record is committed before the plan branch is pushed; the gate
command checks that the record's commit is an ancestor of the training run's commit and that the
test seed was not used before.

**Acceptance Scenarios**:

1. **Given** a training run, **When** its results are scored, **Then** the decision record's commit
   precedes the run's commit.
2. **Given** the test seed, **When** the gate runs, **Then** no earlier experiment record in the
   repository names it.

---

### User Story 5 - The trained model is a portable artefact (Priority: P2)

A researcher exports the carried model, encoder and physics layer together, as one graph with
fixed window length and dynamic batch, plus weights and a manifest, and the same inputs give the
same outputs in the Python, browser and Java runtimes.

**Why this priority**: Constitution VI; P0 proved the harness on a toy model with eight unrolled
iterations and found that the production iteration count needs a loop construct.

**Independent Test**: Export the carried model; run the three runtimes on a golden batch; the
outputs agree with PyTorch to 1e-5 in double.

**Acceptance Scenarios**:

1. **Given** the carried model, **When** exported, **Then** the graph holds the full production
   iteration count without unrolling it (a loop), loads in each runtime in under a minute, and
   agrees to 1e-5.
2. **Given** that a loop construct proves infeasible in one runtime, **When** the export falls
   back, **Then** the fallback and its reason are documented and the conformance test still runs
   at the production iteration count.

---

### User Story 6 - Entry conditions from P0 met (Priority: P1)

The weaknesses P0's panel left for this spec are closed before any training: the covariance flag,
the backward pass, row exclusion, the export loop, and the P0 tooling follow-ups.

**Why this priority**: The panel made them conditions for spec 003.

**Independent Test**: The listed tests exist and pass; the tooling refuses the cases the panel
named.

**Acceptance Scenarios**:

1. **Given** a solution that passes within 1 m of ownship at any valid sample up to the row, or a
   scaled pivot within a small multiple of the ridge, **When** the layer runs, **Then** its
   covariance flag is false.
2. **Given** the physics-equals-least-squares check, **When** fed a crippled layer, a non-finite
   covariance or a lower-cost row with a different state, **Then** it fails.
3. **Given** an experiment folder outside `experiments/`, **When** a gate command runs, **Then** it
   refuses; an edit outside the folder or a commit during the run marks the record dirty.

---

### User Story 7 - Documented (Priority: P3)

A reader finds, on the site, how the model is built and trained (an algorithm note) and, after the
gate, a write-up of the result with the references beside it.

**Why this priority**: The project's site discipline; needed after the result, not before.

**Independent Test**: The model note and the write-up build on the site; the write-up quotes the
experiment record's numbers.

### Edge Cases

- Rows before the zig, or with a singular Cramér–Rao bound, are never scored or used in the loss.
- Rows whose covariance flag is false are excluded from the loss and reported separately in
  scoring.
- A scenario whose zig + 10 min lies beyond its window contributes no speed gate row (coverage is
  stated).
- A dropout at the gate row: the instantaneous estimate at that row uses bearings up to it.
- The learned initial state lands in a different basin from the grid start: the estimate is still
  the physics layer's solution from that start; gross errors count against the model.
- A model whose weights all saturate: the layer still solves; the result is scored as is.
- A training job killed mid-epoch: the next job restarts that epoch from the last checkpoint.
- The test split is scored once; an inconclusive verdict allows one re-score on a larger fresh
  seed named in a re-score decision record.

## Requirements *(mandatory)*

### Functional Requirements

**Entry conditions (from P0)**

- **FR-001**: The physics layer's covariance flag MUST also be false when the solved trajectory
  passes within 1 m of ownship at any valid sample up to the row, or when a Jacobi-scaled pivot is
  within a stated multiple of the covariance ridge; tested at the production iteration count.
- **FR-002**: The P0 physics-equals-least-squares check MUST fail on a non-finite covariance
  (only range ≤ 1 m counts as degenerate), MUST bound the states of rows where the layer reaches
  a lower cost, and MUST have a negative test with a crippled layer.
- **FR-003**: Gate commands MUST refuse an experiment folder outside `experiments/`; tests MUST
  show an edit outside the folder and a commit during a run mark the record dirty.
- **FR-004**: The at-scale IMM check MUST assert that gitma's header names the frozen IMM and that
  gitma's dataset names the expected generator commit; records MUST carry the commands that made
  their datasets and ran the conformance legs.

**Data**

- **FR-005**: Training data MUST be the CV variant (gitma generator 0.3.0 semantics: three ownship
  legs, across-the-line-of-sight zigs, σ ∈ {1°, 2°}, 0–10% dropouts, 10–40 min windows), generated
  on the fly from a declared training seed stream, so no training file is stored.
- **FR-006**: Each truth trajectory MUST be usable with several noise draws per batch: bearings
  re-drawn from the stored truth with a separate seeded stream, with the scenario's σ and dropout
  pattern; the draw is a pure function of (seed, scenario index, draw index).
- **FR-007**: The validation split (seed 302) and the test split (seed 303) MUST be files with
  committed digests; seed 303 is reserved for Gate 1, scored once (plus the permitted re-score on a
  further fresh seed), and recorded as used.

**Model**

- **FR-008**: The model MUST be an encoder of standard operators with a causal mask (the
  instantaneous variant), heads per timestep for per-bearing log-weights (bounded), an initial
  state and a covariance scale, and the declared physics layer with no changepoints, in double
  precision; the reported estimate MUST be the physics layer's output.
- **FR-009**: With untrained heads initialised to uniform weights and the classical grid start,
  the model MUST reproduce the physics layer with trivial inputs.
- **FR-010**: The model's hyperparameters MUST live in its configuration and manifest, not in code.

**Training**

- **FR-011**: The loss MUST be the squared errors of log range, vx and vy at scored rows normalised
  by the row's full-window Cramér–Rao bound, plus β-NLL (β ≈ 0.5) on the calibrated covariance,
  plus a down-weighted CRB-normalised loss on the initial-state head; weights are configuration.
- **FR-012**: Scored rows MUST be sampled per scenario per epoch (the gate rows zig + 5 min and
  zig + 10 min when present, plus random post-zig rows, about four in all), and rows before the
  zig, with a singular bound or with the covariance flag false MUST be excluded.
- **FR-013**: The backward pass through the physics layer MUST NOT unroll the iterations: it uses
  implicit differentiation at the solution (one Gauss–Newton step with gradient from the detached
  solution), whose gradient MUST be checked against finite differences of the converged solution.
- **FR-014**: One epoch over 10^5 scenarios MUST complete in under an hour on a 4-core runner with
  threads pinned; the measurement is recorded before the decision record.
- **FR-015**: Training MUST be deterministic for a seed on one CPU family, checkpoint after every
  epoch with the optimiser state, and resume to the same result.
- **FR-016**: Three training seeds MUST be run for the carried configuration, and the decision
  record MUST name the rule that picks the carried weights among them using validation only.
- **FR-017**: Two controls MUST be trained and reported on validation: (a) the same encoder with a
  direct regression head and the same loss, never carried; (c) the carried configuration on
  shuffled labels.

**Runs**

- **FR-018**: Plan branches `train/<id>` MUST start training on GitHub-hosted runners in chained
  jobs of at most six hours, resume from checkpoints, record every job's duration and CPU model,
  and push results to `results/<plan>-<run>`; nothing merges automatically.

**Gate**

- **FR-019**: A gate command MUST score the carried model on the test split at every post-zig
  timestep, beside naive, batch least squares, the tuned EKF and IMM (frozen on validation before
  training) and the oracle (on CV data, the physics layer with trivial inputs), all on the same
  rows, with efficiency per slice for every estimator.
- **FR-020**: The machine verdict MUST apply SRD §5's Gate 1 criterion with scenario-clustered
  paired bootstrap intervals and the pass / fail / inconclusive rule; the verdict is then decided
  by the agent panel and recorded with `decided_by`.
- **FR-021**: The gate command MUST refuse a decision record, plan, model or test seed that do not
  match, and a decision record that is not an ancestor of the training run.

**Export**

- **FR-022**: The carried model MUST export as one graph with fixed window length and dynamic batch
  holding the production iteration count as a loop (not unrolled), with weights and a manifest;
  the Python, browser and Java runtimes MUST agree with PyTorch to 1e-5 in double on a golden
  batch; if a loop is infeasible in a runtime, the fallback and its reason are documented and
  conformance still runs at the production count.

**Documentation**

- **FR-023**: The site MUST gain a model and training note, and after the gate a write-up with the
  experiment's numbers and the references beside them; new terms enter the glossary and the data
  dictionary regenerates for any schema change.

### Key Entities

- **Training plan**: the dataset seeds and digests, model configurations, seeds, epochs and the
  evaluation step for a plan branch.
- **Model configuration**: encoder size, heads, physics-layer settings, loss weights, rows per
  scenario, noise draws, optimiser; carried in the model's manifest.
- **Checkpoint**: weights, optimiser state, epoch, RNG state, best validation loss, lineage.
- **Decision record**: what is pre-registered (seeds, plan, configurations, controls, carried rule,
  gate rows, consequence), committed before training.
- **Experiment record**: manifest, metrics per estimator and slice, checks, verdict, review.
- **Model artefact**: the exported graph, weights and manifest, with conformance results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every P0 entry condition has a test that fails on the old behaviour and passes now.
- **SC-002**: With heads at their initial values the model's estimates equal batch least squares'
  on the fixture rows under P0's rule.
- **SC-003**: One epoch over 10^5 scenarios takes under an hour on a 4-core runner, measured and
  recorded with peak memory.
- **SC-004**: The implicit gradient agrees with finite differences of the converged solution to
  1e-4 relative on a test batch.
- **SC-005**: A resumed training run produces weights identical to an uninterrupted one.
- **SC-006**: The decision record is committed before the training run; seeds 302 and 303 appear in
  no earlier record.
- **SC-007**: The Gate 1 experiment record holds the model, naive, batch least squares, EKF, IMM
  and oracle on the same rows, the clustered intervals, efficiency per slice and a verdict decided
  by the panel.
- **SC-008**: The exported carried model loads in each runtime in under a minute and agrees with
  PyTorch to 1e-5 in double at the production iteration count.

## Assumptions

- The gated variant is the instantaneous (causal) one, because Gate 1's rows are scored at fixed
  times since the zig; the time-late variant is reported later.
- The backward pass is implicit because the unrolled one costs about 0.16 s and 72 MB per row
  (P0), which would put a 256-row batch at about 41 s and 18 GB.
- The forward pass uses 100 iterations, as P0 established from the grid start (about 6.7 ms per row
  in batches of 256 at four threads); fewer only if a pre-registered measurement shows equal
  results from the learned initial state.
- About four scored rows per scenario per epoch meet the hour budget at that cost; all post-zig
  rows are scored at evaluation.
- The EKF and IMM are re-tuned on the CV validation split with declared grids and frozen before
  training (SRD §5); on CV data the oracle equals the physics layer with trivial inputs.
- Seeds: validation 302, test 303, training stream 310; seeds 301–303 and 310 are then reserved.
- If Gate 1 fails, the SRD allows one pre-registered iteration, then stop and publish.
