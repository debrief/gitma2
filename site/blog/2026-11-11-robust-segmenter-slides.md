---
title: "Slides: the robust segmenter study"
date: 2026-11-11
tags: [slides, spec-011]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 011 write-up](/blog/2026/11/11/robust-segmenter): what
breaks the frozen segmenter under bearing-error mismatch, the most a better segmenter could
yield, and why the robust test we built was not carried.

<!-- truncate -->

<Slides slug="2026-11-11-robust-segmenter-slides" />

## What the figures show

- **Diagnosis.** The frozen C's false transitions and missed changes under each mismatch kind
  at central severity (tuning seed 323, 150 engagements, 593 scored prefixes).
- **Yield.** Median relative range error with the robust final solve: the true manoeuvre times,
  C″'s clean-data segmentation applied to the mismatched bearings, and C″ on the bearings it is
  given.
- **The settings choice.** For every confirmation test on the same 150 engagements: the share
  of the gap closed with its 95% interval, and false transitions against misses.

There are no track plots: the study stopped on the tuning seed before a segmenter was carried,
so there is no pair of systems whose tracks would show a measured difference.

## Reproducing the figures

All three are drawn by `scripts/research/gr_charts.py` from the committed records under
`experiments/20261110-gr-diagnosis/` and `experiments/20261111-gr-choice/`; each figure's
`.json` sidecar names its inputs' digests and the commit.

```bash
uv run python scripts/research/gr_charts.py --out-dir site/static/img/2026-11-11-robust-segmenter-slides
```
