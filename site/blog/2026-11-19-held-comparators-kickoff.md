---
title: "Kickoff: the carried prior against longer windows and a joint solve"
date: 2026-11-19T23:00
tags: [kickoff, spec-030]
---

[Spec 029](/blog/2026/11/19/held-course) found that when the ownship holds course, carrying the
previous window's state as a prior roughly halves the error on turn-free 1-hour windows. That was
measured against the same blind window solved alone.

The owner asked for the comparison that matters in practice: the prior against `ctl` on its
standing 2-hour windows, and against a joint solve over two windows. Spec:
`specs/030-held-comparators/`.

<!-- truncate -->

## Where we are

- **Prior against the same window alone:** on turn-free 1-hour windows, ctl ÷ ctl-prior is
  2.41 [2.06, 2.83] (spec 029).
- **What is still open:** whether the hand-over is a cheap substitute for using the earlier
  bearings directly.

## Where this task moves to

- **The three systems,** on spec 029's held-course engagements (tended contact):
  - (a) `ctl-prior` on 1-hour windows;
  - (b) `ctl` on 2-hour windows overlapping 30 min, stitched;
  - (c) `ctl` on the union of each turn-free hour and the hour before it.
- **Rules:**
  - D1 = (b) ÷ (a) and D2 = (c) ÷ (a), on turn-free windows, with a bootstrap over
    engagements.
  - Each ends "ctl-prior better", "ctl-prior worse" or "not separated".
- **Plan:**
  1. tuning on spent seed 364 (12 engagements);
  2. the decision record;
  3. validation on seed 365;
  4. test on seed 366, scored once;
  5. the panel, then the write-up.
- **Risks:**
  - (b) and (c) see more bearings and may simply win.
  - Compute is about 100 runner-hours on the test.

## How progress will be shown

- D1 and D2 with intervals.
- Per-window ratios.
- Compute per window for each system.
- A track plot of one turn-free hour under all three.
