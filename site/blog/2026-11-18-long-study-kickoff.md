---
title: "Kickoff: long engagements, a registered study"
date: 2026-11-18T04:00
tags: [kickoff, spec-025]
---

The owner chose note 13's registered study. On fresh seeds, with the questions fixed before
any result, it asks three things:
- is carrying state between time-late windows no worse than solving each window cold;
- how much worse the standing control does on a contact the ownship does not tend;
- whether the IMM drifts over twelve hours.

Spec: `specs/025-long-study/`.

<!-- truncate -->

## Where we are

[Spec 024](/blog/2026/11/18/long-engagements-2-slides) built the three recommendations of note 12
on four engagements:
- carrying state was level in accuracy and cheaper in search;
- the incremental C was not adopted;
- an untended contact was three to five times worse where it could be solved at all.

All of these are anecdotes from one engagement per length.

## Where this task moves to

- **E1**: `ctl-carry` is non-inferior to `ctl` if the lower limit of the geometric mean of
  per-window ratios is at least 0.95. Read on the tended contact.
- **E2**: the cost of an untended contact, banded by range. A magnitude, with no rule.
- **E3**: the IMM's drift over 12 hours. Shown if the interval lies above 1.
- **Plan**:
  1. a tuning run on seed 349, giving forecasts;
  2. the decision record, binding the plan and code by digest before seeds 350 and 351 exist;
  3. validation on seed 350, with soundness checks;
  4. the test on seed 351 (30 + 30 realistic engagements of 6 and 12 hours), scored once;
  5. the agent review panel, then the write-up.
- **Risks**: E1 may be inconclusive at this size. E2 confounds geometry with tending, by
  design. E3 reads one IMM tuning.

## How progress will be shown

The slides post will carry:
- E1's per-window ratios against the 0.95 line;
- E2's ratio by range band;
- E3's error and share answered by 2-hour bin, with the intervals.
