---
title: "Slides: time-late, the classical follow-on"
date: 2026-11-13
tags: [slides, spec-014]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 014 write-up](/blog/2026/11/13/time-late-classical):
the controls that split the search's gain, the classes of wrong histories, a target that
never manoeuvres, the owner's thinning idea, and the two code defects and narrowed claims
from the review panel.

<!-- truncate -->

<Slides slug="2026-11-13-time-late-classical-slides" />

## What the figures show

- **Every system as a track** on Annex B data, the shifted prior and held course (test seed
  335).
- **The decided quantities on three seeds**: the refit's share of the gain and the two
  attainable-headroom figures, with intervals and the 10% line.
- **Why the first candidate is wrong**: periods by class. The panel showed these shares
  move when manoeuvres cut by the period's edge are left out.
- **A target that never manoeuvres**: false-manoeuvre rate by system on three seeds. Part of
  the search's rate is a recorded defect in the evidence.
- **Thinning**: each form's cost against the search's run time, clean and with outliers
  (tuning seed 333). The orange points used a rule that broke bins on noise.
- **Bearing errors the fits are not told about**: correlated and outlying errors.

There are no track plots: the per-period tracks are not stored, only their errors.

## Reproducing the figures

```
uv run python scripts/research/tl2_charts.py --out-dir site/static/img/2026-11-13-time-late-classical-slides
```

The script reads only committed records (`experiments/20261112-tl2-tuning/`,
`20261112-tl2-val/`, `20261112-tl2/`, `20261112-tl2-thin/`); each figure's `.json` sidecar
names the inputs' digests and the commit. The data are seeds 333 (tuning), 334 (validation)
and 335 (test), 5-second bearings, ranges files under `configs/timelate/`, generated in the
CI runs.
