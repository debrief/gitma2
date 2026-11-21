---
title: "Slides: several periods of one target across long gaps"
date: 2026-11-21
tags: [slides, spec-033]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 033 write-up](/blog/2026/11/21/long-gaps): joining by gap
length, what holding course does to every system, and why joining fails beyond about an hour.

<!-- truncate -->

<Slides slug="2026-11-21-long-gaps-slides" />

## What the figures show

- **Bands**: `ctl` alone ÷ the joint solve by the gap before a later period, in both runs, with
  95% engagement intervals.
- **Systems**: median range error of `ctl` alone, the joint solve and k4 on later periods, in
  both runs.
- **Evidence**: for each engagement with a gap of at least 70 min (ownship holding course), the
  log evidence of the true gap history minus the declared one, against alone ÷ joint.

## Reproducing the figures

```
uv run python scripts/research/tl12_charts.py --out-dir site/static/img/2026-11-21-long-gaps-slides
```

The script reads only the committed records (results branches
`results/timelate-tl-q-dev-44691013700`, `results/timelate-tl-q-hold-dev-44741196091` and
`results/tl12ev-tl12ev-hold-44803371523`); each figure's `.json` sidecar names the inputs'
digests and the commit.
