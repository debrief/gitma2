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

- Segmentation: identical on 1,770 of 1,770 scored rows (30 scenarios, C and E). Nominations
  and every confirmation decision are identical.
- Near-threshold band (research R2): the largest cost-drop difference is 1.3e-4 (ordinal 8;
  every other scenario is within 5e-9), so the band is 1.3e-3. The smallest decision margin is
  0.154. Nothing fell inside the band.
- Intermediates that differ without changing a decision (research R3 and R4):
  - On ordinal 22, one row's least squares lands in another minimum. It differs by a relative
    75 there, which moves E-s's evidence by 0.50 at row 352 and the GLR statistic by 0.17.
  - Search cost-table entries differ by up to 3% (iteration-capped fits).
- O's codes: identical on every row of every scenario.
- Live mode in Chromium:
  - segmentation identical to Python's on 181 of 181 rows of the six demo engagements;
  - the estimate within 2.7e-6 of the shipped Gate 2 estimate on every row;
  - 24 to 95 s an engagement on one thread, against SC-003's 10 minutes.

  The busiest engagement took 95 s: about 5 s for least squares, 24 s for the search, 47 s for
  confirmation and 18 s for E-w's estimates.

To regenerate:

```
uv run tma2-viewer-dump --split <seed 319 dir>/test.f32pack --out experiments/20261116-port/dump
uv run python -m tma2.segment.evidence_export --out <es> --plan configs/gate2/g2-a.json --weights experiments/20261107-g2-val/models/es-s3/best.safetensors
uv run python -m tma2.viewer.layer_export --out <layer>
(cd conformance/onnx && node port_node.mjs --dump ../../experiments/20261116-port/dump --layer <layer>/model.onnx --es <es>/model.onnx --out <r.json>)
```

Not done: the pasted-scenario input (spec Story 3, P3).
