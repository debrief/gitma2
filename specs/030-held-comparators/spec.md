# Feature Specification: the carried prior against longer windows and a joint solve (spec 030)

**Feature Branch**: `030-held-comparators` (developed on `ccr-fd0a0c59-4nxg4k`)

**Created**: 2026-11-19

**Status**: Draft. A registered study, not a gate. Nothing trained, no GPU.

**Input**: owner, 2026-11-19, after PR 52: "run the comparison against 2-hour ctl and joint
solve". This is the default recommended by spec 029's panel.

**SRD traceability**: §1 (scope). No gate criterion is touched. Registered before its seeds
exist.

## Where we start

Spec 029 (`experiments/20261119-hold/`) found ctl ÷ ctl-prior 2.41 [2.06, 2.83] on 1-hour windows
holding no ownship turn, with the ownship holding each leg for 1–2 h. Its panel narrowed this to
"more data beats no data". `ctl` was given only the blind 1-hour window, while `ctl-prior` was
also given the previous window's information. The operational question was left open: is the
carried prior a cheap substitute for using the earlier bearings directly?

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The prior against the bearings themselves (Priority: P1)

An analyst follows a contact while the ownship holds course. For each turn-free hour, the
analyst wants the best estimate of the target. The candidates:

- **(a)** `ctl-prior` on 1-hour windows. The previous window hands on a state and an uncertainty.
- **(b)** `ctl` on its standing 2-hour windows overlapping 30 min, stitched mid-overlap.
- **(c)** a **joint solve**: `ctl` on the union of the previous and current 1-hour windows
  (1 h 45 min), read on the current window's rows.

With no contact gap between the windows, (c) is spec 025's joint solve: the gap is empty.

**Why this priority**: it decides whether the cheap hand-over should be preferred over
re-solving more bearings.

**Independent Test**: on turn-free 1-hour windows, score (a), (b) and (c) on the same rows, with
a bootstrap over engagements.

**Acceptance Scenarios**:

1. **Given** a held-course engagement, **when** (a), (b) and (c) are each run on their own
   windows, **then** their median range errors are compared on each turn-free 1-hour window's
   rows.
2. **Given** a window with no hand-over (contact lost), or one that any system leaves
   unanswered, **then** it is excluded from the decided estimands, and the counts are reported.

### User Story 2 - What each costs and where the truth is (Priority: P2)

Reported beside, for each window:
- the compute time of each system;
- a reference told the true manoeuvre history over the joint span;
- `ctl-prior` on 2-hour windows;
- one-turn windows for (b).

## Requirements *(mandatory)*

- **FR-001 (data)**: spec 029's engagements: realistic, ownship legs 1–2 h, 6 and 12 hours,
  contact 1.
  - **Tuning:** spent seed 364, 6 + 6 engagements (indices 0–5 and 30–35). Its 1-hour chain is
    already in spec 029's test record.
  - **Validation:** seed 365, 10 + 10 engagements.
  - **Test:** seed 366, 30 + 30 engagements.
  - The next fresh seed is 367.
- **FR-002 (systems)**: unchanged code. Each system runs in its own CI job per engagement.
  - **(a)** spec 028's `carry2` on 1-hour windows overlapping 15 min (`ctl`, `ctl-carry`,
    `ctl-prior`).
  - **(b)** `carry2` on 2-hour windows overlapping 30 min. This gives `ctl`, and `ctl-prior` on
    2-hour windows, which is reported. Its track is stitched mid-overlap (spec 023).
  - **(c)** a new CLI part `jointheld`. For each 1-hour window j ≥ 1 with no ownship turn, it runs
    `ctl` (`timelate.run_windows`) on the union of windows j − 1 and j, and keeps the rows of
    window j. It also keeps the true-history fit over that union (`history-best`) as the span
    reference.
- **FR-003 (classes)**: as in spec 029. The decided class is **held**: no ownship turn overlaps the
  1-hour window. Excluded are each chain's first window, windows with no hand-over in (a), and
  windows any of (a), (b) or (c) leaves unanswered.
- **FR-004 (estimands and rule)**: geometric means over held windows of per-window median range
  error, with a bootstrap over engagements (2,000 resamples, seed 30).
  - **D1** = (b) ÷ (a), 2-hour `ctl` against `ctl-prior`.
  - **D2** = (c) ÷ (a), joint solve against `ctl-prior`.
  - For each estimand:
    - **"ctl-prior better"** if the lower limit is above 1;
    - **"ctl-prior worse"** if the upper limit is below 1;
    - otherwise **"not separated, at this size"**.
  - Course and speed are reported beside.
- **FR-005 (beside)**:
  - medians, trimmed means and shares;
  - D1 on one-turn windows;
  - (b)'s `ctl-prior` ÷ (a);
  - the span reference ÷ (a);
  - spec 029's ctl ÷ ctl-prior replicated;
  - compute time per window for each system;
  - the answered share per system;
  - range bands.
- **FR-006 (soundness, validation)**:
  - **S1:** every engagement present for all three parts, and at least 95% of the 1-hour chain's
    windows ran.
  - **S2:** the per-engagement geometric mean of 1-hour ctl ÷ the true-history fit lies in
    [0.8, 4].
  - **S3:** held-window coverage of the carried 95% region lies in [0.80, 0.99].
  - A failure stops the study.
- **FR-007 (frozen)**: `ctl`, `ctl-carry`, `ctl-prior`, the simulator and the bound files of
  specs 028 and 029 are not edited. New: `jointheld` in `cli/long.py`, `long/study30.py`, the
  `tag` passthrough in `long.yml`, and configs.

## Success Criteria *(mandatory)*

- **SC-001**: the test record states D1's and D2's outputs, with engagement intervals.
- **SC-002**: compute per window is reported for each system.
- **SC-003**: the panel reads the record before the write-up.

## Assumptions

- **The joint solve is a longer window here.** With windows that touch (15-min overlap, no gap),
  "joint over two windows" is `ctl` on 1 h 45 min ending at the current window's end. It differs
  from (b) in where the window sits: (c) always ends at the window scored, while (b)'s fixed
  2-hour grid may centre elsewhere.
- **Held windows only for (c).** Running (c) on every window would roughly triple its cost, and
  the question is about turn-free windows.
- **The hand-over defect stays.** `ctl-prior` is the system recommended for adoption.

## Known limits (stated before any result)

- **Population:** one simulator family, contact 1 only.
- **Window placement:** hand-overs and window starts are moved past true target manoeuvres
  (spec 023's chain).
- **Weighting:** (b) and (c) see more bearings, and the prior weights old information by its
  stated covariance. The comparison is of systems, not of information.
