---
title: "Slides: how progress is now reported, shown on a demo split"
date: 2026-11-08
tags: [slides, process]
---

import Slides from "@site/src/components/Slides";

The [kickoff](/blog/2026/11/08/reporting-kickoff) promised a reporting practice and a plotting
tool. Both exist. The deck below is the first slides post, made with the templates and the tool it
describes, on a seeded demo split with the three estimators every result must carry.

<!-- truncate -->

<Slides slug="2026-11-08-reporting" />

## What the figures show

**Scenario 8**, a 7.7 km engagement, 56 minutes, σ = 1°. The ownship (blue) runs a long leg, zigs
at 2,140 s, and turns back. The target (red) turns once, early. Batch least squares (green) and the
IMM (orange) both place the target 2 to 3 km north of where it is at 5 and 10 minutes after the
zig, because the single-leg model has no way to know the target turned. The oracle (purple), which
is given the manoeuvre times, sits on the track. That is the gap the segmenters and E are meant
to close.

**Scenario 0**, a 28 km engagement, 112 minutes. The IMM's relative range error grows from 10%
to 30% over the hour after the zig while batch least squares settles near 1%. On long, quiet
legs the IMM's manoeuvre model is a cost, not a help.

**Errors against time** for scenario 8: log-scaled relative range, course and speed error on
each estimator's plausible rows from the zig onward. Range error for the two single-model
estimators sits near 30% throughout; the oracle's falls below 1% by the fourth G5 point.

Pre-zig rows are hidden: the physics layer returns finite states there whose range sd is far
larger than the range, and plotting them misleads.

## Reproducing the figures

Data: generator 0.6.0 (MAN2), seed 316, 12 scenarios, `configs/man2-ranges.json` and
`configs/man2-heldout.json`; the train split has 9. Estimators: batch least squares per timestep,
the frozen MAN2 IMM, the oracle.

```bash
uv run tma2-generate --seed 316 --count 12 --out demo --ranges configs/man2-ranges.json --heldout-ranges configs/man2-heldout.json --format f32pack
uv run tma2-solve --in demo/train.f32pack --out demo/lsq.ndjson --per-timestep
uv run tma2-track --in demo/train.f32pack --out demo/imm.ndjson --filter imm --sigma-cv 0.03 --sigma-ct 1 --sigma-omega 0.01 --switch 0.0003 --p0-scale 4 --r-scale 2
uv run tma2-oracle --truth demo/train.f32pack --out demo/oracle.ndjson
P="--predictions demo/lsq.ndjson demo/imm.ndjson demo/oracle.ndjson --labels batch LS,IMM,oracle"
uv run tma2-plot track  --truth demo/train.f32pack $P --scenario 8 --at 2440,2740 --title "Scenario 8: a 7.7 km engagement" --out site/static/img/2026-11-08-reporting/track-8.svg
uv run tma2-plot errors --truth demo/train.f32pack $P --scenario 8 --out site/static/img/2026-11-08-reporting/errors-8.svg
uv run tma2-plot track  --truth demo/train.f32pack $P --scenario 0 --at 3540,5340 --title "Scenario 0: a 28 km engagement, where the IMM drifts" --out site/static/img/2026-11-08-reporting/track-0.svg
```

Each SVG has a `.json` sidecar next to it with the truth and prediction digests, the scenario,
the command line and the code commit (fe0f089, clean tree; the demo directory is written as `demo`).

## Not achieved

- The deck is a static page: the figures do not animate the estimate through time. A per-timestep
  animation is a natural next step for `tma2-plot` and would show convergence better than two
  marks.
- No metric chart from a committed scoring run yet; the first gate slides post (Gate 3) will need
  a small script over its `errors.npz`.
- Figures are 70 to 85 KB each as SVG text; a long deck will want them optimised.

## Next

- The constitution amendment is owner-merged; until then the practice is adopted on the agent
  side as the documents state.
- Spec 008 continues; its kickoff post is written when its spec is next touched, and Gate 3's
  slides post will be the first for a gate.
