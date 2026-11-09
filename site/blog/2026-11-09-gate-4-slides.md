---
title: "Slides: Gate 4, usable uncertainty"
date: 2026-11-09
tags: [slides, gate-4, spec-009]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the Gate 4 write-up](/blog/2026/11/09/gate-4): the course statement
("within ±X with probability P, otherwise unknown"), how honest it is on average and by slice, the
validation verdict and what the review panel found.

<!-- truncate -->

<Slides slug="2026-11-09-gate-4-slides" />

## What the figures show

- **Reliability diagram.** Stated P against the hit rate in five equal-count bins of P, on the
  3,934 validation rows (seed 314, ordinals 500–1499): the oracle and E with statements derived
  from their raw sds, the sd^β temperature and the carried head (st-s3). The diagonal is an honest
  statement.
- **By slice.** Mean stated P beside the hit rate for the temperature and the head: overall,
  settled or not (defined from the truth), with a transition open at the row or not, and by
  minutes after the zig.

## Reproducing the figures

Both figures are drawn by `scripts/research/g4_charts.py` from the committed records
`experiments/20261109-g4-val/calibration.json` and `experiments/20261108-g4-base-val/calibration.json`;
each `.svg.json` sidecar names the inputs' digests and the code commit (4b707b3, clean).
