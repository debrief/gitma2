---
title: "Slides: time-late, repaired and re-registered"
date: 2026-11-13
tags: [slides, spec-015]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 015 write-up](/blog/2026/11/13/time-late-repair): the
three repairs, the decided quantities on fresh seeds, a target that never manoeuvres by
period length, the headroom at every registered sensitivity, and what the review panel
narrowed.

<!-- truncate -->

<Slides slug="2026-11-13-time-late-repair-slides" />

## What the figures show

- **A target that never manoeuvres**: false-manoeuvre rate by period length, spec 014's
  search against the repaired one, with the flat and mixed priors and C″ (test seed 337).
- **The decided quantities on three seeds**: the refit's share of the gain and the two
  headroom figures, with intervals and the 10% line (development seed 335 is spent data).
- **Headroom by sensitivity and split**: the perfect-evidence figure at each class threshold
  and match tolerance, and on every split. The panel showed it also moves with how the
  reference is fitted, which this figure does not show.
- **Manoeuvring targets called quiet**, by number of true manoeuvres: the cost of the repair
  and of the mixed prior.

There are no track plots: the per-period tracks are not stored, only their errors.

## Reproducing the figures

```
uv run python scripts/research/tl3_charts.py --out-dir site/static/img/2026-11-13-time-late-repair-slides
```

The script reads only committed records (`experiments/20261113-tl3-dev/`,
`20261113-tl3-val/`, `20261113-tl3/`); each figure's `.json` sidecar names the inputs'
digests and the commit. The data are seeds 335 (development, spent), 336 (validation) and
337 (test), 5-second bearings, ranges files under `configs/timelate/`, generated in the CI
runs.
