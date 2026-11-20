---
title: "Long engagements: the carried prior where the ownship holds course"
date: 2026-11-19T22:00
tags: [write-up, spec-029]
---

The owner's hypothesis was that knowledge of the previous track can usefully constrain the
solution for the next leg. Spec 028 could not test it, because its ownship never held course
long enough to leave a window blind. This study makes the ownship hold each leg for one to
two hours.

**Result:**
- The registered rule says **gain**, with no harm.
- On 1-hour windows that contain no ownship turn, carrying the previous window's state as a
  prior gives ctl ÷ ctl-prior **2.41 [2.06, 2.83]**. The median window improves 2.15-fold.
- The comparison is against the same window solved alone.

Spec: `specs/029-held-course/`. Record: `experiments/20261119-hold/`.

<!-- truncate -->

## The design

- **Engagements:** spec 024's simulated realism, with ownship legs of 1–2 h, the tended contact
  only.
- **Windows:**
  - With such legs, no 2-hour window is free of turns. Holds long enough to change that lose
    the target beyond detection.
  - So windows are 1 hour, overlapping 15 minutes. That gives about 30% of windows with no
    ownship turn.
- **Systems:** spec 028's `ctl-prior`, at its registered settings, is compared with `ctl` on the
  same windows. `ctl-prior` carries the previous window's state and uncertainty, fitted on
  bearings before the hand-over, into the next window's fit and evidence, with a guard.
- **Rule** (registered before seeds 363 and 364 existed):
  - **Gain** if the lower limit on turn-free windows is above 1.
  - **Harm** if any class's upper limit is below 1.
  - Windows where nothing was handed on are excluded, and the bootstrap is over engagements.

## What happened

Test: seed 364, 60 engagements of 6 and 12 hours, scored once.

| windows | ctl ÷ ctl-prior, range | median window | better |
|---|---|---|---|
| **no ownship turn (registered)** | **2.41 [2.06, 2.83]** | 2.15 | 76% |
| one ownship turn | 1.22 [1.06, 1.40] | 1.12 | 59% |

- **Course and speed** on turn-free windows: 1.96 and 2.24.
- **Median range error** on turn-free windows: from 22.7% to 7.4%.
- **Agreement across seeds:** tuning 2.10, validation 1.91, test 2.41.
- **The prior's own effect:** the carried start alone does little (1.14) and costs 11% on
  one-turn windows. The prior does the work: ctl-carry ÷ ctl-prior is 2.12.
- **Guard:** it fell back on 0.9% of windows.
- **Soundness:** all checks passed; held-window coverage was 0.945.

## What the panel narrowed

Three reviewers, each approve with findings (`experiments/20261119-hold/review.md`):
- **The comparator is a window chosen to be blind.** The result says the predecessor's state
  beats the same 1-hour window alone. Two comparisons were **not** tested: `ctl` on its usual
  2-hour windows, and a joint solve over consecutive windows.
- **The mechanism is range observability.** The previous track constrains this leg's solution
  where the leg alone cannot resolve range. Whether it narrows the set of manoeuvre histories
  was not measured.
- **The gain grows with range:** 1.66 under 15 km, 2.15 at 15–25 km, 3.19 beyond 25 km. Holding
  course pushes range up, so the pooled figure depends on this simulator's range mix. On
  one-turn windows the gain is not separated from 1 under 15 km.
- **The excluded turn-free windows are windows where contact was lost.** Counted as ties, the
  result is 2.34.
- **The coverage figure (0.945) passes the band but is not a calibration.** The region is too
  wide for most hand-overs.
- **Limits:**
  - one simulator, contact 1 only, 1-hour windows;
  - hand-overs never fall inside a target manoeuvre, because windows are placed by truth;
  - spec 028's hand-over defect is kept.
- **`ctl-carry` should not be used without the prior.**

## What it means for the owner's question

The previous track helps a great deal exactly where the owner expected: where the leg's own
bearings cannot fix range. In this simulator, on the tended contact, the median error on such
windows falls by about two-thirds. Spec 028's small average shift was the same mechanism in
windows that rarely needed it.

## Next (the owner's choice)

- **Recommended default:**
  - Adopt `ctl-prior` with its guard as the standing chained time-late system for the tended
    contact.
  - Next, one registered comparison on held-course engagements, each system on its own
    windows: `ctl-prior` on 1-hour windows, `ctl` on 2-hour windows, and a joint solve over two
    consecutive windows, with a reference told the truth over the span. This asks whether the
    prior is a cheap substitute for using the bearings themselves.
- **Alternatives:**
  - repair the hand-over (a neutral refit start) and rerun on spent seeds;
  - the untended contact under held course;
  - close the long-engagement track here.

Slides: [the slides post](/blog/2026/11/19/held-course-slides).
