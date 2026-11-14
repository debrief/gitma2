---
title: "Slides: what the shifted-prior gap is made of"
date: 2026-11-14
tags: [slides, spec-017]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 017 write-up](/blog/2026/11/14/shifted-gap): how
detectable the busier targets' manoeuvres are, what the control misses, the gap as a chain
of references, what the review panel found, and two periods as tracks.

<!-- truncate -->

<Slides slug="2026-11-14-shifted-gap-slides" />

## What the figures show

- **Detectable**: the share of true manoeuvres whose omission adds less than 10, 20 and 40
  to the χ² of the true history's fit, by split.
- **Missed**: on the shifted split, the share of manoeuvres each system misses, by
  detectability band. The search under the targets' own prior misses fewer at every band.
- **Chain**: the control against the reference told every manoeuvre, the cost of not being
  told the ones under 20, the control against that reference, and the control against the
  true-prior search. Grey ticks are median per-period ratios.
- **Share**: the attainable share of the control's gap at each threshold, by split (under
  outliers, against references fitted to the edited bearings).
- **Two periods as tracks**, chosen by a rule in the script: of the 20 stored shifted
  periods with at least two whole true manoeuvres, the one with the largest share under 20
  and the one with the smallest.

The panel's split of the gap into two kinds of period is in the write-up and
`experiments/20261114-tl5/review.md`; it is the reviewers' recomputation, shown on a slide
as a table and not as a generated figure.

## Reproducing the figures

```
uv run python scripts/research/tl5_tracks.py <results folder> experiments/20261114-tl5
uv run python scripts/research/tl5_charts.py --record experiments/20261114-tl5 --out-dir site/static/img/2026-11-14-shifted-gap-slides
```

The charts read only the committed record; each figure's `.json` sidecar names the inputs'
digests and the commit. `tracks.npz` holds the first 20 shifted periods' tracks, extracted
from the results branch `results/timelate-tl-f-test-43618868241`. The data are seed 344,
5-second bearings, ranges files under `configs/timelate/`, generated in the CI run.
