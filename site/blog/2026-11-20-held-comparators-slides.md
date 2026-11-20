---
title: "Slides: the carried prior against longer windows"
date: 2026-11-20T12:30
tags: [slides, spec-031]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to [the write-up](/blog/2026/11/20/held-comparators).
On turn-free 1-hour windows, a joint solve over the hour and the hour before it beats 1-hour
`ctl-prior`: **0.774 [0.632, 0.954]**. The 2-hour systems also beat it. The registered rule reads
"ctl-prior worse" three times. Spec: `specs/031-held-comparators/`.

<!-- truncate -->

<Slides slug="2026-11-20-held-comparators-slides" />

## What was built

- **The `jointheld` part of `tma2-long`:** `ctl` on each turn-free window's union with its
  predecessor.
- **The scorer:** `src/tma2/long/study30.py`, run by `tma2-long study30`.
- **CI:** `long.yml` passes a tag and the window settings through.
- **Configs:** `configs/long/cmp-{val,test}.json` and run files `configs/long/runs/cmp-*.json`.
- **Scripts:** `scripts/research/cmp_{digests,supplement,charts}.py`.
- **Records:**
  - tuning: `experiments/20261119-cmp-tuning/`;
  - decision: `20261120-cmp-decision/`;
  - validation: `20261120-cmp-val/`;
  - test: `20261120-cmp/`, with `review.md` and `supplement.json`.

## What was not achieved

- **Untested:** legs longer than the 2-hour window, which is the owner's blind case at the
  standing configuration.
- **Not measured separately:** each system's own cost, and the 2-hour hand-overs' guard rate and
  coverage.
- **Not decided:** whether 2-hour `ctl-prior` beats 2-hour `ctl`. Here it is supplement only.

## What comes next (the owner's choice)

- **Recommended:** close the long-engagement track with a synthesis.
- **Alternatives:**
  - legs longer than the window;
  - reopen with new information.

Figures: `scripts/research/cmp_charts.py`, with a sidecar beside each SVG.
