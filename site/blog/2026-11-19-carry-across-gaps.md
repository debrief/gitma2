---
title: "Carrying state across gaps: a carried start does not substitute for joining"
date: 2026-11-19
tags: [write-up, spec-026]
---

Spec 025 showed that one solve over several periods of a target beats solving each period
alone. The cheaper habit is to solve period by period and hand each answer on to the next.
This registered study measured that habit against the joint solve. By the rule registered
beforehand, joining is better on Annex B targets, and the carry shows no effect over solving
alone there. The review panel approved and narrowed the result. What was tested is a carried
*start*, not carried information, so the study says nothing yet about carrying a prior.
Nothing was trained. The illustrated companion is
[the slides post](/blog/2026/11/19/carry-across-gaps-slides).

<!-- truncate -->

## What was built

The carry solves each period in order, on that period's own bearings. In the standing control
`ctl`, the search starts from two places: C″'s answer and a start from nothing. The carry
replaces the start from nothing with the previous period's declared state at its last row, run
forward at constant velocity through the gap. Everything else is `ctl`, as spec 024 designed
its carry for overlapping windows. With no carried state the code reproduces `ctl` exactly,
and every run checks this on each engagement's first period. Spec 024's own carry was not run:
it carries over rows that windows share, and across a gap there are none.

## How it was decided

All comparisons are over periods after an engagement's first, on spec 025's rows. Each is a
per-period ratio of period median range error, with a 95% interval from resampling
engagements.

- **Carry ÷ joint**: "joining better" if the interval is wholly above 1, "carry better" if
  wholly below.
- **Alone ÷ carry**: "carrying helps" if the interval is wholly above 1; "carrying harms" if
  the interval is wholly below 1 in range, course or speed.

Annex B decides.

- **Seeds**: tuning on spent seed 353, validation 360 (soundness passed), test 361, scored
  once.

## The result

| split | carry ÷ joint | alone ÷ carry |
|---|---|---|
| Annex B (decides) | **2.33 [1.66, 3.43]**: joining better | 1.07 [0.88, 1.34]: not shown |
| busier targets | 1.351 [0.993, 1.820]: not separated | 1.29 [1.09, 1.54]: helps |
| 2% wild bearings | 3.57 [2.21, 5.68]: joining better | 1.10: not shown |
| held course | 10.5 [5.5, 19.8]: joining better | 1.27: not shown |

No harm on any split in any quantity. The joint solve stays the standing system for several
periods of one target, within spec 025's conditions.

## What it means, as the panel narrowed it

- **Joining had to win.** Nothing from the earlier period enters the period's likelihood or
  prior; only where the search starts changes. Even the per-period fit told the true
  manoeuvre history is 8.4 times worse than joining on these rows (Annex B). So the study
  shows where the information is. It does not show what carrying, done properly, is worth.
- **The carry rarely changes the answer.** About half of later periods end exactly where `ctl`
  alone does. On busier targets the carry helps in about a quarter of periods, about twice as
  good there, almost all where the period has no ownship turn of its own (1.72). That is a
  different minimum of a poorly determined fit, not an answer the bearings endorse.
- **No harm shown, which is not the same as no cost.** Annex B periods with their own turn read
  0.91 [0.78, 1.02]. A wrong carried state replaces the start from nothing, which is the
  carry's only way to do harm.
- **Busier targets.** The range interval misses "joining better" by 0.007; joining is better in
  course and speed. For a busier period that stands alone, neither joining (spec 025: 1.06)
  nor carrying is shown to help.
- **No recommendation.** The first record recommended the carry where a joint solve is
  unavailable. The rule recommends it only if it helps on Annex B, which it does not, so the
  recommendation is withdrawn.
- **What "not shown" excludes.** On Annex B the interval rules out harm worse than about 12% and
  gains above about a third, and nothing smaller.

## Forecasts

Right:

- joining better on Annex B (about 2.2; 2.33);
- carrying not shown on Annex B;
- carrying helping a little on busier targets (1.29, larger than forecast).

Wrong:

- joining better on busier targets (not separated, by a hair);
- held course about 4 (it was 10.5);
- a harm in held-course speed (none).

## What was not done

- A carried prior.
- A test of the carry chain in the unit tests.
- IMM and EKF tracks.

## What next (the owner's choice)

The panel's order:

1. **A carried prior.** The previous period's state and covariance, widened through the gap by
   Annex B's manoeuvre rates, used as a prior in the period's evidence. Scored on spent seeds
   first, this decides whether joining is needed at all.
2. **A consistency flag.** A per-period flag for a failed join, and markers on inferred gap
   manoeuvres.
3. **An uncertainty.** A stated uncertainty for the joined track.
4. **Longer gaps.** Gaps longer than 30 minutes.

Records: decision `experiments/20261118-tl9-decision/`, tuning `20261118-tl9-tuning/`,
validation `20261118-tl9-val/`, test `20261119-tl9/` with the panel's `review.md`. Spec
`specs/026-carry-across-gaps/`.
