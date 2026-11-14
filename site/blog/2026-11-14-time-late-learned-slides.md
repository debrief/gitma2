---
title: "Slides: time-late, classical controls and a learned model"
date: 2026-11-14
tags: [slides, spec-016]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 016 write-up](/blog/2026/11/14/time-late-learned):
the classical controls, the learned whole-period model, the registered comparison on a
fresh seed, what the review panel found the loss was made of, and track plots.

<!-- truncate -->

<Slides slug="2026-11-14-time-late-learned-slides" />

## What the figures show

- **The registered comparison**: declared control ÷ learned track for three training seeds
  on every criterion split, with intervals; the orange ticks are the median per-period
  ratio, which is 1.00 everywhere.
- **Every system** on every split: C″ as a track, the standing search, the classical
  control, the model's own track and its arc read-out, and the fit told the true history.
- **What the classical control adds**, on the tuning, validation and test seeds.
- **Manoeuvres missed and false**: the model's detector misses more and invents far fewer.
- **Training**: the monitor curve of the three seeds.
- **Three periods as tracks.** They are chosen by a rule in the script, not by eye: of the
  20 stored periods of the shifted split, the one where the learned track is worst against
  the control and the one where it is best; and the first stored outlier period with a
  true manoeuvre.

## Reproducing the figures

```
uv run python scripts/research/tl4_charts.py --out-dir site/static/img/2026-11-14-time-late-learned-slides
```

The script reads only committed records (`experiments/20261113-tl4-tuning/`,
`20261113-tl4-val/`, `20261114-tl4/`, `20261114-tlm-runs/`); each figure's `.json`
sidecar names the inputs' digests and the commit. `experiments/20261114-tl4/tracks.npz`
holds the tracks at scored rows for the first 20 periods of three splits, extracted from
the results branch `results/timelate-tl-e-test-43563825793`. The data are seeds 338
(tuning), 340 (validation) and 341 (test), 5-second bearings, ranges files under
`configs/timelate/`, generated in the CI runs.
