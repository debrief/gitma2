# Feature Specification: Uncertainty calibration of the Gate 2 estimator (Gate 3)

**Feature Branch**: `008-uncertainty-calibration` (developed on `claude/happy-galileo-ksybjj`)

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: Spec 008, uncertainty calibration (SRD §7 step 5, first item; the
Gate 2 follow-on recommended in `site/blog/2026-11-08-gate-2.md`, adopted unless the owner
objects). The carried Gate 2 estimator E (e-s3) reports, at every scored row, an uncertainty that
can be trusted. The uncertainty is the physics solve's covariance, corrected by a small learned
calibration. It is judged on a fresh test seed against pre-registered calibration criteria (a new
Gate 3, proposed as an SRD amendment). The spec also takes the Gate 2 panel's follow-ons. The
classical control C″ (zig veto + fixed fading memory) stays as a standing control.

**SRD traceability**:
- SRD research question (§1–2: "with calibrated uncertainty");
- §4 (the calibration scalar head; β-NLL on the calibrated covariance);
- §5 (references, statistics; a new Gate 3 row by amendment);
- §7 step 5 (uncertainty calibration first);
- research note 04 §2 ("the solve's covariance σ²(JᵀJ)⁻¹ is free; a small scalar head calibrates
  it");
- constitution 1.2.0 I–VI.

**Owner decisions this spec implements**:
- **SRD §7 step 5 default order:** uncertainty calibration comes first.
- **Gate 2 follow-on, recommended 2026-11-08 and adopted unless the owner objects:** carry E, and
  keep C″ as a standing control.

## Background from Gate 2 (`experiments/20261107-g2/`, `experiments/20261107-g2-veto/`)

- **E passed G2-a to G2-d on seed 319.** E − C in gap recovered was +0.025 [+0.018, +0.031].
- **Two classical rules reproduce about 72% of that margin.** C″ (zig veto + fixed fading
  memory, nothing learned) − C was +0.018, and E − C″ was +0.007 [+0.001, +0.012].
- **No prediction file carries a covariance today.** The physics layer computes one, and
  conformance tests check it, but scoring uses point estimates only.
- **E-w and the fade rescale the bearing weights,** so their solve covariances are not on C's
  scale (panel R2-5). Some calibration is needed before any covariance is used.
- **Gate 1's calibration (scale) head died in training,** along with the other heads. No working
  calibration exists yet.
- **Gross rows remain.** About 10% of E's test rows have range error above 50%. Any calibration
  claim must say what it does on them.
- **The panel's follow-ons** (`experiments/20261107-g2/review.md`) are listed under FR-060.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every estimate states its uncertainty (Priority: P1)

A researcher reads a prediction file from C, E or a classical control and finds, beside each
row's state, the solve's 4 × 4 covariance and the standard deviations of range, course and speed
derived from it. Every scored estimator then carries its uncertainty on the same rows. Nothing
about the point estimates changes.

**Why this priority**: calibration cannot be measured, trained or gated without the reported
covariance. It is also the cheapest part, and every later story depends on it.

**Independent Test**:
- C's, E's and C″'s prediction files on validation carry a covariance on every row with a
  plausible estimate.
- Re-running Gate 2's validation scoring on the new files gives the same point errors to the
  last bit.

**Acceptance Scenarios**:

1. **Given** a prediction file from any physics-layer estimator, **When** a row has a plausible
   estimate, **Then** it carries a symmetric, positive-definite covariance and range, course and
   speed standard deviations, all in double precision.
2. **Given** the Gate 2 validation files re-made with covariances, **When** they are scored,
   **Then** every point error equals the Gate 2 record's.

---

### User Story 2 - Know how well calibrated the estimators are now (Priority: P1)

A researcher measures calibration on validation, before any calibration is trained. Measured
estimators: C, E, E-w alone, C″, the frozen IMM and EKF (which report covariances), and the
oracle. Measures:
- **coverage** of nominal 68% and 95% intervals in log range, course and speed;
- **NEES**, the normalised estimation error squared, for the 4-state;
- **a proper score**, either the Gaussian negative log-likelihood or the interval score.

Each is reported overall and per slice: time since zig, rows open at k, range band, detectability
band, settled or not, and gross or not.

**Why this priority**: the decision record needs a measured baseline and a forecast, as Gate 2
had. If E's raw covariance is already calibrated, the gate is different.

**Independent Test**: the validation calibration record reproduces from its plan on CI, and a
reviewer recomputes every coverage and NEES figure from the per-row records.

**Acceptance Scenarios**:

1. **Given** validation scoring ordinals 500–1499, **When** calibration is scored, **Then**
   coverage, NEES and the proper score are reported for every estimator, with 97.5%
   scenario-clustered intervals, overall and per slice.
2. **Given** an estimator with no estimate on a row, **When** coverage is computed, **Then** that
   row counts as not covered. The share of such rows is reported beside the coverage.

---

### User Story 3 - A calibration that is learned, and one that is not (Priority: P2)

A small calibration head turns E's solve covariance into a calibrated covariance. It is trained
on the training stream by a Gaussian likelihood loss that does not chase gross outliers (β-NLL,
β ≈ 0.5). It changes only the covariance, never the state.

Controls:
- three seeds;
- a shuffled-label control;
- a classical control: a per-slice temperature fitted on validation tuning ordinals 0–499, with
  no learned features.

**Why this priority**: SRD §4 names the calibration head, and the constitution requires learning
to be tested against a control. Gate 2 showed that classical rules can stand in for what was
learned, so the classical temperature is the bar.

**Independent Test**:
- An untrained calibration head reproduces E's raw covariance.
- E's point estimates are unchanged by the head, to the last bit.
- The head's validation score improves on the raw covariance, and the classical temperature's is
  reported beside it.

**Acceptance Scenarios**:

1. **Given** zero head outputs, **When** E predicts, **Then** the calibrated covariance equals the
   raw covariance.
2. **Given** a trained head, **When** Gate 2's validation scoring is re-run, **Then** every
   G2-a…G2-d point is identical to before.
3. **Given** the shuffled control, **When** it is trained, **Then** its last-epoch weights are
   scored on validation as well as its best-epoch weights (panel G4).

---

### User Story 4 - A pre-registered calibration gate on a fresh seed (Priority: P2)

Gate 3's criteria are fixed in an SRD amendment and in a decision record, before any calibration
training: coverage, NEES, and a learning criterion against the classical temperature. They are
scored on a fresh test seed (320) by the agent review panel.

**Why this priority**: this is the gate, and every earlier gate was pre-registered, fresh-seeded
and panel-decided.

**Independent Test**: the decision record binds the plan, the criteria and the seed before
training. The gate refuses inputs whose digests differ. A reviewer recomputes every interval.

**Acceptance Scenarios**:

1. **Given** the decision record, **When** seed 320 is generated, **Then** its digest is recorded
   beside the decision, after the carried calibration is fixed on validation.
2. **Given** the test record, **When** the panel reviews it, **Then** every criterion has a
   point, an interval and an outcome, and the verdict names the panel round.

---

### User Story 5 - The Gate 2 panel's follow-ons (Priority: P3)

The process gaps found in Gate 2 are closed for this gate and later ones:
- a time-late variant of E (constitution IV);
- shuffled controls scored at their last epoch;
- the scorer asserts that the whole test split is scored, and merge steps count scenarios;
- the scorer stores the errors it re-solves, so a re-score on another CPU family reuses them;
- prediction headers bind the settings of classical controls;
- the shuffled-rule outcome is read from the validation record, not hand-written.

**Why this priority**: none of these changes a Gate 2 number. Each one removes a way a later gate
could go wrong.

**Independent Test**: each follow-on has a unit test or a check that fails on the old behaviour.

**Acceptance Scenarios**:

1. **Given** a test-split score whose ordinals do not cover every σ = 1° scenario, **When** gate
   mode runs, **Then** it refuses.
2. **Given** a stored error file from an earlier scoring, **When** a re-score runs on another
   CPU, **Then** C's and the references' errors are reused byte for byte.

---

### Edge Cases

- **Rows with no plausible estimate** (one leg and the IMM on about a quarter of rows; E on
  0.5%) count as not covered. Coverage is also reported on the rows each estimator answers.
- **Gross rows** (range error above 50%): their coverage is reported separately. A calibration
  that covers them by inflating every row is visible in the proper score and in interval width.
- **Undetermined rows before or near the zig**, with range standard deviation much larger than
  range: coverage is measured in log range, and sharpness (median interval width) is reported
  beside coverage, so wide-but-honest is distinguishable from useful.
- **Course near ±180°** and **speed near zero**: course errors are wrapped, and the speed
  interval is truncated at zero; both are stated in the algorithm note.
- **IMM/EKF covariances** are filter covariances in a different parameterisation. They are
  mapped to range, course and speed by the same linearisation as the physics layer's, and the
  mapping is stated.
- **CPU-family dependence** (Gate 2): covariances are stored in the prediction files, so scoring
  never re-solves E.

## Requirements *(mandatory)*

### Functional Requirements

**Reported uncertainty**

- **FR-001**: Every physics-layer prediction row (C, E, E-w, the classical controls, the oracle)
  MUST carry:
  - the 4 × 4 state covariance at the row;
  - the standard deviations of range, course and speed, by first-order propagation;
  - a flag saying whether the covariance is usable.

  All are in double precision. Point fields MUST be unchanged.
- **FR-002**: The frozen IMM and EKF prediction rows MUST carry their covariances mapped to the
  same quantities.
- **FR-003**: Prediction headers MUST bind every setting of a classical control (veto window,
  fade coefficients) and the digest of any segmentation file read (panel G12, R2-7).

**Measurement**

- **FR-010**: Calibration MUST be measured on σ = 1° G5 rows of validation seed 314 (scoring
  ordinals 500–1499), for C, E, E-w alone, C″, the IMM, the EKF and the oracle, on the same rows.
  Measures:
  - coverage of nominal 68% and 95% intervals in log range, course and speed;
  - NEES of the 4-state (median, and the share of rows within the 95% χ²₄ bound);
  - a proper score.

  Each MUST have 97.5% scenario-clustered paired intervals (2,000 resamples), overall and per
  slice (FR-011).
- **FR-011**: Slices:
  - time since zig (each G5 time);
  - rows open at k;
  - range band;
  - detectability band;
  - settled or not;
  - gross or not.

  Sharpness (median interval width) MUST be reported beside coverage.
- **FR-012**: Rows with no estimate MUST count as not covered. Coverage on the rows each estimator
  answers MUST also be reported.

**Calibration**

- **FR-020**: The calibration MUST act on the covariance only. The carried E's states MUST be
  bit-identical with and without it (constitution III: the physics layer produces the estimate).
- **FR-021**: The learned calibration MUST be a small head on E's encoder state at the row,
  bounded so that zero output is the identity. Its form (scalar, or diagonal in range/course/speed
  axes) MUST be chosen in planning and recorded.
- **FR-022**: It MUST be trained on stream seed 318 by β-NLL (β declared in the plan, default
  0.5), with early stopping on validation tuning ordinals 0–499, three seeds and a shuffled
  control. Encoder and E weights MUST be frozen at the carried e-s3.
- **FR-023**: The classical control MUST be a temperature per slice. Its slices MUST be declared
  in the plan, and it MUST be fitted on validation tuning ordinals 0–499 by the same loss.
- **FR-024**: A time-late variant (non-causal encoder over the whole window, reporting the scored
  row) MUST be trained and scored on validation as constitution IV requires (panel G7). It MUST
  score at least as well as the causal model, or the shortfall is reported.

**Decision and gate**

- **FR-030**: Gate 3's criteria MUST be proposed as an SRD §5 amendment (a new row). The agent
  opens the amendment and the owner merges it. Defaults proposed, owner may change before any
  result:
  - **G3-a (coverage):** 95% intervals in log range, course and speed each cover between 0.92
    and 0.98 of all test rows, interval wholly inside;
  - **G3-b (consistency):** the median NEES over χ²₄'s median, interval wholly inside [0.8, 1.25];
  - **G3-c (learning):** the carried calibration beats the classical temperature on the proper
    score, paired difference wholly favourable, void if the shuffled control also beats it;
  - **G3-d (no regression):** G2-a to G2-d hold for the calibrated E (automatic under FR-020,
    and checked).
- **FR-031**: A decision record MUST be committed before any calibration training. It MUST fix:
  - the criteria;
  - the plan by digest;
  - the carried-seed rule (median by validation proper score);
  - the shuffled rule;
  - the validation rule;
  - the test seed 320;
  - a forecast.
- **FR-032**: Test seed 320 MUST be generated only after the carried calibration is fixed on
  validation (`carried.json`). The whole σ = 1° test split MUST be scored, and the gate MUST
  refuse a partial split (panel G10).
- **FR-033**: The verdict MUST come from the agent review panel: five specialities, in rounds,
  until no reviewer rejects and no blocker or major finding is open.

**Process follow-ons (panel)**

- **FR-060**: Shuffled controls MUST be scored at their last epoch as well as their best (G4).
- **FR-061**: Merge steps MUST count scenarios and refuse gaps (G11).
- **FR-062**: The scorer MUST store the errors it re-solves (C, one leg, oracle, references) and
  MUST reuse a stored file when given one (R2-6).
- **FR-063**: The test gate MUST read the shuffled-rule outcome from the validation record (G9).

### Key Entities

- **Prediction row (extended)**:
  - the existing fields;
  - the state covariance;
  - range, course and speed standard deviations;
  - a covariance-usable flag.
- **Calibration record**: per estimator and slice, coverage (68%, 95%) with intervals, NEES
  summaries, the proper score, sharpness and the no-estimate share.
- **Calibration head**: weights bound by SHA-256; its form and bound by plan.
- **Gate3Decision / Gate3Record**: as Gate 2's, with G3-a to G3-d.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every plausible prediction row from every physics-layer estimator carries a
  usable uncertainty. Re-scoring Gate 2's validation files gives identical point errors.
- **SC-002**: The validation calibration baseline reproduces from its plan, and a reviewer
  recomputes every coverage and NEES figure exactly.
- **SC-003**: An untrained calibration equals the raw uncertainty. A trained one leaves every
  point estimate unchanged.
- **SC-004**: Gate 3's criteria are computed on every σ = 1° scenario of seed 320, and the
  verdict is decided by the panel.
- **SC-005**: The write-up states, for E and for C″, how often the stated 95% interval contains
  the truth, overall and on gross rows. It also states whether learning beat the classical
  temperature.

## Assumptions

- **The carried E is e-s3, unchanged.** Calibration does not retrain E (FR-022), so Gate 2's
  point results carry over.
- **Covariance source:** the physics layer's Gauss–Newton covariance at the final iteration,
  scaled by σ², as the conformance tests already export it.
- **Proper score:** the Gaussian negative log-likelihood of the 4-state (with a stated floor), or
  the 95% interval score per quantity. The decision record picks one; the default is the
  interval score, because it is robust to gross rows.
- **Stream size and epochs** are set in planning from measured cost. The head is small, and
  frozen-encoder features can be cached.
- **Seeds:** 314 validation, 318 training stream, 320 test. 305, 315 and 319 are not reused; the
  next fresh seed after this spec is 321.

## Out of Scope

- Retraining E's point estimate.
- Realistic bearing error (SRD §7 step 5, second item).
- The browser viewer (third item).
- Multi-target engagements.
- Density heads or mixtures (research note 02 option 2). These are candidates if Gaussian
  calibration fails on gross rows.

## Risks

| Risk | Mitigation |
| --- | --- |
| Gross rows make any Gaussian calibration fail coverage | Coverage on gross and non-gross rows reported separately; sharpness reported; the criteria are proposed after the validation baseline (FR-030) |
| The learned head adds nothing over a temperature (as Gate 2's E-s over the veto) | G3-c is against the classical temperature; registered before training |
| The criteria are set with knowledge of validation | Criteria proposed in an SRD amendment before training, owner merges; test seed fresh |
| CPU-family dependence of re-solved errors | FR-062: stored errors reused; covariances stored in prediction files |
