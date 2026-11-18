---
title: "Slides: time-late over several periods of one target, joined through the gaps"
date: 2026-11-18
tags: [slides, spec-025]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 025 write-up](/blog/2026/11/18/joined-periods): one
engagement as tracks, the registered verdict, where the gain comes from, manoeuvres in the
gaps, and what the review panel narrowed.

<!-- truncate -->

<Slides slug="2026-11-18-joined-periods-slides" />

## What the figures show

- **Track**: one Annex B engagement of the test seed (353), chosen by a rule in the script
  (the median engagement among the stored three-period ones): truth red, ownship blue, `ctl`
  alone per period orange, the joint solve green and dashed through the gaps.
- **Verdict**: `ctl` alone ÷ joint in range on every split with 95% engagement intervals, on
  the registered rows and on rows the period determines alone.
- **Kinds**: the same for periods with and without an ownship turn of their own.
- **Gaps**: true manoeuvres inside gaps found and missed, and the share of quiet gaps with
  an invented manoeuvre.

## Reproducing the figures

```
uv run python scripts/research/tl8_charts.py --record experiments/20261118-tl8 --out-dir site/static/img/2026-11-18-joined-periods-slides
```

The script reads only the committed record (results branch
`results/timelate-tl-k-test-44252585727`); each figure's `.json` sidecar names the inputs'
digests and the commit. Data: seed 353, 5-second bearings, `configs/timelate/tl-joined-*.json`,
generated in the CI run.
