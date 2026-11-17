# Feature Specification: Time-late over several periods of one target, joined through the gaps

**Feature Branch**: `025-joined-periods` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-17

**Status**: Draft

**Input**: Owner decision, 2026-11-17, option C: time-late analysis of several periods of one
target. Contact is held for several periods separated by short gaps in which no bearings
arrive; the target's track continues through each gap and may manoeuvre inside it. No
target-specific manoeuvre statistics are learned: the periods are linked by the continuity
of the target's motion only. Classical, CPU only, nothing trained.

**SRD traceability**:
- §1 (the time-late consumer: one best solution for the whole of the data held, not
  moment by moment), §5 (references on the same rows, paired statistics, fresh seeds,
  registration before results) and §9 (the owner's decision of 2026-11-17; proposed, the
  owner merges).
- The time-late account (`site/blog/2026-11-15-time-late-synthesis.md`, "What would justify
  more"): "the information (several periods of the same target ...)".

**Relation to specs 023 and 024** (another session's line, found 2026-11-17): spec 023 ran
`ctl` on long engagements in overlapping 2-hour windows; spec 024 (PR 47, open) adds contact
gaps and `ctl-carry` (state carried from one window to the next). This spec is the registered
study of one joint solve over several periods with gaps. Owner 2026-11-17, option A: keep it
separate, number it 025, take fresh seeds 349 to 351, and score spec 024's carried-state
`ctl` on the same engagements as a comparison once it is merged.

**Owner decisions this spec implements**:
- 2026-11-17: option C, motion continuity only (not a target-specific prior, not both).
- 2026-11-17: choosing when the ownship turns is out of scope; the ownship's track is given.

## Background

The standing time-late system (`ctl`, spec 016: the evidence-scored search over manoeuvre
histories with the arc model, Annex B's prior pooled with a broadened one, wild bearings
edited out, an effective bearing sd under correlated error, a manoeuvre declared at an
evidence margin of 1 with a 1% chance of a quiet target) solves one period of bearings for
one whole-period track. Every study so far gave it one period per target.

In practice contact on a target comes and goes. An analyst holding two or three periods
of the same target would not solve each alone: the target was somewhere during the gap and
its track must join up. A period without an ownship manoeuvre is poorly determined in
range on its own; joined to a period before or after it, across a different ownship leg,
the geometry resembles the cross-fix the ownship's own manoeuvres give. Against that, the
gap hides whatever the target did in it: a manoeuvre in the gap has to be inferred from
the change between periods, and a long gap with several manoeuvres may tell the joint
solve nothing.

This study measures whether solving the periods jointly, the track continuous through the
gaps, gives each period a better whole-period solution than `ctl` solving it alone, and
what the gap's length and contents do to that.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Does joining the periods help each period? (Priority: P1)

The owner sees, for engagements held as two or three periods with gaps, each period's
track error from `ctl` alone and from the joint solve, paired per period with an interval,
in range, course and speed.

**Why this priority**: it is the question.

**Independent Test**: one scoring run gives the paired ratio (alone ÷ joint) with its 95%
engagement-bootstrap interval on each split, and the verdict by the registered rule.

**Acceptance Scenarios**:

1. **Given** the registered rule, **When** the test seed is scored once, **Then** the
   verdict (gain, no gain shown, harm) is stated for each registered split, with the
   median per-period ratio and the shares of periods better, twice as good and twice as
   bad beside it.
2. **Given** that the periods of one engagement are not independent, **When** an interval is
   computed, **Then** it resamples engagements, not periods.

---

### User Story 2 - Where does the gain or loss come from? (Priority: P1)

A researcher sees the ratio split by the period's own geometry (an ownship manoeuvre inside
the period or not), by the gap's length, by whether the target manoeuvred in the gap, and
by how tightly the bound holds on the period's rows.

**Why this priority**: a pooled ratio hides the mechanism, and the panels have asked for
splits by kind of case on every time-late study.

**Independent Test**: each split is a row of a generated table with its period count and
interval.

**Acceptance Scenarios**:

1. **Given** a period with no ownship manoeuvre, **When** it is joined to a period with one,
   **Then** its ratio is reported in its own row.
2. **Given** a gap holding a target manoeuvre, **When** the joint solve declares one in
   that gap or not, **Then** the counts of manoeuvres in gaps found, missed and invented
   are reported.

---

### User Story 3 - What do the gaps cost, and what is left? (Priority: P2)

The owner sees the joint solve beside two readings that bracket it: `ctl` on the whole span
with every bearing (no gaps: what the gaps cost) and a fit told the true manoeuvre history
across the whole span with its times held (a reference, not a bound), and the bound on
each period's rows given the whole span's bearings.

**Independent Test**: the three are reported on the same rows as the joint solve.

---

### User Story 4 - Held course and false manoeuvres (Priority: P2)

The owner sees, on targets that hold course through the whole span, how often the joint
solve declares a manoeuvre (in a period or in a gap) against `ctl` alone.

**Independent Test**: false-manoeuvre rates on a held-course split, by where the manoeuvre
was declared.

### Edge Cases

- A gap so long that the target's history in it is unconstrained: the joint solve must
  not be worse than the periods solved alone by more than the registered harm rule allows;
  reported by gap length.
- A manoeuvre spanning a period's edge and the gap.
- A period too short to determine anything alone (the minimum is registered).
- Wild bearings or a dropout at a period's end, next to the gap.
- The joint solve failing to converge on a span: recorded, scored as its fall-back
  (the periods solved alone), and counted.
- An engagement whose layout yields only one period: not used for the decided figures.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen**

- **FR-001**: C, C″, `ctl` and the registered code paths, plans and records of specs 013 to
  019 MUST NOT change in behaviour. `ctl` alone is run as study L registered it.

**Data**

- **FR-002**: Engagements MUST be generated from the time-late ranges (5-second bearings,
  Annex B targets) with windows long enough to hold the layouts, and each engagement MUST be
  laid out as two or three periods separated by gaps, drawn from a stream of its own seeded
  from the engagement's seed, so that the generator's draws are untouched. Period and gap
  lengths are registered ranges; inside a gap no bearings are used by any system.
- **FR-003**: The target's motion in the gaps MUST follow the same generator (manoeuvres in
  gaps occur at Annex B's rates); the truth records which gaps hold manoeuvres.
- **FR-004**: Splits: Annex B targets (primary), the shifted manoeuvre prior, 2% wild
  bearings, and held course; the same engagements under each where the generator allows.

**Systems**

- **FR-005**: `ctl` alone: each period solved by itself, unchanged.
- **FR-006**: The joint solve: one search over manoeuvre histories spanning the first
  period's start to the last period's end, the track continuous throughout, manoeuvres
  allowed in periods and in gaps, scored by the same kind of evidence (bearings in the
  periods only, the same priors and declaration rule as `ctl`). Its track over each period
  is that period's answer.
- **FR-007**: Readings beside (not decided): `ctl` on the whole span with every bearing (no
  gaps); the true history across the span fitted with its times held from neutral starts,
  and the same per period; C″ and one leg per period. The tuned IMM and EKF are not re-run:
  spec 017 scored them as tracks at 3.8 to 10.5 times the control's error on common rows,
  and they have no state through a gap. Once spec 024 is merged, its `ctl-carry` is run per
  engagement on the same periods and gaps and reported beside the joint solve (a reading).

**Scoring**

- **FR-008**: Each period is scored on its own rows, 30 s apart, where the known-history
  bound on relative range *from the bearings of the whole span* (periods only, gaps
  without bearings) is below 0.5; gaps are not scored. Both systems are scored on the same
  rows, so rows that only the joined data determine count against `ctl` alone; the ratio is
  also reported on rows the period determines by itself (its own bound below 0.5), as spec
  016 scored a period.
- **FR-009**: The decided estimand is the paired per-period ratio of period median range
  error, `ctl` alone ÷ joint, geometric mean with a 95% engagement-bootstrap interval, on
  each registered split. Course and speed are reported the same way.
- **FR-010**: The rule, its splits, sample sizes, period and gap ranges, and what follows
  from each outcome MUST be fixed in a decision record before the validation and test seeds
  exist, with the rule's power stated from tuning data and a check that each outcome could
  occur on tuning data. A *gain* on a split needs the range interval wholly above 1; *harm*
  is an interval wholly below 1 in range, course or speed on any split.
- **FR-011**: Every ratio MUST be reported with its period and engagement counts, the median
  per-period ratio, and the shares better, twice as good and twice as bad; tables MUST be
  generated by a committed script from the record's summary.

**Process**

- **FR-012**: Seeds: 349 tuning, 350 validation (soundness: the span reference's range
  efficiency on tightly bounded rows within [0.8, 1.3], and the joint solve converging on
  at least 95% of spans), 351 test. The test is scored once.
- **FR-013**: The runner and study code MUST have unit tests, including the layout's
  independence from the generator's draws and a check that a joint solve of one period with
  no gaps reproduces `ctl` alone.
- **FR-014**: A five-reviewer panel MUST decide the result; kickoff and slides posts as the
  constitution requires; the record lists what was promised and not delivered.

### Key Entities

- **Layout**: an engagement's periods and gaps (start and length of each), drawn per
  engagement.
- **Joint solve**: one history and one continuous track over the span; each period's answer
  is the track over its rows.
- **Gap event**: a true manoeuvre inside a gap, and whether the joint solve declared one
  there.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each registered split the owner can read one line: the joint solve's
  effect on each period's error, with its interval and the registered verdict.
- **SC-002**: The ratio is stated for periods with and without an ownship manoeuvre of
  their own, and by gap length, each with counts and intervals.
- **SC-003**: The share of manoeuvres in gaps that the joint solve declares, and its false
  manoeuvres on held course, are stated beside `ctl` alone's.
- **SC-004**: What the gaps cost (joint against the whole span with every bearing) and what
  is left (joint against the span reference) are stated on the same periods.

## Assumptions

- Contact gaps are short: about 5 to 30 minutes (registered from tuning; the owner's
  "short gaps"). Periods are at least 15 minutes. Windows are up to the generator's two
  hours; a longer window needs the generator's manoeuvre table checked first (spec 013).
- The bearing error model, ownship track and target statistics are the time-late splits'
  as before; the ownship's manoeuvres are given, not chosen.
- The joint solve reuses `ctl`'s search, evidence and declaration with the bearings of the
  gaps absent; no setting is retuned on the decided seeds. Settings particular to spans
  (how many manoeuvres a gap may hold) are chosen on tuning seed 349 only.
- If the joint solve gains on Annex B targets without harm, it becomes the standing
  time-late system for data with gaps; if not shown, `ctl` per period stays and the result
  is written up. Either way nothing is trained and no GPU is used.
