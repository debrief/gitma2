---
title: "Kickoff: the scaled regressor under bearing-error mismatch"
date: 2026-11-22T10:00
tags: [kickoff, spec-037]
---

Bearing errors that break the simulator's assumptions cost the classical real-time system a
factor of 2.7, and the classical remedy did not close it. The one learned model that beat that
system after manoeuvres has no segmenter to break, and has never been scored under those errors.
This task scores it there, fine-tunes it with what is left of the GPU budget (about $9), asks it
for an uncertainty, and tries a hybrid that reports from the physics layer. Spec:
`specs/037-regressor-mismatch/`.

<!-- truncate -->

## Where we are

- [Gate H](/blog/2026/11/10/gate-h): on the true segmentation there is nothing material to learn
  about the bearing-error model. The cost is in the segmentation: C″ goes from 0.102 to 0.280
  in median range error under the primary condition (0.230 with the robust final solve).
- Spec 011 (a robust classical segmenter) closed at tuning without a gain.
- [Spec 012](/blog/2026/11/12/scaled-regressor): a direct regressor, a control with no physics
  layer, beat C″ after manoeuvres on clean data (0.066 against 0.105). It was worse in course
  efficiency (3.40 against 3.19), and where its margin comes from is open.
- Gates 3 and 4 stopped at validation: there is no uncertainty that can be shown.
- Standing: C″ for real-time estimates, with the robust solve as its control under mismatch.
  About $41 of the owner's $50 GPU budget is spent.

## Where this task moves to

- SRD §5 and §7; a registered study, not a gate. Nothing is carried by it.
- Plan:
  1. Score the three existing regressors unchanged under Gate H's sixteen conditions, on a spent
     seed, beside C″, its robust variants, the IMM, the EKF and one leg. Free, on CPU. A rule
     written beforehand says whether step 2 goes ahead.
  2. Extend the error overlay with a family training will never see (heavy tails, an error level
     that changes within the engagement).
  3. Register the readings, then fine-tune the three regressors under mismatch with interval
     heads for range, course and speed: a pilot and three seeds, about 13 T4-hours in all.
  4. Score once on a fresh test seed: robustness inside and outside the training ranges, the
     fine-tune's own effect, its cost on clean data, and coverage against a temperature control.
  5. The hybrid: C″'s final solve started from the regressor and holding it as a prior.
- Judged by paired per-scenario ratios with intervals (C″-robust ÷ regressor and the rest),
  with course and speed efficiency, the shares twice as good and twice as bad, and coverage with
  a bootstrap interval.
- Risks: conditions inside the training ranges are not a mismatch for the model, hence the
  held-out family; the regressor knows the simulator's manoeuvre prior and C″ does not; the
  simple range-prior control already failed in spec 012, so the hybrid may add nothing; $9 may
  be too little to move a model trained on 10 million scenarios.
- Stop: if the unchanged regressor already holds up, or the pilot's first hour moves nothing,
  no further money is spent before the owner is asked. The ledger refuses anything past $50.

## How progress will be shown

- Median range error by condition for every system, on spent seed 321 (step 1) and test seed
  371 (step 4).
- The distribution of per-scenario ratios, C″-robust against the fine-tuned regressor, clean,
  primary and held out.
- Coverage of the stated intervals by range band and by time since the last target change.
- Track plots of one test engagement, clean and under the primary condition: C″, the regressor
  and the hybrid.
