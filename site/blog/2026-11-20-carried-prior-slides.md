---
title: "Slides: a carried prior across gaps"
date: 2026-11-20
tags: [slides, spec-028]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 028 write-up](/blog/2026/11/20/carried-prior): the
registered comparison, where the carried prior helps, and how well its stated uncertainty covers
the truth.

<!-- truncate -->

<Slides slug="2026-11-20-carried-prior-slides" />

## What the figures show

- **Verdict**: alone ÷ k4 and k4 ÷ joint in range on every split, periods after an engagement's
  first, with 95% engagement intervals.
- **Kinds**: alone ÷ the carried prior, uninflated and k4, for periods with and without an
  ownship turn of their own (Annex B and busier).
- **Coverage**: the truth's squared distance from the carried prior at a period's first row, as a
  cumulative distribution against a calibrated one (Annex B).

## Reproducing the figures

```
uv run python scripts/research/tl10_charts.py --record experiments/20261120-tl10 --out-dir site/static/img/2026-11-20-carried-prior-slides
```

The script reads only the committed record (results branch
`results/timelate-tl-o-test-44618826527`, seed 363); each figure's `.json` sidecar names the
inputs' digests and the commit.
