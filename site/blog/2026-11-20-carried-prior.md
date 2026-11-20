---
title: "A carried prior across gaps: it helps where a period cannot answer alone"
date: 2026-11-20
tags: [write-up, spec-028]
---

Spec 027 showed that carrying a *start* from one period to the next does not substitute for one
solve through the gaps. This registered study carried *information* instead. The previous
period's declared state and its uncertainty become a prior on the next period's starting state.
By the rule registered beforehand, the carried prior helps against solving each period alone on
Annex B targets, and no harm was shown. The review panel approved and narrowed the result:

- the gain is in periods the bearings leave undetermined;
- the 4× inflation chosen in development is not shown to matter;
- the carried uncertainty covers the truth because it is too wide.

The joint solve stays the standing system. Nothing was trained. The illustrated companion is
[the slides post](/blog/2026/11/20/carried-prior-slides).

<!-- truncate -->

## What was built

For each period after an engagement's first, the evidence of the standing control `ctl` gains a
Gaussian prior on the period's starting state (position, course, speed). That prior is built in
three steps:

1. Take the previous period's declared track at its last row.
2. Take that state's Laplace covariance from the previous period's posterior fit.
3. Run both through the gap at constant velocity. Annex B's manoeuvre rate and sizes are added
   as process noise.

The prior replaces the standing prior's terms for those four parameters (range log-uniform,
bearing and course uniform, a soft speed band), and the period's search starts from the carried
state. Everything else in `ctl` is unchanged.

## How k4 was chosen

Development used spent seeds only.

- **Seed 361.** The uninflated prior was overconfident: the truth sat inside its 95% region in
  about half of periods. On this seed it harmed Annex B periods that had an ownship turn of
  their own (0.51).
- **The choice.** Five variants were run: inflation by 2 or 4 in sd, and mixtures with the
  standing prior. A rule written before the results kept only variants with no own-turn harm and
  coverage of at least 0.80. It chose **k4**, the covariance 4 times wider in sd.
- **Seed 360.** A declared check passed here.

## How it was decided

All comparisons use periods after an engagement's first, on spec 025's rows. Each is a ratio of
period median range error, with a 95% interval from resampling engagements.

- **Helps**: `ctl` alone ÷ k4 in range is wholly above 1 on Annex B, the split that decides.
- **Harms**: wholly below 1 in range, course or speed on any split, or in range on Annex B
  periods with their own ownship turn.

Validation used seed 362, where soundness passed. The test used seed 363, scored once.

## The result

| split | alone ÷ k4, range (median per period) | k4 ÷ joint, range |
|---|---|---|
| Annex B (decides) | **1.59 [1.21, 2.13]** (1.09): helps | 1.40 [0.98, 2.01] |
| busier targets | 1.60 [1.28, 1.99] (1.16) | 1.25 [0.94, 1.66] |
| 2% wild bearings | 1.35 [1.01, 1.87] (1.01) | 1.74 [1.23, 2.43] |
| held course | 2.32 [1.49, 3.62] (1.27) | 5.20 [2.93, 9.00] |

No harm on any split in any quantity. On Annex B periods with their own turn the ratio is 1.22
[0.84, 1.85]. On Annex B, k4 is better in 57% of periods and worse in 32%. It is twice as good
in 32% and twice as bad in 11%.

## What it means, as the panel narrowed it

- **The gain is where the bearings leave a period undetermined.**
  - Annex B periods without their own ownship turn: 1.97. With one: 1.22.
  - On rows a period determines by itself: 1.04 [0.77, 1.48], level.
  - So a carried prior makes undetermined periods answerable. It does not improve a period's own
    estimate. This is the same pattern as spec 025's joint solve.
- **The inflation is not shown to matter.**
  - The uninflated prior does as well on the test seed: uninflated ÷ k4 is 0.99 [0.78, 1.25].
  - The uninflated prior would also have passed the rule.
  - The own-turn harm that motivated k4 appeared on one development seed only.
  - What is supported is "a carried prior helps", not "inflate by 4".
- **k4's uncertainty is too wide, not calibrated.**
  - It covers the truth (0.92 to 0.98) because its spread is about 2.6 times too wide: median
    squared distance 0.51 against 3.36 for a calibrated prior.
  - The process noise is mis-shaped. It puts half of a turn's change into speed, and constant
    velocity runs the mean ahead of a turning target.
  - A single history's covariance is too narrow in the tail even with no manoeuvre in the gap.
  - After inflation the prior carries little beyond a band on position.
- **Against the alternatives.**
  - Against spec 027's carried start (not registered): 1.60 [1.05, 2.74] on Annex B.
  - Against joining: on the line on Annex B (lower limit 0.97 to 1.02 by bootstrap seed).
    Separated with wild bearings and on held course.
  - Joining is not shown unnecessary anywhere.
- **Across seeds.** Annex B alone ÷ k4 was 1.59, 1.22, 1.51 and 1.59 on seeds 360 to 363. The
  one that would not pass (361) is the seed k4 was chosen on.
- **When it applies.**
  - Within this simulator, when only the previous declared state and its covariance are kept, a
    period solved under them is better than one solved from nothing.
  - Time-late, the earlier bearings are normally kept, and then the joint solve is the answer.
  - A real hand-over was not tested: a track from another estimator, with uncertain association.
- **Secondary splits are reported, not decided.**
  - Wild bearings is on the line and carried by a tail (median 1.01).
  - Held course's 2.32 is measured against a baseline that is very poor there.

## Forecasts

Right:

- helps on Annex B (1.59, against a forecast of 1.2 to 1.6), with one development seed in two
  failing;
- busier about 1.55 (1.60), held course larger, no harm.

Wrong:

- k4 ÷ joint on Annex B (forecast about 2.1; 1.40, on the line).
- Coverage was "right" (0.92 to 0.98), but by being too wide.

## What was not done

- A calibrated carried uncertainty: a scale near 1.5, noise shaped to turns and speed changes,
  or a prior over the previous period's candidate histories.
- A registered comparison of k4 with the uninflated prior and with the carried start.
- Code that applies the rule: the verdict was applied by hand.
- IMM and EKF tracks.

Recorded, not repaired (the code is registered):

- the wrapped course Gaussian is normalised on the line, not the circle;
- a speed shoulder is left in the fit;
- three small fragilities.

## What next (the owner's choice)

The panel's order:

1. **A consistency flag.** Compare the carried prior's distance with the period's own fit, and
   test whether it finds the twice-as-bad periods.
2. **A calibrated carried prior on spent seeds.** Scale, shaped noise, the manoeuvre mixture and
   candidate histories.
3. **A stress split** with longer gaps and more periods, where a carried state is the realistic
   option.
4. **A real hand-over.** Only if that case matters: a carried state from another estimator, with
   uncertain association.

Records:

- spec `specs/028-carried-prior/`;
- development `experiments/20261119-tl10-dev/` and refinement `20261119-tl10-refine/`;
- decision `20261119-tl10-decision/`;
- validation `20261119-tl10-val/`;
- test `20261120-tl10/`, with the panel's `review.md` and `supplement.json`.
