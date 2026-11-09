# Feature Specification: An honest course statement (Gate 5)

**Feature Branch**: `010-honest-course-statement` (developed on `claude/happy-galileo-ksybjj`)

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: Spec 010, the Gate 4 follow-on, adopted by default
(`site/blog/2026-11-09-gate-4.md`; the owner merged PR 23 without objecting and asked work to
proceed without waiting). The carried estimator E (Gate 2 e-s3, points unchanged) states its course
as one self-consistent probability: the exact von Mises mass; the stated density and P
recalibrated together; a smoother or parametric recalibration fitted on more tuning rows. A causal
"unsettled" proxy lowers P after a suspected manoeuvre, and a two-mode course (the estimate or its
reciprocal) is added if tuning evidence supports it. Range and speed 95% intervals are kept.
Gate 5 is proposed as an SRD amendment. Its criteria are:
- reliability overall and per slice, tested with intervals and a calibration slope rather than
  point bands;
- coverage per slice;
- a usefulness measure;
- a learning claim against pre-registered classical controls: the sd^β temperature, a cross-sd
  quadratic rule and an encoder-only shuffled head.

Design choices are made on validation tuning ordinals 0–499 only, and trial runs are disclosed.
There are three seeds, and the test uses fresh seed 320.

**SRD traceability**:
- §7 step 5, first item (uncertainty), third attempt, after Gate 4 stopped at validation
  (`experiments/20261109-g4-val/`, panel round 2).
- §4: the reported estimate comes from the declared physics layer; learned parts change only what
  is stated about it.
- §5: references on the same rows, paired clustered statistics, fresh test seeds. Gate 5 is a new
  §5 row, proposed as an amendment that the owner merges.

**Owner decisions this spec implements**:
- 2026-11-08: course is stated probabilistically, as "within ±X with probability P, otherwise
  unknown". The 4-state χ² share is reported, not gated.
- 2026-11-09: Gate 4's follow-on is adopted, and work proceeds between gates without waiting for
  the owner.

## Background from Gate 4 (`experiments/20261109-g4-val/`, `review.md`)

- **The stop.** The carried head (st-s3) missed the top bin of P by +0.054 against ±0.05. The cause
  was the 10-knot isotonic map, which was fitted on 1,971 tuning rows and pooled its top knots, so
  it capped P at 0.677. The raw head was slightly over-confident there.
- **The per-bin point band was fragile.** It sits about 2.5 sampling sd wide, so a calibrated
  statement misses it about a quarter of the time.
- **P is honest on average, not where it matters.**
  - On rows still settling after a target manoeuvre (a quarter of rows), P is 0.62 and the hit
    rate 0.30. On settled rows it is 0.63 against 0.73.
  - P varies only from 0.46 to 0.68, and its AUC for a hit is 0.60.
  - 9.5% of rows are more than 90° off in course (consistent with the reciprocal-course ambiguity)
    and still state 0.62.
- **The statement contradicts itself.** P is recalibrated but the scored density is not; per row
  the two differ by up to 0.2. The normal approximation to the von Mises adds up to 0.12.
- **The learning is mostly a classical rule.** The head beat the sd^β temperature by 0.235
  standardised units. A quadratic rule in E's three log sds, fitted on tuning rows, recovers 72% of
  that. The registered shuffled control permuted the errors but kept the sds, so it could not show
  per-row information.
- **Gaps in what was measured.**
  - Coverage falls short at minute 5 (range 0.916, speed 0.903) and beyond 30 km (0.907, 0.867).
  - Nothing before minute 5 is measured.
  - The references were compared with raw statements against E's fitted one.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One course probability that means what it says (Priority: P1)

An operator reads, for each row, "course within ±X of the estimate with probability P, otherwise
unknown". Every number the row states about course (the arc, P and the distribution behind them)
agrees: the stated distribution's mass on ±X is P. P is computed exactly, not by approximation.

**Why this priority**: without it the statement contradicts itself. That is the panel's blocker
for any later claim that the statement is usable.

**Independent Test**: on any row, the stated distribution's probability of the arc equals the
stated P to within numerical precision.

**Acceptance Scenarios**:

1. **Given** any stated row, **When** the stated distribution is integrated over ±X, **Then** the
   result equals P to within 1e-6.
2. **Given** the recalibration, **When** it is applied, **Then** it changes the distribution's
   parameters, and P follows from them.

### User Story 2 - P drops after a suspected manoeuvre (Priority: P1)

When causal signals suggest the target may have manoeuvred, the stated P is lower, so that P
stays reliable on those rows. The signals are those available at the row: time since the
segmenter's last accepted or open transition, the segmenter's open code, E's stated sds and bearing
residuals. If tuning evidence supports it, the statement may also put weight on the reciprocal
course.

**Why this priority**: the unsettled rows are where Gate 4's statement was most wrong (0.62 stated
against 0.30) and where an operator is most at risk.

**Independent Test**: on validation, the reliability of P on rows the causal proxy flags as
unsettled, and on rows it does not, is each reported with its interval. The same holds on the
truth-defined settled and not-settled rows.

**Acceptance Scenarios**:

1. **Given** a row the proxy flags, **When** its statement is formed, **Then** it uses only
   information available at the row.
2. **Given** the proxy's two states, **When** reliability is measured, **Then** each state's
   hit − P interval is reported, and the gate's per-slice check applies to both.

### User Story 3 - Reliability and coverage checked where they matter (Priority: P1)

The gate checks reliability and coverage per slice: minutes since the zig, open transition at the
row, range band, and the unsettled proxy's two states. Each check allows for sampling noise
(intervals, and a calibration slope across P), not a point band. Early rows (before minute 5) are
measured where the scored rows include them.

**Why this priority**: Gate 4's overall reliability (−0.002) hid −0.31 and +0.10 on two halves of
the rows, and its point bands failed on noise.

**Independent Test**: every slice's hit − P and coverage, and the calibration slope, are reported
with 97.5% clustered intervals. The verdict logic is unit-tested on synthetic statements.

**Acceptance Scenarios**:

1. **Given** a calibrated statement on synthetic rows, **When** the gate is applied, **Then** it
   passes in at least 90% of resampled synthetic datasets.
2. **Given** a statement miscalibrated by 0.15 on one slice, **When** the gate is applied, **Then**
   that slice fails.

### User Story 4 - Learning tested against the rules it might be (Priority: P2)

The learned statement is compared, on the same rows, with three pre-registered controls:
- the sd^β per-slice temperature;
- a cross-sd classical rule: each statement parameter a quadratic function of E's three log sds,
  fitted on the same training stream as the head;
- an encoder-only shuffled head: E's encoder state permuted across rows, with the sds and the
  segmenter's code kept, scored at best and last epoch as distinct models.

A learning claim stands only if the head beats the best classical control and the encoder-only
shuffle does not.

**Why this priority**: two gates in a row found that the "learned" gain was largely a rule.

**Independent Test**: all controls are registered in the decision record before any training, and
scored beside the head on the same rows.

**Acceptance Scenarios**:

1. **Given** the decision record, **When** it is committed, **Then** it names every control and
   its fitting data, and no stated estimator has been scored on ordinals 500–1499.
2. **Given** the encoder-only shuffle also beats the best classical control on validation, **When**
   the gate is decided, **Then** the learning claim is void.

### User Story 5 - Fair references (Priority: P3)

The oracle and the frozen IMM are given the same classical statement (the temperature fitted to
their own errors on tuning rows), so that E's statement is compared like for like. The IMM's rows
without an estimate are reported separately.

**Why this priority**: the Gate 4 baseline compared raw reference statements with E's fitted one.

**Independent Test**: the scoring run holds the references' fitted statements on the same rows.

**Acceptance Scenarios**:

1. **Given** the validation scoring, **When** the references are reported, **Then** each appears
   raw and with its fitted temperature.

### Edge Cases

- **No usable covariance:** the row states P = 0 (course unknown) and counts as not covered; the
  share of such rows is reported per estimator.
- **Two-mode statement:** if the reciprocal mode is used, the stated arc and P refer to the
  estimate's arc only. The mass on the reciprocal arc is stated separately, and the log score uses
  the full density.
- **A statement that always says "unknown":** reliable but useless. The usefulness checks fail it.
- **Slices with few rows:** a slice with fewer than a declared minimum of rows is reported, not
  gated.
- **The proxy flags nearly every row, or none:** the gate reports the proxy's flag rate. The
  per-state check needs both states above the minimum.

## Requirements *(mandatory)*

### Functional Requirements

**The statement**

- **FR-001**: Every scored row of E MUST state a course arc half-width X (at most a declared
  maximum), the probability P that the true course lies within it, and the parameters of a course
  distribution whose mass on ±X is exactly P.
- **FR-002**: P MUST be computed exactly, not by an approximation, and any recalibration MUST keep P
  and the density consistent (research R2: the density is defined from P, a truncated shape inside
  the arc and a uniform remainder outside, so the arc mass is P by construction).
- **FR-003**: The statement MUST use causal inputs only. The unsettled proxy uses only information
  available at the row.
- **FR-004**: Every scored row MUST state 95% intervals for range (as a ratio) and speed.
- **FR-005**: Point fields MUST NOT change.
- **FR-006**: A reciprocal-course mode MAY be added, if and only if it improves the course log
  score on tuning rows; the decision and its evidence are recorded before the decision record.

**Measurement**

- **FR-010**: The scorer MUST report, per estimator, overall and per slice (minutes since the zig,
  open transition at the row, range band, the proxy's two states, truth-settled):
  - hit − P and coverage with intervals;
  - the calibration slope (hit on P) with its interval;
  - the AUC of P for a hit;
  - mean P and mean X;
  - the course log score and its gain over "unknown";
  - range and speed coverage and interval scores;
  - the share of rows with no statement.
- **FR-011**: Statistics MUST use the scenario-clustered bootstrap (97.5%, 2,000 resamples) on one
  scoring run's stored arrays.
- **FR-012**: Rows before minute 5 MUST be measured as a reported slice if the scored row set can
  include them without changing the G5 rows. Otherwise the gap MUST be stated (research R5: stated,
  carried as a follow-on).

**Controls and training**

- **FR-020**: The statement MUST be trained on the exact errors the gate scores.
- **FR-021**: Every design setting MUST be chosen on validation tuning ordinals 0–499 only. This
  covers the maximum X, the recalibration form, the proxy's definition and threshold, and whether
  to use two modes. Each setting's evidence MUST be recorded before the decision record. Trial
  trainings before the record MUST be disclosed in it.
- **FR-022**: There MUST be three head seeds and these controls:
  - the sd^β temperature;
  - the cross-sd quadratic rule, fitted on the training stream;
  - the encoder-only shuffled head, at best and last epoch as distinct model names.
- **FR-023**: The references (oracle, frozen IMM) MUST be given the temperature fitted to their own
  errors on tuning rows.
- **FR-024**: The carried seed MUST be chosen by a rule named in the decision record.

**Decision and gate**

- **FR-030**: Gate 5's criteria MUST be proposed as an SRD amendment (the owner merges) before the
  decision record. Proposed defaults:
  - **G5-a (intervals)**: range and speed coverage. Overall, the interval must lie wholly within
    [0.92, 0.98]. In each gated slice it must not lie wholly outside [0.90, 0.99].
  - **G5-b (reliability)**:
    - overall hit − P wholly within ±0.03;
    - the calibration slope's interval wholly within [0.75, 1.33];
    - in each gated slice, including both proxy states, hit − P not wholly outside ±0.05;
    - in each gated slice, the point within ±0.08.
  - **G5-c (usefulness)**: the course log gain over "unknown" wholly above zero, and the AUC of P
    for a hit wholly above 0.55.
  - **G5-d (learning)**: the head's standardised summed score below the best classical control's,
    wholly. The best classical control is the lower of the temperature and the cross-sd rule. The
    claim is void if the encoder-only shuffle (best or last) also beats that control on
    validation.
  - **G5-e (consistency)**: points identical to E's, and each row's P equal to its stated
    distribution's arc mass to within 1e-6.
- **FR-031**: A decision record MUST bind the plan, the criteria, the seeds, the rules and a
  forecast before any training on CI.
- **FR-032**: Seed 320 MUST be generated only after `carried.json`. The whole σ = 1° test split
  MUST be scored.
- **FR-033**: The verdict MUST come from the agent review panel, in rounds.

**Reporting**

- **FR-040**: A kickoff post before implementation and a slides post before the PR. The slides
  carry a reliability diagram, P against hit rate by slice, and plain-language widths.

### Key Entities

- **Course statement**: the arc X, probability P, the distribution's parameters (concentration, the
  peaked weight, the reciprocal weight if used), and the recalibration that produced them.
- **Unsettled proxy**: a causal flag per row, its inputs and its threshold.
- **Classical controls**: the temperature, the cross-sd rule and the reference temperatures, each
  with its fitting data and digest.
- **Gate 5 decision and record**: as Gate 4's, with the controls and the slice definitions bound.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every stated row, the stated P equals the stated distribution's mass on the arc,
  to within 1e-6.
- **SC-002**: On validation, the hit − P of the proxy's unsettled state is reported with its
  interval. Gate 4's −0.31 on truth-unsettled rows is either brought within the per-slice band or
  reported as not achieved.
- **SC-003**: On synthetic calibrated statements, the gate's reliability checks pass in at least
  90% of resampled datasets. On a statement miscalibrated by 0.15 on one slice, they fail that
  slice in at least 90%.
- **SC-004**: The learning claim is decided against the best of three pre-registered classical
  controls, with the encoder-only shuffle as the void rule.
- **SC-005**: The gate is decided by the panel within the pre-registered rules. If the validation
  rule is not met, seed 320 stays unused.

## Assumptions

- E (e-s3), C, the frozen IMM/EKF and the oracle are as in Gate 2. E's points are not retrained.
- The spec 008 feature caches (stream 318, validation 0–1499) are reused. They hold the state, the
  truth, E's encoder state, C's code at the row, open-at-row and the minute. The proxy's extra
  inputs (time since C's last transition, bearing residuals) may need the caches extended. That is
  decided in the plan.
- Validation seed 314: tuning ordinals 0–499 (1,971 rows), scoring ordinals 500–1499. The tuning
  rows are few for a smooth recalibration. Pooling tuning rows from the stream (seed 318) for the
  recalibration is allowed if the stream's rows are shown to be exchangeable on the tuning
  evidence.
- G5 rows start at minute 5. Earlier rows are measured only if they can be added as a reported
  slice (FR-012).
- The scoping evidence (AUC about 0.6) suggests the learning claim will be hard to pass. If only
  G5-d fails, the best classical statement is carried.
- Free 4-core CI runners suffice.
