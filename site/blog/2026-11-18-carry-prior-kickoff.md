---
title: "Kickoff: carrying the previous window as a prior"
date: 2026-11-18T22:00
tags: [kickoff, spec-027]
---

Spec 026's `ctl-carry` gave each 2-hour window the previous window's track as a starting guess.
It found the same answers faster but no better ones, because nothing in the fit itself changed.
The owner expected knowledge of the previous track to narrow the hypotheses for the next window.
This study tests that expectation directly. The previous window's estimate and its uncertainty
enter the next window's fit, and the evidence that ranks manoeuvre histories, as a prior.
Spec: `specs/027-carry-prior/`.

<!-- truncate -->

## Where we are

- [Spec 026's registered study](/blog/2026/11/18/long-study) found carrying a starting guess
  level with solving each window cold. The ratio was 1.021 [0.950, 1.100] without the first
  windows, which are equal by construction. The search was 31% cheaper. A gain of up to about
  10% was not excluded.
- The standing time-late system is `ctl`. It scores 1.5–2.2% median range error on a tended
  contact and 1.3–1.5 times worse on an untended one.
- [Spec 025](/blog/2026/11/18/joined-periods) showed what a real constraint across time can
  win. Solving periods jointly gained about 3× on Annex B targets, mostly where a period had no
  ownship turn of its own.

## Where this task moves to

- SRD §1. A registered study, not a gate. Nothing is trained and nothing runs on GPU.
- **Rule**: gain if the geometric mean of ctl ÷ ctl-prior per window has its lower limit above
  1 on the weak-geometry split. Weak geometry means the untended contact, a window after a
  contact gap, or a window with at most one ownship turn. Harm if any split's upper limit is
  below 1, in range, course or speed. Each chain's first window is excluded.
- **Safeguards**:
  - the carried estimate uses no bearing the next window also uses;
  - its uncertainty is widened for manoeuvres it cannot yet see;
  - a chi-square guard drops the prior where the window's bearings reject it.
- **Plan**:
  1. build `ctl-prior` beside `ctl` and `ctl-carry`, solved in the same job;
  2. tune the widening and the guard's level on seed 354, and check the weak-geometry split
     has at least 100 windows;
  3. write the decision record and its forecasts;
  4. validate on seed 355, including a coverage check of the carried prior;
  5. score the test on seed 356 (30 + 30 engagements of 6 and 12 hours) once;
  6. run the agent review panel, then publish the write-up.
- **Risks**:
  - Laplace covariances have been overconfident before. An overconfident prior pulls each
    window towards the last window's mistakes.
  - A Gaussian prior on one state cannot hand on a second-best manoeuvre history.
  - A gain confined to the untended contact would describe this simulator.
- **Stop**: the study stops before the test if the carried prior's coverage falls outside its
  declared band, or if spec 026's soundness checks fail on validation.

## How progress will be shown

- ctl ÷ ctl-prior per window, by split and contact, with the registered interval against 1.
- The prior's own effect, ctl-carry ÷ ctl-prior, window by window along a chain.
- The carried prior's 95% coverage and the guard's fall-back rate.
- A track plot of one weak-geometry chain: truth, `ctl`, `ctl-prior`.
- All from the test record on seed 356, with tuning seed 354 for the design figures.
