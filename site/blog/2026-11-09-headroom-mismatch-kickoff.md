---
title: "Kickoff: is there anything for learning to win? Gate H"
date: 2026-11-09
tags: [kickoff, spec-010, gate-h]
---

Spec 010 trains nothing. After Gate 4 the owner asked for a reflection on the whole programme,
and its finding is uncomfortable: every learned component so far has turned out, under its
control, to be a simple classical rule. The likely reason is that our simulated bearing errors
are exactly the errors the estimator assumes, so the classical solve is already close to the best
possible. Before any more learning work, this gate measures whether realistic bearing errors
leave room worth learning for.

<!-- truncate -->

## Where we are

- **Gate 4 stopped at validation** ([write-up](/blog/2026/11/09/gate-4),
  [slides](/blog/2026/11/09/gate-4-slides)): the course probability missed its top reliability
  bin, and 72% of the learned head's margin was a quadratic rule in three standard deviations.
- **The pattern across gates** (research note 10, `docs/research/10-reflection-headroom.md`):
  Gate 1's heads died; Gate D's detector read the time since the zig; Gate S's learned segmenter
  did not separate from the classical C; at Gate 2 a zig veto and a fixed fade (C″) gave +0.018
  of the gap and learning +0.007 beyond it.
- **Carried**: C″ as the standing classical estimator, C as its segmenter, the re-tuned IMM and
  EKF, the oracle. E is scored for information only.
- **Set aside** by the owner's decision of 9 November: the Gate 4 follow-on (course-probability
  fixes).
- **Open**: whether learning has anything to win once the error model is wrong.

## Where this task moves to

- **SRD** §1 and §7 step 5 (realistic bearing error, deferred until Gate 2 passed); the gate is a
  new §5 row, proposed as an amendment the owner merges. Spec: `specs/010-headroom-mismatch/`.
- **Judged by**: headroom, the share of the gap between C″ and an *attainable ceiling* that
  remains after a classical robust control. The ceiling is the same solve told the true
  segmentation and the true error model, but not which bearings were wild. The owner's threshold for
  "material": the robust control's median range error at least 10% above the ceiling's, interval
  wholly above, on the primary condition. The panel decides.
- **Plan**:
  1. Generator: four mismatches, separately switchable (correlated error, slow bias, unknown σ,
     outliers), three severities each from open literature. Mismatch off reproduces today's data
     byte for byte.
  2. Two ceilings and the Cramér–Rao bound under the true error model.
  3. A classical robust control on C″'s solve: robust loss, σ from residuals, whitening by an
     estimated correlation. Settings fixed on a tuning seed.
  4. Decision record before any scoring: conditions, threshold, seeds 320 (tuning), 321
     (validation), 322 (test), forecasts.
  5. Score on CI; results as gap fractions and in metres, degrees, knots and minutes to a settled
     solution; panel verdict.
- **What follows**: material headroom means a learned component is trained under mismatch, with
  C″ and the robust control as standing controls. None means the learning track stops and the
  null result is published. Either way the next step after that is the scaled end-to-end
  regressor (research note 04, option B), which answers a question gitma left open: was its
  3 × bound a matter of compute?
- **Risks**: severities chosen until headroom appears (they are fixed with sources before
  scoring); a ceiling that knows too much (hence two ceilings, and only the attainable one
  counts); loss that is really segmentation failure counted as estimation headroom (C″ is also
  scored on the true segmentation); a constant bias, which no estimator can remove.
- **We stop** before the test seed only if the pipeline is unsound: a ceiling far from its bound,
  or a robust control that damages C″ on clean data. A small headroom on validation is a result
  to confirm, not a reason to stop.

## How progress will be shown

- **One engagement's bearings under each mismatch kind**, beside the clean bearings (tuning seed
  320, one scenario, named in the figure's sidecar).
- **Headroom chart** per condition: C″'s gap to the attainable ceiling, the part the robust
  control closes, the part that remains, with intervals (validation seed 321, then test 322).
- **Operational table**: the same gaps in metres, degrees, knots and minutes to a settled
  solution.
- **Track plots** of C″, the robust control and the attainable ceiling on a representative
  engagement of the primary condition, at zig + 10 and zig + 20 min.
- **Efficiency per slice** against the mismatch-aware bound, for every estimator.
