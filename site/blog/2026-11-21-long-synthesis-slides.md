---
title: "Slides: the long-engagement track as a whole"
date: 2026-11-21T15:30
tags: [slides, spec-034]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to [the write-up](/blog/2026/11/21/long-synthesis).
- Stitched 2-hour `ctl` holds up over long engagements.
- A carried start saves compute.
- A carried prior roughly doubles accuracy where a window is blind to range, but does not beat
  keeping the bearings.
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
