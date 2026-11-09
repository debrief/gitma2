# Feature Specification: Usable uncertainty for the carried estimator (Gate 4)

**Feature Branch**: `009-usable-uncertainty` (developed on `claude/happy-galileo-ksybjj`)

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: Spec 009, usable uncertainty: the Gate 3 follow-on, adopted by default
(`site/blog/2026-11-08-gate-3.md`; the owner has not objected), **re-scoped by the owner on
2026-11-08 to a probabilistic course statement** after the tuning rows showed that E's gross course
errors cannot be flagged causally (see Background). Every scored row of the carried estimator E
states: course within ±X° with probability p (otherwise unknown), with X and p calibrated; and
calibrated intervals for log range and speed; trained on the errors the gate scores; controls,
three seeds, the references on the same rows; a new gate proposed as an SRD amendment and scored
on fresh seed 320; spec 008's carried minors.

**SRD traceability**:
- §7 step 5, first item (uncertainty calibration), second attempt after Gate 3 stopped at
  validation (`experiments/20261108-g3-val/`, panel round 2).
- §4 (the reported estimate comes from the declared physics layer; learned parts may only change
  what is stated about it), §5 (references, paired clustered statistics, fresh test seeds).
- The new gate is a §5 row, proposed as an amendment that the owner merges.

**Owner decisions this spec implements**:
- 2026-11-08: Gate 3's G3-b is a tail measure (share within the χ²₄ 95% point), not the median.
- 2026-11-08 (reporting, constitution 1.3.0): a kickoff post now and a slides post before the PR.
- 2026-11-08 (scope): course is stated probabilistically ("within ±X° with probability p,
  otherwise unknown"); the gate checks the reliability of p and the coverage of the range and
  speed intervals; the 4-state χ² share is reported, not gated.
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
- **Gross course errors are not causally predictable** (spec 009 scoping, validation tuning
  ordinals 0–499, 1,971 rows): 35% of E's course errors exceed 30° and 10% exceed 90°. The best
  single causal signal (E's own stated course sd) separates them with AUC 0.61; a logistic model on
  E's encoder state, its stated sds and C's code reaches 0.62 on held-out tuning rows. Declaring
  half the rows "undetermined" still leaves 28–29% of the others over 30° off. An honest course
  statement must therefore carry the probability that it is wrong, rather than a determined /
  undetermined split.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Course stated with the probability that it holds (Priority: P1)

An operator reading E's estimate at a row sees its course as "within ±X° of the estimate with
probability p; otherwise unknown". X and p are stated per row; when they say 70% within ±15°,
about 70% of such rows are within ±15°. The statement never claims more than it can keep, and
never uses a Gaussian standard deviation that wraps past ±180°.

**Why this priority**: a third of E's courses are badly wrong and cannot be told apart in advance;
the only honest statement carries that probability. Gate 3's vacuous intervals are what this
replaces.

**Independent Test**: on validation, rows grouped by stated p have hit rates (true course within
the stated arc) equal to their stated p, within binomial error; the statement is computed from
causal inputs only.

**Acceptance Scenarios**:

1. **Given** the validation rows, **When** they are binned by stated p, **Then** each bin's hit rate
   is within its interval of the bin's mean p.
2. **Given** any row, **When** its future bearings are replaced by noise, **Then** its stated X and
   p are unchanged.
3. **Given** a row, **When** its course statement is read, **Then** the arc half-width X is at most
   the declared maximum (for example 45°).

### User Story 2 - Range and speed intervals that hold (Priority: P1)

Each row states 95% intervals for range (as a ratio) and speed, calibrated on the exact errors the
gate scores, so that about 95% of rows fall inside, and no wider than they need to be.

**Why this priority**: range and speed are what an operator acts on next; Gate 3 reached their
coverage only by over-widening range.

**Independent Test**: coverage of each on validation is reported with its interval, and the
interval score against the raw covariance and the temperature.

**Acceptance Scenarios**:

1. **Given** the calibrated validation rows, **When** coverage is measured, **Then** it is reported
   per quantity with its 97.5% clustered interval.
2. **Given** any row, **When** it is calibrated, **Then** its point estimate is unchanged.

### User Story 3 - Learning tested against a rule (Priority: P2)

The learned statement (p, X and the range and speed scales per row) is trained on the exact errors,
with every design setting chosen on tuning ordinals 0–499, and tested against a classical
temperature (the same statement fitted per slice of time since the zig × open transition) and a
shuffled-label control at best and last epoch, three seeds.

**Why this priority**: Gate 3 showed no learning; the scoping above suggests little per-row signal,
so the claim must be tested, not assumed.

**Independent Test**: the decision record names every setting and its tuning evidence before any
training; the controls are scored beside the head on the same rows.

**Acceptance Scenarios**:

1. **Given** the plan, **When** the decision record is committed, **Then** no calibrated estimator
   has been scored on ordinals 500–1499.
2. **Given** the shuffled control beats the temperature on validation, **When** the gate is
   decided, **Then** a learning pass is void.

### User Story 4 - A pre-registered gate on a fresh seed (Priority: P2)

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

### User Story 5 - Spec 008's carried minors (Priority: P3)

Calibrated prediction files record the commit and dirty flag of the run that made them; best- and
last-epoch control files carry distinct model names; the gate's records name their producing
commit and CPU; the SRD Gate 3 row describes the registered (local) form.

**Why this priority**: none changes a number; each closes a provenance gap the Gate 3 panel found.

**Independent Test**: each has a unit test or a check that fails on the old behaviour.

**Acceptance Scenarios**:

1. **Given** a calibrated file, **When** its header is read, **Then** it names its own commit.
2. **Given** two shuffled files (best, last), **When** their headers are read, **Then** their model
   names differ.

### Edge Cases

- A row with no usable covariance: stated p = 0 (course unknown) and the widest declared range and
  speed intervals; counted as not covered where coverage is measured.
- Zero target speed: course undefined; stated p = 0.
- A statement that always says p = 0 ("course unknown"): perfectly reliable but useless; the
  informativeness check (G4-c) fails it.
- Rows before the zig: not scored (G5 rows start at zig + 5 min).
- The oracle and the references: given the same per-slice statement form (the temperature fitted
  to their own errors) where they state a covariance, so their informativeness is comparable.

## Requirements *(mandatory)*

### Functional Requirements

**Reported uncertainty**

- **FR-001**: Every scored row of E MUST state a course arc half-width X (at most a declared
  maximum) and a probability p that the true course lies within it; computed from causal inputs
  only.
- **FR-002**: Every scored row MUST state 95% intervals for range (as a ratio) and speed.
- **FR-003**: Calibration MUST NOT change any point field.
- **FR-004**: The 4-state covariance MAY be kept for downstream use; its χ² share is reported, not
  gated.

**Measurement**

- **FR-010**: The scorer MUST report, per estimator: the course statement's reliability (hit rate
  against stated p, overall and in bins of p), its sharpness (mean X, mean p), and a proper score
  for it (the log score of the stated course density, a mixture of a peaked part within X and a
  uniform part); 95% coverage, sharpness and the interval score for range and speed; the 4-state
  χ² share for reference.
- **FR-011**: Every measurement MUST use the scenario-clustered paired bootstrap (97.5%, 2,000
  resamples) on one scoring run's stored arrays.

**Calibration and controls**

- **FR-020**: The calibration MUST be trained on the exact errors the gate scores (wrapped course,
  log range ratio, speed).
- **FR-021**: Every design setting (the maximum X, the statement's form, bounds, caps) MUST be
  chosen on validation tuning ordinals 0–499 only, and recorded with the evidence before the
  decision record.
- **FR-022**: Three seeds and a shuffled-label control (best and last epoch) MUST be trained; a
  classical temperature in the same form MUST be fitted per slice on the tuning ordinals.
- **FR-023**: The carried seed MUST be chosen by a rule named in the decision record.

**Decision and gate**

- **FR-030**: Gate 4's criteria MUST be proposed as an SRD amendment, merged by the owner, before
  the decision record. The proposed defaults:
  - **G4-a (range and speed)**: 95% coverage of range and speed on all rows, each interval wholly
    within [0.92, 0.98];
  - **G4-b (course reliability)**: the hit rate minus the mean stated p wholly within ±0.03, and in
    each of five bins of p the same within ±0.05 (point);
  - **G4-c (course informativeness)**: the course log score above the uninformative statement's
    (uniform on the circle), paired, wholly above zero, with mean p at least 0.5;
  - **G4-d (learning)**: the head's summed proper score (course log score and the range and speed
    interval scores, each standardised by the temperature's) better than the temperature's, wholly;
    void if the shuffled control also beats the temperature on validation;
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
  1.3.0), with track plots showing each row's course arc and stated probability.

### Key Entities

- **Course statement**: arc half-width X, probability p, and the peaked part's shape inside the arc.
- **Calibrated row**: the point fields (unchanged), the course statement, range and speed 95%
  intervals, the calibration's settings digest.
- **Calibration record**: per estimator, reliability (overall and binned), sharpness, proper
  scores, coverage, with intervals.
- **Gate 4 decision and record**: as Gate 3's, with the statement form and settings bound.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On validation, rows that state probability p have hit rates within ±0.05 of p in every
  bin, or the failure is reported with its intervals.
- **SC-002**: On validation, range and speed 95% coverage are reported with intervals beside the raw
  covariance's and the temperature's.
- **SC-003**: The course statement's log score is reported against the uninformative statement and
  the temperature's.
- **SC-004**: The gate is decided by the panel within the pre-registered rules; if the validation
  rule is not met, seed 320 stays unused.
- **SC-005**: Every figure in the slides post reproduces from its sidecar.

## Assumptions

- E (e-s3), C, the frozen IMM/EKF and the oracle are as Gate 2; E's points are not retrained.
- The feature caches of spec 008 (stream 318, validation 0–1499) are reused; they hold the state,
  the truth and E's encoder state at each row, which is enough for exact errors.
- Validation seed 314: tuning ordinals 0–499, scoring ordinals 500–1499. Test seed 320 (fresh); the
  next fresh seed after it is 321.
- The scoping evidence (AUC ≈ 0.62) suggests a learned p will add little over the per-slice
  temperature; G4-d is expected to be hard, and that is acceptable: the classical statement is
  carried if only G4-d fails.
- Free 4-core CI runners suffice.
