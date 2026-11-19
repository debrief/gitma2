# Feature Specification: The carried prior where the ownship holds course (spec 029)

**Feature Branch**: `029-held-course` (developed on `ccr-fd0a0c59-4nxg4k`)

**Created**: 2026-11-19

**Status**: Draft. A registered study, not a gate. Nothing is trained and nothing runs on GPU.

**Input**: the owner, 2026-11-19, after PR 51: "test the ownship holding course option". This
is alternative 2 of spec 028's write-up.

**SRD traceability**: §1 (scope). No gate criterion is touched. The study is registered before
its seeds exist (constitution: pre-registered decision records, fresh seeds).

## Where we start

Spec 028 (test record `experiments/20261119-cp/`) carried the previous window's state and
uncertainty into the next window's fit and evidence as a prior (`ctl-prior`):
- **Registered split:** gain not shown, no harm. ctl ÷ ctl-prior was 1.105 [0.963, 1.273].
- **Elsewhere:** a small average shift, about 1.1 in geometric mean and 1.03 in the median
  window.
- **The owner's own case was not sampled.** The ownship turned every 20–40 min, so every
  2-hour window had at least two ownship turns. A window whose bearings cannot resolve the
  target alone never occurred.

**Measured on spent seed 354** (simulator geometry only, no estimate), with the ownship holding
each leg for 1–2 hours:
- **2-hour windows:** none is free of ownship turns; 36 of 60 hold exactly one.
- **1-hour windows** (overlapping 15 min): 40 of 132 later windows hold no ownship turn, and
  92 hold one.
- **Range:** the median rises from 16 to 22 km, and the 95th percentile from 26 to 50 km.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A window the bearings cannot resolve alone (Priority: P1)

An analyst follows a contact while the ownship holds course for an hour or two. In a window
with no ownship manoeuvre, the target's range is not determined by that window's bearings
alone. The previous window, which held a manoeuvre, hands on its state and uncertainty. The
analyst gets a better track than from the window alone.

**Why this priority**: it is the owner's hypothesis, and spec 028 could not test it.

**Independent Test**: on the registered engagements, compare `ctl` with `ctl-prior` on windows
holding no ownship turn, with a bootstrap over engagements.

**Acceptance Scenarios**:

1. **Given** a chain of 1-hour windows of the tended contact, with the ownship holding each leg
   for 1–2 hours, **when** each window after the first is solved with and without the carried
   prior, **then** windows with no ownship turn are compared, and so are those with one turn.
2. **Given** a window with no hand-over (nothing usable carried), **then** it is excluded from
   every registered statistic and counted separately (spec 028 panel).

### User Story 2 - Where it helps and where it hurts (Priority: P2)

A reviewer reads the effect by class, in range, course and speed, as a typical window and as a
mean. The same panel lessons apply: median, trimmed mean, the shares twice as good and twice as
bad, the prior's own effect against `ctl-carry`, the guard, and coverage on the decided
population.

### Edge Cases

- **Contact lost:** the target drifts beyond the 40 km detection range. Windows under 60
  bearings are unanswered and counted. The share answered is an outcome.
- **The first window of a chain:** excluded.
- **A turn in the overlap:** a turn that overlaps any row of a window counts for that window.

## Requirements *(mandatory)*

- **FR-001 (data)**: spec 024's realistic engagements (`configs/long/realistic.json` realism),
  changed in one respect: the ownship holds each leg for 1–2 hours (`leg_s` 3,600–7,200 s).
  - Range keeping still acts at each leg's end.
  - Durations are 6 and 12 hours.
  - Contact 1 only, the tended contact.
- **FR-002 (systems)**: `ctl`, `ctl-carry` and `ctl-prior` (spec 028's `carry2`) on 1-hour
  windows overlapping 15 minutes.
  - The carried prior keeps spec 028's registered settings: scale 4, tail 1,200 s, α 0.001.
  - Tuning checks them as a chain. They change only if tuning's coverage falls outside
    [0.85, 0.99]; any change is recorded before registration.
- **FR-003 (classes)**: from the engagement's own record, before any estimate is read:
  - **held**: no ownship turn overlaps the window's rows;
  - **one turn**: exactly one does;
  - **more**: two or more do.

  Each chain's first window, and any window with no hand-over, is excluded.
- **FR-004 (rule)**:
  - **Estimand:** the geometric mean over windows of ctl ÷ ctl-prior, from per-window median
    range error. The interval comes from a bootstrap over engagements (2,000 resamples).
  - **Gain:** the lower limit on **held** windows is above 1.
  - **Harm:** an upper limit is below 1 on held, one-turn or more-turn windows, in range,
    course or speed.
  - Otherwise the outcome is "not shown, at this size".
- **FR-005 (beside)**, reported:
  - ctl-carry ÷ ctl-prior;
  - medians, trimmed means and shares;
  - the fit told the true manoeuvre history;
  - C″;
  - the guard's rate;
  - coverage by class;
  - the share answered;
  - search time.
- **FR-006 (soundness on validation)**:
  - **S1:** at least 95% of windows ran.
  - **S2:** the per-engagement geometric mean of ctl ÷ the true-history fit lies in [0.8, 4].
  - **Coverage:** on hand-overs into held windows, the carried 95% region covers the truth
    0.80–0.99 of the time. This is the decided population.
  - A failure of any check stops the study.
- **FR-007 (seeds)**:
  - tuning 362, with 6 + 6 engagements;
  - validation 363, with 10 + 10;
  - test 364, with 30 + 30.

  Validation and test seeds are generated only in their CI runs. The next fresh seed is 365.
- **FR-008 (frozen)**: `ctl`, `ctl-carry`, `ctl-prior`, the simulator and spec 028's bound
  files are unchanged. The configs and the scorer (`long/study29.py`) are new. `long.yml`
  passes window length and overlap through.

## Success Criteria *(mandatory)*

- **SC-001**: the test record states the rule's output, with the held class's estimate and
  engagement interval.
- **SC-002**: the record's tables are generated from its summary by a committed script.
- **SC-003**: the panel has read the record before the write-up.

## Assumptions

- **1-hour windows rather than 2-hour.** No 2-hour window is turn-free when legs are 1–2 hours.
  Holds of 2–3 hours would make 2-hour windows turn-free, but the target would drift out of
  detection (95th-percentile range 60–70 km). Both systems run on the same windows.
- **Contact 1 only.** The owner's question is about the contact the ownship tends.
- **The hand-over defect stays.** The refit starts from the full-window fit (spec 028 panel).
  This tests the system as recommended for adoption, not a repaired one.

## Known limits (stated before any result)

- One family of simulated engagements; held legs are the only change.
- Holding course costs range keeping. Some held windows lose contact or sit at long range, so
  geometry and detection are confounded.
- One-turn windows hold a single zig. Their own bearings resolve the target, though weakly.
