---
title: "Kickoff: an honest course statement (spec 010, Gate 5)"
date: 2026-11-09
tags: [kickoff, spec-010, gate-5]
---

Spec 010 is the third attempt at uncertainty the operator can trust. The course statement stays
"within ±X with probability P, otherwise unknown", but it gets three changes. P and the
distribution behind it will agree on every row. P must drop after a suspected manoeuvre. And the
learning claim is tested against the classical rules it turned out to be last time.

<!-- truncate -->

## Where we are

- **Gate 4 stopped at validation** ([write-up](/blog/2026/11/09/gate-4); panel round 2,
  `experiments/20261109-g4-val/`). The carried head missed one per-bin reliability check (top bin
  +0.054 against ±0.05), because the isotonic recalibration capped P at 0.677.
- **What the panel found.** P is honest on average (−0.002) but not on rows still settling after a
  manoeuvre: 0.62 stated against 0.30 hit. The recalibrated P disagrees with the scored density by
  up to 0.2 per row. And 72% of the head's lead over the classical temperature comes back from a
  quadratic rule in E's three standard deviations.
- **Carried:** E (Gate 2 e-s3, points frozen), C, the frozen IMM and EKF, and the oracle. Seed 320
  is still unused.

## Where this task moves to

- **SRD:** §7 step 5 (uncertainty); a new §5 row, Gate 5, proposed as an amendment the owner
  merges. Spec folder: `specs/010-honest-course-statement/`.
- **Criteria (proposed):**
  - **G5-a:** range and speed coverage, overall and per slice.
  - **G5-b:** reliability, overall within ±0.03, a calibration slope in [0.75, 1.33], and per slice
    (minute, open transition, range band, the unsettled proxy's two states) not wholly outside
    ±0.05. These are checks with intervals, not point bands.
  - **G5-c:** usefulness. The course log score beats "unknown", and the AUC of P is above 0.55.
  - **G5-d:** learning. The head beats the better of the sd^β temperature and a cross-sd quadratic
    rule. The claim is void if an encoder-only shuffled head also does.
  - **G5-e:** P equals the stated distribution's arc mass, and the points are identical.
- **Plan:**
  1. On tuning rows 0–499 only: compute P from the exact von Mises mass, recalibrate the
     distribution's parameters rather than P, define a causal unsettled proxy, and test a
     reciprocal-course mode.
  2. Extend the scorer with per-slice reliability, the calibration slope, AUC and early rows where
     possible; fit fitted-temperature references for the oracle and the IMM.
  3. Write the SRD amendment, the baseline and the decision record, with every trial run disclosed.
  4. Train three seeds and the controls on CI, then run validation.
  5. Run test seed 320 only if validation passes; the panel decides either way.
- **Risks:** the per-row course signal is weak (AUC about 0.6), so G5-d may fail again; the proxy
  may not separate the unsettled rows causally. **Stop:** if the validation rule is not met, seed
  320 stays unused and the best classical statement is reported as the usable one.

## How progress will be shown

- A reliability diagram (stated P against the hit rate) for E raw, the temperature, the cross-sd
  rule and the head, beside the oracle with its own temperature.
- P and the hit rate by slice, with the proxy's two states next to the truth's settled split.
- Plain-language widths: the range factor and the speed half-width in knots, by range band.
- The data: validation seed 314, scoring ordinals 500–1499, from the committed experiment records.
