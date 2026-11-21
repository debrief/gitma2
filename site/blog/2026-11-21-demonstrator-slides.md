---
title: "Slides: an interactive TMA demonstrator"
date: 2026-11-21T18:00
tags: [slides, spec-035]
---

import Slides from "@site/src/components/Slides";

The [demonstrator](/demo) is live on the site. Drag the blue ownship and the red target, add
turns, narrow the window, and the target's track is solved from bearings over that window.

- **Solvers:** JavaScript least squares, the physics layer in ONNX (one leg, or told the true
  manoeuvre times) and Gate 2's learned E.
- **Dashboard:** errors across the window beside the Cramér–Rao bound, observability, a
  model-mismatch flag, and bearing and residual charts.

Spec: `specs/035-interactive-demonstrator/`. Not a result: one noise draw at a time, in a toy
world.

<!-- truncate -->

<Slides slug="2026-11-21-demonstrator-slides" />

## What was built

- **The page:** `site/src/pages/demo.js`. It runs on plain ES modules in
  `site/static/demo-data/js/`, the same files the Node tests import. Solvers run in a module
  worker.
- **Types:** `DemoScenario`, `TmaProblem`, `TmaSolution` and `DemoSolverInfo` in LinkML (schema
  0.37.0). Imports are validated against the generated JSON Schema.
- **The ONNX graph:** `tl-layer.onnx` is `PhysicsLayer()` with a reported-row input and its
  parameters as outputs, so the page can draw the whole fitted track. onnxruntime agrees with
  torch within 1.7e-6, and the export reproduces byte for byte.
- **Checks:**
  - Golden least-squares vectors from Python's `solve_batch`. On 11 problems the page builds,
    the JavaScript port agrees within 1e-6 with the same iteration counts.
  - 14 Node tests.
  - A Chromium run of the built page (CI job `demo`).

## Demonstration (preset numbers, seed 1, σ 1°)

| Preset and solver | Range error |
| --- | --- |
| Good geometry, least squares | 0.22% RMS (0.039 NM, bound 0.068 NM); residuals 1.01 σ |
| Target turn, one leg | 80% RMS |
| Target turn, told the turn (oracle) | 1.1% |
| Target turn, one leg on the first target leg only | 1.8% |
| No zig, least squares | 57%, with residuals at 1.01 σ and the indicator red |

On the no-zig preset the bearings fit and the range does not.

Figures: `scripts/research/demo_charts.mjs`, sidecars beside each SVG.

## What was not achieved

- **E is slow.** About three minutes on a two-hour window, because C's confirmation runs on
  every nomination.
- **E is causal.** Its track is a series of real-time estimates, so it is not a like-for-like
  time-late fit.
- **The ONNX layer thins** a two-hour window to every second bearing, so with noise it differs
  from the JavaScript solve.
- **Not built:** Monte Carlo clouds, continuous recompute and the time-late `ctl` system.

## Next

These are the owner's choice:

- show a spread over several noise draws;
- run `ctl` in the browser (a JavaScript port of the search);
- show the joint solve across gaps.
