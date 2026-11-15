"""The physics layer at C's confirmation settings, exported for the browser (spec 021 FR-002).

    uv run python -m tma2.viewer.layer_export --out <dir> [--split <seed 319 test.f32pack>]

C's confirmation scores candidate segmentations by ``PhysicsLayer()``'s cost (default iterations
and knots; ``segment.confirm.confirm`` → ``detect.confirm.layer_costs``). This writes that layer,
unchanged, as one ONNX graph (double, 720 rows, dynamic batch, the iterations as one ``Loop``)
with outputs ``state``, ``cov``, ``cost`` and ``plausible``. It also writes a golden batch in the
layout ``conformance/onnx``'s browser and Java legs read. The golden batch is the first eight
layer requests of C's confirmation on a fixture scenario (seed 316's MAN2 fixture, as the other
720-row exports), or on the first engagement of ``--split`` if given.
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
from torch import Tensor, nn

from tma2.physics.layer import PhysicsInputs, PhysicsLayer

OPSET = 17
TOL = 1e-5
ROWS = 720
INPUTS = (
    "bearing",
    "valid",
    "own",
    "t",
    "sigma",
    "k",
    "theta0",
    "changepoint",
    "speed_weight",
    "log_weight",
    "speed_skip",
)
OUTPUTS = ("state", "cov", "cost", "plausible")


class ConfirmLayer(nn.Module):
    """``PhysicsLayer()`` with its inputs as tensors and its flags as doubles."""

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
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        out = self.physics(
            PhysicsInputs(
                bearing, valid, own, t, sigma, k, changepoint, speed_weight, log_weight, theta0,
                speed_skip=speed_skip,
            )
        )  # fmt: skip
        return out.state, out.cov, out.cost, out.plausible.to(bearing.dtype)


def capture_requests(split: Path | None, n: int = 8) -> dict[str, np.ndarray]:
    """The first ``n`` layer requests of C's confirmation on one scenario, as padded inputs."""
    from tma2.cli.oracle import inputs_for
    from tma2.data.f32pack import iter_pack_raw
    from tma2.detect import confirm as dconf
    from tma2.export.onnx_export import man2_fixture
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment.score import g5_rows
    from tma2.segment.segmenter import segment
    from tma2.types.generated.tma import SegmentParameters

    root = Path(__file__).resolve().parents[3]
    gs = json.loads((root / "configs/segment/gs-plan.json").read_text())
    p = SegmentParameters.model_validate(gs["segmenter"]["parameters"])
    got: list[Any] = []
    orig = dconf.layer_costs

    def spy(layer: PhysicsLayer, items: list[Any], r_max: int) -> list[float]:
        got.extend(items)
        return orig(layer, items, r_max)

    with tempfile.TemporaryDirectory() as tmp:
        pack = split if split is not None else man2_fixture(Path(tmp))[0]
        for _, meta, own, _tgt, obs in iter_pack_raw(pack):
            d = bearing_data_from_arrays(meta, own, obs)
            ks = g5_rows(meta, d.n)
            if not ks or not meta.get("manoeuvres"):
                continue
            import tma2.segment.confirm as sconf

            setattr(sconf, "layer_costs", spy)  # noqa: B010
            try:
                segment(PhysicsLayer(), [d], [meta], [ks], p)
            finally:
                setattr(sconf, "layer_costs", orig)  # noqa: B010
            if len(got) >= n:
                break
    if len(got) < n:
        raise ValueError(f"only {len(got)} confirmation requests captured")
    x = inputs_for(got[:n], ROWS)
    return {name: getattr(x, name).numpy() for name in INPUTS}


def export(out_dir: Path, split: Path | None = None) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    model = ConfirmLayer().double().eval()
    batch = capture_requests(split)
    tensors = tuple(torch.from_numpy(batch[name]) for name in INPUTS)
    with torch.no_grad():
        ref = [o.numpy() for o in model(*tensors)]
    onnx_path = out_dir / "model.onnx"
    with torch.no_grad():
        torch.onnx.export(
            model,
            tensors,
            str(onnx_path),
            input_names=list(INPUTS),
            output_names=list(OUTPUTS),
            dynamic_axes={name: {0: "batch"} for name in (*INPUTS, *OUTPUTS)},
            opset_version=OPSET,
            dynamo=False,
        )
    for name, arr in batch.items():
        (out_dir / f"in_{name}.bin").write_bytes(np.ascontiguousarray(arr).tobytes())
    for name, arr in zip(OUTPUTS, ref, strict=True):
        (out_dir / f"out_{name}.bin").write_bytes(np.ascontiguousarray(arr).tobytes())
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "model": "model.onnx",
                "inputs": {
                    n: {"shape": list(a.shape), "dtype": str(a.dtype)} for n, a in batch.items()
                },
                "outputs": {
                    n: {"shape": list(a.shape), "dtype": str(a.dtype)}
                    for n, a in zip(OUTPUTS, ref, strict=True)
                },
            },
            indent=2,
        )
    )
    import onnx
    import onnxruntime as ort  # type: ignore[import-untyped]

    graph = onnx.load(str(onnx_path)).graph
    t0 = time.perf_counter()
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    got = sess.run(None, {name: batch[name] for name in INPUTS})
    run_s = time.perf_counter() - t0
    for name, a in zip(OUTPUTS, got, strict=True):
        (out_dir / f"ort_{name}.bin").write_bytes(np.ascontiguousarray(a).tobytes())
    diffs = {
        name: float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1.0)))
        for name, a, b in zip(OUTPUTS, got, ref, strict=True)
    }
    ins = b"".join((out_dir / f"in_{n}.bin").read_bytes() for n in sorted(batch))
    record = {
        "what": "PhysicsLayer() at C's confirmation settings (spec 021)",
        "max_rel_diff": diffs,
        "tol": TOL,
        "dtype": "float64",
        "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "inputs_sha256": hashlib.sha256(ins).hexdigest(),
        "runtime": f"onnxruntime {ort.__version__} (Python)",
        "nodes": len(graph.node),
        "loop_nodes": sum(node.op_type == "Loop" for node in graph.node),
        "load_s": load_s,
        "run_s": run_s,
        "window_rows": ROWS,
        "iterations": model.physics.iterations,
        "knots": model.physics.knots,
    }
    (out_dir / "python_leg.json").write_text(json.dumps(record, indent=2))
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", help="take the golden batch from this pack's first engagement")
    a = ap.parse_args(argv)
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)  # the scripted loop's constants follow it
    try:
        record = export(Path(a.out), Path(a.split) if a.split else None)
    finally:
        torch.set_default_dtype(default)
    print(json.dumps(record, indent=2))
    bad = {k: v for k, v in record["max_rel_diff"].items() if not v <= TOL}
    if bad:
        print(f"python leg exceeds {TOL}: {bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
