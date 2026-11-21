---
title: "Kickoff: several periods of one target across long gaps"
date: 2026-11-20
tags: [kickoff, spec-033]
---

Spec 030 found that a carried prior helps a period that cannot answer alone, while one solve
through the gaps stays the better choice. Both findings come from gaps of 5 to 30 minutes. This
task stretches the gaps to 30–90 minutes, with up to four periods, where joining has to bridge
hours of unseen manoeuvres. Nothing is trained.

<!-- truncate -->

## Where we are

- [Spec 030](/blog/2026/11/20/carried-prior): the carried prior helps against solving each
  period alone (1.59 on Annex B), but is not shown equal to the joint solve.
- A per-period consistency flag was judged not worth registering: the periods it would need
  to catch are mostly ones where `ctl` alone happened to land close.

## Where this task moves to

- Spec `specs/033-long-gaps/`: 6-hour engagements from the long simulator (ownship legs of
  20–40 minutes, Annex B targets), laid out as 2–4 periods with gaps of 30–90 minutes.
- Spec 030's systems run unchanged: `ctl` alone, the joint solve, the carried start, and the
  carried prior both uninflated and as k4.
- Development first, on a spent seed. Then a proposal: register on fresh seeds, or stop.
- Risks:
  - the joint solve over 3–4 hours may hit `ctl`'s cap of ten manoeuvres, and it costs more;
  - the long simulator's ownship steers on the true target.

## How progress will be shown

- The ratios by gap length and by whether a period has its own ownship turn.
- The joint solve's cost and how often it meets the cap.
- How often the truth falls inside the carried prior's stated uncertainty.
