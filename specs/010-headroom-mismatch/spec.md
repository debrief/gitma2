# Feature Specification: Headroom under bearing-error mismatch (Gate H)

**Feature Branch**: `010-headroom-mismatch` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: Headroom gate (Gate H) under bearing-noise mismatch, with no learned
model. Owner decision 2026-11-09, after Gate 4 stopped at validation: before any further learning
work, measure whether there is anything for a learned component to win once the bearing errors
stop matching the estimator's model. Realistic bearing error in the generator (correlated, slowly
biased, unknown σ, outliers); the standing classical estimators scored against oracles that know
the true error model; a classical robust control; a pre-registered materiality criterion decided
by the panel; the scaled end-to-end regressor control recorded as the next step after this gate.

**SRD traceability**:
- §1 (realistic bearing error, deferred until Gate 2 is passed: it has been) and §7 step 5,
  second item (realistic bearing error).
- §5 (references on the same rows, efficiency against the bound, paired clustered statistics,
  fresh seeds). Gate H is a new §5 row, proposed as an amendment that the owner merges.
- `docs/research/10-reflection-headroom.md`: the reflection behind the decision.

**Owner decisions this spec implements**:
- 2026-11-09: the next spec is a headroom gate under bearing-error mismatch, not the Gate 4
  follow-on (course-probability fixes), which is set aside.
- 2026-11-09: after this gate, whatever its result, the scaled end-to-end regressor control
  (`docs/research/04-proposal.md` §3, option B: "was gitma undertrained?") runs on Modal within
  its free credit. That needs an account and a secret, which are the owner's to set up; it is a
  separate spec and no part of this one.

## Background (`docs/research/10-reflection-headroom.md`)

- Every learned component so far, once tested against a classical control, has reduced to a
  simple rule: Gate 1's heads died; Gate D's detector read the time since the zig; Gate S's L did
  not separate from C; at Gate 2 a zig veto and a fixed fade (C″) gave +0.018 of the gap and
  learning +0.007 beyond it; at Gate 4, 72% of the head's margin was a quadratic rule.
- The likely reason is structural. The generator's bearing errors are white and Gaussian with a
  known σ, and its target moves in constant-velocity legs: exactly the model the physics layer
  solves. Where an estimator's model is the truth, maximum likelihood is close to the best
  possible and learning has nothing to add.
- Learned and hybrid estimators in the literature win where the model is wrong or unknown
  (`docs/research/02-literature.md` §2). Real bearings are not white: they are correlated in
  time, carry a slowly moving bias, have a σ nobody tells the estimator, and include wild values.
- Whether that leaves room worth learning for is measurable without training anything. Research
  note 05 did the same for segmentation, and it was the most useful measurement in the project.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bearings with realistic error (Priority: P1)

A researcher generates engagements whose bearing errors are no longer white Gaussian with a known
σ. Four kinds of mismatch can be switched on separately or together, each at declared severities:
errors correlated in time; a slowly varying bias; a σ drawn per engagement and not told to the
estimator; occasional wild bearings. Everything else about the engagement (ownship, target,
manoeuvres, dropouts) is as MAN2. Each file records which mismatch it carries and the truth of it
(the error process's parameters and its per-bearing realisation), so that an oracle can use them.

**Why this priority**: nothing else in the gate exists without the data.

**Independent Test**: with every mismatch off, the new generator version's output is the current
version's, byte for byte in the data; with one on, the bearing errors' measured statistics match
the declared process, and truth, ownship and target tracks are unchanged.

**Acceptance Scenarios**:

1. **Given** a seed and every mismatch off, **When** a split is generated, **Then** it equals the
   current generator's split for that seed in every data byte.
2. **Given** a seed and one mismatch kind on, **When** the split is generated twice, **Then** the
   two are identical, and the tracks equal those of the mismatch-off split for the same seed.
3. **Given** a split with correlated errors at a declared correlation time, **When** the errors'
   autocorrelation is measured over the split, **Then** it matches the declared value within
   sampling error; likewise the bias drift, the σ distribution and the outlier rate.
4. **Given** any mismatch split, **When** an estimator reads its inputs, **Then** it receives the
   bearings and the nominal σ only; the mismatch truth is in fields only an oracle reads.

### User Story 2 - What knowing the error model would be worth (Priority: P1)

For each mismatch condition the researcher sees, on the same rows, how the standing estimators do
and how well the same solve does when it is told the truth about the errors. Two ceilings are
stated, because they answer different questions:

- the **attainable ceiling**: the solve given the true segmentation and the true error *model*
  (σ, correlation time, bias process, outlier rate) but not its realisation. A perfect learner of
  the error model could reach this, and no more;
- the **realisation ceiling**: additionally told which bearings were outliers. Nothing causal can
  reach it; it is reported so that the attainable ceiling is not mistaken for the best
  conceivable.

The Cramér–Rao bound under the true error model is reported beside both.

**Why this priority**: headroom is defined against the attainable ceiling. Measured against
anything looser, it would promise gains no estimator could deliver.

**Independent Test**: with every mismatch off, both ceilings equal the existing oracle on every
row; on a mismatch split the attainable ceiling's efficiency against the mismatch-aware bound is
near 1 on settled rows.

**Acceptance Scenarios**:

1. **Given** a mismatch-off split, **When** the ceilings are computed, **Then** each equals the
   existing oracle's predictions row for row.
2. **Given** a mismatch split, **When** the attainable ceiling is scored against the bound under
   the true error model, **Then** its efficiency on settled rows is reported per condition, and a
   value far from 1 is investigated before any headroom is quoted.
3. **Given** any row, **When** either ceiling is computed, **Then** it uses no bearing after that
   row's time.

### User Story 3 - Headroom, after the cheap classical fixes (Priority: P1)

The researcher sees, per mismatch kind and severity and per slice, how much of the distance from
the standing classical estimator (C″) to the attainable ceiling remains once a **classical robust
control** has had its turn. The control is what a careful engineer would try first, with nothing
learned: a robust loss against wild bearings, σ estimated from the residuals, and whitening by an
estimated correlation. Headroom that the control removes is not headroom for learning.

Results are stated twice: as a fraction of the gap, with intervals, and in operational units
(metres of range error, degrees of course, knots of speed, and minutes from the zig until the
solution is settled).

**Why this priority**: this is the number the gate decides on, and the control is what stops a
later learned component from being credited with a textbook fix (the lesson of Gates 2 and 4).

**Independent Test**: on a mismatch-off split the robust control is no worse than C″ beyond a
declared small tolerance, and the reported headroom is zero within its interval.

**Acceptance Scenarios**:

1. **Given** a mismatch split, **When** it is scored, **Then** naive, batch least squares, the
   re-tuned IMM and EKF, C, C″, the robust control and both ceilings are scored on the same rows.
2. **Given** the scores, **When** headroom is reported, **Then** each condition shows the C″ gap,
   the gap the robust control closes and the gap that remains, each with a paired
   scenario-clustered interval.
3. **Given** the same scores, **When** the operational table is read, **Then** every gap is also
   given in metres, degrees, knots and minutes to a settled solution.
4. **Given** a mismatch-off split, **When** headroom is computed, **Then** its interval contains
   zero.

### User Story 4 - A pre-registered verdict (Priority: P2)

Before any mismatch split is scored, a decision record fixes: the mismatch conditions and their
severities; the primary condition; the robust control's settings and how they are tuned; the
materiality threshold; the seeds. The settings are tuned on a tuning seed, the validation rule is
applied on a separate validation seed, and the verdict is scored once on a fresh test seed. The
agent review panel decides. The verdict is one of:

- **material**: enough headroom remains after the robust control. The follow-on is a learned
  component trained under mismatch, with C″ and the robust control as standing controls;
- **not material**: the learning track stops, and the result is published as it stands: on this
  problem the classical estimator with textbook robust fixes is close to the best attainable;
- **inconclusive**: one re-score on a larger fresh seed, then final (SRD §5).

**Why this priority**: as every gate; here it also guards against choosing severities until
headroom appears.

**Independent Test**: the decision record binds the plan by digest and is committed before any
scoring run on validation or test rows; the scorer refuses a partial test split.

**Acceptance Scenarios**:

1. **Given** the plan, **When** the decision record is committed, **Then** no estimator has been
   scored on validation or test rows of any mismatch split.
2. **Given** a verdict of not material, **When** the write-up is published, **Then** it states the
   null result plainly and names what was not tested.
3. **Given** any verdict, **When** the write-up is published, **Then** it records the scaled
   regressor control as the next step and what the owner must set up for it.

### User Story 5 - The reflection on record (Priority: P3)

A reader of the repository finds why the project changed direction: research note 10 states the
record of learned components against their controls, the structural explanation, the criticism of
the process (validation seed 314 reused across many tunings; authors and panel of one model
family; effects never stated in operational units) and the corrected reading of gitma's 3 × bound
(a small, undertrained model; the scaled test was proposed and never run).

**Why this priority**: it changes no number, but the decision must be traceable.

**Independent Test**: the note exists, is linked from the SRD's decision line and the kickoff post,
and every figure in it cites a committed record.

**Acceptance Scenarios**:

1. **Given** the SRD §9 line of 2026-11-09, **When** a reader follows its link, **Then** they reach
   the note and each of its figures names its experiment record.

### Edge Cases

- A mismatch severity so mild that it is indistinguishable from none: headroom is reported as
  zero within its interval, not omitted.
- A severity so harsh that every estimator, ceilings included, is undetermined on most rows: the
  condition is reported with its share of usable rows and cannot be the primary condition.
- Bias that is constant over the whole window is unobservable to any estimator (it rotates the
  whole solution): the ceilings cannot remove it, and the write-up says so rather than counting
  it as headroom.
- A robust loss that rejects true bearings around a target manoeuvre as outliers: the control is
  scored on mismatch-off data too, so that damage is visible.
- Estimated correlation or σ on a short leg (few bearings): the control must fall back to the
  nominal value, by a rule stated in the plan.
- The re-tuned IMM and EKF: tuned once per primary condition on the tuning seed, by the declared
  grids, so that the references are not handicapped by a tuning made for white noise.
- Rows on which an estimator states nothing or runs away: counted as in Gate S (the comparison is
  also given on the rows every estimator answers).
- C's nominations divide by σ: with an unknown σ the nominal value is used, and the effect on C's
  false alarms is reported, since a segmentation failure is not an estimation headroom.

## Requirements *(mandatory)*

### Functional Requirements

**Data**

- **FR-001**: The generator MUST offer, under a new version, four bearing-error mismatches that
  can be enabled independently: time-correlated error (a first-order process with a declared
  correlation time), a slowly varying bias (a declared drift process), an engagement-level σ drawn
  from a declared distribution and not given to the estimator, and outliers (a declared rate and
  spread).
- **FR-002**: With every mismatch off, the new version MUST reproduce the current version's data
  byte for byte for the same seed; existing fixtures, digests and gates MUST be unaffected.
- **FR-003**: Enabling a mismatch MUST NOT change the ownship track, target track, manoeuvres or
  dropouts drawn for a seed; only the bearing errors change.
- **FR-004**: Every mismatch file MUST record the condition (kinds and severities) and the truth
  an oracle needs: the error model's parameters per engagement and the per-bearing error
  components (correlated part, bias, outlier flag).
- **FR-005**: Estimators other than the ceilings MUST receive only the bearings, the times, the
  ownship track and the nominal σ. A test MUST show that the mismatch truth cannot reach them.
- **FR-006**: The model forms MUST come from open literature and be cited; the severities are a
  declared design grid that brackets plausible behaviour, fixed before any scoring. Nothing above
  OFFICIAL and no real sensor's figures may be used (constitution).
- **FR-007**: Seeds MUST be fresh and distinct for tuning, validation and test (320, 321, 322;
  the next fresh seed is then 323). Seed 314 MUST NOT be used for any choice in this spec.

**Ceilings and bound**

- **FR-010**: The attainable ceiling MUST be the declared physics-layer solve with the true
  segmentation and the true error model's parameters, without the realisation (no outlier flags,
  no bias values).
- **FR-011**: The realisation ceiling MUST additionally be told which bearings are outliers. It is
  reported, never the denominator of headroom.
- **FR-012**: The Cramér–Rao bound under the true error model MUST be computed for each condition
  and efficiency reported per slice for every estimator.
- **FR-013**: With every mismatch off, both ceilings MUST equal the existing oracle row for row.
- **FR-014**: The ceilings MUST be causal in the bearings (no bearing after the row's time).

**Estimators scored**

- **FR-020**: On the same rows: naive, batch least squares, the IMM and EKF, C, C″, the robust
  control, and the two ceilings. No learned estimator is trained or scored in this spec; the
  carried E MAY be scored for information only and takes no part in the verdict.
- **FR-021**: The robust control MUST be classical throughout: a robust loss, σ estimated from
  residuals, and whitening by an estimated correlation, applied to C″'s solve. Its settings MUST
  be fixed on the tuning seed and named in the decision record.
- **FR-022**: The IMM and EKF MUST be re-tuned on the tuning seed for the primary condition with
  declared grids and frozen before validation.
- **FR-023**: The robust control MUST also be scored on mismatch-off data, and its difference
  from C″ there reported.

**Headroom and reporting**

- **FR-030**: Headroom MUST be defined per condition as the share of the gap in median range
  error between C″ and the attainable ceiling that remains after the robust control, with a
  paired scenario-clustered bootstrap interval. The same is reported for course and speed.
- **FR-031**: Headroom MUST be reported per mismatch kind, per severity, for the combined
  condition, and per slice (time since the zig, time since the last manoeuvre, range band, open
  transition).
- **FR-032**: Every gap MUST also be reported in operational units: metres, degrees, knots, and
  the share of engagements with a settled solution by each scored time after the zig (settled as
  defined in the plan; a score, so it uses the truth).
- **FR-033**: Where C″'s loss under mismatch comes from segmentation (false or missed
  transitions) and not from estimation, the report MUST separate the two by also scoring C″'s
  solve on the true segmentation.
- **FR-034**: Comparisons between estimators MUST be made within one scoring run (the scorer's
  re-solves are not identical across CPU families).

**Gate**

- **FR-040**: Gate H's criteria MUST be proposed as an SRD §5 row in an amendment the owner
  merges, and fixed by a decision record, bound to the plan by digest, before any scoring on
  validation or test rows.
- **FR-041**: The decision record MUST name the primary condition, the severities, the
  materiality threshold, the validation rule, the seeds and forecasts.
- **FR-042**: Materiality (owner, 2026-11-09, before any result): on the primary condition (all
  four kinds at their central severities), G5 rows, the robust control's median range error
  exceeds the attainable ceiling's by at least 10% of the ceiling's, with the paired interval
  wholly above 10%; **not material** if the interval is wholly below 10%; otherwise inconclusive.
  Refined in planning (research R6; flagged for the owner in the SRD row): both sides are given
  the true segmentation, so that the segmentation shortfall already measured at Gates S and 2 is
  not counted as error-model headroom. The comparison on C's segmentation is reported beside it.
- **FR-043**: The validation rule MUST stop the gate before the test seed is generated only if
  the pipeline is unsound (a ceiling far from its bound, a control worse than C″ on mismatch-off
  data beyond tolerance). A small headroom on validation is a result to confirm on test, not a
  reason to stop: a null result needs its test score as much as a positive one.
- **FR-044**: The agent review panel decides the verdict. The write-up MUST propose the follow-on
  the verdict implies and record the scaled regressor control as the next step in either case.
- **FR-045**: The scorer MUST refuse a test scoring that covers fewer than every scenario of the
  primary condition.

**Record and reporting**

- **FR-050**: Research note 10 MUST record the reflection and the decision, citing committed
  records for each figure.
- **FR-051**: SRD §9 MUST gain the dated owner decision, and `AGENTS.md` the new status and seeds.
- **FR-052**: A kickoff post now and a slides post before the implementation PR (constitution
  1.3.0). The slides post carries: an illustration of each mismatch kind on one engagement's
  bearings; the headroom chart per condition (C″ gap, closed by the control, remaining); the
  operational table; track plots of C″, the control and the attainable ceiling on a
  representative engagement.

### Key Entities

- **Mismatch condition**: the kinds enabled and their severities; one is primary.
- **Mismatch truth**: per engagement, the error model's parameters; per bearing, the correlated
  component, the bias and the outlier flag. Read by ceilings only.
- **Attainable ceiling / realisation ceiling**: the two oracle estimators of User Story 2.
- **Robust control**: the classical estimator of User Story 3.
- **Headroom**: the remaining share of the C″-to-attainable-ceiling gap, per condition and slice.
- **Gate H plan and decision record**: conditions, settings, threshold, seeds, forecasts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With mismatch off, 100% of data bytes equal the current generator's for the same
  seed, and both ceilings equal the existing oracle on 100% of rows.
- **SC-002**: For each mismatch kind, the measured error statistics on the tuning split match the
  declared process within sampling error.
- **SC-003**: The attainable ceiling's efficiency against the mismatch-aware bound on settled
  rows is reported for every condition; on the primary condition it is within a band the
  decision record declares.
- **SC-004**: For every condition, the report gives the C″ gap, the share the robust control
  closes and the share remaining, each with an interval, and each also in metres, degrees, knots
  and minutes.
- **SC-005**: The decision record is committed before any validation or test scoring, and the
  panel returns one of three verdicts on the test seed.
- **SC-006**: A reader can tell from the write-up alone whether further learning work is
  justified, what size of gain is available in operational terms, and what was not tested.
- **SC-007**: No learned model is trained in this spec.

## Assumptions

- Realistic bearing error is in scope now (SRD §1: deferred until Gate 2 is passed; Gate 2
  passed). Proposing Gate H's row is an SRD amendment, which the owner merges.
- The engagement model is MAN2 (generator 0.6.0) unchanged; only the bearing errors differ. σ's
  nominal value stays 1°.
- Severities are a declared grid (plan research R2): a search found the model forms in open
  sources but no authoritative open figures. The owner, who knows the domain, is asked to confirm
  or change the grid before the decision record. Each kind is run at three severities.
- C″ (C with the zig veto and the fixed fade, `experiments/20261107-g2-veto/`) is the standing
  classical estimator, as the Gate 2 write-up recommended; C is frozen at its Gate 2 code and
  parameters.
- The 10% materiality threshold was confirmed by the owner on 2026-11-09 with no result behind
  it; the decision record binds it.
- Target-motion mismatch (a target that does not move in constant-velocity legs) is a second
  kind of model error and is out of scope here; the write-up lists it as not tested.
- Scoring runs on CI (`score/**`), not in a session; one long run at a time.
- The scaled regressor control needs a Modal account and a repository secret, which only the
  owner can create; this spec does not depend on it.
