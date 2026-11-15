---
title: "Slides: the time-late track as a whole"
date: 2026-11-15T20:30
tags: [slides, spec-019]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to
[the account of the time-late track](/blog/2026/11/15/time-late-synthesis): the standing
system, what it gained over the old one, what remains, the attempts to beat it, the last
diagnostic, and three periods as tracks, good and bad.

<!-- truncate -->

<Slides slug="2026-11-15-time-late-synthesis-slides" />

## What the figures show

- **Gains**: the old system (C″ read as a track) ÷ the standing control, by kind of target
  and bearing error, on the test seeds of specs 017 and 018.
- **Remaining**: the standing control ÷ a fit told the true manoeuvre history, on three
  test seeds. A reference, not a bound.
- **Challengers**: the standing control ÷ each attempt to beat it, on Annex B and busier
  targets: the learned model's read-out and its own track (spec 016), the search told the
  true statistics (017, 018), the prior adapted to the period, declared and hedged (018).
- **Ladder**: development work on 130 used periods: the standing control ÷ the search
  under the broadened prior taking on the true statistics a part at a time, and each part
  alone; orange ticks are the same ratio without its ten best periods.
- **Three periods as tracks**, chosen by a rule in the script: of the 20 stored shifted
  periods of spec 017's test, those where the standing control is best, median and worst
  against the old system.

## Reproducing the figures

```
uv run python scripts/research/tl_synthesis.py --out experiments/20261115-tl-synthesis/tables.md --fig-dir site/static/img/2026-11-15-time-late-synthesis-slides
```

The script reads only committed records (`experiments/20261114-tl4/`, `20261114-tl5/`,
`20261115-tl6/`, `20261115-tl7-dev/`); each figure's `.json` sidecar names the inputs' digests and the commit.
The data are test seeds 341, 344 and 347, 5-second bearings, generated in their CI runs.
