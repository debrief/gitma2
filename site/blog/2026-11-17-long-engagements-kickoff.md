---
title: "Kickoff: longer engagements, 6 to 48 hours"
date: 2026-11-17T13:00
tags: [kickoff, spec-023]
---

Issue #42 asks what it takes to apply our TMA to engagements of 6, 12, 24 and 48 hours, and to
show them on the viewer and time-late pages. This task is an investigation: it simulates one
engagement of each length, runs the standing systems on them as they are, measures what that
costs and how they do, and lists the implementation challenges. Spec:
`specs/023-long-engagements/`.

<!-- truncate -->

## Where we are

- Every engagement so far is 40 to 120 minutes with one ownship zig (MAN2, generator 0.6.0).
- The real-time model E (Gate 2) is carried and [runs in the browser](/viewer). Its exported
  graph takes exactly 720 rows: two hours of 10-second bearings.
- The time-late track [closed](/blog/2026/11/15/time-late-synthesis) with the classical control
  `ctl` standing, decided on periods of 20 to 120 minutes.

## Where this task moves to

- **Acceptance** (no gate, nothing trained, no GPU):
  - four engagements (seed 348, fresh) of 6, 12, 24 and 48 hours, with Annex B's target
    manoeuvres and an ownship that turns at each 20–40 minute leg and keeps the target in range;
  - every system runs to the end of each: real-time every 10 minutes on a sliding 2-hour window
    (E, C″, one leg) and over the whole engagement (IMM); time-late `ctl` on a chain of 2-hour
    windows, stitched;
  - a research note listing the challenges, each measured where it can be;
  - long-engagement sections on `/viewer` and `/timelate`.
- **Plan:**
  - a separate simulator, so generator 0.6.0 stays byte-identical (its table holds 32 target
    changes; 48 hours needs about 100);
  - windows cut from the long engagement in the form every estimator already reads;
  - the runs on CI (about 14 CPU-hours for the real-time part alone);
  - a timing of `ctl` on single periods of 0.5 to 6 hours, to show why it is run on windows.
- **Risks:** `ctl` may be too slow on long periods to time at all; four engagements are anecdotes,
  so the note will not claim rates.

## How progress will be shown

The slides post will carry the tracks of the 48-hour engagement, error against time for each
system, run time against period length, and the list of challenges.
