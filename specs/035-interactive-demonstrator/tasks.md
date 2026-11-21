# Tasks: spec 035

- [x] T001 LinkML types `DemoLeg`, `DemoTrack`, `DemoWindow`, `DemoScenario`, `DemoSpan`, `TmaProblem`, `TmaSolution`, `DemoSolverInfo`, `DemoSolveStatus`; schema 0.37.0; regenerate
- [x] T002 `scripts/site/demo_schema.py` and `tests/unit/test_demo_schema.py`
- [x] T003 `track.js`: waypoints, arcs with clamping, `stateAt`, edits (FR-001..006)
- [x] T004 `scenario.js`: seeded bearings, window, problem (FR-010, 011, 021)
- [x] T005 `solvers.js`: `ls-js`, `layer-cv`, `layer-oracle`, `e-gate2` (FR-024, 025)
- [x] T006 `metrics.js`: errors over the window, the bound, observability, mismatch (FR-031..036)
- [x] T007 `codec.js`: URL fragment, JSON Schema validator (FR-042, 043); `presets.js` (FR-041)
- [x] T008 `demo_layer_export.py` → `tl-layer.onnx` (Python check of onnxruntime against torch)
- [x] T009 `worker.js` with stale-result discard (FR-023)
- [x] T010 `demo.js` page: editor, plot, sliders, dashboard, undo/redo, import/export (FR-007, 020, 022, 030..036)
- [x] T011 Owner feedback: time down the left in the lower charts; a toggle to hide each one
- [x] T012 Golden vectors (`demo_problems.mjs`, `demo_golden.py`, `demo/golden-ls.json`, `tests/unit/test_demo_golden.py`)
- [x] T013 `demo_node.mjs` (acceptance 1–5, FR-002..005, 011, 043, ONNX); `DEMO_E=1` for E
- [x] T014 `demo_page.mjs` in Chromium; CI job `demo`
- [x] T015 Kickoff and slides posts; AGENTS.md entry; PR
- [x] T016 Owner feedback on the PR: progress bar and cancel; leg speed labels; NM grid; arcs drawn finely; click-to-split hint
- [x] T017 Owner: drop real-time E; spec 016's whole-period model, three seeds (`demo_tlm_export.py`, `tlm.js`, `golden-tlm.json`, CI re-export); presets inside its training range
- [x] T018 Owner: one-screen full-width layout; hidden charts widen only
