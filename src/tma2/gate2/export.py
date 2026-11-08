"""Export of E-w to one ONNX graph (spec 007 T033; constitution VI).

``python -m tma2.gate2.export --out <dir> [--plan configs/gate2/g2-a.json --weights
best.safetensors]`` writes ``model.onnx`` (double precision, MAN2's 720-row window, dynamic batch,
the physics iterations as one ONNX ``Loop``, 12 knots), ``weights.safetensors``, the golden batch
(``in_*.bin``, torch outputs ``out_*.bin``, onnxruntime outputs ``ort_*.bin``, ``manifest.json``,
``shapes.json``), ``ops.txt`` and ``python_leg.json``, in the layout the browser and Java legs of
``conformance/onnx/`` read.

The graph is E-w's inference path on one scored row per window: its inputs are C's hand-over of
that prefix (bearings, ownship, knots, speed weights, the speed-continuity skip, masked
log-weights and the grid start, as ``gate2.inputs.prefix_inputs`` builds it) and C's code
channel; its outputs are the state at the row, its covariance and the two flags. C itself, and
E-s's evidence network (exported by ``segment.evidence_export`` with ``--plan
configs/gate2/g2-a.json``), are host code and a separate graph: E = E-s's evidence into C's
confirmation, then this graph on the resulting hand-over. The golden batch is C's own
segmentation of MAN2 fixture scenarios (seed 316), one G5 row each, alternating rows with an open
transition. Without weights E-w has seeded random weights in every layer, its zero-initialised
heads included, so the check exercises them.
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
from torch import Tensor, nn

from tma2.physics.layer import PhysicsInputs
from tma2.types.generated.tma import PhysicsModelConfig

from .model import EWeights

OPSET = 17
TOL = 1e-5
MAX_LOAD_S = 60.0
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
    "code",
)
OUTPUTS = ("state", "cov", "plausible", "cov_ok")


class EWExport(nn.Module):
    """C's hand-over of one prefix per window and C's code channel in; E-w's state at the row,
    its covariance and the plausible and cov_ok flags (0/1 doubles) out."""

    def __init__(self, model: EWeights) -> None:
        super().__init__()
        self.model = model

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
        code: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        x = PhysicsInputs(
            bearing=bearing,
            valid=valid,
            own=own,
            t=t,
            sigma=sigma,
            k=k,
            changepoint=changepoint,
            speed_weight=speed_weight,
            log_weight=log_weight,
            theta0=theta0,
            speed_skip=speed_skip,
        )
        o = self.model(x, code)
        dt = bearing.dtype
        return o.state, o.cov, o.plausible.to(dt), o.cov_ok.to(dt)


def model_config(plan: dict[str, Any], seed: int = 1) -> PhysicsModelConfig:
    return PhysicsModelConfig.model_validate({**plan["encoder"], "id": "ew-export", "seed": seed})


def seeded_model(cfg: PhysicsModelConfig, seed: int) -> EWeights:
    """E-w with seeded random weights everywhere, the zero-initialised heads' last layers too."""
    torch.manual_seed(seed)
    model = EWeights(cfg).double()
    g = torch.Generator().manual_seed(seed + 1)
    with torch.no_grad():
        for head in (model.weight_head, model.init_head):
            last = head[-1]
            assert isinstance(last, nn.Linear)
            last.weight.copy_(0.05 * torch.randn(last.weight.shape, generator=g))
            last.bias.copy_(0.02 * torch.randn(last.bias.shape, generator=g))
    return model


def golden_batch(n: int = 6) -> dict[str, np.ndarray]:
    """``n`` windows of the MAN2 fixture (seed 316), C's segmentation at one G5 row each: on even
    windows the first G5 row whose hand-over holds an open transition if there is one, else the
    last G5 row; on odd windows the last G5 row."""
    from tma2.cli.oracle import inputs_for
    from tma2.data.f32pack import iter_pack_raw
    from tma2.export.onnx_export import man2_fixture
    from tma2.physics.layer import PhysicsLayer
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment import TRANSITION
    from tma2.segment.score import g5_rows
    from tma2.segment.segmenter import segment
    from tma2.types.generated.tma import SegmentParameters

    from .inputs import code_channel, prefix_inputs

    root = Path(__file__).resolve().parents[3]
    gs = json.loads((root / "configs/segment/gs-plan.json").read_text())
    p = SegmentParameters.model_validate(gs["segmenter"]["parameters"])
    items: list[Any] = []
    codes: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as tmp:
        pack, rows = man2_fixture(Path(tmp))
        assert rows == ROWS
        for _, meta, own, _tgt, obs in iter_pack_raw(pack):
            d = bearing_data_from_arrays(meta, own, obs)
            ks = g5_rows(meta, d.n)
            if not ks or not meta.get("manoeuvres"):
                continue
            seg = segment(PhysicsLayer(), [d], [meta], [ks], p)[0]
            by_k = {s.k: s.intervals for s in seg}
            pick = ks[-1]
            if len(items) % 2 == 0:
                opened = [
                    k
                    for k in ks
                    if any(iv.kind == TRANSITION and iv.open for iv in by_k.get(k, []))
                ]
                pick = opened[0] if opened else pick
            ivs = by_k.get(pick)
            if ivs is None:
                continue
            inp = prefix_inputs(d, pick, ivs, str(p.mode), p.open_handover)
            if inp is None:
                continue
            items.append((d, pick, inp))
            codes.append(np.pad(code_channel(ivs, pick, d.n), (0, ROWS - d.n)))
            if len(items) == n:
                break
    if len(items) < n:
        raise ValueError(f"only {len(items)} fixture windows qualify")
    x = inputs_for(items, ROWS)
    out = {name: getattr(x, name).numpy() for name in INPUTS[:-1]}
    out["code"] = np.stack(codes).astype(np.float64)
    return out


def export(model: EWeights, out_dir: Path) -> dict[str, Any]:
    """Export ``model`` (double) and run the Python leg; returns the leg's record."""
    out_dir.mkdir(parents=True, exist_ok=True)
    model = model.double().eval()
    model.set_implicit(False)
    wrapper = EWExport(model).eval()
    batch = golden_batch()
    tensors = tuple(torch.from_numpy(batch[name]) for name in INPUTS)
    with torch.no_grad():
        ref = [o.numpy() for o in wrapper(*tensors)]
    onnx_path = out_dir / "model.onnx"
    with torch.no_grad():
        torch.onnx.export(
            wrapper,
            tensors,
            str(onnx_path),
            input_names=list(INPUTS),
            output_names=list(OUTPUTS),
            dynamic_axes={name: {0: "batch"} for name in (*INPUTS, *OUTPUTS)},
            opset_version=OPSET,
            dynamo=False,
        )
    save_file(
        {k: v.contiguous() for k, v in model.state_dict().items()}, out_dir / "weights.safetensors"
    )
    for name, arr in batch.items():
        (out_dir / f"in_{name}.bin").write_bytes(np.ascontiguousarray(arr).tobytes())
    for name, arr in zip(OUTPUTS, ref, strict=True):
        (out_dir / f"out_{name}.bin").write_bytes(np.ascontiguousarray(arr).tobytes())
    (out_dir / "shapes.json").write_text(json.dumps({n: list(a.shape) for n, a in batch.items()}))
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
    ops = sorted({node.op_type for node in graph.node})
    (out_dir / "ops.txt").write_text("\n".join(ops) + "\n")
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
        "max_rel_diff": diffs,
        "tol": TOL,
        "dtype": "float64",
        "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "inputs_sha256": hashlib.sha256(ins).hexdigest(),
        "runtime": f"onnxruntime {ort.__version__} (Python)",
        "nodes": len(graph.node),
        "loop_nodes": sum(node.op_type == "Loop" for node in graph.node),
        "ops": ops,
        "load_s": load_s,
        "run_s": run_s,
        "window_rows": ROWS,
        "iterations": model.cfg.iterations,
        "knots": model.physics.knots,
    }
    (out_dir / "python_leg.json").write_text(json.dumps(record, indent=2))
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", default="configs/gate2/g2-a.json")
    ap.add_argument("--weights", help="E-w's best.safetensors (default: seeded random)")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)  # the scripted loop's constants follow it
    try:
        cfg = model_config(plan, a.seed)
        model = seeded_model(cfg, a.seed)
        source = f"seeded random (seed {a.seed}, heads perturbed)"
        if a.weights:
            model.load_state_dict(load_file(a.weights))
            source = a.weights
        record = export(model, Path(a.out))
    finally:
        torch.set_default_dtype(default)
    record["weights"] = source
    (Path(a.out) / "python_leg.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    bad = {k: v for k, v in record["max_rel_diff"].items() if not v <= TOL}
    if bad:
        print(f"python leg exceeds {TOL}: {bad}", file=sys.stderr)
        return 1
    if record["load_s"] > MAX_LOAD_S:
        print(f"the graph took {record['load_s']:.0f} s to load", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
