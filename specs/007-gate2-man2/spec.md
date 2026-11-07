# Feature Specification: Gate 2 on MAN2, end-to-end learning on the owner's manoeuvre model

**Feature Branch**: `007-gate2-man2` (developed on `claude/inspiring-curie-j192v9`)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: Gate 2 on MAN2 after Gate S. The classical segmenter C (with the Gate
S panel's fixes) is the segmenter and the control. A learned model E (the Gate 1 encoder's
weighting and initialisation heads, plus learned segmentation acting where C makes its
decisions) is trained end to end through the physics layer. It is judged on a fresh test seed
against the SRD's three Gate 2 criteria and one added learning criterion: E must recover more of
the one-leg-to-oracle gap than C.

**SRD traceability**: SRD §5 (references, metrics, statistics; the Gate 2 MAN row), §7 step 4 as
superseded by Annex A §A.9 (Gate 2 uses Gate S's carried segmenter, C, and reports its "half the
gap to the oracle" for C too), §3 (MAN2 data), §4 (encoder, heads, physics layer, implicit
differentiation), Annex B (the owner's manoeuvre model); constitution 1.2.0 I–VI.

**Owner decisions this spec implements**:
- **2026-11-05:** a learned nominator, or evidence trained through C's confirmation step, is
  tested within Gate 2, not as a separate gate.
- **2026-11-06:** keep the SRD's three Gate 2 criteria and add one learning criterion. E must
  recover more of the gap than C fed to the physics layer with no learned weights, with the
  interval wholly above zero, and with a shuffled-label control as in Gate S. The SRD amendment
  is opened by the agent and merged by the owner.

**Why the added criterion.** On MAN2, C with no learning already meets the SRD's three criteria
on validation:
- it beats the frozen IMM (0.22 × its median range error);
- its settled rows are far inside 1.1 × the one-leg fit;
- it recovers 0.89 of the one-leg-to-oracle gap, against the 0.5 required.

So without a criterion against C, Gate 2 could pass with nothing learned.

## Background from Gate S (`experiments/20261105-gs-r2/`)

- C recovers 0.898 of the gap on the test rows; 0.838 on the rows every estimator answers. One
  leg and the IMM fail outright (no plausible estimate) on about a quarter of the rows.
- Rows ending inside an open transition are C's weakest: 0.66 of the gap against 0.91 elsewhere.
  The whole difference between Gate S's learned segmenter L and C sat on those rows.
- L's evidence was trained through the additive search's lattice. That is the weaker nominator,
  and L added nothing measurable. One failed fit in the search's cost table dominated its
  validation loss and stopped training early.
- C is 2.7 × the known-manoeuvres Cramér–Rao bound in range; the oracle is 1.6 ×.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A classical control that is fixed before learning starts (Priority: P1)

A researcher re-validates C with the panel's fixes on the validation split. The open-transition
hand-over is chosen there, and C is frozen by its parameter and code digests before any model is
trained. Every Gate 2 comparison is then made against a control that cannot move.

**Why this priority**: the learning claim is E minus C. If C changes after training starts, the
claim means nothing.

**Independent Test**: C's validation record reproduces from its committed plan on CI. The
decision record names C's parameter digest and code digest. The gate refuses segmentations whose
digests differ.

**Acceptance Scenarios**:

1. **Given** the fixed C, **When** it is scored on validation with each of the three
   open-transition hand-overs, **Then** the convention with the lowest median range error over
   G5 rows is chosen. It is recorded with its open-at-k stratum and frozen in the decision record.
2. **Given** a segmentation made by other code, **When** it is given to the gate, **Then** the
   gate refuses it and names the digest that differs.

---

### User Story 2 - A learned model trained end to end where C makes its decisions (Priority: P1)

A researcher trains E: the encoder's per-bearing weights and initialisation, plus learned
segmentation in one of the owner's two forms:
- **(a)** a learned nominator whose candidates C's confirmation tests;
- **(b)** evidence trained through the confirmation step itself.

The loss is the downstream error of the physics layer's estimate, through the solve. Three
seeds and a shuffled-label control train on free runners within a declared budget. The carried
seed is chosen by a rule fixed in advance.

**Why this priority**: this is the experiment. Gate S showed that learning attached to the wrong
stage changes nothing, so this design puts it where C's estimate is decided.

**Independent Test**: an untrained E reproduces C's estimate. On a small training set E's
outputs vary across rows. The loss decreases on a fixed validation slice, measured with a robust
statistic.

**Acceptance Scenarios**:

1. **Given** E at initialisation, **When** it is scored, **Then** its segmentation and estimate
   equal C's within the physics layer's tolerance.
2. **Given** a training prefix with an absurd cost (a failed fit), **When** the loss is computed,
   **Then** the prefix is clipped or excluded and early stopping uses a robust statistic, so one
   prefix cannot decide it.
3. **Given** the shuffled-label control, **When** it is scored on validation, **Then** its
   comparison with C is recorded, and S4-style voiding applies if it beats C.

---

### User Story 3 - Gate 2 judged on a fresh seed with all references on the same rows (Priority: P1)

A researcher scores E, C and every reference on a fresh test seed:
- the references: naive, one-leg batch least squares, the frozen IMM and EKF, GLR + confirm and
  the oracle;
- the rows: σ = 1° G5 rows;
- the statistics: scenario-clustered paired 97.5% intervals.

The machine verdict names each criterion's outcome. The agent review panel decides.

**Why this priority**: the gate is the deliverable. Its verdict decides whether learning on MAN2
is shown.

**Independent Test**: the gate CLI refuses mismatched decision, plan, seed, data, weights,
parameter or code digests. It reproduces its verdict from the committed per-row errors.

**Acceptance Scenarios**:

1. **Given** the committed decision record and a fresh test split generated after it, **When**
   the gate runs, **Then** it writes metrics, a report, a verdict and a manifest that binds every
   input by SHA-256, with the provenance read before any output.
2. **Given** a configuration that fails any gated check's point on validation, **When** the
   validation rule is applied, **Then** that configuration is not carried. If none is carried,
   the test split is not generated.

---

### User Story 4 - An honest record of what was and was not shown (Priority: P2)

A reader of the write-up sees:
- C's own half-gap beside E's;
- gross rates, finite-row medians and efficiency;
- the open-at-k stratum where the lever is;
- the shuffled control.

They can tell whether any gain came from learning, from the hand-over, or from rows where the
references fail.

**Independent Test**: the write-up's figures match the record. Every caveat the panel raises is
answered in `review.md`.

**Acceptance Scenarios**:

1. **Given** the gate's record, **When** the write-up is built, **Then** it states the verdict,
   the four criteria, C's own figures beside E's, and the follow-on fixed in advance.

### Edge Cases

- **E reproduces C exactly** (the learning collapses to zero): G2-d is inconclusive or fails,
  and the record says learning was not shown.
- **E beats C only on rows where the references fail:** reported through the finite-row figures
  and the strata. G2-d is still the gated statistic.
- **Every estimator fails on a stratum cell:** the cell reports +inf, not an error.
- **The shuffled control beats C on validation:** a G2-d pass is void, recorded as not passed.
- **A criterion has no rows:** it is inconclusive.
- **The container restarts mid-run:** every long job runs on CI and resumes, so no gate input
  depends on a local process.
- **Physics-layer results differ in the last bits between CPU families and batch layouts:** each
  run records its CPU model, and the gate reproduces from the plan's ordinals and shards.

## Requirements *(mandatory)*

### Functional Requirements

**Prerequisites (C, fixed before the decision record)**

- **FR-001**: C MUST include the Gate S panel's fixes:
  - monotone cost tables;
  - no transition overlapping another through an open one;
  - the open-transition hand-over as a declared parameter;
  - a code digest in every segmentation header.
- **FR-002**: The open-transition hand-over MUST be chosen on validation (seed 314, scoring
  ordinals 500–1499) among `knot_at_k`, `start_masked` and `start_chord`, by the lowest median
  range error over σ = 1° G5 rows. It MUST be applied to C and to E alike. The choice, its
  open-at-k stratum and the oracle's figures under it MUST be recorded before the decision
  record.
- **FR-003**: C MUST be re-validated on validation with the chosen convention, on the same rows
  as Gate S's validation:
  - gap recovered;
  - the comparison with GLR + confirm;
  - gross rates, efficiency and strata.

  Its parameter digest and code digest MUST be bound in the decision record.

**Data**

- **FR-010**: Data MUST be MAN2 (generator 0.6.0):
  - **validation:** seed 314 (tuning ordinals 0–499, scoring ordinals 500–1499);
  - **training stream:** seed 318;
  - **test:** seed 319, generated only after the decision record is committed.

  Digests MUST be pinned in the plan. Seeds 305 and 315 MUST NOT be used.
- **FR-011**: Gate rows MUST be the σ = 1° G5 rows (zig + 5/10/15/20 min where reached).
  Settled rows MUST be as `eval/rows.py`. The test split's σ = 1° scenarios MUST all be scored.

**Model E**

- **FR-020**: E's reported estimate MUST come from the physics layer (constitution III). E MUST
  consist of:
  - the encoder's per-bearing weights and initialisation heads (smooth activations, heads that
    cannot die; spec 004's prerequisites);
  - learned segmentation in form (a), a learned nominator, or form (b), confirmation-trained
    evidence (owner, 2026-11-05).
- **FR-021**: Planning research MUST settle on validation which form is built first. It MUST
  favour the cheapest form that plausibly reaches the open-at-k rows. Both forms MAY be carried
  as variants, each judged at 97.5%.
- **FR-022**: E at initialisation MUST reproduce C's segmentation and estimate within the physics
  layer's tolerance. A test MUST assert it.
- **FR-023**: E MUST be causal per prefix: its output at row k uses rows ≤ k only (as spec 005
  FR-002). Tests MUST cut the scenario at k, not mask the bearings after it.
- **FR-024**: Training MUST minimise the downstream error of the physics layer's estimate,
  CRB-normalised against the truth state, by implicit differentiation through the solve.
  Prefixes with absurd costs (failed fits) MUST be clipped or excluded, and early stopping MUST
  use a robust (median or trimmed) validation loss.
- **FR-025**: Three seeds of each carried configuration and one shuffled-label control MUST be
  trained. The carried seed MUST be chosen by the rule named in the decision record (default:
  the median seed by validation gap recovered).
- **FR-026**: Training MUST run on free 4-core GitHub runners in chained, resumable jobs. The
  throughput per epoch MUST be measured before the decision record.

**Gate 2**

- **FR-030**: Gate 2 MUST apply these criteria on the fresh test seed. Each is judged with a
  scenario-clustered paired bootstrap (2,000 resamples, 97.5%), `inverted_cdf` medians, and the
  point and the whole interval on the passing side:
  - **G2-a:** E's median range and course over all G5 rows, divided by the frozen IMM's, wholly
    below 1.
  - **G2-b:** on settled rows, E's range, course and speed within 1.1 × batch least squares
    (the one-leg fit; weak on MAN2, so also reported against C).
  - **G2-c:** E's gap recovered in median range, one leg to oracle, wholly above 0.5.
  - **G2-d (the learning claim):** E minus C in gap recovered (median range), wholly above zero.
    It is void if the shuffled-label control's interval against C on validation lies wholly
    above zero.
- **FR-031**: Gate 2 MUST pass if G2-a to G2-d all pass, and fail if any fails. It is
  inconclusive otherwise, and inconclusive counts as not passed for the follow-on. The decision
  record MUST say whether the constitution's one re-score on a larger fresh seed is taken; the
  default is not, by the minimum-effect argument of Gate S.
- **FR-032**: Validation rule: a configuration MUST be carried to test only if every gated
  check's point meets its limit on validation. If none is carried, the test split MUST NOT be
  generated, and the record says so.
- **FR-033**: The gate CLI MUST refuse a decision, plan, seed, data digest, weights digest,
  parameter digest or code digest that does not match. It MUST read provenance before writing
  any output, and bind every input file by SHA-256 in its manifest.
- **FR-034**: The SRD amendment adding G2-d (and recording that Gate 2 uses C, per Annex A §A.9)
  MUST be opened by the agent and merged by the owner before the decision record is committed.

**Reporting (constitution IV)**

- **FR-040**: The following MUST be reported, not gated, on the same rows:
  - naive, one leg, the frozen IMM and EKF, GLR + confirm, C, E and the oracle;
  - per estimator: medians and P90s, gross rates (no estimate; range error over 50%),
    finite-row medians, and efficiency against the known-manoeuvres bound;
  - C's half-gap;
  - strata: detectability, zig angle, time since zig, range band, latest change kind,
    speed-only and open-at-k.
- **FR-041**: The follow-on MUST be stated in the write-up with a recommended default, per the
  SRD's Gate 2 row. It is adopted if the owner has not objected by the next spec.

**Pre-registration and decision**

- **FR-050**: A decision record MUST be committed before any E training. It fixes:
  - seeds and digests;
  - configurations;
  - criteria and limits;
  - the carried-seed rule and the shuffled rule;
  - the open-transition convention;
  - C's parameter and code digests;
  - a forecast.
- **FR-051**: Gate 2's verdict MUST come from the agent review panel: five specialities, in
  rounds until no reviewer rejects and no blocker or major finding is open. `review.md` is
  committed and `decided_by` set.
- **FR-052**: Site pages MUST cover:
  - an algorithm note on E;
  - glossary terms;
  - the Gate 2 write-up.

### Key Entities

- **Gate2Decision**: the record of FR-050, bound by digest in the gate's manifest.
- **E model**: encoder, heads and learned segmentation. Its weights are bound by SHA-256 and its
  configuration by plan.
- **Gate2Record / verdict**: G2-a to G2-d with points and intervals, the reference used, the
  shuffled-rule outcome and `decided_by`.
- **Segmentation header**: as spec 005, with `code_sha256` and the parameter `open_handover`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: C's validation record with the chosen hand-over reproduces from its plan on CI.
  The gate refuses segmentations whose parameter or code digest differs from the decision's.
- **SC-002**: An untrained E equals C on validation: identical segmentations, and estimates
  within the physics layer's tolerance.
- **SC-003**: One training epoch over the training stream fits the measured budget on a free
  4-core runner, and every training job resumes after interruption.
- **SC-004**: Gate 2's four criteria, gross rates, efficiency and strata are computed on every
  σ = 1° test scenario. A reviewer recomputes every interval from the per-row errors to the last
  digit.
- **SC-005**: The verdict is decided by the panel, and the write-up states what was shown and
  what was not, with C's own figures beside E's.

## Assumptions

- **Encoder:** the Gate 1 encoder design (spec 003, with spec 004's head fixes) is the starting
  point, retrained on MAN2. Gate 1's weights are not carried, since they were trained on CV data.
- **Settled rows and the IMM:** settled rows and the frozen IMM/EKF are as in Gate S (tuned on
  seed 314). The tracker caveat stands: they were tuned on rows that include their scoring rows.
- **Data budget:** the training stream size and epoch budget are set in planning from measured
  throughput.
- **C's frozen digests:** the decision record freezes C's code digest after the open-transition
  convention is chosen. Any later change to C's code needs a new decision record.

## Out of Scope

- Realistic bearing error.
- Multi-target engagements.
- The browser viewer.
- Uncertainty calibration.
- A Gate S re-score.

## Risks

| Risk | Mitigation |
| --- | --- |
| E collapses to C (learning adds nothing again) | Learning acts in confirmation or nomination, where C decides; the open-at-k rows are the measured lever; the untrained equality test makes a collapse visible |
| Training cost: gradients through confirmation are expensive | Planning research measures per-prefix cost; form (a) is cheaper and comes first if form (b) does not fit the budget |
| The gate passes on rows where the references fail | G2-d is against C, which fails on 0.4% of rows; finite-row figures are reported |
| Runner noise | Paired comparisons within one run; CPU model recorded; plans fix ordinals and shards |
