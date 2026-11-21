"""The physics layer as a time-late solver for the demonstrator (spec 035 FR-025).

    uv run python -m tma2.viewer.demo_layer_export --out site/static/demo-data

Spec 021's ``layer.onnx`` reports the state at the last row it fits. The demonstrator fits a
whole window and draws the track at every bearing, so this graph is the same ``PhysicsLayer()``
(default iterations and knots, double, 720 rows, dynamic batch) with one more input, ``k_state``
(the row whose state and covariance are reported, spec 003's time-late variant), and the
solution's parameters as outputs: ``theta`` (p0, u0 and one velocity increment per knot),
``knots`` (rows, as doubles) and ``knot_weights``. The page rebuilds the track from them:
p(t) = p0 + u0 t + sum_j c_j relu(t - t_knot_j) d_j. It writes ``tl-layer.onnx`` and
``tl-layer.json`` (digests, the Python check of onnxruntime against torch on spec 021's golden
batch of C's confirmation requests, with ``k_state`` at the middle row).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
from torch import Tensor, nn

from tma2.physics.layer import PhysicsInputs, PhysicsLayer
from tma2.viewer.layer_export import INPUTS as BASE_INPUTS
from tma2.viewer.layer_export import OPSET, TOL, capture_requests

INPUTS = (*BASE_INPUTS, "k_state")
OUTPUTS = ("state", "cov", "cost", "plausible", "theta", "knots", "knot_weights", "cov_ok")


class TimeLateLayer(nn.Module):
    """``PhysicsLayer()`` with ``k_state`` and its parameters as outputs (flags as doubles)."""

    def __init__(self) -> None:
        super().__init__()
        self.physics = PhysicsLayer()

    def forward(
        self,
        bearing: Tensor,
        valid: Tensor,
        own: Tensor,
        t: Tensor,
        sigma: Tensor,
        k: Tensor,
        theta0: Tensor,
        changepoint: Tensor,
        speed_weight: Tensor,
        log_weight: Tensor,
        speed_skip: Tensor,
        k_state: Tensor,
    ) -> tuple[Tensor, ...]:
        out = self.physics(
            PhysicsInputs(
                bearing, valid, own, t, sigma, k, changepoint, speed_weight, log_weight, theta0,
                speed_skip=speed_skip, k_state=k_state,
            )
        )  # fmt: skip
        dt = bearing.dtype
        return (
            out.state,
            out.cov,
            out.cost,
            out.plausible.to(dt),
            out.theta,
            out.knots.to(dt),
            out.knot_weights,
            out.cov_ok.to(dt),
        )


def export(out_dir: Path) -> dict[str, object]:
    import onnx
    import onnxruntime as ort  # type: ignore[import-untyped]

    out_dir.mkdir(parents=True, exist_ok=True)
    model = TimeLateLayer().double().eval()
    batch = capture_requests(None)
    batch["k_state"] = (batch["k"] // 2).astype(np.int64)
    tensors = tuple(torch.from_numpy(batch[name]) for name in INPUTS)
    with torch.no_grad():
        ref = [o.numpy() for o in model(*tensors)]
    onnx_path = out_dir / "tl-layer.onnx"
    with tempfile.TemporaryDirectory() as tmp, torch.no_grad():
        tmp_path = Path(tmp) / "m.onnx"
        torch.onnx.export(
            model,
            tensors,
            str(tmp_path),
            input_names=list(INPUTS),
            output_names=list(OUTPUTS),
            dynamic_axes={name: {0: "batch"} for name in (*INPUTS, *OUTPUTS)},
            opset_version=OPSET,
            dynamo=False,
        )
        onnx_path.write_bytes(tmp_path.read_bytes())
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    got = sess.run(None, {name: batch[name] for name in INPUTS})

    def rel(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1.0)))

    o, r = dict(zip(OUTPUTS, got, strict=True)), dict(zip(OUTPUTS, ref, strict=True))
    # Inert knots (weight 0) tie in top-k and the runtimes break ties differently, so theta and
    # knots are compared through what they mean: p0, u0 and the active knots' rows and
    # increments, sorted by row.
    diffs = {n: rel(o[n], r[n]) for n in OUTPUTS if n not in ("theta", "knots")}
    diffs["theta_p0u0"] = rel(o["theta"][:, :4], r["theta"][:, :4])

    def active(x: dict[str, np.ndarray], b: int) -> np.ndarray:
        m = x["knot_weights"].shape[1]
        d = x["theta"][b, 4:].reshape(m, 2)
        rows = [(x["knots"][b, j], *d[j]) for j in range(m) if x["knot_weights"][b, j] > 0]
        return np.array(sorted(rows), dtype=np.float64).reshape(-1, 3)

    diffs["active_knots"] = max(
        (rel(active(o, b), active(r, b)) if active(r, b).size else 0.0)
        for b in range(o["theta"].shape[0])
    )
    record: dict[str, object] = {
        "what": "PhysicsLayer() as a time-late solver with k_state and its parameters (spec 035)",
        "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "max_rel_diff": diffs,
        "tol": TOL,
        "runtime": f"onnxruntime {ort.__version__} (Python)",
        "nodes": len(onnx.load(str(onnx_path)).graph.node),
        "window_rows": int(batch["bearing"].shape[1]),
        "iterations": model.physics.iterations,
        "knots": model.physics.knots,
        "inputs": list(INPUTS),
        "outputs": list(OUTPUTS),
    }
    (out_dir / "tl-layer.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)  # the scripted loop's constants follow it
    try:
        record = export(Path(a.out))
    finally:
        torch.set_default_dtype(default)
    print(json.dumps(record, indent=2))
    diffs = record["max_rel_diff"]
    assert isinstance(diffs, dict)
    bad = {k: v for k, v in diffs.items() if not v <= TOL}
    if bad:
        print(f"python check exceeds {TOL}: {bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
