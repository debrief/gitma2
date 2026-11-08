# Feature Specification: Usable uncertainty for the carried estimator (Gate 4)

**Feature Branch**: `009-usable-uncertainty` (developed on `claude/happy-galileo-ksybjj`)

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: Spec 009, usable uncertainty: the Gate 3 follow-on, adopted by default
(`site/blog/2026-11-08-gate-3.md`; the owner has not objected). Every scored row of the carried
estimator E states an uncertainty an operator can act on: course as a circular statement or as
explicitly undetermined, the statement gated on observability by a causal test, the joint
statement honest on the rows it covers, trained on the errors the gate scores; controls, three
seeds, the references on the same rows; a new gate proposed as an SRD amendment and scored on
fresh seed 320; spec 008's carried minors.

**SRD traceability**:
- §7 step 5, first item (uncertainty calibration), second attempt after Gate 3 stopped at
  validation (`experiments/20261108-g3-val/`, panel round 2).
- §4 (the reported estimate comes from the declared physics layer; learned parts may only change
  what is stated about it), §5 (references, paired clustered statistics, fresh test seeds).
- The new gate is a §5 row, proposed as an amendment that the owner merges.

**Owner decisions this spec implements**:
- 2026-11-08: Gate 3's G3-b is a tail measure (share within the χ²₄ 95% point), not the median.
- 2026-11-08 (reporting, constitution 1.3.0): a kickoff post now and a slides post before the PR.
- The Gate 3 write-up's follow-on, adopted because the owner has not objected.

## Background from Gate 3 (`experiments/20261108-g3-val/`)

- E's raw covariance is badly overconfident: 95% coverage 0.60 in log range, 0.33 of rows within
  the χ²₄ 95% point. The oracle, with the true segmentation, is close to calibrated (0.875, 0.75).
- A learned scale in local coordinates reached 0.92–0.99 marginal coverage, but:
  - **course coverage was vacuous**: on half the rows the 95% course interval was the whole
    circle (median stated course sd 101°);
  - **the joint statement was not honest**: 0.835 within the χ²₄ 95% point, mostly because the
    calibration kept the solve's near-singular correlations (0.957 if they are dropped);
  - **it trained on linearised errors**, which cannot see a course flip;
  - **no learning was shown**: the head was nearly a constant and no better than a per-slice
    temperature.
- **Much of the failure is physical**: on rows during or just after a manoeuvre even the oracle
  falls short (0.635 within the χ²₄ point). There, course is not yet determined by the bearings,
  and the honest statement is "undetermined", not a wide Gaussian.
- **Process lessons**: choose every design setting on tuning ordinals 0–499 only; train on the
  errors the gate scores; test any learned part against the classical rule it might be.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each row says whether its course is determined (Priority: P1)

An operator reading E's estimate at a row sees one of two states. **Determined**: the stated
uncertainty (range, course, speed and their joint statement) can be trusted at its stated level.
**Undetermined** ("manoeuvre suspected or course not yet determined"): the course is not stated as
an interval; range and speed still carry intervals. The state is decided only from what E knew at
the row (causal), never from the truth.

**Why this priority**: Gate 3 showed that half the rows cannot carry a meaningful course interval.
Saying so is the first thing an operator needs, and every later measurement depends on it.

**Independent Test**: on validation, the state is computed for every scored row from causal inputs
only (changing anything after the row changes nothing), and the share of rows declared
undetermined is reported with the course errors on each side.

**Acceptance Scenarios**:

1. **Given** a row in a long steady leg after the zig, **When** E reports it, **Then** it is
   declared determined and carries course, range and speed intervals.
2. **Given** a row inside a transition C holds open, or shortly after a detected change, **When**
   E reports it, **Then** it may be declared undetermined, and the course interval is absent.
3. **Given** any row, **When** its future bearings are replaced by noise, **Then** its declared
   state and stated uncertainty are unchanged.

### User Story 2 - Course stated on the circle (Priority: P1)

On determined rows, the course uncertainty is a statement on the circle (a concentration or an
arc), never a Gaussian standard deviation that wraps past ±180°. Its coverage and score are
computed on wrapped errors.

**Why this priority**: a Gaussian course sd above ~90° was Gate 3's vacuous statement; a circular
statement makes coverage mean something.

**Independent Test**: the stated course arc never exceeds the declared maximum on a determined
row; coverage on wrapped errors matches the stated level on synthetic von-Mises data.

**Acceptance Scenarios**:

1. **Given** a determined row, **When** its course statement is read, **Then** the 95% arc is
   below the declared maximum width.
2. **Given** synthetic rows with known circular errors, **When** coverage is measured, **Then** it
   equals the stated level within binomial error.

### User Story 3 - An honest joint statement on determined rows (Priority: P1)

On determined rows, the 4-state uncertainty (position and velocity) passes the joint consistency
test: about 95% of rows within the χ²₄ 95% point. The correction may reshape the solve's
covariance (shrink its correlations or replace it in local coordinates), not only rescale it.

**Why this priority**: the joint statement is what a downstream user combines with other sensors;
Gate 3 failed it through the kept correlations.

**Independent Test**: on validation, the share within the χ²₄ 95% point on determined rows is
reported with its interval, for the calibration, the temperature and the raw covariance.

**Acceptance Scenarios**:

1. **Given** the calibrated determined rows, **When** the joint share is measured, **Then** it is
   reported with its 97.5% clustered interval.
2. **Given** any row, **When** it is calibrated, **Then** its point estimate is unchanged.

### User Story 4 - Learning tested against a rule, on the errors the gate scores (Priority: P2)

The learned calibration is trained on the exact errors the gate scores (wrapped course, log
range ratio, speed), with every design setting chosen on tuning ordinals 0–499. Its claim to have
learned something is tested against a classical temperature in the same form and a shuffled-label
control (best and last epoch), three seeds.

**Why this priority**: Gate 3 showed no learning; a claim without these controls is not a claim.

**Independent Test**: the decision record names every setting and the tuning rows it was chosen
on before any training; the controls are scored beside the head on the same rows.

**Acceptance Scenarios**:

1. **Given** the plan, **When** the decision record is committed, **Then** no training and no
   scoring of ordinals 500–1499 by a calibrated estimator exists yet.
2. **Given** the shuffled control beats the temperature on validation, **When** the gate is
   decided, **Then** a learning pass is void.

### User Story 5 - A pre-registered gate on a fresh seed (Priority: P2)

Gate 4 (usable uncertainty) is proposed as an SRD amendment (the owner merges), fixed by a decision
record before training, applied on validation by a validation rule, and scored on fresh test seed
320 only if the validation rule is met. The agent review panel decides.

**Why this priority**: as every earlier gate.

**Independent Test**: the decision record binds the plan by digest; seed 320 is generated only after
`carried.json`; the scorer refuses a partial test split.

**Acceptance Scenarios**:

1. **Given** the validation rule is not met, **When** the record is written, **Then** seed 320 is
   not generated and the write-up proposes the follow-on.
2. **Given** a test scoring, **When** it covers fewer than every σ = 1° scenario, **Then** it is
   refused.

### User Story 6 - Spec 008's carried minors (Priority: P3)

Calibrated prediction files record the commit and dirty flag of the run that made them; best- and
last-epoch shuffled files carry distinct model names; the gate's validation record names its
producing commit and CPU; the SRD Gate 3 row describes the registered (local) form.

**Why this priority**: none changes a number; each removes a provenance gap the Gate 3 panel found.

**Independent Test**: each has a unit test or a check that fails on the old behaviour.

**Acceptance Scenarios**:

1. **Given** a calibrated file, **When** its header is read, **Then** it names its own commit.
2. **Given** two shuffled files (best, last), **When** their headers are read, **Then** their model
   names differ.

### Edge Cases

- A row with no usable covariance (no plausible estimate): declared undetermined; counted as not
  covered wherever coverage is measured over all rows.
- A row before the zig: not scored (G5 rows start at zig + 5 min), as in Gates 2 and 3.
- Zero target speed: course is undefined; the row is declared undetermined.
- Every row declared undetermined: the gate's bound on the undetermined share fails it, so the
  trivial answer cannot pass.
- The oracle's own state: computed by the same causal rule from the oracle's inputs, so the
  undetermined share can be compared with what perfect segmentation leaves undetermined.
- Heavy tails in range and speed on undetermined rows: their intervals may come from a
  heavy-tailed component; their coverage is still measured.

## Requirements *(mandatory)*

### Functional Requirements

**Reported uncertainty**

- **FR-001**: Every scored row of E MUST carry a state, determined or undetermined, computed from
  causal inputs only (E's own stated information, time since the last detected change, C's code
  at the row); never from the truth.
- **FR-002**: Determined rows MUST carry calibrated intervals for log range, speed and course and a
  4-state covariance; course MUST be stated on the circle with a 95% arc below a declared maximum.
- **FR-003**: Undetermined rows MUST carry calibrated intervals for log range and speed and MUST
  NOT carry a course interval; they MAY carry a heavy-tailed range and speed statement.
- **FR-004**: Calibration MUST NOT change any point field (range, course, speed, position).

**Measurement**

- **FR-010**: The scorer MUST report, per estimator, on all rows and on determined rows: 95%
  coverage of log range and speed; circular 95% coverage of course on determined rows; the share
  within the χ²₄ 95% point; the undetermined share; a proper score for each quantity (the interval
  score for log range and speed, a proper circular score for course); sharpness.
- **FR-011**: The same causal state rule MUST be applied to the oracle and the references, so the
  undetermined share is comparable across estimators.
- **FR-012**: Every measurement MUST use the scenario-clustered paired bootstrap (97.5%, 2,000
  resamples) on one scoring run's stored arrays.

**Calibration and controls**

- **FR-020**: The calibration MUST be trained on the exact errors the gate scores.
- **FR-021**: Every design setting (thresholds of the state rule, form, bounds, caps) MUST be
  chosen on validation tuning ordinals 0–499 only, and recorded with the evidence before the
  decision record.
- **FR-022**: Three seeds and a shuffled-label control (scored at best and last epoch) MUST be
  trained; a classical temperature in the same form MUST be fitted on the tuning ordinals.
- **FR-023**: The carried seed MUST be chosen by a rule named in the decision record.

**Decision and gate**

- **FR-030**: Gate 4's criteria MUST be proposed as an SRD amendment, merged by the owner, before
  the decision record. The proposed defaults:
  - **G4-a (coverage)**: 95% coverage of log range and speed on all rows, and circular 95%
    coverage of course on determined rows, each interval wholly within [0.92, 0.98];
  - **G4-b (joint consistency)**: on determined rows, the share within the χ²₄ 95% point wholly
    within [0.92, 0.98];
  - **G4-c (the state is not a dodge)**: the undetermined share at most the oracle's undetermined
    share under the same rule plus 0.10, and the median course error on undetermined rows at
    least twice that on determined rows;
  - **G4-d (learning)**: the head's summed proper score below the temperature's (paired, wholly
    below zero), void if the shuffled control also beats the temperature on validation;
  - **G4-e (no regression)**: points identical to E's.
- **FR-031**: A decision record MUST bind the plan, the criteria, the seeds, the rules and a
  forecast before any calibration training.
- **FR-032**: Seed 320 MUST be generated only after `carried.json`; the whole σ = 1° test split
  MUST be scored.
- **FR-033**: The verdict MUST come from the agent review panel, in rounds.

**Carried minors (spec 008)**

- **FR-040**: Calibrated files MUST record the commit and dirty flag of the run that made them.
- **FR-041**: Best- and last-epoch control files MUST carry distinct model names.
- **FR-042**: The gate's validation and test records MUST name their producing commit and CPU.
- **FR-043**: The SRD amendment MUST correct the Gate 3 row's description of the registered form.

**Reporting**

- **FR-050**: A kickoff post before implementation and a slides post before the PR (constitution
  1.3.0), with track plots showing determined and undetermined rows.

### Key Entities

- **Row state**: determined or undetermined, with the causal inputs that decided it.
- **Calibrated row**: the point fields (unchanged); log-range and speed intervals; on determined
  rows a circular course statement and a 4-state covariance; the calibration's settings digest.
- **Calibration record**: per estimator and slice (all rows, determined rows), coverage, joint
  share, undetermined share, proper scores, sharpness, with intervals.
- **Gate 4 decision and record**: as Gate 3's, with the state rule and its settings bound.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On validation, no determined row states a course 95% arc wider than the declared
  maximum, and the course coverage on determined rows is reported with its interval.
- **SC-002**: On validation determined rows, the calibrated share within the χ²₄ 95% point is
  reported with its interval beside the raw covariance's and the temperature's.
- **SC-003**: The undetermined share of E and of the oracle are reported under the same rule.
- **SC-004**: The gate is decided by the panel within the pre-registered rules; if the validation
  rule is not met, seed 320 stays unused.
- **SC-005**: Every figure in the slides post reproduces from its sidecar.

## Assumptions

- E (e-s3), C, the frozen IMM/EKF and the oracle are as Gate 2; E's points are not retrained.
- The feature caches of spec 008 (stream 318, validation 0–1499) are reused if their contents
  suffice; otherwise they are re-made by the same workflow.
- Validation seed 314: tuning ordinals 0–499, scoring ordinals 500–1499. Test seed 320 (fresh);
  the next fresh seed after it is 321.
- The default bands follow Gate 3's ([0.92, 0.98]); the undetermined-share margin (0.10) and the
  course-error ratio (2) are proposals the owner may change in the amendment.
- Free 4-core CI runners suffice (Gate 3's training took minutes per seed from caches).
