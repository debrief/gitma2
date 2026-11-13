---
title: "Slides: Gate T, the track after the fact"
date: 2026-11-12
tags: [slides, gate-t, spec-013]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the Gate T write-up](/blog/2026/11/12/gate-t): the question
(the whole track over a period, after the fact), why a test of fit cannot answer it, the
classical search that uses the owner's manoeuvre statistics, the gate on test seed 331, and
what the review panel narrowed.

<!-- truncate -->

<Slides slug="2026-11-12-gate-t-slides" />

## What the figures show

- **Two histories, the same bearings.** One tuning period in which a history with no
  manoeuvre fits the bearings as well as the true one.
- **Told the manoeuvres, the arc model reaches the bound.** Tuning seed 329: the chord
  solve and the arc solve against the Cramér–Rao bound.
- **The ratio on three seeds.** C″ ÷ search with its 95% interval, on Annex B data and the
  shifted prior, beside the registered thresholds.
- **Every system as a track.** Median period range error on the test seed.
- **The reference by how tight the bound is.** The fit from neutral starts against the fit
  started at the truth, which sits below the bound where the bound is loose.
- **Stated probability against hit rate**, and **manoeuvres found minus true**.

There are no track plots with uncertainty ellipses: the search states candidate tracks
with probabilities and no covariance.

## Reproducing the figures

```
uv run python scripts/research/gt_charts.py --out-dir site/static/img/2026-11-12-gate-t-slides
uv run python scripts/research/tl_charts.py --out-dir site/static/img/2026-11-12-time-late-slides --data <dir>
```

The first script reads only committed records (`experiments/20261112-gt-val/`,
`20261112-gt2-val/`, `20261112-gt2/`); the second made the first two figures from tuning
records and, for the ambiguity figure, from tuning seed 329 (count 400,
`configs/timelate/tl-ranges.json`). Each figure's `.json` sidecar names the inputs' digests
and the commit. The gate's data are seeds 330 and 332 (validation) and 331 (test), 5-second
bearings, `configs/timelate/tl-ranges.json` and `tl-shift-ranges.json`, generated in the
scoring runs.
