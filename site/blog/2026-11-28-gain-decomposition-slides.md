---
title: "Slides: where the regressor's gain comes from"
date: 2026-11-28T11:00
tags: [slides, spec-038]
---

import Slides from "@site/src/components/Slides";

Spec 038 asked why a learned regressor beats our classical real-time system under bearing
errors, with nothing trained. The deck shows the test record and what the review panel made of
it. The critical account is the [write-up](/blog/2026/11/28/gain-decomposition); this post is
its illustrated companion.

<!-- truncate -->

<Slides slug="2026-11-28-gain-decomposition" />

## What the figures show

- **Systems**: C″-robust ÷ each system in range over 500 test engagements, in distribution, with
  clean bearings and under the primary mismatch. Above 1 the system is better than C″-robust.
- **Gap closed**: the share of the log gap to the regressor that each classical control closes,
  on four split and condition pairs. Dashed is the registered "most" line, dotted "little". The
  panel found these shares are carried by about a quarter of the engagements.
- **Lead by split**: C″-robust ÷ the fine-tuned regressor in distribution, on busier targets and
  on far ranges. The panel found the differences are mostly C″-robust moving.

## Reproducing the figures

```bash
uv run python scripts/research/gd_charts.py --out-dir site/static/img/2026-11-28-gain-decomposition
```

The charts are built from the committed `decomp.json` files of `experiments/20261128-gd/`;
sidecars beside each SVG name the inputs' digests and the commit.

## Not achieved

- A prior control tight enough to move the classical solve, so "prior or bearings" stays open.
- A classical segmenter that closes the gap without a cost on clean data.
- Track plots of a test engagement: not made for this task.

## Next

- Recommended, the owner's choice: a causal classical estimator given the generator's own
  priors, on CPU. No GPU spending.
