---
title: "Kickoff: the carried prior where the ownship's legs outlast the 2-hour window"
date: 2026-11-20T14:00
tags: [kickoff, spec-032]
---

[Spec 031](/blog/2026/11/20/held-comparators) found that a 1-hour window with a carried prior is
no substitute for a longer window or a joint solve. But with ownship legs of 1–2 h, a 2-hour
window always contains a turn. The owner's case is a leg longer than the standing 2-hour window,
so that the window itself is blind. Spec: `specs/032-long-legs/`.

<!-- truncate -->

## Where we are

- **Standing:** `ctl` on 2-hour windows, with spec 028's `ctl-prior` (the previous window's state
  and uncertainty as a prior, with a guard) for tended contacts.
- **Spec 029:** on blind 1-hour windows the prior beat the window alone (about 1.7 to 2.4).
- **Spec 031:**
  - A joint solve over the same past bearings beat the 1-hour prior (0.774 [0.632, 0.954]).
  - Not tested: legs longer than the 2-hour window.

## Where this task moves to

- **Engagements:** the ownship holds each leg for 2–4 h, with the same realism. The range drifts
  out, so about half of bearings are lost at long range.
- **Systems on turn-free 2-hour windows:**
  - 2-hour `ctl`;
  - 2-hour `ctl-prior`;
  - a joint solve: `ctl` on the window and the one before it, 3.5 h, past bearings only.
- **Rules:**
  - **E1** = `ctl` ÷ `ctl-prior`; **E2** = joint ÷ `ctl-prior`. Each ends "ctl-prior better",
    "worse" or "not separated".
  - **Harm:** E1 on one-turn windows has its upper limit below 1.
- **Plan:**
  1. tuning on spent seed 366;
  2. the decision record;
  3. validation on seed 367;
  4. test on seed 368, scored once;
  5. the panel, then the write-up.
- **Risks:**
  - Lost contact thins the turn-free windows. Held windows are far-range windows.
  - The joint solve's cost on 3.5 h is unknown.

## How progress will be shown

- E1 and E2 with intervals, and per-window ratios.
- Errors by system, by range band and by detected share.
- Guard rate, and coverage and NEES of the 2-hour hand-overs.
- Compute per engagement-hour.
