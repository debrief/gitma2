# Spec 021: the carried model end to end in the browser, checked

This is not a gate and not a result. It records how the JavaScript port of C's host code was
checked against Python. Nothing is trained and no fresh seed is used: the scenarios come from
used seed 319.

## What was compared

- `dump/`: `tma2-viewer-dump` on 30 check scenarios. These are the six demo engagements and the
  next 24 eligible σ = 1° ordinals of seed 319's test split. Each scenario runs alone, padded to
  720 rows. The dump holds every intermediate of C and E: LS states, GLR statistic, O's codes,
  features, E-s's evidence, search cost tables and transitions, nominations, every confirmation
  decision, and the intervals at every scored row.
- `node-per-scenario.json`, `node-summary.json`: `conformance/onnx/port_node.mjs` under Node
  (onnxruntime-web 1.31.1, WASM), then `port_summary.py`. CI runs the same in job
  `browser-port`.
- `browser-live.json`: `viewer_leg.mjs --live all` in headless Chromium 153 in this project's
  container, 2026-11-16. The built page runs live mode on each demo engagement.

## Readings

Corrected after review (spec 021 review). An earlier draft overstated how far the differences
lay from thresholds and understated the cost-table differences.

- **Decisions.** Segmentation is identical on 1,770 of 1,770 scored rows (30 scenarios, C and
  E). Nominations, search transitions and every confirmation decision are identical.
- **Confirmation.** Cost drops agree to 5.4e-9, except one of 1.3e-4 on ordinal 8. The smallest
  decision margin is 0.152 (ordinal 31, E). Nothing fell inside the band of 1.3e-3.
- **GLR statistic.** It differs by up to 2.93 in absolute value (ordinal 1). At one row, ordinal
  1's row 256, the two values lie either side of the alarm threshold: 2.98 in the browser, 5.91
  in Python. Nominations stayed identical only because that row falls between retests. A
  scenario where such a crossing falls on a nomination would fail the check (research R3).
- **Least squares and evidence.** On ordinal 22 one row's least squares lands in another minimum
  (relative 75), which moves E-s's evidence by 0.50 at row 352. The least-squares comparison is
  vacuous on ordinals 8 and 16 (no usable row).
- **Search cost tables.** Entries differ by up to 22% (ordinal 30), and by 19% on ordinal 20,
  from iteration-capped fits. The transitions are identical.
- **O.** Its codes are identical on every row of every scenario.
- **Not compared directly.** The hand-over arrays are checked only through what they produce
  (confirmation costs, E-w's estimates), and `pipeline.js` only in the six-engagement browser
  leg.
- **Live mode in Chromium** (`browser-live.json`): segmentation identical to Python's on 181 of
  181 rows of the six demo engagements, and every decision identical. The live estimate is within
  3.2e-6 of the shipped Gate 2 estimate on every row (state, and covariance on its own scale).
  Each engagement takes 25 to 93 s on one thread, against SC-003's 10 minutes. The first scored
  row appears only after confirmation: about 76 s on the busiest engagement (20 to 76 s across the six), which misses
  SC-003's one-minute target for the first row (spec amended to say so).

To regenerate:

```
uv run tma2-viewer-dump --split <seed 319 dir>/test.f32pack --out experiments/20261116-port/dump
uv run python -m tma2.segment.evidence_export --out <es> --plan configs/gate2/g2-a.json --weights experiments/20261107-g2-val/models/es-s3/best.safetensors
uv run python -m tma2.viewer.layer_export --out <layer>
(cd conformance/onnx && node port_node.mjs --dump ../../experiments/20261116-port/dump --layer <layer>/model.onnx --es <es>/model.onnx --out <r.json>)
```

Not done: the pasted-scenario input (spec Story 3, P3).
