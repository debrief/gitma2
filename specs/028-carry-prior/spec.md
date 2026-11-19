# Feature Specification: Carrying the previous window as a prior (spec 027)

**Feature Branch**: `027-carry-prior` (developed on `ccr-fd0a0c59-4nxg4k`)

**Created**: 2026-11-18

**Status**: Draft. A registered study, not a gate. Nothing trained, no GPU.

**Input**: The owner said "yes" on 2026-11-18, after PR 47, to this proposal. Spec 026's
`ctl-carry` used the previous window's track only as the search's starting guess. It could
therefore save time but not narrow the hypotheses. The owner's expectation is different:
"knowledge of the previous track can usefully constrain the range of permutations for this
leg". This spec tests that expectation as stated: the previous window's estimate enters the
next window's fit and evidence as a prior.

**SRD traceability**: §1 (scope). No gate criterion is touched. Registered before its seeds
exist (constitution: pre-registered decision records, fresh seeds).

## Where we start

- Spec 026 (test record `experiments/20261118-ls/`, seed 351) compared `ctl-carry` with `ctl`
  on the tended contact. Accuracy was level:
  - E1 1.017 [0.958, 1.082];
  - without each chain's first window (equal by construction), 1.021 [0.9502, 1.100];
  - where the two differ, 1.034 [0.923, 1.168].
- `ctl-carry` cost 31% less search where it ran. A gain of up to about 10% was not excluded.
- In these realistic engagements the ownship turns every 20 to 40 minutes, so most 2-hour
  windows are well determined on their own (`ctl` 1.5–2.2% median range error on contact 1).
  The untended contact 2 is 1.3 to 1.5 times worse.
- Spec 025 (joined periods) showed what a real constraint across time is worth. Solving
  periods jointly, with motion continuity through the gaps, gained 3.1× on Annex B targets.
  Most of that came from periods without an ownship turn of their own; where a period stood
  alone, the gain was about 1.6×.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A window that knows where the target was (Priority: P1)

An analyst follows one contact for 6 to 12 hours. Each new 2-hour window is solved with
the previous window's estimate of where the target was, how it was moving, and how sure that
estimate was. Where the new window's bearings alone say little (no useful ownship turn, an
untended contact, just after a contact gap), the analyst gets a better track than from the
window alone. Where the bearings say a lot, the analyst gets no worse a track.

**Why this priority**: it is the owner's question, and the only one this spec decides.

**Independent Test**: on the registered engagements, compare `ctl` with the window solved
under the carried prior (`ctl-prior`), per window. The comparison uses the weak-geometry
split and the engagement bootstrap.

**Acceptance Scenarios**:

1. **Given** a chain of windows on one contact, **When** each window after the first is
   solved with the previous window's carried state and uncertainty as a prior, **Then** the
   prior enters both the fit and the evidence that ranks manoeuvre histories, so it can change
   which history is declared, not only where the search starts.
2. **Given** the carried estimate, **When** it is handed on, **Then** it holds no bearing
   that the receiving window also uses: no information is counted twice.
3. **Given** a window whose own bearings contradict the carried prior, **When** the
   consistency check rejects it at the declared level, **Then** the window is solved without
   the prior. Each such fall-back and its cost are recorded.

---

### User Story 2 - Knowing when the prior helps and when it hurts (Priority: P2)

A reviewer reads where the gain or loss comes from.

**Why this priority**: spec 026's panel showed that a pooled ratio can hide where the
difference lies.

**Independent Test**: every comparison is reported by split, by contact, by duration, in
range, course and speed, as a median per-window ratio, with the shares of windows twice as
good and twice as bad.

**Acceptance Scenarios**:

1. **Given** the scored record, **When** the reviewer reads it, **Then** the record shows:
   - how often the guard fell back;
   - how the prior's own stated uncertainty compares with its actual error at hand-over;
   - whether errors carried from one window grow along a chain.

---

### User Story 3 - Against a joint solve (Priority: P3, reported only)

A reviewer asks how much of a full joint solve the cheap hand-over recovers.

**Independent Test**: on a sample of consecutive window pairs of the tuning seed, compare
`ctl-prior` with spec 025's joint solve over both windows.

**Acceptance Scenarios**:

1. **Given** up to 40 window pairs, **When** both are solved, **Then** the ratio and its
   cost in time are reported. Nothing is decided from them.

### Edge Cases

- **First window of a chain**: it has no prior and equals `ctl` by construction. It is
  excluded from every registered statistic (spec 026 panel).
- **Contact gaps**: a window can start after a gap, or the hand-over time can fall inside
  one. The carried state is predicted across the gap. Its uncertainty is widened for the
  manoeuvres Annex B's rates allow in that time.
- **A manoeuvre at the hand-over time**: the carried uncertainty in course and speed is
  widened by the declared factor. The guard is the backstop.
- **A wrong carried estimate**: for example, the previous window declared the wrong history.
  The guard must stop it propagating down the chain. The record reports the chains where a
  fall-back occurred and the error before and after.
- **A previous window that did not answer**: there is nothing to carry, so the window is
  solved as `ctl`. Such windows are counted in their own row.
- **An undetermined carried state** (an enormous range sd): the prior then adds little, by
  construction. Such windows are reported, not removed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (systems)**: on every window of a chain, in one job, solve:
  - `ctl`, the standing control, unchanged;
  - `ctl-carry`, spec 026's carried start, unchanged;
  - `ctl-prior`, `ctl-carry` with the carried prior in its fit and evidence, and the guard;
  - `ctl-prior-noguard`, the same without the guard (reported only).

  The chain of `ctl-prior` hands on its own answers. Since `ctl-prior` and `ctl-carry` share
  their start, the ratio between them isolates the prior.
- **FR-002 (what is carried)**: the hand-over time is the first row of the receiving window
  (the start of the overlap). The previous window hands on, at that time:
  - its estimate of position, course and speed under its declared manoeuvre history;
  - the uncertainty of that estimate.

  The estimate is fitted on the previous window's bearings before the hand-over time only,
  together with the prior that window itself received. Information therefore flows forward
  and is never counted twice.
- **FR-003 (widening)**: the carried uncertainty is widened in course and speed by a declared
  amount for target manoeuvres the bearings could not yet show. Across a gap it is widened
  further, by Annex B's manoeuvre rates over the gap's length. The amounts are set on
  tuning data and bound in the decision record.
- **FR-004 (guard)**: before declaring, compare the window's best fit with and without the
  prior. If the prior adds more misfit than a chi-square test at the declared level allows,
  the window is declared without it. The level is set on tuning and bound in the decision
  record.
- **FR-005 (splits)**: windows are classed before scoring, from the engagement's known
  geometry and contact record. No estimator's output is used. Classes:
  - *weak geometry*: any window of contact 2; and any window of contact 1 that starts after
    a contact gap, or whose own rows hold at most one ownship turn;
  - *other*: every remaining window of contact 1.

  If tuning shows fewer than 100 weak-geometry windows from at least 10 engagements at the
  planned test size, the definition is replaced before registration and the change is
  recorded. The replacement is the window-alone bound on relative range at the window's last
  row, above its tuning median.
- **FR-006 (estimand and rule)**:
  - The estimand is the geometric mean over windows of ctl ÷ ctl-prior, from median range
    error per window. Each chain's first window is excluded. The interval comes from a
    bootstrap over engagements (2,000 resamples).
  - **Gain**: the lower limit on the weak-geometry split is above 1.
  - **Harm**: the upper limit is below 1 on the weak-geometry split, the other split, or
    either contact. Harm is also read in course and speed.
  - Otherwise: **not shown**, at this size.
- **FR-007 (reported beside, decided by nothing)**:
  - ctl-carry ÷ ctl-prior, which shows the prior's own effect;
  - `ctl-prior-noguard`;
  - per-window medians and the shares of windows twice as good and twice as bad;
  - course and speed;
  - by contact and duration;
  - by window position along the chain;
  - the guard's fall-back rate and the error of its windows;
  - share answered;
  - search time per system.
- **FR-008 (prior soundness)**: report the coverage of the carried state's 95% region
  against the truth at hand-over. Report it by contact and after gaps, with an engagement
  interval. A soundness band is declared from tuning. If validation falls outside it, the
  study stops before the test.
- **FR-009 (other soundness)**: spec 026's checks, read on validation:
  - at least 95% of windows ran;
  - the per-engagement geometric mean of ctl ÷ the true-history fit lies in [0.8, 4].
- **FR-010 (data)**: realistic engagements (spec 024's `configs/long/realistic.json`
  realism) of 6 and 12 hours, at spec 026's sizes:
  - tuning, seed 354, 6 + 6 engagements;
  - validation, seed 355, 10 + 10;
  - test, seed 356, 30 + 30.

  Seeds 355 and 356 are generated only in their CI runs. The next fresh seed is 357.
- **FR-011 (order)**: tuning → decision record (plan, run files and code bound by digest,
  forecasts written) → validation → test, scored once → agent review panel → write-up and
  slides.
- **FR-012 (joint solve, reported only)**: on up to 40 consecutive window pairs of the tuning
  seed, run spec 025's joint solve over both windows beside `ctl-prior`, and report the ratio
  and the time.
- **FR-013 (frozen pieces)**: `ctl`, `ctl-carry`, the simulator and spec 026's bound files
  are not edited. New behaviour lives in new modules.

### Key Entities

- **Carried prior**: the state at the hand-over time (position, course, speed), its
  covariance, its source window, the widening applied, and whether it crossed a gap.
- **Window record**: per system, the track, the declared history, the answered flag, the
  search time and, for `ctl-prior`, the guard's statistic and decision.
- **Window class**: weak geometry or other, with the reasons (contact, gap, ownship turns).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: the test record states the rule's output: gain, harm or not shown. It gives the
  estimate and engagement interval on each split, with chains' first windows excluded.
- **SC-002**: the guard's fall-back rate, and the coverage of the carried state's 95% region,
  are reported with intervals on validation and test.
- **SC-003**: every registered figure is reproducible from committed raw outputs by one
  committed script, and the record's tables are generated from its summary.
- **SC-004**: the agent review panel has read the record before the write-up is published,
  and the write-up uses the panel's narrowing.
- **SC-005**: the study fits in the free CI allowance. It is no more than twice spec 026's
  test run in runner time.

## Assumptions

- **Fall-back target**: the owner's words were "fall back to ctl". The fall-back is the same
  window without the prior, which is `ctl-carry`'s answer. This keeps the ratio between
  `ctl-carry` and `ctl-prior` a clean test of the prior. The registered estimand is still
  against `ctl`.
- **Hand-over at the overlap's start**: the estimate excludes overlap bearings. The
  alternative, using the previous window's full fit, counts the overlap twice and would make
  the prior overconfident.
- **Uncertainty**: the carried uncertainty is the fit's Laplace covariance. Spec 008 found
  such covariances overconfident, so FR-003's widening and FR-008's coverage check are
  required, not optional.
- **One simulator family**: the realism is spec 024's chosen parameters, not measured ones.
  A gain here says what a prior is worth under these realisms only.
- **Window length and overlap**: these stay at 2 hours and 30 minutes, as in spec 026, so
  that results compare.
- **Cost**: `ctl-prior` adds one search and one fit per window. On spec 026's test sizes this
  is about 1.5 times its runner time, on free CI runners.

## Known limits (stated before any result)

- A Gaussian prior on one state cannot carry the previous window's uncertainty about its
  manoeuvre history: a second-best history is not handed on. A hedge over candidate
  histories is not built here.
- The weak-geometry split mixes three causes (contact 2, gaps, few ownship turns). Each part
  is reported, but only the union is decided.
- If the gain appears only on contact 2, it measures this simulator's untended contact, not
  tracking in general.
