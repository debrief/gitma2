---
title: "Slides: the carried model, running in a browser"
date: 2026-11-15T21:30
tags: [slides, spec-020]
---

import Slides from "@site/src/components/Slides";

The last item of the SRD's default plan: a [viewer page](/viewer) that runs Gate 2's carried
model's exported graph in your browser on six simulated engagements, beside the classical
systems. CI checks it row by row against Python. A demonstration, not a result. The figures
of record stay in [Gate 2's write-up](/blog/2026/11/08/gate-2).

<!-- truncate -->

<Slides slug="2026-11-15-browser-viewer-slides" />

## What was built

- `tma2-viewer-data` picks six engagements of Gate 2's used test seed 319 by a fixed rule
  (`tma2.viewer.choose`):
  - quiet, one manoeuvre, busy;
  - the first where E's median range error over the G5 rows is worse than C″'s;
  - then one more "one manoeuvre" and one more "busy".

  For each engagement, every 60 s from zig + 5 min, it builds:
  - C's segmentation with E-s's evidence, and C's hand-over;
  - from those, the twelve inputs of E-w's exported graph;
  - Python's onnxruntime outputs on them;
  - the truth, and the estimates of one leg, the frozen IMM, C and C″.

  A manifest binds the result by SHA-256. The data are 0.16 MB gzipped, beside a 1.06 MB
  graph.
- The page (`site/src/pages/viewer.js`) runs the graph in ONNX Runtime Web 1.31.1 (WASM, one
  thread, in a worker). It computes the current time first, then fills in the trail. It
  checks every file's digest before showing an estimate. The ellipse is off by default and
  never shown without the Gate 3 warning.
- CI (`onnx-conformance`) runs three checks:
  - the page's graph is byte-identical to a fresh export of the carried weights;
  - a fresh Python run reproduces the shipped outputs;
  - the built page in Chromium matches Python on every row (`conformance/onnx/viewer_leg.mjs`).

## What the figures show

- **Tracks**: the busy engagement (ordinal 3) and the one where E loses to C″ (ordinal 6),
  at the last scored time. The trails are each system's estimate at each scored time, from
  zig + 5 min.
- **Range error**: every system on every engagement. E is close to C and C″ throughout, and
  is neither best nor worst everywhere. On engagement 5 the one-leg fit is better late on.
  Six engagements say nothing about which system is better: Gate 2's 4,983 do.
- **Conformance**: 181 rows. The browser's state is within 2.7e-6 of Python's, and the
  covariance on its own scale within 3.2e-6. The flags are identical. Element-wise, one
  off-diagonal covariance element of one row (engagement 4, row 432, inside an open
  transition) differs by 3.2e-5, above the constitution's 1e-5. Torch and Python's
  onnxruntime agree on that row to 7e-8, so the difference is the browser runtime's. Why is
  not established. The check now gates the covariance relative to its own scale, and reports
  the element-wise figure on every run (`specs/020-browser-viewer/research.md` R6).
- **Timing**: about 0.27 s a row on one thread. The graph loads in 1 s, the first estimate
  appears 1.7 s after the page opens, and a whole engagement takes 5 to 15 s. These were
  measured headless on this project's container; CI's figures go in its step summary.

## What was not achieved

- C and its confirmation still run in Python. A live viewer would need them ported by hand
  from the algorithm note.
- The page shows E's raw covariance, which is overconfident: no calibration was carried
  (Gates 3 and 4 stopped).
- The relaxed covariance measure is a change made after the first result. It is stated as
  such, not hidden.

## What comes next

The SRD's default plan (§7) is complete with this step. What follows is the owner's choice.
The records point to:
- real data;
- several periods of one target;
- ownship advice;
- a port of C for a live viewer.
