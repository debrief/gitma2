# Feature Specification: Time-late TMA, the whole track over a given period (Gate T)

**Feature Branch**: `013-time-late` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description (owner, 2026-11-11): pause GPU training and take considered steps
towards the time-late problem. Time-late takes a period of bearings and wants the most
consistent solution across the whole period; real-time wants the best solution now. Bearings
arrive at about 5-second intervals. The analyst has no control over which period of data is
available. Where the bearing rate is steady, the observations might be thinned; whether that
helps is unknown.

**SRD traceability**:
- §3 ("both consumers remain: instantaneous, causal; time-late, full window"); §5 (references on
  the same rows, efficiency against the bound, paired clustered statistics, fresh seeds).
  Gate T is a new §5 row, proposed as an amendment the owner merges.
- Annex B (the owner's manoeuvre model, MAN2) and its segmentation measures.
- Earlier time-late attempts: Gate D's time-late detector (failed), spec 008's time-late
  weights (no gain); neither was built for time-late from the start.

**Owner decisions this spec implements**:
- 2026-11-11: a time-late solution is judged on **the whole track across the period**:
  position, course and speed at every moment, and the manoeuvre times.
- 2026-11-11: bearings at 5-second intervals.
- 2026-11-11: the period is not the analyst's to choose. Modelled here as a random portion of
  a longer scenario (the owner offered this, or the scenarios as they are; see Assumptions).
- 2026-11-11: GPU training is paused; nothing is trained in this spec.

## Background

- Every result so far scores the estimate at the latest moment. C″ run to the end of a window
  already yields a segmentation and a fitted track for the whole window; that track has never
  been scored.
- On validation seed 327 (spec 012): least squares on held course is at the bound (1.01); C″
  after manoeuvres is at 0.105 in median relative range error against 0.063 on the true
  manoeuvre times, and a direct regressor at 0.065. Missed manoeuvres are the largest part of
  C″'s gap (spec 011: about 30% of true changes).
- A causal system has minutes of evidence after a recent change. With the whole period, every
  change but the last has bearings on both sides. Whether that removes most misses is a
  hypothesis this spec measures.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A time-late solution and its score (Priority: P1)

An analyst hands over a period of bearings and the ownship track for that period and receives
the target's track over the whole period (position, course and speed at every moment), the
times of its manoeuvres, and for each stretch whether the data determine the solution at all.
A researcher sees that track scored against the truth at every moment, beside a bound.

**Why this priority**: nothing can be compared until the output and its score exist.

**Independent Test**: from one committed scoring run, the whole-track errors of every system,
the bound and the manoeuvre-timing counts can be recomputed.

**Acceptance Scenarios**:

1. **Given** a period with no ownship manoeuvre in it, **When** it is solved, **Then** the
   solution says range is undetermined rather than stating a range, and the score treats those
   moments apart.
2. **Given** a period and a system's track, **When** scored, **Then** errors are reported over
   every moment of the period, not only its end.

---

### User Story 2 - Periods as an analyst gets them, at 5 seconds (Priority: P1)

The simulator produces bearings every 5 seconds and periods cut at random from longer
engagements, so a period can begin or end mid-leg and may contain several ownship manoeuvres
or none.

**Why this priority**: the present scenarios are built to be observable (an ownship zig across
the line of sight in the middle); a time-late result on them alone would flatter every system.

**Independent Test**: with the new options off, existing data reproduce byte for byte; with
them on, the share of periods with zero, one and more ownship manoeuvres is reported.

---

### User Story 3 - What the classical approach already gives, and what is left (Priority: P1)

A researcher sees, on a tuning seed and then on fresh seeds: C″ read as a time-late solution;
a classical full-period pass that re-tests every declared change with all the data and looks
for missed ones; the least-squares solve told the true manoeuvre times; and the bound. The gap
between the best classical system and the true-manoeuvre solve, with its interval, is the
headroom for anything better, learned or not.

**Why this priority**: the project's standing lesson is to measure the headroom before
training anything, and to give the classical side its best shot first.

**Independent Test**: the headroom statistic and its interval, the segmentation counts
(matched, missed, false) for each system, from one scoring run.

**Acceptance Scenarios**:

1. **Given** the registered rule, **When** the test seed is scored, **Then** the record says
   whether the headroom is material, by a threshold fixed beforehand.
2. **Given** the causal and the full-period classical systems, **When** compared, **Then** the
   record says how many of the causal system's misses the full period recovers.

---

### User Story 4 - Does thinning by bearing rate help? (Priority: P2)

A researcher sees the owner's idea tested: where the bearing rate is steady within a
tolerance, a run of bearings is replaced by fewer observations. Three forms are compared with
the full data: dropping bearings, fixed-length normal points (one fitted bearing per bin with
its reduced variance), and adaptive bins set by bearing-rate steadiness. For each: accuracy
against the bound, run time, and behaviour when some bearings are wild.

**Why this priority**: at 5 seconds the classical systems do twice the work; if compression is
nearly free in accuracy it pays for the full-period pass, and a robust bin may also remove the
wild bearings that broke the segmenter in spec 011.

**Independent Test**: efficiency against the bound with and without each form on the same
engagements, and the run time of each.

### Edge Cases

- A period shorter than one leg, or holding only a turn: solved and scored; the "undetermined"
  statement applies.
- A manoeuvre that began before the period: the track inside the period is scored; the change
  itself is not counted as missed.
- The last leg of a period, with few bearings after its start: scored, and reported apart,
  since full-period evidence does not help it.
- Dropouts and wild bearings inside a compression bin.
- A period in which the target is never determined: every system's row errors there are kept
  out of the headline and counted.

## Requirements *(mandatory)*

### Functional Requirements

**Data**

- **FR-001**: The simulator MUST offer bearings at 5-second intervals and periods cut at random
  from longer engagements (random start and length within declared limits), behind options
  that leave existing data byte-identical when off.
- **FR-002**: Each period's record MUST say how many ownship and target manoeuvres fall inside
  it and which began before it.
- **FR-003**: The error model of the 5-second bearings (independent or correlated, and the σ of
  one bearing) MUST be declared before any scoring; the default is in Assumptions.

**The time-late solution and its score**

- **FR-010**: A time-late solution MUST state, for every moment of the period, the target's
  position, course and speed; the manoeuvre intervals; and where the data do not determine it.
- **FR-011**: Scoring MUST cover every moment of the period: relative range, position in
  metres, course and speed errors; summarised per engagement and then across engagements with
  scenario-clustered intervals; with the manoeuvre measures of Annex B (matched, missed, false,
  timing error).
- **FR-012**: A bound for the state at every moment given the whole period (manoeuvre times
  known) MUST be computed on the same rows, and moments the bound calls undetermined reported
  apart from the headline.
- **FR-013**: Results MUST be split by the number of ownship manoeuvres in the period, by
  position in the period (first leg, interior, last leg), and by range band.

**Systems (nothing trained)**

- **FR-020**: C″ run causally to the period's end and read as a track (the frozen C; its
  digests unchanged).
- **FR-021**: A classical full-period system: C″'s result re-tested with all the data (each
  declared change kept or dropped; missed changes sought in the full-period residuals), by
  classical means only, with settings chosen on a tuning seed by a rule declared first.
- **FR-022**: The least-squares solve told the true manoeuvre times (the reference; not a
  ceiling for systems that do not segment), one leg, and the tuned IMM with a fixed-interval
  smoother if one can be had at reasonable cost, otherwise the forward IMM, named as such.
- **FR-023**: Every comparison within one scoring run, on the same periods.

**Compression (the owner's bearing-rate idea)**

- **FR-030**: Dropping, fixed normal points and adaptive bins by bearing-rate steadiness MUST
  each be compared with the full data on the same engagements: efficiency against the bound on
  held-course periods, whole-track error on manoeuvring periods, run time, and the same under
  the outlier condition of spec 010.
- **FR-031**: The tolerance and bin lengths MUST be chosen on the tuning seed by a declared
  rule, and the cost in accuracy stated with an interval, not asserted.

**Decision**

- **FR-040**: Gate T MUST be proposed as an SRD row the owner merges and bound by a decision
  record before the validation and test seeds exist. Proposed: **T-a** soundness (the
  true-manoeuvre solve within a declared band of the bound on determined rows; the compression
  adopted, if any, within a declared cost); **T-b** the headroom: the best classical system's
  whole-track median range error over the reference's, minus 1, material if its interval lies
  wholly above 10%, not material if wholly below, otherwise inconclusive.
- **FR-041**: Material headroom → the next spec trains a full-period proposer whose output a
  least-squares solve turns into the answer, with the classical full-period system as its
  control. Not material → the classical full-period system is the time-late answer and is
  published as such.
- **FR-042**: The panel decides. Seeds MUST be fresh: 329 tuning, 330 validation, 331 test
  (324 and 325 stay unused).

**Reporting**

- **FR-050**: The slides post MUST show: one period's bearings and bearing-rate curve with the
  compression bins; whole-track plots (truth, C″ read as a track, the full-period system, the
  reference) on representative periods with and without an ownship manoeuvre; the headroom
  chart; the misses recovered by the full period; the compression trade-off.

### Key Entities

- **Period**: a contiguous portion of an engagement handed to the analyst; its bearings,
  ownship track, and counts of manoeuvres inside.
- **Time-late solution**: the track over the period, manoeuvre intervals, determined flags.
- **Whole-track score**: errors at every moment, per engagement and pooled.
- **Reference**: least squares on the true manoeuvre times, full period.
- **Classical full-period system**: C″ plus a full-period re-test; the control for any learned
  successor.
- **Normal point**: one fitted bearing standing for a bin of bearings, with its variance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every system's whole-track errors, the bound and the manoeuvre counts are
  reported on the same periods, with intervals.
- **SC-002**: With the new data options off, existing datasets reproduce byte for byte.
- **SC-003**: The record states the headroom with its interval and the verdict by the rule
  fixed beforehand.
- **SC-004**: The record states how many of the causal system's missed manoeuvres the full
  period recovers.
- **SC-005**: The record states what each form of thinning costs in accuracy and saves in run
  time, and whether the owner's idea is adopted, with the evidence.
- **SC-006**: Nothing is trained and no GPU time is used.
- **SC-007**: A reader can tell from the write-up alone what a time-late solution is, how good
  the classical one is, and whether a learned one is worth building.

## Assumptions

- **Periods**: cut from MAN2 engagements of the present length (40 to 120 minutes): a start
  uniform over the engagement and a length uniform between 20 minutes and what remains. The
  owner offered this or the scenarios as they are; cutting is adopted because the present
  scenarios all contain an ownship zig across the line of sight near the middle, which an
  analyst's period need not. Uncut scenarios are scored beside as one stratum.
- **5-second errors**: independent between bearings, with the same σ per bearing as today (1°
  or 2°), as the primary condition; the correlated condition of spec 010 (60 s) is scored
  beside it. Independent errors at twice the rate nearly double the information, which a real
  sensor may not deliver; this is the owner's to correct before the decision record.
- "Undetermined" is decided from the solution's own covariance for the systems and from the
  bound for the score; the threshold is fixed in the plan.
- The 10% threshold in T-b repeats Gate H's and Gate R's; it is a proposal until the decision
  record.
- Out of scope: any learned model (the follow-on, if the headroom is material); live operation
  (alarms, detection delay); the scaled regressor's remaining questions (spec 012 is finished
  with its test reading); real data.
