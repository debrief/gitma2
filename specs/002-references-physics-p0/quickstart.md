# Quickstart: References, Physics Layer and Gate P0

## 1. References reproduce gitma

```bash
uv run pytest tests/conformance/test_references.py -q -rA
```

Expected: classical (per-timestep), EKF and IMM rows equal gitma's prediction fixtures on the
seed-777 test and validation splits under the one-ulp rule; residual counts printed.

## 2. Physics layer equals least squares; oracle inputs work

```bash
uv run pytest tests/unit/test_physics_layer.py -q -rA
```

Expected: trivial-input state equals the ported solver to float32 on fixture rows where gitma
converged; NumPy reference agrees to 1e-6; gradient checks pass; masking exact.

## 3. Evaluation equals gitma's, plus efficiency

```bash
uv run tma2-eval --truth tests/fixtures/gitma/phase4-seed777/test.f32pack \
  --predictions tests/fixtures/gitma/phase4-seed777/predictions/test-lsq.ndjson \
  --crb /tmp/crb.ndjson --points 300,600 --out /tmp/eval-lsq
```

Expected: `metrics.csv` with gitma's columns plus efficiency; least squares' settled-row speed
efficiency at σ = 1° between 0.8 and 1.3.

## 4. Export and runtimes

```bash
uv run python -m tma2.export.onnx_export --out /tmp/toy && (cd conformance/onnx && npm ci && npm test)
```

Expected: Python and WASM outputs agree with torch to 1e-5; Java leg runs or prints its deferral.

## 5. Gate P0

```bash
uv run tma2-generate --seed 301 --count 100000 --out data/p0 \
  --ranges tests/fixtures/gitma/phase4-seed777/ranges.json \
  --heldout-ranges tests/fixtures/gitma/phase4-seed777/heldout-ranges.json --format f32pack
uv run tma2-p0 --experiment experiments/$(date +%Y%m%d)-p0 --oracle-data data/p0
```

Expected: every check `pass`, the oracle ratios inside the research note's intervals, exit 0;
then the panel review is run and `decided_by` set.
