---
title: "Kickoff: a robust classical segmenter, Gate R"
date: 2026-11-10
tags: [kickoff, spec-011, gate-r]
---

Gate H found that knowing the bearing-error model is worth nothing to the solve once the
manoeuvre times are right, and that getting the manoeuvre times right under mismatch is worth a
factor of two. Spec 011 goes after that factor by the cheapest means first. It trains nothing:
it finds out what breaks our segmenter, makes the segmenter's own tests robust, and measures how
much of the gap that closes. What is left is the headroom a better segmenter could claim.

<!-- truncate -->

## Where we are

- **Gate H: headroom not material** ([write-up](/blog/2026/11/10/gate-h),
  [slides](/blog/2026/11/10/gate-h-slides)). On the true manoeuvre times, a textbook robust fit
  is as accurate as a fit told the true error model.
- **On our own segmenter's output the picture is different.** Under the primary mismatch
  condition the standing classical system's median range error is 0.280, or 0.230 with the
  robust control in its final solve, against 0.114 with the true manoeuvre times. C recovers
  0.92 of the gap between one leg and the oracle on clean data and 0.66 under mismatch.
- **Carried**: C, frozen, as the segmenter and control; C″ (C with the zig veto and fixed fade);
  the robust control for the final solve; the mismatch model and its severity grid.
- **Open**: which kind of mismatch breaks C, and whether it declares manoeuvres that did not
  happen or misses ones that did. Only the combined condition was run, and only the downstream
  error was measured.

## Where this task moves to

- **SRD** §7 step 5 (realistic bearing error), Annex A §A.3 (segmentation measures) and §A.9
  (segmenter C); the gate is a new §5 row, proposed as an amendment the owner merges. Spec:
  `specs/011-robust-segmenter/`.
- **Judged by**: the share of the gap between C's segmentation and the true manoeuvre times that
  the robust segmenter C-r closes, each with the robust final solve, under the primary condition
  on a fresh test seed. C-r must not cost more than a declared limit on clean data. The panel
  decides.
- **Plan**:
  1. Diagnose on a fresh tuning seed (323): C″ under each mismatch kind alone and all four, with
     false transitions, misses and delay measured against the truth, and what the design could
     yield at most.
  2. Design C-r from what the diagnosis measured: scatter and correlation estimated from
     residuals, wild bearings discounted, in C's own nomination and confirmation tests. C itself
     stays frozen.
  3. Choose C-r's settings on the tuning seed, by a declared rule, after a pilot.
  4. Decision record before any validation or test data: criteria, forecasts, every breakdown
     that will be reported.
  5. Validation (seed 324), test (seed 325), panel, write-up.
- **Risks**: fixing the wrong mechanism (hence the diagnosis first); estimating correlation from
  the residuals of the very hypothesis under test; a gain under mismatch bought with a loss on
  clean data; a pooled figure hiding a split by range (the range-band table is registered in
  advance this time).
- **We stop and revise the plan** if the diagnosis shows the loss is not in C's nominations or
  confirmations at all.

## How progress will be shown

- **The diagnosis**: segmentation measures and range error by mismatch kind (tuning seed 323).
- **One engagement's segmentation** by C and by C-r against the truth, under the primary
  condition.
- **The three systems' errors** with the share of the gap closed and its interval (test seed
  325), and the same by range band.
- **Track plots** of the three systems on a representative engagement, at zig + 10 and + 20 min.
- **Operational table**: metres, degrees, knots and the share of engagements settled.
