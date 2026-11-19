---
title: "Kickoff: long engagements, carrying state, an incremental C, realism"
date: 2026-11-17T19:00
tags: [kickoff, spec-024]
---

The owner asked for note 12's three recommendations to be implemented. They are: carry state
between time-late windows, make C incremental, and make the long engagements more realistic.
Spec: `specs/024-long-carry-incremental-realism/`.

<!-- truncate -->

## Where we are

- [Spec 023](/blog/2026/11/17/long-engagements-slides) ran the standing systems on 6 to 48 hour
  engagements, on windows. The time-late control held 1.6–2.7% median range error. Each
  real-time estimate re-ran C over its 2-hour window (27–37 s). The scenario was kind: the ownship
  steered on the truth, contact was never lost, and there was one target.

## Where this task moves to

- **Carry**: each time-late window also starts its search from the previous window's declared
  history, in place of the start from nothing. It is compared with `ctl` on every window.
- **Incremental C**: one confirmation per 2-hour block of estimates. Each estimate keeps the
  confirmed legs inside its 2-hour window. For blocks of one estimate this equals spec 023's run.
- **Realism**, from a random stream of its own, so the first target is spec 023's:
  - the ownship steers on measured bearings and a range belief with 30% error;
  - contact gaps, and detection that fades beyond about 40 km;
  - a second target that the ownship does not manoeuvre for, with bearings mis-associated where
    the two contacts cross.
- **Risks:** the second contact may be held too rarely to score, and one engagement per length
  gives anecdotes, not rates. A registered study is proposed afterwards, not run.

## How progress will be shown

The slides post will carry:
- `ctl` and `ctl-carry` error and run time by window;
- the incremental run's cost per estimate beside spec 023's;
- each engagement's realistic tracks for both contacts;
- error against time with the gaps marked.
