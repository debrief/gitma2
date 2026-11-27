# Feature Specification: Where the regressor's gain comes from

**Feature Branch**: `038-gain-decomposition` (developed on `claude/lucid-wright-y1xstj`)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: owner 2026-11-27, "Follow on with option A": the panel's first
recommendation on spec 037. Prior-informed and mismatch-hardened classical controls, and a
decomposition of the regressor's gain into prior and bearings. CPU only, nothing trained, no
GPU spending, existing weights only.

**SRD traceability**:
- §5 (references on the same rows, efficiency per slice, paired clustered statistics, fresh
  seeds), §7 (the plan's controls), §9 (owner decisions). No gate row: a registered study with
  estimands fixed beforehand.
- Spec 037's record and panel review (`experiments/20261126-rmis/review.md`), whose findings 2
  and 3 this spec answers; specs 010 and 011 (the mismatch's cost is in C's segmentation; a
  Huber confirmation test did not close it); spec 012 (the margin's source is open; the
  ownship-only regressor exists); spec 016 (classical wild-bearing editing and an effective
  bearing sd).

**Owner decisions this spec implements**:
- 2026-11-27: option A. No GPU run; about $3 of the $50 remains and is not touched.

**Standing of the systems**: nothing is carried by this spec. C stays frozen; every hardened
variant is a control built around it. The regressors are spec 012's and spec 037's weights,
unchanged.

**Why this**: spec 037 found a regressor twice as good as the classical real-time system under
bearing errors, and its panel found that the comparison could not say why. Two explanations
were left standing: the classical segmenter is simply not hardened against those errors, and
the regressor knows the simulator's manoeuvre statistics and geometry while C″ is told nothing.
Until both are measured, the result cannot guide what is built next.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A classical system given a fair chance under bearing errors (Priority: P1)

A reader sees, under the primary mismatch condition and the kinds outside spec 037's training
mix, how much of the regressor's lead over C″ survives when the classical segmenter is hardened
by classical means: a raised confirmation threshold, and wild bearings edited out with an
effective bearing sd, each with the robust final solve.

**Why this priority**: the panel's largest finding was that the factor of two is C's segmenter
failing. If cheap classical hardening closes most of it, the headline changes.

**Independent Test**: one scoring run on the fresh seed gives the paired ratio best hardened
control ÷ fine-tuned regressor with its interval, beside C″-robust ÷ fine-tuned on the same
engagements, and the share of the gap the hardening closes.

**Acceptance Scenarios**:

1. **Given** the hardened controls' settings chosen on spent seeds and bound before the test,
   **When** the test seed is scored, **Then** the record states, per condition, how much of
   the gap between C″-robust and the fine-tuned regressor each control closes, with an interval.
2. **Given** clean data, **When** a hardened control is scored, **Then** its cost against
   C″-robust is stated; a control that buys robustness by losing clean accuracy is not hidden.

---

### User Story 2 - The pure prior, alone and inside a classical solve (Priority: P1)

A reader sees the regressor's gain over C″ split into three parts: what a model that reads no
bearings at all achieves (the simulator's prior given the ownship's track), what that prior adds
to C″'s classical solve, and what is left for reading the bearings.

**Why this priority**: it answers "prior or bearings", which spec 012 and spec 037 both left
open, with a control tight enough to move the solve.

**Independent Test**: on the test seed, the three ratios (prior alone, prior inside C″'s solve,
the fine-tuned regressor; each against C″-robust) in range, course and speed, clean and under
mismatch, and by how tight the bound is.

**Acceptance Scenarios**:

1. **Given** the ownship-only regressor, **When** it is scored alone, **Then** the record gives
   its error beside C″-robust and the fine-tuned regressor on the same rows, by range third and
   by how tight the bound is.
2. **Given** the hybrid solve with the ownship-only regressor as its prior, **When** scored,
   **Then** the record gives the share of the fine-tuned regressor's gain over C″-robust that
   this "C″ told the prior" obtains, with an interval, and says what remains.

---

### User Story 3 - Where the simulator's prior is wrong (Priority: P1)

The same systems are scored on engagements whose targets are busier than the training
statistics and on geometry outside the training ranges, clean and under the primary mismatch
condition. C″ is told no prior, so it is the yardstick that should not move.

**Why this priority**: a gain that is prior knowledge should shrink when the prior is wrong; a
gain that is reading the bearings should not.

**Independent Test**: the paired ratio C″-robust ÷ fine-tuned on the shifted and held-out
splits beside the in-distribution split, with the difference of log ratios and its interval.

**Acceptance Scenarios**:

1. **Given** the shifted-prior and held-out-geometry splits, **When** scored, **Then** the
   record states for each whether the regressor's lead holds, shrinks or reverses against the
   in-distribution split, in range, course and speed.
2. **Given** a split on which every system degrades, **When** read, **Then** the record says
   so and does not credit the regressor with a relative gain alone.

---

### User Story 4 - The readings spec 037 owed (Priority: P2)

The test record carries the readings that spec 037 promised and did not run, on its own
decided systems: by time since the last target change, by whether the first bearing is an
outlier, by whether C″'s segmentation was right (classified on rows other than those scored),
efficiency by how tight the bound is, and every comparison also on rows every system answers.

**Independent Test**: each reading appears in the generated tables with its engagement counts.

### Edge Cases

- A hardened control closes most of the gap on development data: by the stop rule that control
  is registered as the headline comparator before the test, and the record says the earlier
  headline was a property of an unhardened segmenter.
- The ownship-only regressor was trained on clean data and never fine-tuned: it reads no
  bearings, so bearing errors cannot reach it; this is asserted by a test, not assumed.
- The prior inside C″'s solve is given a weight chosen on spent data; a weight at the grid's
  edge extends the grid before registration.
- A shifted or held-out split has no rows at the scored prefixes, or breaks the generator's
  limits: found on spent seeds before registration (generated locally first).
- Every system degrades on a split so that ratios are ratios of failures: absolute errors are
  given beside every ratio.
- A decision line sits within the bootstrap's own noise: thresholds are checked over bootstrap
  seeds on development data before they are registered, and three decimals are printed near a
  line.
- The classical systems do not answer every row: shares answered are registered as outcomes.

## Requirements *(mandatory)*

### Functional Requirements

**Hardened classical controls (part 1)**

- **FR-001**: Two hardened segmenter controls MUST be built around the frozen C, each followed
  by Gate H's robust final solve: (a) C with a raised confirmation threshold; (b) C run on
  bearings from which wild ones have been edited by a classical rule, with an effective bearing
  sd estimated from the bearings. C's code and parameters stay as frozen and its digests are
  asserted unchanged.
- **FR-002**: Each control's settings MUST be chosen on spent seeds by a rule stated before the
  choice (the pooled range ratio against C″-robust over clean and primary data, with clean-data
  cost reported), and bound in the decision record.
- **FR-003**: Neither control may be told the condition, the error model or the true manoeuvre
  times.

**The pure prior (part 2)**

- **FR-010**: Spec 012's ownship-only regressor MUST be scored alone on the same rows as every
  other system. A test MUST show its output does not depend on the bearings.
- **FR-011**: A "C″ told the prior" control MUST be built: spec 037's hybrid solve with the
  ownship-only regressor's estimate and stated uncertainty as the prior, its weight chosen on
  spent seeds from a grid that brackets the best value.
- **FR-012**: The decomposition MUST be reported as paired ratios against C″-robust on the same
  engagements: prior alone; prior inside C″'s solve; the fine-tuned regressor; and the share of
  the fine-tuned regressor's log gain that the prior inside C″'s solve obtains, with an
  engagement bootstrap interval.

**Where the prior is wrong (part 3)**

- **FR-020**: Two further splits MUST be scored, each clean and under the primary mismatch
  condition: a shifted manoeuvre prior (busier targets than the training statistics) and
  geometry outside the training ranges. The ranges files are checked locally against the
  generator's limits and for rows at the scored prefixes before registration.
- **FR-021**: The estimand is the difference of the paired log ratio C″-robust ÷ fine-tuned
  between each such split and the in-distribution split, with an interval; "shrinks" if wholly
  below zero, "holds" if the interval lies within a stated band about zero, otherwise "not
  separated". Absolute errors are given beside.

**Owed readings (part 4)**

- **FR-030**: The record MUST give, for C″-robust ÷ fine-tuned and C″-robust ÷ hybrid: by time
  since the last target change; by whether the first bearing is an outlier; by whether C″'s
  segmentation was right, classified on rows other than those scored; efficiency in range,
  course and speed by thirds of the bound; and the same ratios on rows every system answers,
  with engagement counts.

**Registration and reporting**

- **FR-040**: Development uses spent seeds only (321, 370, 371). A decision record MUST precede
  the test: estimands, thresholds, the controls' bound settings, forecasts labelled by their
  basis, the code and plan digests, the seed. Fresh test seed 372, generated in its run only,
  scored once. The readings script is committed before the test is launched.
- **FR-041**: Statistics as spec 037's protocol (per-engagement medians, paired log ratios,
  engagement bootstrap, three seeds pooled where a system has three), with, beside every ratio:
  the median ratio, shares better, twice as good and twice as bad, course and speed, and
  absolute errors.
- **FR-042**: **Stop rule**: if on development data a hardened control closes at least half of
  the log gap between C″-robust and the fine-tuned regressor under the primary condition, that
  control is registered as the headline comparator for every reading that names C″-robust.
- **FR-043**: Three reviewers review the test record. A kickoff post now; a write-up and a
  slides post before the PR: the decomposition as a stacked chart, the hardened controls beside
  C″ and the regressor by condition, the lead by split, track plots of one engagement.
- **FR-044**: What was promised and not run is listed in the record. No GPU run is made and no
  money is spent.

### Key Entities

- **Hardened control**: C with a raised threshold, or C behind bearing editing and an effective
  sd, plus the robust final solve; classical, told nothing.
- **Pure prior**: the ownship-only regressor; reads the ownship's track and the stated bearing
  sd, never a bearing.
- **C″ told the prior**: the hybrid solve with the pure prior as its prior.
- **Splits**: in-distribution; shifted manoeuvre prior; held-out geometry; each clean and under
  the primary mismatch condition (and the kinds outside the training mix for part 1).
- **Decomposition**: the fine-tuned regressor's log gain over C″-robust, and the shares the
  prior alone and the prior inside C″'s solve obtain.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The record states how much of the gap between C″-robust and the fine-tuned
  regressor each hardened control closes under mismatch, with intervals, and its clean-data
  cost.
- **SC-002**: The record states the share of the regressor's gain that the pure prior inside a
  classical solve obtains, clean and under mismatch, with intervals, and by how tight the bound
  is.
- **SC-003**: The record states, for a shifted prior and for held-out geometry, whether the
  regressor's lead holds, shrinks or is not separated.
- **SC-004**: Every reading spec 037 owed appears with its counts.
- **SC-005**: The decision record and the readings script predate the test launch; the test is
  scored once; no GPU time is used.
- **SC-006**: A reader can say from the write-up alone which of these the evidence supports:
  the lead is mostly an unhardened segmenter; mostly prior knowledge; mostly reading the
  bearings; or a stated mixture.

## Assumptions

- Seeds: development on spent 321, 370 and 371; test 372; the next fresh seed is 373.
- The ownship-only regressor's weights are retrievable from spec 012's results branch with
  their digest.
- The shifted-prior and held-out ranges reuse existing files where they fit the scorer's
  prefixes (the time-late track's shifted ranges and the MAN2 held-out ranges); if they do not,
  new ones are derived and checked on spent seeds first.
- Scoring runs on CI on CPU. Each classical segmenter run costs about 35 to 60 minutes per 100
  engagements, so the test size is set from that (about 500 engagements a split and condition).
- The regressors are real-time (causal); the time-late track is untouched.

## Out of Scope

- Any training, fine-tuning or GPU run. Carrying or exporting any system.
- A new learned segmenter; changes to C; real data.
- The conditional coverage study of the intervals (the panel's second recommendation).
