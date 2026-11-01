"""Export of a Gate 1 model to one ONNX graph (spec 003 FR-020; research R2; constitution VI).

``python -m tma2.models.export --out <dir> [--plan p --model id --checkpoint c]`` writes
``model.onnx`` (double precision, fixed window of ``rows_for(ranges)`` rows, dynamic batch, the
physics iterations as one ONNX ``Loop``), ``weights.safetensors``, ``architecture.json``, the
golden batch (``in_*.bin``, torch outputs ``out_*.bin``, onnxruntime outputs ``ort_*.bin``,
``manifest.json``), ``ops.txt`` and ``python_leg.json``. The browser and Java legs
(``conformance/onnx/``) read the same files; ``manifest.json`` names the model file.

Without a checkpoint the model is the plan's architecture with seeded random weights in every
layer, the zero-initialised head outputs included, so the conformance check exercises the heads
(an untrained model would be batch least squares with dead heads).

The exported graph is the instantaneous model's inference path: one scored row per window
(row ``k``), the classical grid start computed in the graph (:func:`grid_start_tensor`), the
heads and the physics solve without the training-time Newton step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors.torch import save_file
from torch import Tensor, nn

from tma2.data.f32pack import iter_pack_raw
from tma2.physics.segmentation import grid_start_tensor
from tma2.references.classical import bearing_data_from_arrays
from tma2.sim.ranges import rows_for
from tma2.types.generated.tma import PhysicsHead, PhysicsModelConfig

from .gate1 import Gate1Model

OPSET = 17
TOL = 1e-5
MAX_LOAD_S = 60.0  # spec 003: the graph must load in under a minute
INPUTS = ("bearing", "valid", "ox", "oy", "t", "sigma", "k")
OUTPUTS = ("state", "cov", "cov_ok", "plausible")
FIXTURE = Path("tests/fixtures/gitma/iter4-seed777")


class Gate1Export(nn.Module):
    """One row per window: inputs [B, R] (bearing, valid 0/1, ownship x and y, time), σ [B] and
    the row k [B]; outputs the state (x, y, vx, vy) at k, its calibrated covariance, and cov_ok
    and plausible as 0/1 doubles."""

    def __init__(self, model: Gate1Model) -> None:
        super().__init__()
        if model.cfg.head != PhysicsHead.physics or not model.cfg.causal:
            raise ValueError("only the causal physics model is exported (controls are not carried)")
        self.model = model

    def forward(
        self,
        bearing: Tensor,
        valid: Tensor,
        ox: Tensor,
        oy: Tensor,
        t: Tensor,
        sigma: Tensor,
        k: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        b, r = bearing.shape
        source = torch.arange(b, device=bearing.device)
        n_rows = torch.full_like(k, r)  # unused by the causal encoder
        theta_grid = grid_start_tensor(t, ox, oy, bearing, valid, k)
        out = self.model(bearing, valid, ox, oy, t, sigma, n_rows, source, k, theta_grid)
        dt = bearing.dtype
        return out.state, out.cov, out.cov_ok.to(dt), out.plausible.to(dt)


def seeded_model(cfg: PhysicsModelConfig, seed: int) -> Gate1Model:
    """The architecture with seeded random weights everywhere, heads' last layers included."""
    torch.manual_seed(seed)
    model = Gate1Model(cfg)
    g = torch.Generator().manual_seed(seed + 1)
    with torch.no_grad():
        for head in (model.weight_head, model.init_head, model.scale_head):
            last = head[-1]
            assert isinstance(last, nn.Linear)
            last.weight.copy_(0.05 * torch.randn(last.weight.shape, generator=g))
            last.bias.copy_(0.02 * torch.randn(last.bias.shape, generator=g))
    return model


def golden_batch(fixture: Path, r_max: int, n: int = 8) -> dict[str, np.ndarray]:
    """``n`` windows of the CV fixture, one row each: zig + 30 rows (or the last row) on even
    windows, the last row on odd ones, so both young and full windows are checked."""
    cols: dict[str, list[Any]] = {name: [] for name in INPUTS}
    for i, (_, meta, own, _tgt, obs) in enumerate(iter_pack_raw(fixture / "test.f32pack")):
        d = bearing_data_from_arrays(meta, own, obs)
        k = min(d.zig_index + 30, d.n - 1) if i % 2 == 0 else d.n - 1

        def pad(a: np.ndarray) -> np.ndarray:
            out = np.zeros(r_max)
            out[: a.shape[0]] = a
            return out

        cols["bearing"].append(pad(d.z))
        cols["valid"].append(pad(d.valid.astype(np.float64)))
        cols["ox"].append(pad(d.ox))
        cols["oy"].append(pad(d.oy))
        cols["t"].append(pad(d.t))
        cols["sigma"].append(float(d.sigma))
        cols["k"].append(k)
        if len(cols["k"]) == n:
            break
    out = {name: np.asarray(v, dtype=np.float64) for name, v in cols.items() if name != "k"}
    out["k"] = np.asarray(cols["k"], dtype=np.int64)
    return out


def export(model: Gate1Model, out_dir: Path, r_max: int, fixture: Path = FIXTURE) -> dict[str, Any]:
    """Export ``model`` (double) and run the Python leg; returns the leg's record."""
    out_dir.mkdir(parents=True, exist_ok=True)
    model = model.double().eval()
    model.set_implicit(False)
    wrapper = Gate1Export(model).eval()
    batch = golden_batch(fixture, r_max)
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

    graph = onnx.load(str(onnx_path)).graph
    ops = sorted({node.op_type for node in graph.node})
    loops = [node for node in graph.node if node.op_type == "Loop"]
    (out_dir / "ops.txt").write_text("\n".join(ops) + "\n")
    import onnxruntime as ort  # type: ignore[import-untyped]

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
    record = {
        "max_rel_diff": diffs,
        "tol": TOL,
        "dtype": "float64",
        "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "runtime": f"onnxruntime {ort.__version__} (Python)",
        "nodes": len(graph.node),
        "loop_nodes": len(loops),
        "ops": ops,
        "load_s": load_s,
        "run_s": run_s,
        "window_rows": r_max,
        "iterations": model.cfg.iterations,
    }
    (out_dir / "python_leg.json").write_text(json.dumps(record, indent=2))
    return record


def architecture(cfg: PhysicsModelConfig, r_max: int, source: str) -> dict[str, Any]:
    return {
        "config": json.loads(cfg.model_dump_json(exclude_none=True)),
        "window_rows": r_max,
        "inputs": {
            "bearing": "[B, R] true bearing, rad, clockwise from north",
            "valid": "[B, R] 1 where the bearing is present",
            "ox": "[B, R] ownship x (east), m",
            "oy": "[B, R] ownship y (north), m",
            "t": "[B, R] time, s",
            "sigma": "[B] bearing noise sd, rad",
            "k": "[B] int64 row whose state is estimated (samples after k are ignored)",
        },
        "outputs": {
            "state": "[B, 4] (x, y, vx, vy) at row k, m and m/s",
            "cov": "[B, 4, 4] calibrated covariance of the state",
            "cov_ok": "[B] 1 where the covariance is valid",
            "plausible": "[B] 1 where the solution is plausible",
        },
        "dtype": "float64",
        "opset": OPSET,
        "weights": source,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", help="training plan naming the model (default: the R3 defaults)")
    ap.add_argument("--model", default="g1-conformance")
    ap.add_argument("--checkpoint", help="trained weights; seeded random weights if omitted")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--iterations", type=int, help="override the plan's K (conformance only)")
    a = ap.parse_args(argv)
    from .config import model_config
    from .train import load_plan, model_from_plan

    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        if a.plan:
            plan, _ = load_plan(a.plan)
            cfg = model_from_plan(plan, a.model)
        else:
            if a.checkpoint:
                ap.error("--checkpoint needs --plan")
            cfg = model_config(a.model)
        if a.iterations is not None:
            cfg = cfg.model_copy(update={"iterations": a.iterations})
        ranges = json.loads((FIXTURE / "ranges.json").read_text())
        r_max = rows_for(ranges)
        if a.checkpoint:
            from .predict import load_model

            model = load_model(a.plan, a.model, a.checkpoint)
            source = str(a.checkpoint)
        else:
            model = seeded_model(cfg, a.seed)
            source = f"seeded random (seed {a.seed}, heads perturbed)"
        out = Path(a.out)
        record = export(model, out, r_max)
        (out / "architecture.json").write_text(
            json.dumps(architecture(model.cfg, r_max, source), indent=2)
        )
    finally:
        torch.set_default_dtype(default)
    print(json.dumps(record))
    bad = {k: v for k, v in record["max_rel_diff"].items() if v > TOL}
    if bad or record["loop_nodes"] != 1 or record["load_s"] > MAX_LOAD_S:
        print(
            f"python leg fails: diffs {bad}, loops {record['loop_nodes']}, "
            f"load {record['load_s']:.1f} s (limit {MAX_LOAD_S} s)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
