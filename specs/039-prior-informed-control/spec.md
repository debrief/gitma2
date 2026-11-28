# Feature Specification: a classical control given the generator's priors

**Feature Branch**: `039-prior-informed-control` (developed on `claude/lucid-wright-y1xstj`)

**Created**: 2026-11-28

**Status**: Draft

**Input**: User description: owner 2026-11-28, "Follow panel's recommendation": the first item of
spec 038's panel's order. A causal classical estimator given the generator's own manoeuvre, speed
and range priors, on CPU, spent seeds first, read by thirds of the bound. Nothing trained.

**SRD traceability**:
- §5 (references on the same rows, efficiency per slice, paired clustered statistics, fresh
  seeds), §7 (the plan's controls), §9 (owner decisions). No gate row: a registered study.
- Spec 038's record and review (`experiments/20261128-gd/review.md`, findings 4 and 5): the
  prior control was too weak to move the solve; against a solve told the true manoeuvre times the
  regressor wins where the bound is loose and loses where it is tight. Spec 012's control run
  (a precision-weighted range prior did not explain the margin). Specs 013 to 016 (the evidence
  search under Annex B's prior).

**Owner decisions this spec implements**:
- 2026-11-28: follow the panel's recommendation. No GPU run; no money.

**Standing of the systems**: nothing is carried by this spec. C stays frozen and C″ stands. The
regressors are spec 012's and spec 037's weights, unchanged.

**Why this**: twice now (specs 037 and 038) the control meant to test "prior or bearings" could
not move the classical solve, so its null said nothing. The regressor minimises an error under
the simulator's distribution; a classical fit returns the mode of a likelihood. Where the
bearings determine range poorly the two differ most, and that is where the regressor wins. The
missing control is a classical estimator that is told the same distribution and reports the
centre of its posterior, not its mode.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The prior with the right structure (Priority: P1)

A reader sees whether a classical solve that is told the true manoeuvre times, the generator's
speed limits and the generator's distribution of range, and that reports the centre of its
posterior over range, removes the regressor's advantage where the bound is loose, without losing
where the bound is tight.

**Why this priority**: it separates prior from segmentation. If this estimator matches or beats
the regressor in every third of the bound, the regressor's remaining edge over a solve told the
true times was prior knowledge.

**Independent Test**: on the test seed, the paired ratio prior-informed told-truth solve ÷
fine-tuned regressor by thirds of the bound, beside the plain told-truth solve ÷ fine-tuned on
the same rows, in range, course and speed.

**Acceptance Scenarios**:

1. **Given** the control's settings bound before the test, **When** the test seed is scored,
   **Then** the record states the share of the regressor's loose-third advantage over the
   told-truth solve that the priors remove, with an interval, and the control's cost or gain in
   the tight third.
2. **Given** development data, **When** the control is first run, **Then** it is shown to move
   the solve (a stated share of rows changed by more than 10% in range) before anything is
   registered; a control that does not move the solve is not registered.

---

### User Story 2 - The prior in a causal system (Priority: P1)

The same posterior read-out is put behind C″'s own segmentation (and behind C with edited
bearings), giving a causal classical system told the generator's priors. A reader sees how much
of the regressor's lead over C″-robust it closes, clean and under mismatch.

**Independent Test**: the gap-closed share of spec 038, for the prior-informed C″ against
C″-robust, with medians and both-end trims beside the mean.

**Acceptance Scenarios**:

1. **Given** the test seed, **When** scored, **Then** the record gives the share of the log gap
   closed in range, course and speed, as a mean, as a ratio of medians and trimmed, clean and
   under the primary condition, and pooled over both.

---

### User Story 3 - Manoeuvre statistics as a prior on the history (Priority: P2)

The time-late evidence search under Annex B's manoeuvre prior, cut at the scored row and read at
its last moment, is measured on development data as a causal estimator: its accuracy and its
cost. It is registered for the test only if it can be scored on at least 300 engagements within
the CI budget.

**Independent Test**: a development table of the cut search beside C″-robust, the told-truth
solve and the regressor on the same rows, with seconds per estimate.

### User Story 4 - Where the priors are wrong (Priority: P2)

The prior-informed controls are scored on the busier-target and far-range splits with MAN2's
priors, as the regressor is. A reader sees whether a classical estimator told the wrong prior
loses ground the way the regressor does on clean data there.

### Edge Cases

- The posterior over range is narrower than the grid: the grid is refined about the mode, and
  the read-out returns the mode's solve to within a stated tolerance where the posterior is
  tight (tested).
- Under mismatch the stated bearing sd is wrong and the posterior is too narrow: the profile is
  tempered by the robust solve's own fitted error model; both tempered and untempered are run on
  development data and one is bound.
- The speed limits exclude every grid point (a fit outside the generator's support): the
  read-out falls back to the mode and the row is counted.
- A posterior with two separated modes (a mirror solution): the read-out is the median of the
  whole, which may lie between them; counted on development data.
- The far-range split lies partly outside the range prior's support: said beforehand; the
  controls are expected to lose there.

## Requirements *(mandatory)*

### Functional Requirements

**The prior-informed read-out (part 1)**

- **FR-001**: A classical read-out MUST be built that, for a given segmentation and scored row,
  profiles the robust solve's cost over the target's range at that row, weights the profile by
  the generator's distribution of range at scored rows and its support for speed, and reports
  the posterior median of range with the matching course and speed. The physics layer's code is
  not edited.
- **FR-002**: The range distribution MUST be tabulated from the generator on a spent seed with
  MAN2's ranges, committed with its digest, and never from a test seed. The speed support is the
  ranges file's.
- **FR-003**: The read-out MUST NOT read the truth, the condition or the error model. Applied to
  the true segmentation it is a reference; applied to C″'s it is a causal control.
- **FR-004**: Tests MUST show: where the posterior is tight the read-out equals the mode's solve
  within tolerance; with a flat prior and a symmetric profile it returns the mode; on a
  synthetic weakly observable case it moves toward the prior.

**Development and registration**

- **FR-010**: Development uses spent seeds (321, 370, 371, 372). The read-out's settings (grid,
  tempering, whether velocity is taken from the median point or averaged) are chosen there by a
  rule stated before the choice: the pooled log range ratio against the plain solve on the same
  segmentation, over clean and primary data, on the true segmentation.
- **FR-011**: Before registration the record MUST show that the control moves the solve: the
  share of rows whose range changes by more than 10%, by thirds of the bound.
- **FR-012**: A decision record MUST precede the test: estimands, lines, forecasts labelled by
  their basis, bound settings and digests. Fresh test seed 373, generated in its run only,
  scored once.

**Estimands**

- **FR-020 (Q1)**: on rows in the loosest third of the range bound, in distribution, clean and
  primary: the share of ln(told-truth ÷ fine-tuned) removed by the priors, 1 − ln(prior-informed
  told-truth ÷ fine-tuned) ÷ ln(told-truth ÷ fine-tuned). Beside it the same ratios in the
  middle and tight thirds, and prior-informed ÷ plain told-truth in each third (harm if wholly
  above 1 in the tight third).
- **FR-021 (Q2)**: the share of the log gap C″-robust → fine-tuned closed by the prior-informed
  C″, in distribution, clean, primary and pooled over both; as a mean, a ratio of medians and
  trimmed at both ends.
- **FR-022 (Q3, reported)**: the same controls on the shifted and far splits; yardstick ÷
  reference and reference ÷ system differences beside any split difference.
- **FR-023**: Beside every ratio: median, shares better, twice as good and twice as bad, course
  and speed, absolute errors, efficiency by thirds of the bound, shares answered.

**The cut evidence search (part 3)**

- **FR-030**: The time-late control's search under Annex B's prior MUST be run on prefixes ending
  at scored rows of a development subset, reading the state at the last moment, with its seconds
  per estimate. It is registered for the test only if 300 engagements fit the CI budget;
  otherwise the development table is reported and the reason given.

**Reporting**

- **FR-040**: Statistics as spec 038's (per-engagement medians, paired log ratios, engagement
  bootstrap, three training seeds pooled). Three reviewers review the test record. A kickoff
  post now; a write-up and a slides post before the PR.
- **FR-041**: What was promised and not run is listed in the record. No GPU run; no money.

### Key Entities

- **Range profile**: the robust solve's cost as a function of the target's range at the scored
  row, each point a constrained refit.
- **Prior table**: the generator's distribution of ln range at scored rows (MAN2), and the
  speed support.
- **Prior-informed solve**: the posterior median over the profile; on the true segmentation
  (reference) or on C″'s (causal control).

## Success Criteria *(mandatory)*

- **SC-001**: The record states whether a classical solve told the true manoeuvre times and the
  generator's priors matches the regressor in each third of the bound, with intervals.
- **SC-002**: The record states the share of the gap between C″-robust and the regressor that
  the priors close in a causal system, with its typical-engagement versions.
- **SC-003**: The control is shown to move the solve before registration.
- **SC-004**: A reader can say from the write-up which holds: the regressor's edge over a solve
  told the true times is prior knowledge; it is not; or a stated part is.
- **SC-005**: The decision record predates the test launch; the test is scored once; no GPU
  time is used.

## Assumptions

- Seeds: development on spent seeds; test 373; the next fresh seed is 374.
- The scored rows are the scorer's (5, 10, 15 and 20 min after the ownship's zig).
- A profile costs a few tens of constrained solves per row; scoring runs on CI.
- The median of the posterior is the right centre for a median absolute relative error.

## Out of Scope

- Any training or GPU run; a new segmenter; changes to C; real data.
- A full Bayesian posterior over histories in real time (part 3 measures one classical
  approximation of it on development data).
- The conditional coverage study of the regressor's intervals.
