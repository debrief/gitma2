---
title: "Slides: the scaled regressor"
date: 2026-11-12
tags: [slides, spec-012]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 012 write-up](/blog/2026/11/12/scaled-regressor): a
learned control trained on a rented GPU, its two registered readings on the test seed, what
the review panel withdrew, and the classical control that did not explain the result.

<!-- truncate -->

<Slides slug="2026-11-12-scaled-regressor-slides" />

## What the figures show

- **Held course.** Error against the Cramér–Rao bound by geometry quartile, least squares
  beside the regressor (test seed 328, 7,816 rows). The regressor is furthest from the bound
  where the geometry is best and below it where the geometry is worst.
- **After manoeuvres.** Median relative range error by true-range quartile, regressor against
  C″, on the test seed and on the split with longer initial ranges. The margin grows with
  range on one and vanishes at the far end of the other.
- **Efficiency and the control.** Error against the bound on settled rows after manoeuvres
  (the regressor is worse than C″ in course), and the registered range-prior control beside
  C″ and the regressor.

There are no track plots: the regressor is a control that states no covariance and no
manoeuvre times, so there is no track with an uncertainty to draw beside the classical one.

## Reproducing the figures

```
uv run python scripts/research/r_charts.py --out-dir site/static/img/2026-11-12-scaled-regressor-slides
```

The script reads only committed records (`experiments/20261111-r-test/`,
`experiments/20261112-r-control/test.json`); each figure's `.json` sidecar names the inputs'
digests and the commit. The data behind those records are test seed 328 (5,600 engagements,
`configs/man2-ranges.json` and `configs/regress/held-course-ranges.json`), generated in the
scoring runs.
