---
title: "Slides: a manoeuvre prior that adapts to the period, and a hedged track"
date: 2026-11-15
tags: [slides, spec-018]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 018 write-up](/blog/2026/11/15/adaptive-prior):
the family of priors, the registered comparison on a fresh seed, where a gain was
expected, the hedged track's spread, what the review panel found, and two periods as
tracks.

<!-- truncate -->

<Slides slug="2026-11-15-adaptive-prior-slides" />

## What the figures show

- **Verdict**: the standing control ÷ the adaptive control (declared, hedged) and ÷ the
  search told the true statistics, in range, on every split, with intervals and period
  counts. Grey ticks are median per-period ratios.
- **Quantities**: the same in range, course and speed on Annex B and shifted targets.
- **Kinds**: shifted targets by kind of period: where the standing control misses a
  manoeuvre the bearings show, where it does not, and by how tight the bound is.
- **Groups**: the prior chosen by one period, by groups of 5 and 20, and by the whole split.
- **Spread**: the share of rows within one and two stated sds of the hedged track's range,
  against the registered band.
- **Two periods as tracks**, chosen by a rule in the script: of the 20 stored shifted
  periods, the one where the hedged track is best against the control and the one where
  it is worst.

The panel's readings (how flat the choice among priors is, the pooled figures over three
seeds) are the reviewers' recomputations; they are on a slide as a table and in
`experiments/20261115-tl6/review.md`, not in a generated figure.

## Reproducing the figures

```
uv run python scripts/research/tl6_tracks.py <results folder> experiments/20261115-tl6
uv run python scripts/research/tl6_charts.py --record experiments/20261115-tl6 --out-dir site/static/img/2026-11-15-adaptive-prior-slides
```

The charts read only the committed record; each figure's `.json` sidecar names the inputs'
digests and the commit. `tracks.npz` holds the first 20 shifted periods' tracks, extracted
from the results branch `results/timelate-tl-g-test-43677426621`. The data are seed 347,
5-second bearings, ranges files under `configs/timelate/`, generated in the CI run.
