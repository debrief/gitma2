# Feature Specification: A robust classical segmenter under bearing-error mismatch (Gate R)

**Feature Branch**: `011-robust-segmenter` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: the Gate H write-up's recommended follow-on, with the owner's go-ahead
of 2026-11-10. Nothing is trained. Gate H's comparison on C″'s own segmentation showed that the
cost of bearing-error mismatch is in the segmentation. Diagnose which kind of mismatch breaks C
and how; build a robust classical segmenter C-r; measure, pre-registered, how much of the gap it
closes; what remains is the headroom any better segmenter, learned or not, could claim.

**SRD traceability**:
- §7 step 5 (realistic bearing error), continued from spec 010; §5 (references on the same rows,
  paired clustered statistics, fresh seeds). Gate R is a new §5 row, proposed as an amendment the
  owner merges.
- Annex A §A.3 (segmentation measures: false alarms on held legs, misses, delay) and §A.9
  (segmenter C, the reference).
- `site/blog/2026-11-10-gate-h.md` (the follow-on) and `experiments/20261110-gh-c2/`.

**Owner decisions this spec implements**:
- 2026-11-10: Gate R's verdict rule: the gap is closed if the remainder's interval lies wholly
  below 10% (R-b), fixed before any Gate R result.
- 2026-11-10: go ahead with the robust classical segmenter before the scaled regressor.
- 2026-11-09: the mismatch model and its severity grid (spec 010 research R2), reused unchanged.

## Background (`experiments/20261110-gh-c2/`, validation seed 321, 1,000 engagements)

| Median relative range error | No mismatch | Primary condition |
| --- | --- | --- |
| Robust control, true manoeuvre times | 0.060 | 0.114 |
| C″: our segmenter, plain solve | 0.102 | 0.280 |
| C″ with the robust control in its final solve | 0.103 | 0.230 |

- With the true manoeuvre times, mismatch doubles the error. On C's own segmentation it nearly
  triples it. C recovers 0.92 of the gap between one leg and the oracle on clean data and 0.66
  under mismatch.
- C ran unchanged: it was tuned on clean data, its nominations divide by the stated σ, its
  confirmation costs assume white noise, and nothing robust reaches them.
- Not known: which kind of mismatch does the damage, and whether C nominates falsely or misses.
  Only the combined condition was run, and only the downstream error was measured.
- Gate H's panel left lessons this spec must apply: name a reference for what it is told; check
  a pooled statistic by range band; do not state an explanation that has not been tested; run
  every registered comparison with the gate; work out beforehand what the design can yield; keep
  CI runs lean.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Know what breaks the segmenter before fixing it (Priority: P1)

A researcher sees, on a fresh tuning seed, how the standing classical system (C″) behaves under
each kind of mismatch alone and under all four: the segmentation measured against the truth
(transitions declared on held legs, target changes missed, delay in declaring a change) and the
downstream error, beside the same system on clean data. The diagnosis says which kind does the
damage and by which mechanism, and so what a fix must address.

**Why this priority**: Gate H's author explained a gap without testing the explanation and was
wrong. A fix designed from a guess may fix the wrong thing.

**Independent Test**: the diagnosis record names, for each kind, the change in false
transitions, misses and delay against clean data with intervals, and the share of the combined
condition's downstream loss each kind accounts for.

**Acceptance Scenarios**:

1. **Given** the tuning seed under no mismatch, each single kind at central severity and the
   combined condition, **When** C″ is run and measured, **Then** the record gives false
   transitions per engagement, the miss rate, the median delay and the median range error for
   each, with the difference from clean data and its interval.
2. **Given** the diagnosis, **When** the design is written, **Then** every mechanism the design
   addresses is one the diagnosis measured, and any it leaves alone is named.
3. **Given** the diagnosis record, **When** it is read, **Then** it states what the design can
   yield at most: the downstream error if the segmentation were as good as on clean data.

### User Story 2 - A segmenter that holds up under mismatch (Priority: P1)

The researcher has C-r: C's own tests made robust by classical means only. It estimates the
bearings' scatter and their correlation from its own residuals, and discounts wild bearings,
when deciding whether to nominate and whether to confirm a target change. C itself is kept
exactly as frozen, as the control. Nothing is learned.

**Why this priority**: it is the cheapest thing that could close the gap, and it is the control
any learned segmenter would have to beat.

**Independent Test**: on clean data C-r's segmentation agrees with C's within a declared
tolerance; on mismatch data it is causal (no bearing after a row changes that row's
segmentation) and uses only the bearings, the times, the ownship track and the stated σ.

**Acceptance Scenarios**:

1. **Given** clean data, **When** C-r and C segment it, **Then** their segmentation measures
   differ by no more than the declared tolerance.
2. **Given** any engagement, **When** the bearings after a row are replaced by noise, **Then**
   C-r's segmentation at that row is unchanged.
3. **Given** a mismatch split, **When** C-r runs, **Then** it reads nothing from the mismatch
   truth, and a test shows it cannot.
4. **Given** the repository after this work, **When** C's code digest is computed, **Then** it is
   the frozen value.

### User Story 3 - How much of the gap it closes, measured before it is believed (Priority: P1)

Under the primary mismatch condition, on a fresh test seed, the researcher sees three systems on
the same rows, each with the robust control in its final solve: on C's segmentation, on C-r's
segmentation, and on the true manoeuvre times. The headline is the share of the gap between the
first and the third that C-r closes, with an interval. It is also given per mismatch kind, by
range band, in metres, degrees, knots and time to a settled solution, and with the segmentation
measures, so that a pooled figure cannot hide where it holds and where it does not.

**Why this priority**: this is what the gate decides on, and what any later claim for a learned
segmenter will be measured against.

**Independent Test**: the test record reports the share closed with its interval, the clean-data
cost of C-r, and every registered breakdown; a reader can find each without asking.

**Acceptance Scenarios**:

1. **Given** the test seed under the primary condition, **When** the three systems are scored,
   **Then** the share of the gap closed is reported with a paired, scenario-clustered interval.
2. **Given** the same seed with no mismatch, **When** C-r is scored against C″, **Then** its cost
   on clean data is reported and checked against the declared limit.
3. **Given** the scores, **When** the record is written, **Then** it carries the range-band table,
   the per-kind table, the operational table and the segmentation measures, all registered
   before the data existed.

### User Story 4 - A pre-registered verdict and an honest remainder (Priority: P2)

Gate R is proposed as an SRD row the owner merges and fixed by a decision record before any
validation or test data exist. The agent review panel decides. The write-up states what C-r
achieved and, as plainly, what remains: the gap still open after C-r is the headroom a better
segmenter of any kind could claim, and C-r is from then on the standing control.

**Why this priority**: as every gate. Here it also sets the bar for the scaled regressor and for
any learned segmenter that follows.

**Independent Test**: the decision record binds the plan by digest and predates the validation
and test seeds; the write-up gives the remainder in the same units as the gain.

**Acceptance Scenarios**:

1. **Given** the plan, **When** the decision record is committed, **Then** neither the validation
   nor the test seed has been generated.
2. **Given** any verdict, **When** the write-up is published, **Then** it states the remaining gap
   with its interval and names C-r as the control for whatever comes next.

### Edge Cases

- The diagnosis finds that one kind accounts for nearly all the loss: the design addresses that
  kind and says the others were left alone.
- The diagnosis finds the loss is not in nominations or confirmations at all (for example in the
  hand-over to the solve): the spec's design does not apply, and the plan is revised before
  anything is built.
- C-r fixes false transitions but adds misses or delay: both are reported, and the downstream
  error decides.
- C-r helps under mismatch but costs on clean data beyond the limit: the gate's soundness check
  fails and the result is reported as a trade, not a gain.
- Engagements with no usable leg after the zig, and rows no system answers: counted as at
  Gate S and Gate H.
- A short prefix with too few bearings to estimate scatter or correlation: C-r falls back to the
  stated values, by a rule fixed on the tuning seed.
- The estimate of correlation is itself corrupted by an unmodelled target manoeuvre (the thing
  being tested for): the design must say how it avoids testing with a model fitted to the
  residuals of the hypothesis it is rejecting.
- Segmentation is not a function of an engagement alone (batch padding): every system is run in
  the same chunks.

## Requirements *(mandatory)*

### Functional Requirements

**Diagnosis**

- **FR-001**: Before any design, C″ MUST be run on a fresh tuning seed under no mismatch, each of
  the four kinds alone at central severity, and the combined condition, on a sample large enough
  to separate the kinds and no larger.
- **FR-002**: For each, the record MUST give the segmentation measures of Annex A §A.3 against
  the truth (false transitions on held legs, misses, delay) and the downstream errors, with
  intervals, and each kind's share of the combined condition's downstream loss.
- **FR-003**: The record MUST state the most the design can yield: the downstream error of the
  robust final solve on a segmentation as good as C achieves on clean data, and on the true
  manoeuvre times.
- **FR-004**: No explanation of a difference may be stated in the record unless a measurement in
  it supports it; otherwise it is marked as untested.

**The robust segmenter**

- **FR-010**: C-r MUST use classical means only: estimates of scatter and correlation from
  residuals, and weights or costs that discount wild bearings, in confirmation, and in
  nomination only if the pilot shows an effect (the diagnosis found nomination is not where C
  fails; plan research R2). Nothing is trained.
- **FR-011**: C-r MUST be causal and MUST read only the bearings, their times, the ownship track
  and the stated σ.
- **FR-012**: C MUST remain exactly as frozen (code and parameter digests unchanged) and MUST be
  runnable beside C-r as the control.
- **FR-013**: C-r's settings MUST be chosen on the tuning seed by a rule declared before the
  search, after a pilot that drops any setting with no effect.
- **FR-014**: The design MUST state how its estimates avoid being fitted to the residuals of the
  very hypothesis under test.

**Measurement**

- **FR-020**: On the same rows, each with the robust control in its final solve: on C's
  segmentation (C″-r, the baseline), on C-r's segmentation, and on the true manoeuvre times (the
  true-segmentation reference). Reported beside them: C″ with the plain solve, one leg, the
  re-tuned IMM and EKF.
- **FR-021**: The headline MUST be the share of the gap in median range error between the
  baseline and the true-segmentation reference that C-r closes, under the primary condition,
  with a paired, scenario-clustered interval; the same for course and speed.
- **FR-022**: Registered before the data and delivered with the gate: the same statistic by
  quartile of true range, per mismatch kind, in operational units, on rows every system answers,
  and at P90; and the segmentation measures for C and C-r.
- **FR-023**: C-r's cost on clean data against C″-r MUST be measured and gated by a declared
  limit, in a form the sample size can decide.
- **FR-024**: Seeds MUST be fresh and distinct for tuning, validation and test (323, 324, 325;
  the next fresh seed is then 326). Seeds 320 to 322 MUST NOT be used for any choice.
- **FR-025**: Comparisons MUST be made within one scoring run, with every system run in the same
  chunks.

**Gate**

- **FR-030**: Gate R's criteria MUST be proposed as an SRD §5 row the owner merges and fixed by
  a decision record, bound to the plan by digest, before the validation or test seed exists.
- **FR-031**: Proposed criteria, open to the owner until the decision record: **R-a**
  (soundness) C-r's clean-data cost within the declared limit; **R-b** (the verdict) the share
  of the gap closed: C-r is **adopted as the standing control** if the interval is wholly above
  zero; the gap is **closed** if in addition the remainder's interval lies wholly below 10% of
  the true-segmentation reference's error; otherwise the remainder is **open headroom**, stated
  with its interval.
- **FR-032**: The decision record MUST carry forecasts and, computed from the diagnosis, what the
  design can yield at most.
- **FR-033**: The panel decides. The write-up MUST state the remainder in the units of the gain
  and name C-r (or C, if C-r is not adopted) as the control for what follows.
- **FR-034**: CI runs MUST be lean: the decisive conditions at full size, the others at the
  smallest size that answers their question, and no grid before a pilot.

**Reporting**

- **FR-040**: A kickoff post now and a slides post before the implementation PR: the diagnosis
  as a chart of segmentation measures by kind; one engagement's segmentation by C and by C-r
  against the truth; the three systems' errors with the share closed; the range-band table;
  track plots of the three systems on a representative engagement.

### Key Entities

- **C″-r**: the standing classical system with the robust control in its final solve; the
  baseline.
- **C-r**: the robust classical segmenter, with the same final solve.
- **True-segmentation reference**: the robust control given the true manoeuvre times. A
  reference, not a ceiling: it is told the segmentation and nothing else.
- **Diagnosis record**: segmentation measures and downstream error per kind on the tuning seed.
- **Share of the gap closed**: (baseline − C-r) / (baseline − reference) in median range error.
- **Gate R plan and decision record**.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The diagnosis attributes the combined condition's downstream loss to the four
  kinds with intervals, and names the mechanism (false transitions, misses or delay) for the
  largest.
- **SC-002**: On clean data C-r's median range error is within the declared limit of C″-r's.
- **SC-003**: C's code and parameter digests are unchanged, and C-r passes its causality and
  isolation tests.
- **SC-004**: The test record states the share of the gap closed with its interval, and every
  registered breakdown, on a fresh seed.
- **SC-005**: The decision record predates the validation and test seeds, and the panel returns
  a verdict.
- **SC-006**: A reader can tell from the write-up alone how much error a better segmenter could
  still remove under this mismatch, in metres, and what it would have to beat.
- **SC-007**: No model is trained.

## Assumptions

- The mismatch model, its severity grid and the primary condition are spec 010's, unchanged; the
  robust control's settings are those frozen for Gate H (`configs/gateh/gh-a.json`).
- "Robust by classical means" excludes anything fitted to labelled data; settings chosen on the
  tuning seed by a declared rule are tuning, not training.
- The 10% bound in R-b echoes Gate H's materiality threshold; the owner fixed it on 2026-11-10,
  with no Gate R result behind it.
- C's speed (about 16 s per engagement per system on one core) limits sample sizes: the primary
  condition at about 2,000 engagements on the test seed, others at 500 or fewer.
- Out of scope: any learned component; the scaled end-to-end regressor (next, on the owner's
  Modal account); a zig-coupled bias and bursty outliers (the following extension of the
  mismatch model); why the solve is 1.25 times the bound; target-motion mismatch.
