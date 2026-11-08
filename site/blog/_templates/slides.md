---
title: "Slides: <task name in one line>"
date: YYYY-MM-DD
tags: [slides, <spec-NNN or gate-X>]
---

import Slides from "@site/src/components/Slides";

<!-- Slides post (site/docs/process/reporting.md). Built before the PR is opened;
     /speckit-report-slides fills it. The deck is site/static/slides/<date-slug>/index.html,
     copied from static/slides/_template. Delete these comments. -->

Two or three sentences: what was built and what the deck shows. For a gate, link the critical
write-up; this post is its illustrated companion.

<!-- truncate -->

<Slides slug="<date-slug>" />

## What the figures show

One short paragraph per figure: the scenario, the times marked, what to look at. Track plots:
ownship blue, target red, estimator trails from the zig with 1-σ ellipses at the marks.

## Reproducing the figures

```bash
# data
uv run tma2-generate --seed <seed> --count <n> --out <dir> --ranges <f> --heldout-ranges <f> --format f32pack
# predictions
uv run tma2-solve --in <dir>/train.f32pack --out lsq.ndjson --per-timestep
# figure
uv run tma2-plot track --truth <dir>/train.f32pack --predictions lsq.ndjson ... --scenario <i> --at <t1>,<t2> --out site/static/img/<date-slug>/track-<i>.svg
```

Sidecars next to each SVG name the digests, the scenario, the command and the commit.

## Not achieved

- Plainly.

## Next

- The follow-on, with the recommended default where the SRD leaves it to the owner.
