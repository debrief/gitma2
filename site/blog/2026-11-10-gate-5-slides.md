---
title: "Slides: Gate 5, an honest course statement"
date: 2026-11-10
tags: [slides, gate-5, spec-010]
---

import Slides from "@site/src/components/Slides";

This is the illustrated companion to [the Gate 5 write-up](/blog/2026/11/10/gate-5). It covers the
consistent course statement, how P now ranks hits, where P is still not honest, the validation
verdict and what the review panel found.

<!-- truncate -->

<Slides slug="2026-11-10-gate-5-slides" />

## What the figures show

- **Reliability diagram.** Stated P against the hit rate, in five equal-count bins of P, on the
  3,934 validation rows (seed 314, ordinals 500–1499). The statements shown are E with a
  statement from its raw sds, the sd^β temperature, the carried classical rule and the head
  st5-s1. The diagonal is an honest statement.
- **By slice.** Mean stated P beside the hit rate, for the classical rule and the head. The slices
  are overall, the causal proxy's flag, the truth's settled split (reported, not gated) and three
  range bands.

## Reproducing the figures

Both figures are drawn by `scripts/research/g5_charts.py` from the committed records
`experiments/20261109-g5-val/calibration.json` and
`experiments/20261109-g5-base-val/calibration.json`. Each `.svg.json` sidecar names the inputs'
digests and the code commit (d0ea691, clean).
