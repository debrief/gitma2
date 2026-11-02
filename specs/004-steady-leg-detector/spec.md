# Feature Specification: Steady-leg detector and Gate D

**Feature Branch**: `004-steady-leg-detector`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Spec 004: steady-leg detector and Gate D. The Gate 1 follow-ups that
must precede further training (heads that cannot die, alive-unit and learnability checks, a
relative minimum improvement in early stopping, weights bound by digest, git_dirty in job records,
amendments in gate manifests, one median convention, one convergence definition); manoeuvring
data with a fresh validation split and test seed; a detector sharing the gitma2 encoder, with a
'now' head, soft changepoint weights and manoeuvre kinds that feed the physics layer; classification
losses with a tolerance and a held-leg weighting plus the downstream error of the physics-layer
solve as the primary objective; causal and time-late variants, three seeds each; CUSUM, GLR, the
IMM's mode probability and gitma phase 3b as controls; Annex A's metrics and Gate D with the
validation rule and the follow-on fixed in advance; an export of the detector with cross-runtime
conformance and a browser speed limit; a pre-registered decision record, the agent panel, site
pages."

**SRD traceability**: SRD Annex A §A.0–A.8 (problem, controls, metrics, design constraints, Gate D,
follow-on, defaults D1–D4); SRD §3 (data on the fly, labels), §4 (encoder, heads, physics layer,
compute, export), §5 (references, metrics, statistics), §7 step 3; constitution 1.2.0 I–VI; Gate 1
panel follow-ups (`specs/003-gate1-cv/tasks.md`, "Follow-ups from the Gate 1 panel").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Heads that cannot silently die (Priority: P1)

A researcher trains any gitma2 model knowing that a network that has stopped responding to its
input will be caught before it reaches a gate, unlike Gate 1, where every head of the carried
model ended with no active units and the pass meant only that the model reduced to batch least
squares.

**Why this priority**: Gate 1's panel made this a prerequisite for further training; a detector
that cannot learn would fail Gate D for an uninformative reason, or pass a check vacuously.

**Independent Test**: Train the detector briefly on a small set where its labels vary across rows;
measure the share of hidden units that respond to some input and how much each head's output varies
across rows; both must clear declared floors, and a deliberately dead model must fail the check.

**Acceptance Scenarios**:

1. **Given** the head architecture, **When** a head's output layer starts at zero, **Then** no
   hidden layer can become permanently inactive (no hidden unit whose gradient is zero for every
   input once it has gone negative).
2. **Given** a model trained for a few hundred steps on detector labels, **When** the learnability
   check runs, **Then** each head's outputs vary across rows above a declared floor and a model with
   constant outputs fails the same check.
3. **Given** early stopping, **When** the validation loss improves by less than the declared
   relative minimum, **Then** the epoch does not count as an improvement.

---

### User Story 2 - Records bind what was scored (Priority: P1)

A reviewer can show from the committed record alone which weights produced each prediction, whether
each training job ran from a clean tree, which amendments to the decision record applied, and why
each gross error was gross.

**Why this priority**: Gate 1's reproducibility review had to establish these by hand from git
history; Gate D adds a second learned artefact and more controls, so the record must carry them.

**Independent Test**: Score a gate with a prediction file made from different weights, or with an
amendment missing from the manifest; the gate command refuses. Inspect a job record and a gross-row
report; both carry the new fields.

**Acceptance Scenarios**:

1. **Given** checkpoint weights, **When** predictions are written and a gate is scored, **Then**
   the weights' SHA-256 appears in the checkpoint metadata, the prediction header and the gate
   manifest, and the gate refuses a mismatch or missing best weights.
2. **Given** a training job, **When** it finishes, **Then** its job record says whether the tree
   was dirty.
3. **Given** a decision record with amendments, **When** a gate is scored, **Then** each
   amendment's digest is listed in the gate manifest.
4. **Given** the gross-error check, **When** it is reported, **Then** every estimator is counted
   under one convergence definition and the gross rows are split by cause.
5. **Given** efficiency, **When** it is reported in checks and in metrics, **Then** both use one
   median convention.

---

### User Story 3 - A detector that finds manoeuvres without crying wolf (Priority: P1)

A researcher has a detector that, from bearings and ownship state alone, says at each timestep
whether a manoeuvre is in progress or has just begun, where earlier legs ended, and whether each
change was a course or a speed change, so that the physics layer can fit the target's track leg by
leg. It false-alarms on held legs in fewer than 5% of scored rows, where gitma's flag fired on
29–31%.

**Why this priority**: segmentation alone takes the piecewise solve from 1.15 × the IMM's median
range error to 0.64 × in the oracle experiment; the detector is the learned part of gitma2 that
must earn that.

**Independent Test**: On the manoeuvring validation split, run the trained detector at every
timestep and measure detection delay, miss rate, held-leg false alarms, kind accuracy,
segmentation F1 and calibration; feed its exported knots and kinds to the physics layer with
trivial weights and score the estimate.

**Acceptance Scenarios**:

1. **Given** a window up to timestep k, **When** the causal detector runs, **Then** it outputs the
   probability that a manoeuvre is in progress or began within the last 60 s, soft changepoint
   weights over every earlier timestep, and for each candidate changepoint the probability that it
   is a course change rather than a speed change.
2. **Given** the soft changepoint weights, **When** they are exported, **Then** the knots are the
   local maxima above the threshold fixed in the decision record, with their kinds.
3. **Given** the detector's outputs, **When** the physics layer is fed them, **Then** the estimate
   is the physics layer's, with trivial per-bearing weights, so the detector is credited only for
   segmentation.
4. **Given** a time-late variant over the whole window, **When** it is scored, **Then** it does at
   least as well as the causal variant.

---

### User Story 4 - The detector beats what an engineer would build without learning (Priority: P1)

A researcher compares the detector with CUSUM on the least-squares innovations, a windowed
one-versus-two-leg likelihood-ratio detector (GLR) and the IMM's mode probability, each tuned on
validation to the detector's own false-alarm rate, so every comparison is at a matched operating
point.

**Why this priority**: Annex A requires the detector to beat CUSUM and GLR; without matched
controls a lower delay could simply be a looser threshold.

**Independent Test**: Tune each control's threshold on validation to the detector's held-leg
false-alarm rate at its declared operating point; on the same rows report delay, misses and false
alarms for every detector; gitma phase 3b's flag numbers are reported from gitma's record.

**Acceptance Scenarios**:

1. **Given** the detector's declared operating point, **When** a control is tuned, **Then** its
   threshold is the one whose held-leg false-alarm rate on validation is closest to the detector's,
   and the tuned value is frozen in the decision record before the test split is scored.
2. **Given** the controls, **When** they run on the test split, **Then** they see the same rows,
   scenarios and timesteps as the detector.

---

### User Story 5 - Gate D decided as pre-registered (Priority: P1)

The project learns, from a fresh manoeuvring test seed scored once, whether the detector passes
Gate D: detection delay below the best control's at a matched false-alarm rate, no more misses,
held-leg false alarms wholly below 5%, a downstream estimate below the IMM's overall and within
1.1 × batch least squares on settled rows; with the follow-on for every outcome fixed before the
result.

**Why this priority**: Gate D decides what segments the data at Gate 2.

**Independent Test**: Run the gate command on the test split with the committed decision record,
plan, carried weights and controls; it checks every binding, computes every check with
scenario-clustered paired intervals at 97.5%, and writes the experiment record and the machine
verdict; the agent panel decides.

**Acceptance Scenarios**:

1. **Given** a decision record, plan, carried weights and test seed that do not match, **When** the
   gate runs, **Then** it refuses before scoring.
2. **Given** the scores, **When** Gate D is applied, **Then** it passes only if D-delay, D-miss,
   D-false, D-downstream-all and D-downstream-settled pass for at least one carried variant; it
   fails if every carried variant fails at least one; otherwise it is inconclusive.
3. **Given** validation results, **When** no variant meets every gated check's point and has no
   interval wholly beyond its limit, **Then** the test split is not scored.

---

### User Story 6 - Pre-registered before training (Priority: P1)

The decision record names, before any detector is trained: the seeds, the plan, the configurations,
the defaults D1–D4 with a reason each, the operating threshold and tolerance, the held-leg
weighting, the knot-export threshold, the carried rule, the controls' tuning rule and a forecast.

**Why this priority**: constitution IV; Gate 1 showed what a validation rule written for another
architecture costs.

**Independent Test**: The decision record's commit is an ancestor of every training job's commit,
and its digest is bound in the gate manifest.

**Acceptance Scenarios**:

1. **Given** the decision record, **When** training runs, **Then** every job records a commit
   descended from the record's commit, and the gate refuses otherwise.
2. **Given** every control and validation check, **When** it is written into the decision record,
   **Then** it is checked against the detector's architecture (a check that every physics-layer
   model passes or fails by construction is not used).

---

### User Story 7 - A portable detector (Priority: P2)

A developer runs the detector alone outside Python: in the browser, in Java and in Python's runtime,
on a 360-row window, with the same outputs to 1e-5, in under one second per window in the browser.

**Why this priority**: constitution VI; Annex A §A.4 requires the detector to run in the viewer.

**Independent Test**: Export the trained detector; run the conformance harness's three legs on a
golden batch; time a window in the browser leg.

**Acceptance Scenarios**:

1. **Given** the exported detector, **When** each runtime runs the golden batch, **Then** its
   outputs agree with the training framework to 1e-5.
2. **Given** the browser runtime, **When** it runs one 360-row window, **Then** it takes under one
   second.

---

### User Story 8 - Documented (Priority: P3)

A reader finds the detector's algorithm note, the glossary terms and a Gate D write-up that reads
its own result critically, as Gate 1's did.

**Why this priority**: constitution development workflow.

**Independent Test**: The site builds with the new pages; the write-up states what the result does
and does not show.

**Acceptance Scenarios**:

1. **Given** the site, **When** it builds, **Then** the algorithm note, glossary entries and
   write-up are present and linked.

### Edge Cases

- A scenario with no manoeuvre: every post-zig row is on a held leg; any alarm is a false alarm.
- Two manoeuvres closer together than the 60 s tolerance: each truth span is matched at most once;
  an alarm inside the overlap counts once, for the earlier span.
- A manoeuvre that starts before the ownship zig: it is detected only once bearings carry
  information about it; detection delay counts from its start and is reported as such.
- A manoeuvre near the window's end: a span whose end + 300 s lies beyond the window and that has
  no alarm is reported as unresolved, not as a miss.
- A speed change during a course change: the kind truth is the span's recorded kind; the physics
  layer's speed-continuity prior follows the predicted kind.
- Soft weights that produce more local maxima than the physics layer has knots: the highest are
  kept, and the count dropped is reported.
- Rows whose physics-layer covariance says the state is undetermined (before the zig): excluded
  from the downstream loss and reported separately in scoring.
- The IMM's own held-leg false-alarm rate below 5% on validation: D-false's limit becomes that
  rate (D3), and the decision record says so.
- A training job killed mid-epoch: the next job resumes from the last checkpoint.
- An inconclusive Gate D: one re-score on a larger fresh seed named in a re-score decision record,
  then final.

## Requirements *(mandatory)*

### Functional Requirements

**Gate 1 prerequisites**

- **FR-001**: Head architectures MUST NOT contain a hidden layer that can become permanently
  inactive in front of a zero-initialised output layer; the chosen form is stated in the algorithm
  note.
- **FR-002**: A test MUST train a model briefly on labels that vary across rows and assert that each
  head keeps a declared share of responsive hidden units and that its outputs vary across rows above
  a declared floor; a constant-output model MUST fail it.
- **FR-003**: Early stopping MUST count an epoch as an improvement only if the validation loss falls
  by at least a declared relative minimum.
- **FR-004**: The SHA-256 of the weights used MUST be recorded in the checkpoint metadata, every
  prediction header and the gate manifest; the gate MUST refuse a mismatch and MUST NOT fall back to
  non-best weights.
- **FR-005**: Every training job record MUST record whether its working tree was dirty.
- **FR-006**: Gate manifests MUST list every amendment to the decision record by digest.
- **FR-007**: Reported efficiencies MUST use one median convention in checks and in metrics.
- **FR-008**: Gross-error counting MUST apply one convergence definition to every estimator, and
  gross rows MUST be reported by cause (not converged, error over the gross limit).

**Data**

- **FR-009**: The detector MUST be trained and gated on the manoeuvring problem: generator 0.5.0
  semantics, phase-4 ranges, σ ∈ {1°, 2°}, 0–10% dropouts, 0–3 course changes, one speed change in
  30% of scenarios.
- **FR-010**: Training data MUST be generated on the fly from training seed 311 with seeded noise
  re-draws; the validation split (seed 304) and the test split (seed 305, reserved, scored once)
  MUST exist as files with digests pinned in the plan.
- **FR-011**: Per-timestep labels MUST be derived from the stored truth: the manoeuvre spans with
  their kinds, the 60 s "now" label, the held-leg and settled-row flags of the existing row
  definitions.

**Detector**

- **FR-012**: The detector MUST use the gitma2 causal encoder design, so a Gate 2 model can start
  from its weights, over the declared input channels (bearing sine and cosine, ownship position,
  course and speed, time, validity, mask, bearing rate and its validity flag, bearing-line
  intercept), with input scaling from fixed constants only.
- **FR-013**: The detector MUST output, at every timestep k: `p_change[k]`; `w_change[k, j]` for
  j ≤ k; `p_kind[k, j]` for every candidate changepoint.
- **FR-014**: Knot export MUST take the local maxima of `w_change` above the threshold fixed in the
  decision record, up to the physics layer's knot count, with the kind from `p_kind`.
- **FR-015**: A time-late variant over the whole window MUST be trained and carried alongside the
  causal one (D2), and MUST score at least as well.

**Training**

- **FR-016**: The training objective MUST include the downstream error of the piecewise
  physics-layer solve fed by the soft segmentation and kinds, with trivial per-bearing weights,
  normalised by each row's Cramér–Rao bound for the known manoeuvres, with gradients through the
  solve by implicit differentiation.
- **FR-017**: The objective MUST also include span-derived classification losses for `p_change`,
  `w_change` and `p_kind`, with the ±60 s tolerance and a held-leg weighting declared in the
  decision record.
- **FR-018**: A detector trained on the classification losses alone MUST be trained as a declared
  control and never carried.
- **FR-019**: Each carried variant MUST be trained with three seeds; the carried seed MUST be
  chosen by a rule named in the decision record.
- **FR-020**: One epoch over 10^5 scenarios MUST complete in under an hour on a free 4-core runner,
  measured on the runner and recorded.
- **FR-021**: Training MUST run on free GitHub-hosted runners through the existing plan-branch
  workflows, resumably, with results on results branches.

**Controls and references**

- **FR-022**: CUSUM on the per-timestep batch least-squares innovations MUST be implemented, its
  threshold tuned on validation to the detector's held-leg false-alarm rate at its declared
  operating point.
- **FR-023**: A GLR detector comparing one and two constant-velocity legs over a sliding window
  MUST be implemented and tuned the same way.
- **FR-024**: The frozen IMM's mode probability, thresholded, MUST be reported as a detector, and
  its held-leg false-alarm rate on validation MUST set D-false's limit if it is below 5% (D3).
- **FR-025**: gitma phase 3b's detection figures MUST be reported from gitma's record for
  continuity.
- **FR-026**: The IMM and EKF MUST be re-tuned on the manoeuvring validation split with declared
  grids, starting from P0's phase-4 setting, and frozen before any test scoring.
- **FR-027**: Every result MUST sit beside naive, batch least squares, the tuned IMM and EKF and the
  physics layer's oracle ceiling (true manoeuvre times and kinds) on the same rows.

**Metrics and gate**

- **FR-028**: The metrics of Annex A §A.3 MUST be computed on the σ = 1° slice of the test split
  with scenario-clustered paired bootstraps at 97.5%: detection delay (median and P90 by kind and
  angle band), miss rate, held-leg false alarms (per hour and share of held-leg G5 rows), kind
  accuracy, segmentation F1 at ±60 s, downstream error (all G5 rows and settled rows), calibration.
- **FR-029**: Gate D MUST be applied exactly as Annex A §A.5: D-delay, D-miss, D-false,
  D-downstream-all and D-downstream-settled gated; D-kind and D-gap reported; pass, fail and
  inconclusive as stated.
- **FR-030**: The validation rule of §A.5 MUST stop the phase before the test split if no variant
  meets every gated check's point with no interval wholly beyond its limit.
- **FR-031**: A gate command MUST check the decision record, plan, seeds, weights' digests and
  ancestry before scoring, and MUST write the experiment record and machine verdict; the verdict's
  decided-by field MUST name the panel round that approves it.
- **FR-032**: The follow-on of Annex A §A.6 MUST be recorded in the decision record before training.

**Export, pre-registration, documentation**

- **FR-033**: The trained detector MUST export alone to one portable graph (360-row window, dynamic
  batch) with weights and manifest, agree with the training framework to 1e-5 in the three
  runtimes, and run one window in under one second in the browser runtime.
- **FR-034**: A decision record MUST be committed before training, naming seeds, plan,
  configurations, D1–D4 with a reason each, the 0.5 threshold and ±60 s tolerance, the held-leg
  weighting, the knot-export threshold, the carried rule, the controls' tuning rule, the validation
  rule, the follow-on and a forecast.
- **FR-035**: Each control and validation check in the decision record MUST be checked against the
  detector's architecture before it is registered, and the check recorded.
- **FR-036**: The site MUST gain the detector's algorithm note, glossary entries and a Gate D
  write-up that states what the result does and does not show.

### Key Entities

- **Detector configuration**: encoder size, heads, input channels, loss weights (classification,
  held-leg weighting, downstream), tolerance, knot count and export threshold, optimiser, seed.
- **Detector outputs**: per timestep, the "now" probability, the soft changepoint weights over
  earlier timesteps and the kind probabilities.
- **Detection record**: per scenario and detector, the alarms, matched spans, delays, misses and
  held-leg alarms.
- **Control configuration**: the CUSUM, GLR and IMM-mode settings, with the tuned thresholds.
- **Decision record**: as spec 003, extended with D1–D4, thresholds, the held-leg weighting, the
  controls' tuning rule and the follow-on.
- **Experiment record**: manifest (with weights and amendment digests), metrics, checks, verdict,
  review.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every Gate 1 follow-up listed in spec 003 has a test or record field that fails on the
  old behaviour and passes now.
- **SC-002**: A deliberately dead model fails the learnability check; the trained detector passes it.
- **SC-003**: One epoch over 10^5 manoeuvring scenarios, with the physics layer in the loop, takes
  under an hour on a free 4-core runner, measured.
- **SC-004**: The decision record is committed before training; seeds 304, 305 and 311 appear in no
  earlier record; the test split is generated once.
- **SC-005**: The Gate D experiment record holds the detector variants, CUSUM, GLR, the IMM's mode
  probability and gitma phase 3b's figures on matched operating points, and the downstream estimate
  beside naive, batch least squares, the IMM, the EKF and the oracle on the same rows, with a
  verdict decided by the panel.
- **SC-006**: The exported detector agrees with the training framework to 1e-5 in three runtimes and
  runs a 360-row window in under one second in the browser.
- **SC-007**: The write-up states plainly what Gate D shows and what it does not, including any
  check that passes for a reason unrelated to the detector.

## Assumptions

- The defaults of Annex A §A.8 are adopted: threshold 0.5 and ±60 s (D1), both variants carried at
  97.5% (D2), the 5% held-leg limit or the IMM's lower rate (D3), fresh seeds from 301 onward (D4:
  304 validation, 305 test, 311 training stream; 301–303 and 310 are used).
- The frozen IMM for manoeuvring data is re-tuned on seed 304's validation split, as spec 003 did,
  starting from P0's phase-4 setting.
- Held legs and settled rows follow the existing definitions (gitma Annex C §C.5, as implemented
  for P0).
- The physics layer's knot count stays at P0's eight unless research shows the detector needs more.
- The downstream objective uses the Cramér–Rao bound for the known manoeuvres, as P0 did for
  manoeuvring rows.
- Gate 2's end-to-end fine-tuning, realistic bearing error and multiple targets are out of scope.
- If the physics layer in the loop does not fit the hour budget, research measures what does
  (sampled rows, fewer knots, the 50-iteration training solve of spec 003) before the plan is fixed.
