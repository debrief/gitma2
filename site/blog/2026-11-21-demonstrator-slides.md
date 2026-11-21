---
title: "Slides: an interactive TMA demonstrator"
date: 2026-11-21T18:00
tags: [slides, spec-035]
---

import Slides from "@site/src/components/Slides";

The [demonstrator](/demo) is live on the site. Drag the blue ownship and the red target, add
turns, narrow the window, and the target's track is solved from bearings over that window.

- **Solvers:** JavaScript least squares, the physics layer in ONNX (one leg, or told the true
  manoeuvre times) and spec 016's time-late whole-period learned model (three seeds).
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

Range error, RMS over the window:

| Preset | Least squares | Learned, whole period (seed 1) | Other |
| --- | --- | --- | --- |
| Good geometry | 0.30% (residuals 1.01 σ) | 9.9% | |
| Target turn | 33% (one leg) | 12% | told the turn 1.0%; one leg on the first target leg 1.8% |
| No zig | 130% (residuals 1.01 σ; indicator red) | 5.8% | |

Where the geometry is good, the fit wins. Where the bearings cannot fix range, the learned
model's prior wins.

Figures: `scripts/research/demo_charts.mjs`, sidecars beside each SVG.

## What was not achieved

- **The learned model is easily out of its training range** (initial range 2–20 km, 5-second
  bearings, at most two hours). It did not state the target-turn preset's turn. Study L stopped
  it against the classical control.
- **Size:** 26 MB per seed.
- **The ONNX layer thins** a two-hour window to every second bearing, so with noise it differs
  from the JavaScript solve.
- **Not built:** Monte Carlo clouds, continuous recompute and the time-late `ctl` system.

## Next

These are the owner's choice:

- show a spread over several noise draws;
- run `ctl` in the browser (a JavaScript port of the search);
- show the joint solve across gaps.
