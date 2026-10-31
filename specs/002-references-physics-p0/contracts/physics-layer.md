# Contract: the physics layer

```python
from tma2.physics.layer import PhysicsLayer, PhysicsInputs, PhysicsOutputs

layer = PhysicsLayer(iterations=30, ridge_tau_mps=3.0, speed_tau_mps=1.0,
                     lambda0=1e-3, lambda_min=1e-12, lambda_max=1e12)
out: PhysicsOutputs = layer(inputs)   # all tensors float64 on CPU; float32 allowed for export tests
```

## Inputs (batch B, rows R)

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `bearing` | [B, R] | observed bearings (rad), 0 where invalid |
| `valid` | [B, R] | 1 where a bearing exists and the row is ≤ k, else 0 |
| `own` | [B, R, 2] | ownship x, y (m) |
| `t` | [B, R] | seconds since window start |
| `sigma` | [B] | bearing noise σ (rad), floored at 1e-4 |
| `k` | [B] | current row (int); rows after k are masked out |
| `changepoint` | [B, R] | c_j ∈ [0, 1]: how free velocity row j is to differ from row j − 1 (0 everywhere = one segment) |
| `speed_weight` | [B, R] | s_j ∈ [0, 1]: strength of the speed-continuity prior across knot j |
| `log_weight` | [B, R] | per-bearing log-weight added to the residual weighting (0 = uniform) |
| `theta0` | [B, 4] | initial (x0, y0, vx, vy) at t = 0, e.g. the classical grid start |

## Outputs

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `state` | [B, 4] | (x, y, vx, vy) at t_k |
| `cov` | [B, 4, 4] | σ²-scaled covariance of `state` |
| `range`, `course`, `speed` | [B] | derived, with gitma's conventions (course in [0, 2π)) |
| `cost` | [B] | final weighted cost |
| `plausible` | [B] bool | speed ≤ 25 m/s and range ≤ 100 km and finite |
| `theta0_out` | [B, 4] | state at t = 0 of the first segment (for warm starts) |

## Guarantees

- No data-dependent control flow: the graph is identical for every input (fixed K, `where`).
- Differentiable in `changepoint`, `speed_weight`, `log_weight`, `theta0`.
- Masking exact: rows > k and invalid rows contribute nothing; batch results equal single runs.
- Trivial inputs (`changepoint = 0`, `speed_weight = 0`, `log_weight = 0`, `theta0` = grid
  start) reproduce gitma's batch least squares (spec FR-007) within one float32 ulp on rows where
  gitma converged and was plausible.
- Truth segmentation (`tma2.physics.segmentation.oracle_inputs(spans, k, speed_prior)`) gives
  the oracle ceiling (spec FR-008).
- A NumPy mirror `tma2.physics.reference.solve(...)` implements the same equations in the same
  order; `layer` and `reference` agree to 1e-6 relative on the golden batch.
- Exported to ONNX (opset 17, standard ops only); `tma2.export.onnx_export.export_toy(...)`.
