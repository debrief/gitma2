---
title: "Kickoff: usable uncertainty, Gate 4"
date: 2026-11-08
tags: [kickoff, spec-009, gate-4]
---

Spec 009 is the second attempt at stating how far each estimate can be trusted. Gate 3 showed that
widening E's covariance cannot make it honest: half the rows cannot carry a meaningful course
interval, and the joint statement fails through the solve's own correlations. This spec makes E say
so: each row is either *determined*, with intervals that can be trusted, or *undetermined*, with no
course interval at all.

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
- **Proposed criteria**: 95% coverage of log range and speed on all rows and of course on
  determined rows (G4-a); the joint χ²₄ share on determined rows (G4-b), both in [0.92, 0.98];
  the undetermined share bounded by the oracle's own under the same rule plus 0.10, and those rows
  really worse (G4-c); learning beats the temperature, void if the shuffled control does too
  (G4-d); points unchanged (G4-e).
- **Plan**:
  1. A causal row state and a circular course statement; choose the rule's settings on validation
     tuning ordinals 0–499 only.
  2. Reshape, not only rescale, the covariance (correlation shrinkage) and train on the exact
     errors the gate scores.
  3. The amendment and the decision record, then three seeds, the shuffled control and the
     temperature.
  4. Validation; seed 320 only if the validation rule is met; the panel decides.
- **Risks**: the undetermined state could become a dodge (G4-c bounds it); the joint check may
  stay out of reach if the tails are not Gaussian even on determined rows. We stop at validation
  if the rule is not met, as Gate 3 did.

## How progress will be shown

- Track plots of validation seed 314 scenarios (a settled leg and a manoeuvring target, as in Gate
  3's slides) with determined rows drawn with ellipses and course arcs and undetermined rows
  marked as such.
- Charts: coverage and joint share on determined rows, and the undetermined share, for E raw, the
  temperature, the head, the oracle and the IMM, from the validation scoring run's stored arrays.
