---
title: "Kickoff: the carried prior where the ownship holds course"
date: 2026-11-19T14:00
tags: [kickoff, spec-029]
---

[Spec 028](/blog/2026/11/19/carry-prior) carried the previous window's state and uncertainty
into the next window as a prior. It found a small average shift and no harm, but it could not
test the owner's own case. In that simulator the ownship turned every 20–40 minutes, so every
window could resolve the target from its own bearings. The owner asked to test the ownship
holding course. This study does that. Spec: `specs/029-held-course/`.

<!-- truncate -->

## Where we are

- **Standing time-late system:** `ctl`. `ctl-prior` is recommended for adoption, scoped as "a
  small refinement, no harm shown".
- **Spec 028's registered split showed no gain:** 1.105 [0.963, 1.273]. That split was mostly
  the untended contact. The owner's case never occurred.

## Where this task moves to

- **Engagements:** realistic engagements where the ownship holds each leg for 1–2 hours,
  tended contact only.
- **Windows:** 1-hour windows overlapping 15 minutes. With 2-hour windows no window is free of
  ownship turns.
- **Turn-free windows:** about 30% of windows contain no ownship turn (measured on spent seed
  354).
- **Rule:**
  - Gain if ctl ÷ ctl-prior on turn-free windows has its lower limit above 1, with a
    bootstrap over engagements.
  - Harm if any class's upper limit is below 1, in range, course or speed.
  - Windows where nothing was handed on are excluded.
- **Plan:**
  1. tuning on seed 362 checks the split and the carried prior's coverage;
  2. the decision record;
  3. validation on seed 363;
  4. test on seed 364, scored once;
  5. the panel, then the write-up.
- **Risks:**
  - Holding course costs range keeping: the target drifts to 50 km at the 95th percentile,
    beyond detection, so geometry and detection mix.
  - The carried prior's settings were set on 2-hour windows.
  - The hand-over defect spec 028's panel found stays in.
- **Stop:** soundness or coverage outside its band on validation.

## How progress will be shown

- ctl ÷ ctl-prior by class (no turn, one turn, more), with intervals.
- Per-window ratios.
- Coverage of the carried prior on turn-free windows.
- A track plot of a turn-free window.
