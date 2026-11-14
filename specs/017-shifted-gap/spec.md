# Feature Specification: Time-late, the standing control and the shifted-prior gap

**Feature Branch**: `017-shifted-gap` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-14

**Status**: Draft

**Input**: Owner decision, 2026-11-14, after study L's panel review: option A. Adopt the
classical control as the standing time-late system, and run one cheap classical study of
whether the gap under a shifted manoeuvre prior is a limit of identifiability. CPU only;
nothing trained.

**SRD traceability**:
- §1 (the time-late consumer), §5 (references on the same rows, paired statistics, fresh
  seeds, registration before results) and §9, 2026-11-14 (the owner's decision; proposed,
  the owner merges).
- Panel review `experiments/20261114-tl4/review.md`: major findings 6 to 9, "What the panel
  wants next" option 1, and "Owed to the record either way".

**Owner decisions this spec implements**:
- 2026-11-14: option A.

## Background

Study L left one large gap open for every system. On targets that manoeuvre more often and
less sharply than Annex B says (three manoeuvres a period, turns of 15° to 75°, 15-minute
legs) the classical control's track error is 1.7 to 2.1 times that of a fit told the true
manoeuvre history. A broadened prior did not close it; a learned model trained on such
targets did not close it; half the manoeuvres are missed however the match is counted, and
the fit told the true structure itself drifts in a quarter of periods.

Two explanations make opposite recommendations. If the bearings and any honest prior
cannot tell these histories apart, the gap is a property of the problem: no estimator will
close it, and the remedy is information (longer periods, ownship manoeuvres) or a hedged
answer. If the manoeuvres are detectable and the search or its evidence fails to find
them, the gap is attainable, and the trained models of study L are candidates to propose
them. The panel judged the first more likely and said the study cannot prove it. This
feature measures it.

The panel also listed what study L's record still owes, whatever comes next.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - How detectable is each true manoeuvre? (Priority: P1)

A researcher sees, for every true manoeuvre of a period, how much worse the bearings are
fitted when that manoeuvre is left out of the true history, and how the control's misses
divide between manoeuvres the bearings barely show and manoeuvres they show clearly.

**Why this priority**: it is a measure of identifiability that depends on no search and no
evidence approximation.

**Independent Test**: on periods of any split the detectability of each true manoeuvre and
the miss rate by detectability are reported, for Annex B and shifted targets side by side.

**Acceptance Scenarios**:

1. **Given** a true manoeuvre the bearings barely show, **When** it is left out, **Then** the
   fit's cost rises by less than the evidence needs to declare a manoeuvre.
2. **Given** a manoeuvre cut by the period's edge, **When** detectability is computed,
   **Then** it is reported apart.

---

### User Story 2 - What would a system told only the detectable manoeuvres achieve? (Priority: P1)

The owner sees the gap between the control and the fit told the true history split in two:
the part that remains even for a system told every detectable manoeuvre (identifiability),
and the part between that system and the control (attainable by a better search or
evidence).

**Why this priority**: it is the decision. It says whether a proposer is worth trying.

**Independent Test**: one scoring run gives the two parts on the shifted split with
intervals, at each registered detectability threshold, beside the same on Annex B data.

**Acceptance Scenarios**:

1. **Given** the registered thresholds, **When** the test seed is scored, **Then** the share
   of the gap that is identifiability is stated with its interval at each, and the verdict
   by the registered rule.
2. **Given** a reference whose fit drifts, **When** it is used, **Then** its times are held
   and the share of periods so treated is stated.

---

### User Story 3 - What is knowing the true statistics worth? (Priority: P2)

A researcher sees the control's search run with the shifted targets' own statistics as its
prior: the classical ceiling for "the prior was wrong".

**Independent Test**: the true-prior search's error and manoeuvre counts are reported beside
the control's on the shifted splits.

---

### User Story 4 - The standing system and what study L's record owes (Priority: P2)

The owner sees the classical control recorded as the standing time-late system, with its
known limits, and the omissions the panel listed made good: which weights the test scored,
the export check on the trained models, the tuned IMM and EKF read as tracks beside, a
reference fitted to edited bearings where there are outliers, and tests for the code that
produced the decided numbers.

**Independent Test**: each item exists in the repository with its evidence, or is stated as
not possible with the reason.

### Edge Cases

- A period with no whole true manoeuvre: nothing to class; reported and left out of shares.
- Two true manoeuvres so close that leaving one out is absorbed by the other.
- A manoeuvre whose removal makes the fit diverge.
- The control declaring a manoeuvre where the truth has an undetectable one: neither a hit
  nor a false alarm in the detectable reading.
- A threshold at which no manoeuvre of a period is detectable: the reference is the
  no-manoeuvre fit.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen**

- **FR-001**: C, C″, and the registered code paths, plans and records of Gate T and specs
  014 to 016 MUST NOT change in behaviour. The control is run as study L registered it.

**Detectability**

- **FR-002**: For each whole true manoeuvre of a period the study MUST compute its
  detectability: the rise in the bearings' cost when the true history is refitted without
  it, the other manoeuvres' times held. It uses the truth and is a reading, not a system.
- **FR-003**: The control's missed and found manoeuvres MUST be reported by detectability
  band, with the false manoeuvres beside, on Annex B and shifted targets.

**The gap, split**

- **FR-004**: A reference told only the detectable manoeuvres (those above a threshold)
  MUST be fitted with their times held, at each registered threshold.
- **FR-005**: The gap from the control to the true-history reference MUST be split into
  the part from the full reference to the detectable-only reference and the part from that
  to the control, paired per period with intervals, at every registered threshold and
  under each way of fitting the reference.
- **FR-006**: The search MUST also be run with the split's own manoeuvre statistics as its
  prior, reported beside.
- **FR-007**: The verdict's rule, thresholds, sample sizes and what follows MUST be fixed in
  a decision record before the fresh seeds exist, with the power of the rule stated from
  tuning data. No rule may be registered whose outcome is forecast as near even.

**Owed to study L's record**

- **FR-008**: The digests of the weights scored in study L's test MUST be recovered from the
  run's shard headers and committed, or the failure to recover them recorded.
- **FR-009**: The export check MUST be run on the three trained checkpoints.
- **FR-010**: The tuned IMM and EKF read as tracks, and one leg, MUST be scored on the same
  periods in this study.
- **FR-011**: Where a split has outliers, a true-history reference fitted to the edited
  bearings MUST be reported beside the unedited one.
- **FR-012**: The runner and the scorer of study L MUST gain unit tests.

**Process**

- **FR-013**: Every statistic MUST be reported with its median per-period ratio and the
  shares of periods over twice as bad on each side; every table MUST be generated by a
  committed script; the record MUST list what was promised and not delivered.
- **FR-014**: Seeds: 342 tuning, 343 validation, 344 test. The test is scored once.
- **FR-015**: A five-reviewer panel MUST decide the result; kickoff and slides posts as the
  constitution requires. The SRD's §9 MUST record the control as the standing time-late
  system (proposed; the owner merges).

### Key Entities

- **Detectability**: per true manoeuvre, the cost its omission adds.
- **Detectable-only reference**: the fit told the manoeuvres above a threshold.
- **True-prior search**: the control's search with the split's own statistics as prior.
- **Gap split**: identifiability part and attainable part, with intervals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The share of the shifted-prior gap that is identifiability is stated with a
  95% interval at each registered threshold, and the verdict by the registered rule.
- **SC-002**: The miss rate of the control is stated for manoeuvres above and below each
  threshold, on Annex B and shifted targets.
- **SC-003**: The owner can read from one table whether a proposer inside the search has
  anything to find, and how much.
- **SC-004**: Each item study L's record owes is delivered or its impossibility recorded.

## Assumptions

- The control's settings are study L's, unchanged; nothing is tuned for the shifted split.
- Detectability is measured on the bearings alone (no prior), so that it does not depend
  on the prior under question.
- Thresholds are in units of the cost a manoeuvre must save for the evidence to declare it
  under Annex B's prior, read from tuning data; three values are registered.
- If the gap is mostly identifiability, the learned-proposer option is not taken and the
  time-late track is written up; if mostly attainable, a proposer study is proposed to the
  owner. A mixed result is reported and the owner decides.
