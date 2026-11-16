# Implementation Plan: the carried model end to end in the browser

**Spec**: `specs/021-browser-segmenter/spec.md` · **Date**: 2026-11-15 · CPU only; nothing
trained; no fresh seed (seed 319, used).

## Summary

A JavaScript port of everything in E's pipeline that is not already an exported graph:
- the per-row batch least squares;
- the ownship segmenter O;
- E-s's features;
- the GLR statistic;
- the search (Levenberg–Marquardt segment costs and the dynamic programme);
- C's confirmation, interval logic and hand-over;
- E-w's prefix inputs and code channel.

Three graphs run in ONNX Runtime Web:
- E-s's evidence network, with the carried weights;
- the physics layer at confirmation's settings (`PhysicsLayer()`: default iterations, 8 knots),
  with cost and flags outputs;
- spec 020's E-w graph.

The port is plain ES modules under `site/static/viewer-data/js/`. They run in the page's worker
and also under Node for the unit-level comparisons, which is faster than a browser for
development. A Python dump (`tma2-viewer-dump`) writes every intermediate of C's and E's run on
a scenario alone, padded to the graphs' 720 rows. Two comparison jobs read it:
- `conformance/onnx/port_node.mjs`: pure-JS stages under Node;
- `viewer_leg.mjs`: the whole pipeline in Chromium.

## Technical context

- C's Python (the reference, frozen at code `4d2c084f…`), and the files to port:

  | Path | Lines | Contents |
  | --- | --- | --- |
  | `references/classical.py` | 186 | per-timestep batch least squares |
  | `references/lsq.py` | 226 | the same |
  | `detect/controls.py` | about 120 used | `ls_states`, `glr_stat` |
  | `segment/ownship.py` | 186 | O |
  | `segment/evidence.py` | about 60 used | features, innovations |
  | `segment/search.py` | 296 | numba LM segment costs, the DP |
  | `segment/confirm.py` | about 250 | confirmation |
  | `segment/segmenter.py` | about 120 | nominations, `intervals_at` |
  | `segment/__init__.py` | 121 | codes and intervals |
  | `segment/inputs.py` | 84 | hand-over |
  | `physics/segmentation.py` | 143 | `LayerInputs` |
  | `gate2/inputs.py` | 49 | prefix inputs, code channel |

- Cost, measured on seed 319 ordinal 3 (703 rows, busy): C's confirmation makes 63 layer calls
  over 582 rows, 55 s in Python on one thread. The GLR statistic and the search cost seconds once
  numba is warm. In the browser the layer is about 0.25 s a row, so about 2.5 minutes for C,
  and the same again for E's segmentation (confirmation with evidence). The viewer needs E's
  segmentation only. C's own is computed for the check, not for the page.
- Padding: the reference is Python with `r_max = 720`, the graphs' window, so the two sides pad
  identically. Gate 2's chunked segmentation is compared and reported, not gated.
- Near-threshold band: from the first comparison, ten times the largest browser–Python
  difference in a confirmation cost drop. It is recorded in `research.md` before the band is
  used to excuse anything.

## Constitution check

- I: no record types change; the dump is a development artefact (JSON).
- II: seed 319 is used, the check scenarios are chosen by a rule, and runs are deterministic.
- III: the estimate is still E-w's physics-layer solve. Confirmation's costs come from the same
  layer, exported.
- IV: disagreements are reported with their margins, the shipped mode stays the default, and the
  page says which mode drew what.
- V: none. VI: three new graph checks: the layer graph gets three-runtime conformance, and E-s's
  graph already has it.
- Mock data only; nothing above OFFICIAL; no money.

## Structure

```
src/tma2/viewer/layer_export.py     PhysicsLayer() at confirmation's settings → ONNX, golden batch
src/tma2/viewer/dump.py             every intermediate of C and E on one scenario (r_max 720)
src/tma2/cli/viewer_dump.py         tma2-viewer-dump
site/static/viewer-data/js/         lsq.js, glr.js, ownship.js, features.js, search.js, confirm.js,
                                    intervals.js, handover.js, pipeline.js (ES modules)
site/static/viewer-data/ (graphs)   layer.onnx, es.onnx (+ manifest entries)
site/static/viewer-data/worker.js   gains a "live" message: the pipeline over a scenario
site/src/pages/viewer.js            live mode, progress, comparison with the shipped hand-over
conformance/onnx/port_node.mjs      Node: pure-JS stages against the dump
conformance/onnx/viewer_leg.mjs     gains the live comparison
tests/unit/test_viewer_dump.py
.github/workflows/ci.yml            layer export legs; port_node; live leg
```

## Steps

1. Layer export (`layer_export.py`) with its three legs. Check that its costs equal
   `PhysicsLayer()`'s on confirmation requests from the dump.
2. The dump: C and E on the six demo engagements and 24 more, chosen by rule:
   the next 24 eligible σ = 1° ordinals of seed 319 after the demos', in order.
3. Port the stages in pipeline order, checking each against the dump under Node before the next:
   LS states, GLR, O, features, search, nominations, confirmation (with the layer graph in
   onnxruntime-web under Node), intervals, hand-over, code channel.
4. Live mode in the worker and the page. The live leg in Chromium.
5. CI wiring, record, slides, AGENTS.md, PR.
