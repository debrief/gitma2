"""Export of L's evidence network to ONNX (spec 005 FR-045, research R8, task T035).

``python -m tma2.segment.evidence_export --out <dir> [--plan p --weights best.safetensors]``
writes ``model.onnx`` (double precision, a fixed 720-row window, dynamic batch),
``weights.safetensors``, ``architecture.json``, the golden batch (``in_features.bin``, torch
outputs ``out_evidence.bin``, onnxruntime outputs ``ort_evidence.bin``, ``manifest.json``),
``ops.txt`` and ``python_leg.json``, in the layout the browser and Java legs of
``conformance/onnx/`` read.

The graph is the network alone: the causal features (``evidence.scenario_features``: bearing,
ownship, O's online labels, least-squares innovations) are host code, as are the search,
confirmation and physics layer (R8). Without weights the network has seeded random weights, its
zero-initialised head perturbed, so the check exercises every layer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors.torch import load_file, save_file

from tma2.data.f32pack import iter_pack_raw
from tma2.references.classical import bearing_data_from_arrays

from . import default_parameters
from .evidence import CHANNELS, CausalConv, EvidenceNet, scenario_features

OPSET = 17
TOL = 1e-5
ROWS = 720
MAX_LOAD_S = 60.0
INPUTS = ("features",)
OUTPUTS = ("evidence",)


def golden_features(n: int = 4) -> np.ndarray:
    """[n, CHANNELS, ROWS] causal features of the first n scenarios of seed 316's MAN2 pack,
    zero-padded on the right (causal, so padding never reaches an earlier row)."""
    from tma2.export.onnx_export import man2_fixture

    p = default_parameters()
    with tempfile.TemporaryDirectory() as tmp:
        pack, rows = man2_fixture(Path(tmp))
        assert rows == ROWS
        out = np.zeros((n, CHANNELS, ROWS))
        for i, (_, meta, own, _tgt, obs) in enumerate(iter_pack_raw(pack)):
            if i >= n:
                break
            d = bearing_data_from_arrays(meta, own, obs)
            f = scenario_features(d, own, p)
            out[i, :, : f.shape[1]] = f
    return out


class MatMulNet(torch.nn.Module):
    """The evidence network with every convolution written as matrix products: onnxruntime's
    CPU provider has no double-precision ``Conv`` kernel. A causal convolution is a left pad,
    then one product per kernel tap of the weights with the input shifted by the tap's dilated
    offset; ``SiLU`` is ``x · sigmoid(x)``. Equal to ``EvidenceNet`` (checked at export)."""

    def __init__(self, net: EvidenceNet) -> None:
        super().__init__()
        self.net = net

    @staticmethod
    def _conv(m: CausalConv, x: torch.Tensor) -> torch.Tensor:
        w = m.conv.weight  # [cout, cin, K]
        assert m.conv.bias is not None
        d = int(m.conv.dilation[0])
        r = x.shape[2]
        xp = torch.nn.functional.pad(x, (m.pad, 0))
        out = m.conv.bias.reshape(1, -1, 1)
        for k in range(w.shape[2]):
            out = out + torch.matmul(w[:, :, k], xp[:, :, k * d : k * d + r])
        return out

    @staticmethod
    def _silu(x: torch.Tensor) -> torch.Tensor:
        return x * torch.sigmoid(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        n = self.net
        h = self._silu(self._conv(n.inp, x))
        for b in n.blocks:
            assert isinstance(b, CausalConv)
            h = h + self._silu(self._conv(b, h))
        assert n.head.bias is not None
        out = torch.matmul(n.head.weight[:, :, 0], h) + n.head.bias.reshape(1, -1, 1)
        return out[:, 0, :]


def seeded_net(cfg: dict[str, Any], seed: int) -> EvidenceNet:
    torch.manual_seed(seed)
    net = EvidenceNet(
        width=int(cfg["width"]), kernel=int(cfg["kernel"]), dilations=tuple(cfg["dilations"])
    ).double()
    g = torch.Generator().manual_seed(seed + 1)
    with torch.no_grad():
        assert net.head.bias is not None
        for prm in (net.head.weight, net.head.bias):
            prm.copy_(0.1 * torch.randn(tuple(prm.shape), generator=g, dtype=torch.float64))
    return net


def export(net: EvidenceNet, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    net = net.double().eval()
    batch = {"features": golden_features()}
    x = torch.from_numpy(batch["features"])
    graph_net = MatMulNet(net).eval()
    with torch.no_grad():
        ref = net(x).numpy()
        same = float(np.max(np.abs(graph_net(x).numpy() - ref)))
    if same > 1e-12:
        raise AssertionError(f"MatMulNet differs from EvidenceNet by {same}")
    onnx_path = out_dir / "model.onnx"
    with torch.no_grad():
        torch.onnx.export(
            graph_net,
            (x,),
            str(onnx_path),
            input_names=list(INPUTS),
            output_names=list(OUTPUTS),
            dynamic_axes={name: {0: "batch"} for name in (*INPUTS, *OUTPUTS)},
            opset_version=OPSET,
            dynamo=False,
        )
    save_file(
        {k: v.contiguous() for k, v in net.state_dict().items()}, out_dir / "weights.safetensors"
    )
    (out_dir / "in_features.bin").write_bytes(np.ascontiguousarray(batch["features"]).tobytes())
    (out_dir / "out_evidence.bin").write_bytes(np.ascontiguousarray(ref).tobytes())
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "model": "model.onnx",
                "inputs": {"features": {"shape": list(x.shape), "dtype": "float64"}},
                "outputs": {"evidence": {"shape": list(ref.shape), "dtype": "float64"}},
            },
            indent=2,
        )
    )
    import onnx
    import onnxruntime as ort  # type: ignore[import-untyped]

    graph = onnx.load(str(onnx_path)).graph
    ops = sorted({node.op_type for node in graph.node})
    (out_dir / "ops.txt").write_text("\n".join(ops) + "\n")
    t0 = time.perf_counter()
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    (got,) = sess.run(None, {"features": batch["features"]})
    run_s = time.perf_counter() - t0
    (out_dir / "ort_evidence.bin").write_bytes(np.ascontiguousarray(got).tobytes())
    diff = float(np.max(np.abs(got - ref) / np.maximum(np.abs(ref), 1.0)))
    record = {
        "max_rel_diff": {"evidence": diff},
        "tol": TOL,
        "dtype": "float64",
        "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "inputs_sha256": hashlib.sha256((out_dir / "in_features.bin").read_bytes()).hexdigest(),
        "runtime": f"onnxruntime {ort.__version__} (Python)",
        "nodes": len(graph.node),
        "ops": ops,
        "load_s": load_s,
        "run_s": run_s,
        "run_s_per_window": run_s / x.shape[0],
        "window_rows": ROWS,
    }
    (out_dir / "python_leg.json").write_text(json.dumps(record, indent=2))
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", default="configs/segment/gs-plan.json")
    ap.add_argument("--weights", help="best.safetensors of a trained L (default: seeded random)")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.plan).read_text())["evidence_network"]
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        net = seeded_net(cfg, a.seed)
        source = f"seeded random (seed {a.seed}, zero-initialised head perturbed)"
        if a.weights:
            net.load_state_dict(load_file(a.weights))
            source = (
                f"{a.weights} (sha256 {hashlib.sha256(Path(a.weights).read_bytes()).hexdigest()})"
            )
        out = Path(a.out)
        record = export(net, out)
        arch = {
            "config": cfg,
            "window_rows": ROWS,
            "inputs": {
                "features": f"[B, {CHANNELS}, {ROWS}] evidence.scenario_features, zero-padded"
            },
            "outputs": {
                "evidence": f"[B, {ROWS}] per-row log-likelihood ratio, steady vs transition"
            },
            "dtype": "float64",
            "opset": OPSET,
            "weights": source,
        }
        (out / "architecture.json").write_text(json.dumps(arch, indent=2))
    finally:
        torch.set_default_dtype(default)
    print(json.dumps(record))
    if record["max_rel_diff"]["evidence"] > TOL or record["load_s"] > MAX_LOAD_S:
        print("python leg fails", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
