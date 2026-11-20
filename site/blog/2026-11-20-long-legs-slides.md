---
title: "Slides: the carried prior where the ownship's legs outlast the window"
date: 2026-11-20T23:45
tags: [slides, spec-032]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to [the write-up](/blog/2026/11/20/long-legs). On
blind 2-hour windows, `ctl` ÷ `ctl-prior` is **1.54 [1.16, 2.03]** ("ctl-prior better"). Against
a joint solve over the same past bearings it is 1.11 (not separated). There is no harm. Spec:
`specs/032-long-legs/`.

<!-- truncate -->

<Slides slug="2026-11-20-long-legs-slides" />

## What was built

- **The scorer:** `src/tma2/long/study32.py`, run by `tma2-long study32`.
- **`jointheld`** always writes its `.npz`.
- **Configs:** `configs/long/legs-{tuning,val,test}.json` and run files
  `configs/long/runs/legs-*.json`.
- **Scripts:** `scripts/research/legs_{digests,charts}.py`.
- **Tests:** `tests/unit/test_long_study32.py`.
- **Records:**
  - tuning: `experiments/20261120-legs-tuning/`;
  - decision: `20261120-legs-decision/`;
  - validation: `20261120-legs-val/`;
  - test: `20261120-legs/`, with `review.md`.

## What was not achieved

- **Unscored:** the windows where contact was lost (half the blind windows).
- **Untested:** ordinary ranges with the ownship holding course, and chains of blind windows.
- **Not calibrated:** the carried uncertainty, which is not a stated uncertainty.

## What comes next (the owner's choice)

- **Recommended:** adopt 2-hour `ctl-prior` for the tended contact, and close the track with a
  synthesis.
- **Alternatives:**
  - an E2 study at ordinary ranges;
  - repair the hand-over;
  - lost-contact prediction.

Figures: `scripts/research/legs_charts.py`, with a sidecar beside each SVG.
