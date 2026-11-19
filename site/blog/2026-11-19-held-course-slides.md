---
title: "Slides: the carried prior where the ownship holds course"
date: 2026-11-19T22:30
tags: [slides, spec-029]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to [the write-up](/blog/2026/11/19/held-course).
The ownship holds each leg for 1–2 hours. On 1-hour windows with no ownship turn, the previous
window's state, carried as a prior, gives ctl ÷ ctl-prior **2.41 [2.06, 2.83]**, against the
same window alone. The registered rule says gain, with no harm. Spec: `specs/029-held-course/`.

<!-- truncate -->

<Slides slug="2026-11-19-held-course-slides" />

## What was built

- **Configs:** `configs/long/hold-{tuning,val,test}.json`, which hold the ownship's legs to
  1–2 h.
- **CI:** `long.yml` passes the window length and overlap through.
- **The scorer:** `src/tma2/long/study29.py`, run by `tma2-long study29`. It classifies windows
  by ownship turns, applies the rule, and reads coverage and soundness.
- **Scripts:** `scripts/research/hold_{digests,supplement,charts}.py`.
- **Records:**
  - tuning: `experiments/20261119-hold-tuning/`;
  - decision: `20261119-hold-decision/`;
  - validation: `20261119-hold-val/`;
  - test: `20261119-hold/`, with `review.md` and `supplement.json`.

## What was not achieved

- **Untested comparisons:** `ctl` on 2-hour windows, and a joint solve over consecutive windows.
- **Not measured:** whether the prior narrows the set of manoeuvre histories.
- **Untested settings:** the untended contact, and real data.
- **Kept defect:** spec 028's hand-over defect.

## What comes next (the owner's choice)

- **Recommended:** adopt `ctl-prior` with its guard for the tended contact. Then run one
  registered comparison against 2-hour `ctl` and a joint solve, on held-course engagements.
- **Alternatives:**
  - repair the hand-over;
  - the untended contact under held course;
  - close the track.

Figures: `scripts/research/hold_charts.py`, with a sidecar beside each SVG.
