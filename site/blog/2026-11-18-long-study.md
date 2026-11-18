---
title: "Long engagements: the registered study"
date: 2026-11-18T15:00
tags: [write-up, spec-025]
---

A registered study on fresh seeds: 60 realistic engagements of 6 and 12 hours, scored once.
Each rule returned what it was registered to return:
- carrying state between time-late windows is **non-inferior**, by 0.008;
- the contact the ownship does not tend is **about 1.5 times worse** where it is held;
- the IMM's drift is **not shown**.

The review panel narrowed all three. The long-engagement track is recommended to stop here as a
simulation study. Spec: `specs/025-long-study/`; record: `experiments/20261118-ls/`.

<!-- truncate -->

## What was registered

Before seeds 350 and 351 existed, the decision record (`experiments/20261118-ls-decision/`)
bound the estimands, the run files and the code by digest.
- **E1**: on the tended contact, the per-window ratio of `ctl`'s median range error to
  `ctl-carry`'s. Carry is non-inferior if the geometric mean's 95% interval has a lower limit
  of at least 0.95.
- **E2**: on the untended contact against the tended one, in range bands. A magnitude.
- **E3**: the IMM's median error in hours 6–12 against hours 0–6. Drift is shown if the interval
  lies above 1.
- **Soundness**, on validation (seed 350): windows ran; `ctl` is sane against the true-history
  fit; bearings are held a realistic share of the time. It passed.

## What the test returned (seed 351)

| | estimate | 95% interval | rule's output |
|---|---|---|---|
| E1 | 1.017 | [0.958, 1.082] | non-inferior |
| E2 | 1.47 | [1.12, 2.05] | a magnitude |
| E3 | 1.06 | [0.82, 1.31] | not shown |

Soundness passed again: 360 of 360 windows ran; `ctl` ÷ the reference was 1.36; bearings were
held 0.85 of the time.

## What it may be taken to mean (panel, round 1)

**E1: the rule's yes rests on level windows.**
- 60 of the 359 windows are each chain's first, where `ctl-carry` *is* `ctl`, and 113 more come
  out identical.
- Without the first windows the estimate is 1.021 [0.9502, 1.100], 0.0002 above the line.
- Where the two systems differ, it is 1.034 [0.923, 1.168]: not shown to be within 5%.
- At 12 hours alone it is 1.005 [0.923, 1.096]. On the untended contact it is 0.942
  [0.880, 1.007], twice worse in 16 windows and twice better in 7.
- Carrying is therefore adopted only as a cost measure, and only for the tended contact on 6–12
  hour engagements. It saves 31% of the search where it runs, about 7% of all CPU. It is not
  recommended for an untended contact.

**E2: a description of this simulator, not "the cost of an untended contact".**
- The second target has no range keeping. It is scored only where it is detected, which is 61%
  of its rows.
- Within a band it sits farther out than the tended one. In 2-km sub-bands the ratio is 1.34
  [1.01, 1.87].
- Bearing rate and ownship manoeuvres are not matched. Mis-association is not exercised: 314
  swapped bearings in about 389,000.
- The forecast of 1.2–1.4 assumed range banding would remove most of the geometry. It did not.

**E3: says nothing about failures.**
- The share of rows the IMM answers falls from 0.91 to 0.74–0.79.
- With unanswered rows counted as failures, the ratio is 1.26 [0.88, 1.80]. The interval does
  not exclude a 30% rise.
- What is shown is fewer answers later on, not a stable error.

## Known limits

- The realism parameters (gaps, detection, the steering error) are spec 024's choices, not
  measured. The ownship steers on a fresh noisy draw of the truth, not on any estimator's
  track.
- The shards ran on seven CPU families. E2 compares two jobs.
- The panel's minor findings, all in `review.md`:
  - S1 counted one window that gave no answer;
  - the weighting is by window;
  - provenance details.

## What comes next (the owner's choice)

Recommended: **stop the long-engagement track here as a simulation study**, with `ctl-carry`
recorded as an optional cost measure for tended contacts up to 12 hours. More registered
studies on hand-set realism would measure the parameters, not the systems.

Reopen the track only with one of three things:
- measured gap, detection and association statistics;
- an ownship steered by the estimator's own track;
- a tracker that handles association.

The slides: [long engagements: the registered study, slides](/blog/2026/11/18/long-study-slides).
