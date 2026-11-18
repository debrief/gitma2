---
title: "Several periods of one target, joined through the gaps: a gain, mostly where a period could not stand alone"
date: 2026-11-18
tags: [write-up, spec-025]
---

Contact on a target comes and goes. Every time-late study so far gave the standing system
one period per target. This one gave it two or three periods of the same target, separated
by gaps with no bearings, and asked whether one solve over the whole span, with the track
continuous through the gaps, beats solving each period alone. By the rule registered
beforehand it does, on all four splits and with no harm. The review panel approved and
narrowed what that means: most of the gain is periods that cannot be solved alone becoming
solvable. Nothing was trained. The illustrated companion is
[the slides post](/blog/2026/11/18/joined-periods-slides).

<!-- truncate -->

## What was built

The joint solve needed no new search. The standing control `ctl` (spec 016: the evidence
search over manoeuvre histories with the arc model, wild bearings edited, declared at an
evidence margin of 1) already handles missing bearings. Given the span from the first
period's start to the last period's end, with the gaps' bearings marked missing, it runs
unchanged. The arc model carries the track through each gap, and the search may place
manoeuvres there.

Each engagement is laid out as two or three periods of 15 to 30 minutes with gaps of 5 to 30
minutes, from a random stream of its own. Three solves run on the same bearings:

- each period alone;
- the joint solve;
- the span with every bearing (what the gaps cost).

Each period is scored on rows 30 s apart where the known-history bound from the span's
bearings is below 0.5. Both sides use the same rows.

## How it was decided, and the first registration that stopped

The rule: the per-period ratio of median range error, alone ÷ joint, has its geometric mean
over periods and a 95% interval from resampling engagements.

- *gain*: the interval is wholly above 1;
- *harm*: the interval is wholly below 1 in range, course or speed on any split.

The first registration stopped at validation (seed 350). Its soundness check read 0.75
against a band of 0.8 to 1.5. The check was a median over the rows of about twenty
engagements, but a fit's rows share one error, so each engagement is in effect one draw. On
tuning the check's own interval had already crossed the band's edge. That was my fault in
the registration, not the reference's. With the owner's agreement it was re-registered
(fresh seeds 352 and 353) with a statistic over engagements. It passed validation at 1.13
[0.80, 1.62] over 66 engagements. The test seed was scored once.

## The result

| split | alone ÷ joint, range | on rows a period determines alone |
|---|---|---|
| Annex B (decided) | **3.10 [2.22, 4.58]** | 2.64 [1.68, 4.70] |
| busier targets | **1.97 [1.63, 2.39]** | 1.28 [0.95, 1.75], not shown |
| 2% wild bearings | **2.72 [2.04, 3.75]** | 2.21 [1.52, 3.29] |
| held course | **12.8 [8.5, 20.4]** | 3.56 [2.33, 5.43] |

Gain on every split; no harm in any quantity. The median per-period ratio is 2.09 on Annex
B and 1.69 on busier targets.

## What it means, as the panel narrowed it

- **Mostly an answer where there was none.** Rows were chosen by the span's bound. On rows
  that only the joined data determine, `ctl` alone's median relative range error is about
  0.46, the scoring cut-off: it had no estimate there. Periods without an ownship turn of
  their own gain 4.35 (Annex B). Periods with one gain 1.65 (Annex B) and 1.13 [0.90, 1.43]
  on busier targets, where no gain is shown. The difference between the two kinds of period
  is the one reading that is real on every split.
- **Held course is the easy case.** On held course the whole span is one leg, which suits
  the model by construction. The 12.8 says nothing about how far the result reaches.
- **The splits are not independent.** The wild-bearing split is Annex B's engagements with
  outliers added, and held course shares 69 of 70 layouts with Annex B.
- **One period in eight is twice as bad joined** (12% Annex B, 15% busier). Nothing in the
  output says which.
- **Gap manoeuvres.** Of true manoeuvres inside gaps the joint solve declares 40 of 43
  (Annex B) but only 83 of 130 on busier targets (36% missed). It invents one in about a
  fifth of quiet gaps. An inferred gap manoeuvre looks the same in the output as an observed
  one.
- **What the gaps cost.** With every bearing the span is solved about 1.6 times better
  (every bearing ÷ joint 0.61), but only on rows the gaps make hard. On rows a period
  determines alone the difference is not shown (0.86 [0.62, 1.18]).
- **The soundness check is a screen.** It catches a reference that returns its start. It
  does not measure efficiency: a perfectly efficient reference reads about 0.79 under its
  own model, and the geometric mean hides runaway fits, which reach 773 on test.

So the outcome is narrower than "joining is three times better". Within these simulated
conditions the joint solve is the standing time-late system for two or three periods of one
target in at most two hours. The conditions are periods of 15 to 30 minutes, gaps of 5 to 30
minutes, certain association and Annex B manoeuvres in the gaps. It beats ignoring the other
periods. Whether it beats carrying state from one window to the next (spec 024) is not
tested.

## Forecasts

Right: Annex B about 3, wild bearings about 2.5, held course about 10, busier targets a gain.

Wrong:

- a loss on busier periods with their own ownship turn: they came out level;
- a loss on 10 to 20 minute gaps: they gained;
- gaps costing a factor of two: it was about 1.6.

The held-course false-manoeuvre forecast (under 0.15) came out at 0.17, which is not
separated from it.

## What was not done

- No comparison with spec 024's carried state: it was not merged when the test ran.
- No IMM or EKF tracks beside.
- No test of the runner's slicing; a reviewer's check stands in.
- Run-to-run variation between CI machines (about 8% on tuning) was not re-measured. It
  cannot change the verdict.
- Gaps over 30 minutes, uncertain association across a gap and several targets are
  untested.

## What next (the owner's choice)

The panel's order:

1. Score spec 024's carried state on these engagements.
2. A per-period consistency flag and markers on inferred gap manoeuvres, measured first on
   spent seeds for whether the flag finds the twice-as-bad periods.
3. A stated uncertainty for the joined track.
4. A stress split with longer, busier gaps.
5. Association across a gap is a scope question for the owner.

Records: decision `experiments/20261118-tl8-decision2/` (the first,
`20261118-tl8-decision/`, stopped at `20261118-tl8-val/`), validation
`20261118-tl8-val2/`, test `20261118-tl8/` with the panel's `review.md`, tuning
`20261117-tl8-tuning/`. Spec `specs/025-joined-periods/`.
