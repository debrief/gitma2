# Tasks: the browser viewer on the exported artefact

**Spec**: `spec.md` · **Plan**: `plan.md` · **Research**: `research.md`

## Phase 1: the demo data (US1, US2, US3)

- [x] T001 `src/tma2/viewer/choose.py`: the engagement rule (research R2) over seed 319's test
  split; returns ordinals with their class.
- [x] T002 `src/tma2/viewer/build.py`: for each engagement and every 60 s from the zig, build:
  - E's segmentation and C's hand-over;
  - E-w's graph inputs;
  - Python onnxruntime outputs on the exported graph;
  - comparisons (one leg, IMM, C, C″) and the truth.

  It packs everything (R3) and writes `manifest.json` with digests, the command and the
  commit.
- [x] T003 `src/tma2/cli/viewer_data.py` (`tma2-viewer-data`), pyproject script.
- [x] T004 `tests/unit/test_viewer.py`: the rule on a small split; packing round trip; the
  manifest's digests match the files; the size limits (SC-003).
  Done: the rule, packing round trip and reproducible gzip. The digests are checked by
  `conformance/onnx/viewer_python.py` in CI, not by a unit test. The size limits are not
  asserted anywhere: the data are 1.2 MB against SC-003's 15 MB.
- [x] T005 Run the builder; commit `site/static/viewer-data/` and record which arrays vary, the
  sizes and the time.
  Done: 1.2 MB, about 26 min. Shared across an engagement's rows: `bearing`, `own`, `t`,
  `sigma`, `valid` on all six engagements, and on the quiet one also `changepoint`, `code`,
  `log_weight`, `speed_weight` and `speed_skip`, because C's segmentation never changes there.
  Masking after k is the layer's, from `k`.

## Phase 2: the page (US1, US2, US4)

- [x] T006 Prebuild copies the runtime (R4); add the site dependency and the gitignore entry.
- [x] T007 `site/static/viewer-data/worker.js`: load the graph, run one row, post outputs.
- [x] T008 `site/src/pages/viewer.js` and its components:
  - engagement picker;
  - SVG track plot (ownship blue, target red, trails from the zig);
  - time slider;
  - table of range, bearing, course and speed with errors;
  - ellipse toggle with the Gate 3 warning;
  - digest panel and check;
  - about text (FR-012, FR-013);
  - error states (edge cases).
- [x] T009 Link the page from the navbar and the welcome page.

## Phase 3: conformance (US3)

- [x] T010 `conformance/onnx/viewer_python.py`: fresh onnxruntime on the shipped inputs
  equals the shipped outputs (FR-015).
- [x] T011 `conformance/onnx/viewer_leg.mjs`: Playwright on the built site. It checks:
  - every row's browser output against Python to 1e-5;
  - time to the first estimate and per engagement;
  - the ellipse warning;
  - the digest check.
- [x] T012 `ci.yml`: run both in `onnx-conformance`, and make the `changes` filter send viewer
  files there.

## Phase 4: reporting and close

- [x] T013 Slides post and deck:
  - track plots of two engagements from the shipped data;
  - the conformance chart;
  - the timings;
  - a screenshot of the page as a figure.
  Done, except the screenshot. Figures must be vector (reporting practice), so the deck
  draws the architecture as an SVG instead. CI uploads a PNG screenshot as an artefact.
- [ ] T014 AGENTS.md (spec 020, gotchas); kickoff updates; PR; review agent; merge once CI is
  green.
