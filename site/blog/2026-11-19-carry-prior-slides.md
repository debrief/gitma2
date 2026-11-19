---
title: "Slides: the previous window as a prior"
date: 2026-11-19T12:30
tags: [slides, spec-027]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to
[the write-up](/blog/2026/11/19/carry-prior). The registered rule's output is **not shown, at
this size**, with no harm. Beside the rule, carrying the previous window's state as a prior
gives a small average shift: about 10% in geometric mean and 3% in the median window. Spec:
`specs/027-carry-prior/`.

<!-- truncate -->

<Slides slug="2026-11-19-carry-prior-slides" />

## What was built

- **`src/tma2/long/carried.py`**: the carried prior.
  - The fit and evidence carry it as a Gaussian term. With no prior they equal the originals,
    which a unit test checks.
  - The hand-over excludes the next window's bearings.
  - It also holds the widening and the χ²(4) guard.
- **`src/tma2/long/carry2.py`**: `ctl-prior` beside `ctl` and `ctl-carry` in one job. A test
  checks that `ctl` and `ctl-carry` equal spec 026's.
- **`src/tma2/long/study27.py`**: the scorer. CLI: `tma2-long carry2`, `study27` and
  `jointpair`.
- **CI:** `long.yml` now ignores pushes to main and pushes its results to an orphan branch.
- **Records:**
  - tuning `experiments/20261118-cp-tuning/`;
  - decision `20261119-cp-decision/`;
  - validation `20261119-cp-val/`;
  - test `20261119-cp/`, with `review.md`, `supplement.json` and `ties.json`.

## What was not achieved

- **The owner's case:** a window without useful ownship geometry does not occur in this
  simulator.
- **Gain on the registered split:** not shown.
- **Whether the prior narrows the set of histories:** not tested.
- **The hand-over defect:** the refit's start is recorded, not repaired.

## What comes next (the owner's choice)

- **Recommended:** adopt `ctl-prior` with its guard for tended contacts up to 12 hours, then
  close the track.
- **Alternatives:**
  - an ownship that holds course for one to two hours, which answers the owner's question
    directly;
  - a registered joint solve over consecutive windows.

Figures: `scripts/research/cp_charts.py`, with a sidecar beside each SVG.
