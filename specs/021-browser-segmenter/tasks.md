# Tasks: the carried model end to end in the browser

- [x] T001 `viewer/layer_export.py`: `PhysicsLayer()` at confirmation's settings, with three
  legs (CI `onnx-conformance`).
- [x] T002 `viewer/dump.py`, `tma2-viewer-dump`: every intermediate of C and E on a scenario
  alone. The 30 check scenarios (six demos and the next 24 eligible) are committed in
  `experiments/20261116-port/dump/`.
- [x] T003 The port, ES modules in `site/static/viewer-data/js/`:
  - `lsq.js`, `glr.js`, `codes.js`, `ownship.js`, `features.js`, `search.js`;
  - `confirm.js`, `handover.js`, `pipeline.js`.
- [x] T004 `conformance/onnx/port_node.mjs` and `port_summary.py`: stage-by-stage comparison
  under Node (CI job `browser-port`).
- [x] T005 Live mode: a module worker, `Engine.live`, the page's live panel and trail, and the
  comparison with Python (`compareLive`).
- [x] T006 `viewer_leg.mjs --live all`: live mode on every demo engagement in Chromium (SC-001,
  SC-003).
- [x] T007 `--install`: scenario files and graphs into the viewer data, and manifest digests.
  Unit tests in `tests/unit/test_viewer_dump.py`.
- [ ] T008 Story 3, the pasted scenario (P3). Not done in this spec.
- [x] T009 Record, slides post, AGENTS.md, PR.
