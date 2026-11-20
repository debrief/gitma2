# Feature Specification: the carried prior where the ownship's legs outlast the 2-hour window (spec 032)

**Feature Branch**: `032-long-legs` (developed on `ccr-fd0a0c59-4nxg4k`)

**Created**: 2026-11-20

**Status**: Draft. A registered study, not a gate. Nothing trained, no GPU.

**Input**: owner, 2026-11-20, after PR 54: "Test ownship legs longer than the 2-hour window, which
is your 'blind leg' case at the standing configuration". This was alternative (a) of spec 031's
interpretation reviewer.

**SRD traceability**: §1 (scope). No gate criterion is touched. Registered before its seeds
exist.

## Where we start

- **Spec 029:** carrying the previous window's state as a prior (`ctl-prior`) beats a blind
  1-hour window solved alone (2.41).
- **Spec 031** (`experiments/20261120-cmp/`):
  - With ownship legs of 1–2 h, a 2-hour window is never blind.
  - Against `ctl` on 2-hour windows, and against a joint solve over the same past bearings,
    1-hour `ctl-prior` is worse (D2 0.774 [0.632, 0.954]).
  - `ctl-prior` on 2-hour windows stands from spec 028.
- **Open:** the owner's case at the standing configuration. When the ownship holds a leg longer
  than the 2-hour window, the window itself is blind. Does the carried prior help there? And is
  it a substitute for re-solving the past bearings?

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The blind 2-hour window (Priority: P1)

An analyst follows a contact while the ownship holds each leg for 2–4 h. Some 2-hour windows
contain no ownship turn at all. For those windows the analyst wants to know two things:
- **E1:** whether 2-hour `ctl-prior` (the previous window's state and uncertainty handed on)
  beats 2-hour `ctl` on the same window;
- **E2:** whether a joint solve (`ctl` on the union of the previous and current 2-hour windows,
  3.5 h ending at the current window's end) beats `ctl-prior`. It uses the same past bearings,
  and neither side sees later ones.

**Why this priority**: this is the owner's case, and the only remaining question where a carried
prior could be the remedy.

**Independent Test**: on turn-free 2-hour windows, score each system on the window's rows, with a
bootstrap over engagements.

**Acceptance Scenarios**:

1. **Given** a held-course engagement with 2–4 h legs, **when** `carry2` runs on 2-hour windows
   and `jointheld` on each turn-free one, **then** E1 and E2 are computed on each turn-free
   window's rows.
2. **Given** a window with no hand-over, or one that a decided system leaves unanswered, **then**
   it is excluded from the decided estimands, and its count and each system's answered share are
   reported.

### User Story 2 - Harm, cost and honesty of the hand-over (Priority: P2)

Reported beside:
- E1 on one-turn windows: harm is read there;
- the guard's fall-back rate on decided windows;
- coverage and median NEES of the 2-hour hand-overs;
- a reference told the true history over the joint span;
- compute per engagement-hour;
- the share of bearings detected;
- results by range band.

## Requirements *(mandatory)*

- **FR-001 (data)**: `configs/long/realistic.json`'s realism with ownship legs of 2–4 h
  (`leg_s` 7200–14400 s), engagements of 6 and 12 hours, contact 1.
  - **Tuning:** spent seed 366, 6 + 6 engagements. Seed 366 was spec 031's test seed; these are
    different engagements under this config.
  - **Validation:** seed 367, 10 + 10 engagements.
  - **Test:** seed 368, 30 + 30 engagements.
  - The next fresh seed is 369.
- **FR-002 (systems)**: unchanged code, each in its own CI job per engagement.
  - **(a)** spec 028's `carry2` on 2-hour windows overlapping 30 min: `ctl`, `ctl-carry`,
    `ctl-prior`, the no-guard variant and the true-history fit. This is the standing
    configuration.
  - **(c)** `jointheld` at 7200/1800 s: for each turn-free 2-hour window j ≥ 1, `ctl` on the union
    of windows j − 1 and j, kept on window j's rows, with the true-history fit over the union.
- **FR-003 (classes)**: by ownship turns overlapping the 2-hour window: held (none), one, more.
  - The decided class is **held**.
  - Excluded: each chain's first window; windows with no hand-over in (a), which are constructed
    ties; windows that `ctl`, `ctl-prior` or (c) leaves unanswered.
  - Windows where the guard fell back are kept, because the fall-back is to `ctl-carry`, not to
    `ctl`.
- **FR-004 (estimands and rule)**: geometric means of per-window median range error over decided
  held windows, with a bootstrap over engagements (2,000 resamples, seed 32).
  - **E1** = 2-hour `ctl` ÷ 2-hour `ctl-prior`.
  - **E2** = joint solve ÷ 2-hour `ctl-prior`.
  - For each:
    - **"ctl-prior better"** if the lower limit is above 1;
    - **"ctl-prior worse"** if the upper limit is below 1;
    - otherwise **"not separated, at this size"**.
  - **Harm** is read if E1 on one-turn windows (handed on, both answered) has its upper limit
    below 1.
  - Course and speed are reported beside.
- **FR-005 (beside)**:
  - medians, 10% trimmed means, and the shares better, twice as good and twice as bad;
  - ctl-carry ÷ ctl-prior;
  - the span reference ÷ ctl-prior (not a ceiling: it is told the truth);
  - E1 and E2 without the guard's fall-back windows;
  - by range band (under 15, 15–25, 25–35, over 35 km) and by detected share (under or over 0.75);
  - E1 and E2 on 6- and 12-hour engagements;
  - guard rate;
  - coverage and median NEES of decided hand-overs;
  - answered shares;
  - compute per engagement-hour for each job.
- **FR-006 (soundness, validation)**:
  - **S1:** every engagement present for both parts, and at least 95% of the 2-hour chain's
    windows ran.
  - **S2:** the per-engagement geometric mean of `ctl` ÷ the true-history fit lies in [0.8, 4].
    It is a screen for gross faults.
  - **S3:** coverage of the carried 95% region on decided held hand-overs lies in [0.80, 0.99].
  - A failure stops the study.
- **FR-007 (frozen)**: the systems, the simulator and the bound files of specs 028, 029 and 031 are
  not edited.
  - New: `long/study32.py` and `tma2-long study32`, configs and run files.
  - `jointheld` writes its `.npz` even when it has no held window (spec 031 panel). This changes
    no output.

## Success Criteria *(mandatory)*

- **SC-001**: the test record states E1's and E2's outputs and the harm reading, with engagement
  intervals.
- **SC-002**: the guard rate and the coverage and median NEES of the 2-hour hand-overs are
  reported.
- **SC-003**: the panel reads the record before the write-up.

## Assumptions

- **Long legs lose contact.** On spent seed 366, legs of 2–4 h let range drift (median about
  35 km against a detection midpoint of 40 km). About half of bearings are detected. About 38%
  of 2-hour windows are turn-free, and about a third of those are mostly out of contact.
  - The realism is kept unchanged, because losing contact is a consequence of holding course.
  - Windows with no hand-over are excluded. Detected share is reported as a band.
- **(c) uses only past bearings, as (a) does.** Neither side sees bearings after the window. E2
  is past-only like for like (spec 031 panel).
- **The hand-over defect stays** (spec 028). The chain moves window starts past true target
  manoeuvres.

## Known limits (stated before any result)

- **Population:** one simulator family, contact 1, one realism setting.
- **Window placement:** hand-overs are never inside a target manoeuvre.
- **Range:** drifts with the leg length, so the held windows are far-range windows. E1 is read
  by range band beside.
- **Weighting:** the prior weights old information by its stated covariance. This is a comparison
  of systems.
