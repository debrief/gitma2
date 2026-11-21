# Plan: spec 035, interactive TMA demonstrator

**Constitution check**:
- Types once in LinkML: `DemoScenario`, `TmaProblem`, `TmaSolution` and `DemoSolverInfo`, schema 0.37.0.
- Seeded randomness only: the page's noise is seeded, and the seed is in the scenario and the URL.
- Mock data only: the presets are generic.
- No result is claimed: the page is a demonstrator, so the rules on references, efficiency and
  three seeds do not apply.

## Architecture

```
site/src/pages/demo.js            React page (BrowserOnly): editor, plot, sliders, dashboard
site/src/pages/demo.module.css
site/static/demo-data/
  js/track.js                      legs → waypoints, arcs, state at t; edits (FR-001..006)
  js/scenario.js                   seeded bearings, window rows, TmaProblem (FR-010, 011, 021)
  js/solvers.js, solver-info.js    plug-ins (FR-024, 025): ls-js, layer-cv, layer-oracle, e-gate2
  js/metrics.js, linalg.js         errors over the window, the bound, observability (FR-030..036)
  js/presets.js, codec.js          presets, URL fragment, JSON Schema validation (FR-040..043)
  worker.js                        module worker; ONNX Runtime Web loaded on first ONNX solve
  tl-layer.onnx, tl-layer.json     PhysicsLayer() with k_state and theta/knots outputs
  demo-scenario.schema.json        DemoScenario's JSON Schema, from the generated schema
src/tma2/viewer/demo_layer_export.py   exports tl-layer.onnx and checks onnxruntime against torch
scripts/site/demo_schema.py            extracts the schema (--check in a unit test and CI)
conformance/onnx/demo_*                golden vectors, Node tests, Chromium checks (CI job `demo`)
```

Reused from spec 021: `viewer-data/js/lsq.js` (least squares), `handover.js` (layer inputs),
`pipeline.js` (E end to end), and `es.onnx`, `layer.onnx` and `model.onnx`.

## Steps

1. Schema types; regenerate; the site schema extractor.
2. Track kinematics, bearings, solvers and metrics in plain ES modules, tested in Node.
3. The time-late layer export, and the ONNX solvers through the worker.
4. The page and its interactions; screenshots to the owner during layout.
5. Golden vectors from Python, Node tests, the Chromium check and the CI job.
6. Kickoff and slides posts; AGENTS.md; the PR.
