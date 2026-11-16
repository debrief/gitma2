---
title: "Slides: the carried model end to end in the browser"
date: 2026-11-16T00:30
tags: [slides, spec-021]
---

import Slides from "@site/src/components/Slides";

The [viewer](/viewer) can now run Gate 2's carried model live, from bearings alone. The
classical segmenter C, E-s's evidence and E-w's estimate all run in the browser. On 30 check
scenarios every decision matches Python's. Spec: `specs/021-browser-segmenter/`. Record:
`experiments/20261116-port/`.

<!-- truncate -->

<Slides slug="2026-11-16-browser-segmenter-slides" />

## What was built

- A JavaScript port of C's host code from its frozen Python (`site/static/viewer-data/js/`):
  - the per-row least squares and the GLR statistic;
  - the ownship segmenter O and E-s's features;
  - the search, its Levenberg–Marquardt segment costs and the dynamic programme;
  - nominations, confirmation, intervals and the hand-over.
- The physics layer at confirmation's settings, exported as its own graph. Its three-runtime
  conformance passes, with cost agreeing to 7e-15 in the browser.
- A live mode on the page: a module worker runs the whole pipeline with progress and a cancel,
  draws the live trail beside the others, and compares it with Python.
- The checks:
  - a committed dump of every intermediate for 30 scenarios of used seed 319;
  - a Node comparison stage by stage (CI job `browser-port`);
  - live mode on every demo engagement in Chromium (`viewer_leg.mjs`).

## What the figures show

- **Agreement**: identical segmentations on 1,770 of 1,770 scored rows, for C and for E.
- **Margins**: the largest difference in a confirmation cost drop per scenario, against the
  smallest margin of any decision from its threshold.
  - The differences are 5.4e-9 or less, except one of 1.3e-4.
  - The margins are 0.152 or more.

  The gap explains the identity. It does not guarantee it: an engagement with a decision within
  1e-3 of its threshold could differ, and the check would say so.
- **Stages**: live mode takes 25 to 93 s an engagement on one WASM thread. Confirmation is most
  of it. The first row waits for confirmation: about 76 s on the busiest engagement, which misses
  the spec's one-minute target for the first row.

## What was not achieved

- Pasting a scenario of one's own (the spec's third story, P3) is not built.
- Some intermediates differ without changing a decision:
  - one row's least squares on ordinal 22 lands in another minimum;
  - search cost tables differ by up to 22% where fits hit their iteration cap.
  - the GLR statistic differs by up to 2.9. At one row (ordinal 1, row 256) it lies on the other
    side of the alarm threshold from Python's. No nomination changed there, but one could on
    another scenario, and the check would fail.

  These are recorded in the research notes, not hidden.

## What comes next

The owner's choice. The remaining options from spec 020's write-up are real data, several
periods of one target, and ownship advice.
