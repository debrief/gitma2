---
title: "Slides: carrying state across gaps, against joining through them"
date: 2026-11-19
tags: [slides, spec-027]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the spec 027 write-up](/blog/2026/11/19/carry-across-gaps): the
registered comparison, how often the carry changes anything, and where.

<!-- truncate -->

<Slides slug="2026-11-19-carry-across-gaps-slides" />

## What the figures show

- **Verdict**: carry ÷ joint and alone ÷ carry in range on every split, periods after an
  engagement's first, with 95% engagement intervals.
- **Ties**: the share of later periods where the carry is within 1% of `ctl` alone, better or
  worse.
- **Kinds**: alone ÷ carry for periods with and without an ownship turn of their own.

## Reproducing the figures

```
uv run python scripts/research/tl9_charts.py --record experiments/20261119-tl9 --out-dir site/static/img/2026-11-19-carry-across-gaps-slides
```

The script reads only the committed record (results branch
`results/timelate-tl-m-test-44440932257`, seed 361); each figure's `.json` sidecar names the
inputs' digests and the commit.
