---
title: "Slides: the long-engagement track as a whole"
date: 2026-11-21T15:30
tags: [slides, spec-034]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to [the write-up](/blog/2026/11/21/long-synthesis).
- Stitched 2-hour `ctl` held up on the tended contact (registered to 12 h; 24 and 48 h one engagement each).
- A carried start is not shown to help accuracy; it saves about 31% of the search where it runs.
- A carried prior beats the same window alone where that window is blind to range (1.7–2.4 on
  1-hour windows, 1.37 pooled on 2-hour windows at far range), and is not shown to beat keeping the bearings.
- The owner adopted 2-hour `ctl-prior`, and the track closes here.

Spec: `specs/034-long-synthesis/`.

<!-- truncate -->

<Slides slug="2026-11-21-long-synthesis-slides" />

## What was built

- **The figures script:** `scripts/research/long_synthesis.py`. It reads every figure of record
  from the test records of specs 026, 028, 029, 031 and 032, and writes
  `experiments/20261121-long-synthesis/tables.md`, `summary.json` and the two charts.
- **Records:** no new runs, and no new seed.

## What was not achieved

These were never tested: real bearings, association, an ownship steered by its own track, a
calibrated carried covariance, hand-overs inside a manoeuvre, and registered comparisons beyond
12 hours.

## What comes next (the owner's choice)

The track is closed unless the owner reopens it. It would be worth reopening with measured
realism, with association, or for a case where only a hand-over can travel.

Figures: `scripts/research/long_synthesis.py`, with a sidecar beside each SVG.
