---
title: "Kickoff: usable uncertainty, Gate 4"
date: 2026-11-08
tags: [kickoff, spec-009, gate-4]
---

Spec 009 is the second attempt at stating how far each estimate can be trusted. Gate 3 showed that
widening E's covariance cannot make it honest: half the rows cannot carry a meaningful course
interval. A third of E's courses are badly wrong, and nothing E knows at the time tells which.
So this spec states course with the probability that it holds: "within ±X° with probability p,
otherwise unknown", with X and p calibrated, and calibrated intervals for range and speed.

<!-- truncate -->

## Where we are

- **Gate 3 stopped at validation** ([write-up](/blog/2026/11/08/gate-3),
  [slides](/blog/2026/11/08/gate-3-slides)). A learned scale reached 0.92–0.99 marginal coverage
  only by stating course intervals that cover the whole circle on half the rows; 0.835 of rows
  fell within the χ²₄ 95% point against 0.92 required; the head was no better than a per-slice
  temperature. Even the oracle falls short just after manoeuvres.
- **Carried**: Gate 2's E (e-s3) and its point estimates, C as the segmenter and control, C″ as a
  standing classical control; the time-late check showed the causal E-w leaves nothing usable in
  the future bearings.
- **Open**: E's raw covariance (95% coverage 0.60) must not be shown to an operator as an
  uncertainty. Test seed 320 is unused.

## Where this task moves to

- **SRD**: §7 step 5, first item (uncertainty calibration, second attempt); a new §5 row, Gate 4,
  proposed as an amendment the owner merges. Spec: `specs/009-usable-uncertainty/`.
- **Why a probability**: on the validation tuning rows, 35% of E's course errors exceed 30°, and
  the best causal signal (E's encoder state, its stated sds, C's code) separates them only with
  AUC 0.62. The owner chose (8 November) to state course probabilistically rather than flag
  "undetermined" rows.
- **Proposed criteria**: range and speed 95% coverage in [0.92, 0.98] (G4-a); stated p reliable,
  overall within ±0.03 and per bin within ±0.05 (G4-b); the course statement more informative than
  "unknown", with mean p at least 0.5 (G4-c); learning beats the per-slice temperature, void if the
  shuffled control does too (G4-d); points unchanged (G4-e).
- **Plan**:
  1. Choose the statement's form and settings on validation tuning ordinals 0–499 only.
  2. Train on exact errors (wrapped course, range ratio, speed): three seeds, the shuffled control
     and the temperature.
  3. The amendment and the decision record before any training.
  4. Validation; seed 320 only if the validation rule is met; the panel decides.
- **Risks**: the learned p may add nothing over the temperature (expected from the scoping AUC);
  then G4-d fails and the classical statement is carried. We stop at validation if the rule is not
  met.

## How progress will be shown

- Track plots of validation seed 314 scenarios (a settled leg and a manoeuvring target, as in Gate
  3's slides) with each scored row's course arc and stated probability.
- A reliability diagram (hit rate against stated p) and coverage charts for range and speed, for E
  raw, the temperature and the head, from the validation scoring run's stored arrays.
