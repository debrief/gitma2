---
title: "Long engagements: the carried prior against longer windows"
date: 2026-11-20T12:00
tags: [write-up, spec-031]
---

Spec 029 found that on held-course 1-hour windows, carrying the previous window's state as a
prior (`ctl-prior`) beats solving the window alone. Its panel called that "more data beats no
data" and asked for the fair comparisons: `ctl` on its standing 2-hour windows, and a joint solve
over the turn-free hour and the hour before it.

**The result:** the registered rule reads **"ctl-prior worse" against every comparator**. The
clean comparison is the joint solve. It uses the same past as the carried prior and no later
bearings, and its error is **0.774 [0.632, 0.954]** of the prior's. A 1-hour window with a carried
prior is not a substitute for using the bearings themselves.

Spec: `specs/031-held-comparators/`. Record: `experiments/20261120-cmp/`.

<!-- truncate -->

## The design

- **Engagements:** spec 029's held-course engagements: ownship legs of 1–2 h, the tended contact,
  60 engagements of 6 and 12 h.
- **Systems,** each on its own windows and read on the same turn-free 1-hour windows:
  - **(a)** 1-hour `ctl-prior`, spec 029's system;
  - **(b)** `ctl` and `ctl-prior` on 2-hour windows overlapping 30 min, stitched mid-overlap;
  - **(c)** `ctl` on the union of the turn-free hour and the hour before it: the joint solve.
- **Estimands,** each comparator's error ÷ (a)'s in range, as a geometric mean with a bootstrap
  over engagements:
  - **D1:** 2-hour `ctl`;
  - **D2:** the joint solve;
  - **D3:** 2-hour `ctl-prior`, added on tuning before validation.
- **Rule:** "ctl-prior better" or "worse" when the interval excludes 1. The rule was registered
  before seeds 365 and 366 existed (`experiments/20261120-cmp-decision/`).

## What happened

Test: seed 366. 179 decided turn-free windows from 56 engagements, scored once. Soundness passed.

| comparator ÷ 1-hour `ctl-prior` | range | median | (a) better | (a) twice as bad |
|---|---|---|---|---|
| D1: 2-hour `ctl` | 0.730 [0.579, 0.917] | 0.90 | 43% | 35% |
| **D2: joint solve** | **0.774 [0.632, 0.954]** | 0.78 | 41% | 37% |
| D3: 2-hour `ctl-prior` | 0.488 [0.386, 0.619] | 0.58 | 26% | 45% |

- **Course and speed** agree in direction, with intervals wholly below 1.
- **Median range error on turn-free windows:**

  | system | median error |
  |---|---|
  | 1-hour `ctl` | 22.4% |
  | 1-hour `ctl-prior` | 10.2% |
  | 2-hour `ctl` | 9.0% |
  | joint solve | 7.0% |
  | 2-hour `ctl-prior` | 4.2% |

- **Spec 029's gain replicates** at 1.71 [1.40, 2.14]. Quote it as about 1.7 to 2.4.
- **The forecasts** were 1.1–1.3 for D1 and D2, and **wrong in direction**. Tuning had pointed
  that way on about 34 windows, but it compared (a) from spec 029's run on another CPU family with
  (b) and (c) from this run, which spec 024's gotcha forbids. D3's forecast was right in direction,
  and the effect was larger than forecast.

## What the panel narrowed

Three reviewers each approved with findings (`experiments/20261120-cmp/review.md`). Every decided
number was reproduced independently.

- **D2 is the clean comparison.**
  - D1 and D3 take 98% of their rows from a 2-hour window that contains an ownship turn, and that
    window runs a median of 29 min past the hour.
  - So they also measure geometry and latency. The joint solve has neither advantage and still
    wins.
- **These are averages with wide spread.** The 1-hour prior is better in about 4 windows in 10 and
  twice as bad in about a third.
- **The readings are conservative.** Four windows where 1-hour `ctl-prior` gave no answer at all
  are excluded, and the comparators answered all four.
- **Heterogeneity.** D2 is 0.62 on 6-hour engagements and 0.90 [0.69, 1.17] on 12-hour ones.
- **2-hour `ctl-prior` is not shown best here.**
  - Its edge over 2-hour `ctl` (1.49 held, median 1.14; 1.26 one-turn, median 1.01) is supplement
    only, and validation went the other way.
  - The registered support for it is spec 028's test.
- **Cost and latency.** Per engagement-hour, the 2-hour job costs about 2.1× the 1-hour one, but
  both run several systems, so no single system's cost is known. A 2-hour estimate waits for up to
  an hour of later bearings and updates every 90 min instead of 45.
- **Limits:**
  - ownship legs of 1–2 h;
  - contact 1;
  - one simulator;
  - windows placed past true target manoeuvres;
  - spec 028's hand-over defect kept.

  Legs longer than the standing 2-hour window, the owner's blind case at the standing
  configuration, were not tested.

## What it means for the owner's question

The previous track does constrain a blind leg: spec 029 shows that. But the same past bearings
used directly in a joint fit constrain it better than a Gaussian summary of them. The carried
prior compresses the past into four numbers and a covariance. Where those bearings are available,
fitting them beats summarising them.

Spec 029's recommendation, `ctl-prior` on 1-hour windows, is **withdrawn**. What stands is spec
028's: `ctl-prior` with its guard on 2-hour windows for tended contacts up to 12 h.

## Next (the owner's choice)

- **Recommended default:** close the long-engagement track as a simulation study, with `ctl` on
  2-hour windows and spec 028's `ctl-prior` standing. Write one synthesis of specs 023 to 030.
- **Alternatives:**
  - **Legs longer than the window:** ownship legs of 2–4 h with 2-hour windows, compared on past
    bearings only, reporting the 2-hour hand-overs' guard rate and coverage.
  - **Reopen with new information:** measured realism, an ownship steered by its own track, or
    association.

Slides: [the slides post](/blog/2026/11/20/held-comparators-slides).
