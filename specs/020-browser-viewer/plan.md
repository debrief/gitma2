# Implementation Plan: the browser viewer on the exported artefact

**Spec**: `specs/020-browser-viewer/spec.md` · **Date**: 2026-11-15 · CPU only; nothing
trained; no fresh seed (Gate 2's used test seed 319).

## Summary

1. A Python command, `tma2-viewer-data`, builds the demo data. It takes six engagements of seed
   319's test split, chosen by a fixed rule. For each, every 60 s from the zig, it builds E's
   segmentation (C's confirmation with E-s's evidence) and C's hand-over, and from them E-w's
   graph inputs. It runs Python's onnxruntime on them for the reference outputs. It adds the
   truth and the comparison estimates: one leg (plain batch least squares on the zig leg),
   the frozen IMM, C and C″. All of this goes to `site/static/viewer-data/` with a manifest of
   digests. The graph itself is `gate2.export`'s output with the carried weights.
2. A site page, `site/src/pages/viewer.js`, is a React page under Docusaurus. It loads
   onnxruntime-web 1.31.1, which the site's prebuild copies from `node_modules`, so the page
   needs no CDN. The page runs the graph on the shipped inputs, one row at a time in a Web
   Worker, current time first. It draws the track plot in SVG with a time slider, the
   comparison trails, a numeric table and the ellipse toggle with its warning. It shows the
   manifest's digests and checks them.
3. A conformance script, `conformance/onnx/viewer_leg.mjs`, runs Playwright against the built
   page. It runs every demo row through the page's own worker code and compares the outputs
   with the shipped Python outputs (tolerance 1e-5). It also checks the ellipse warning. A
   Python check re-runs onnxruntime on the shipped inputs (FR-015). Both run in `ci.yml`'s
   `onnx-conformance` job, which runs whenever the viewer's files or the exports change.
4. Slides post and deck with track plots from the shipped data (`tma2-plot`) and the
   conformance chart.

## Technical context

- Python 3.12 (data builder), JavaScript (React page in Docusaurus 3, a classic Web Worker;
  no new framework). onnxruntime-web 1.31.1, as `conformance/onnx` pins.
- Measured on this session's container, before writing the plan: E-w's export with the
  carried weights is 1.06 MB, 3,008 nodes and one Loop. It loads in Python in 0.4 s. Six
  windows run in 0.84 s in Python and 1.83 s in Chromium's WASM, single-threaded, so about
  0.3 s a row. The browser output differs from torch by at most 6.3e-7 (state) and 6.2e-7
  (cov).
- An engagement window is 40 to 120 min. From the zig, every 60 s, that is at most about 100
  rows, or about 30 s a whole engagement on one thread. That is within SC-002's 60 s, so a
  worker and current-time-first are enough, with no batching tricks.
- Data size: a row's graph inputs are 12 arrays of 720 doubles (own is 720 × 2), about 75 KB.
  At 100 rows × 6 engagements that is 45 MB raw, which would exceed SC-003's 15 MB. So
  arrays that are the same for every row of an engagement (`bearing`, `own`, `t`, `sigma`,
  and `valid` before masking) are stored once. Per row only the arrays that differ are stored
  (`k`, `theta0`, `changepoint`, `speed_weight`, `log_weight`, `speed_skip`, `code`, and
  `valid`/`bearing` when the hand-over masks them). Everything is gzipped and decoded with the
  browser's built-in `DecompressionStream`. The builder checks the total, and research R3
  records which arrays turn out to vary.

## Constitution check

- I (types once): the demo data are a site asset, not a record type. The manifest is plain
  JSON described in `data-model.md`. No schema change. If the plan finds a need to store E's
  rows as records, it uses the existing prediction row type.
- II (determinism): seed 319 is used, not fresh; the ordinals are chosen by a rule in code.
  Regenerating at the same commit reproduces the digests (SC-004). Gzip carries no timestamp
  (`mtime=0`).
- III (physics layer): the estimate shown is E-w's physics-layer solve, exported.
- IV (honest measurement): the page says it is a demonstration, not a result, and links Gate
  2's write-up. The ellipse carries the Gate 3 warning. Every system shows its own "no answer"
  rows. One engagement is chosen where E loses to C″.
- V (gates): none. No criterion changes.
- VI (portable artefact): the page runs the exported graph in ONNX Runtime Web (WASM),
  WebGPU not used. CI checks the page's outputs against Python to 1e-5.
- Mock data only; nothing above OFFICIAL; no money. The site is this repository's own, so
  this is not publishing outside it.

## Structure

```
src/tma2/viewer/__init__.py
src/tma2/viewer/choose.py      the rule that picks the six engagements
src/tma2/viewer/build.py       inputs, Python outputs, comparisons, manifest
src/tma2/cli/viewer_data.py    tma2-viewer-data (pyproject script)
tests/unit/test_viewer.py      rule, packing round trip, digests reproduce, sizes
site/src/pages/viewer.js       the page
site/src/components/viewer/    plot, table, digest panel
site/static/viewer-data/            manifest.json, model.onnx, engagement-<i>.json.gz, rows-<i>.bin.gz
site/static/viewer-data/worker.js   loads ort, runs rows (shared with the conformance leg)
site/scripts/prebuild.mjs      also copies ort.wasm.min.js and its wasm into build-time static
conformance/onnx/viewer_leg.mjs   Playwright against the built page
conformance/onnx/viewer_python.py fresh onnxruntime on the shipped inputs (FR-015)
.github/workflows/ci.yml       onnx-conformance: build the site, run both checks
site/blog/2026-11-1x-browser-viewer-slides.md; deck; figures
```

## Steps

1. Research (R1 to R5 in `research.md`), then the builder and its tests. Run it locally. Six
   engagements at about 100 rows each need C and E-s on one scenario at a time, which is
   seconds per engagement. If it takes over about 10 minutes, it runs on CI instead.
2. The page and its worker. Check locally with `npm run build && npm run serve` and Playwright
   screenshots.
3. The conformance leg and the CI wiring; push and watch CI.
4. Slides post, AGENTS.md, tasks ticked, PR, and the code-review agent. No panel, since this
   is not a gate. The agent may merge once CI is green and review approves: the PR touches no
   owner-only item.
