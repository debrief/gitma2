# Tasks: the browser viewer on the exported artefact

**Spec**: `spec.md` · **Plan**: `plan.md` · **Research**: `research.md`

## Phase 1: the demo data (US1, US2, US3)

- [ ] T001 `src/tma2/viewer/choose.py`: the engagement rule (research R2) over seed 319's test
  split; returns ordinals with their class.
- [ ] T002 `src/tma2/viewer/build.py`: for each engagement and every 60 s from the zig, build:
  - E's segmentation and C's hand-over;
  - E-w's graph inputs;
  - Python onnxruntime outputs on the exported graph;
  - comparisons (one leg, IMM, C, C″) and the truth.

  It packs everything (R3) and writes `manifest.json` with digests, the command and the
  commit.
- [ ] T003 `src/tma2/cli/viewer_data.py` (`tma2-viewer-data`), pyproject script.
- [ ] T004 `tests/unit/test_viewer.py`: the rule on a small split; packing round trip; the
  manifest's digests match the files; the size limits (SC-003).
- [ ] T005 Run the builder; commit `site/static/viewer/` and record which arrays vary, the
  sizes and the time.

## Phase 2: the page (US1, US2, US4)

- [ ] T006 Prebuild copies the runtime (R4); add the site dependency and the gitignore entry.
- [ ] T007 `site/static/viewer/worker.js`: load the graph, run one row, post outputs.
- [ ] T008 `site/src/pages/viewer.js` and its components:
  - engagement picker;
  - SVG track plot (ownship blue, target red, trails from the zig);
  - time slider;
  - table of range, bearing, course and speed with errors;
  - ellipse toggle with the Gate 3 warning;
  - digest panel and check;
  - about text (FR-012, FR-013);
  - error states (edge cases).
- [ ] T009 Link the page from the navbar and the welcome page.

## Phase 3: conformance (US3)

- [ ] T010 `conformance/onnx/viewer_python.py`: fresh onnxruntime on the shipped inputs
  equals the shipped outputs (FR-015).
- [ ] T011 `conformance/onnx/viewer_leg.mjs`: Playwright on the built site. It checks:
  - every row's browser output against Python to 1e-5;
  - time to the first estimate and per engagement;
  - the ellipse warning;
  - the digest check.
- [ ] T012 `ci.yml`: run both in `onnx-conformance`, and make the `changes` filter send viewer
  files there.

## Phase 4: reporting and close

- [ ] T013 Slides post and deck:
  - track plots of two engagements from the shipped data;
  - the conformance chart;
  - the timings;
  - a screenshot of the page as a figure.
- [ ] T014 AGENTS.md (spec 020, gotchas); kickoff updates; PR; review agent; merge once CI is
  green.
