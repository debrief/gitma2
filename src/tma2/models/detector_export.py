"""Export of the steady-leg detector alone to ONNX (spec 004 FR-033; research R12; Annex A §A.4).

``python -m tma2.models.detector_export --out <dir> [--plan p --model id --checkpoint c]`` writes
``model.onnx`` (double precision, a fixed window of ``rows_for(ranges)`` rows, dynamic batch),
``weights.safetensors``, ``architecture.json``, the golden batch (``in_*.bin``, torch outputs
``out_*.bin``, onnxruntime outputs ``ort_*.bin``, ``manifest.json``), ``ops.txt`` and
``python_leg.json``, in the layout the browser and Java legs of ``conformance/onnx/`` read.

The graph takes the raw inputs (bearing, valid, ownship x, y, course, speed, time, window mask),
computes the 13 feature channels in the graph (``detector.features``) and returns ``p_change`` at
every row, and ``w_change`` and ``p_kind`` for the questions the variant asks: every row (causal,
[B, R, R]) or the last row of the window (time-late, [B, 1, R]). Knot export (local maxima ≥ the
threshold) is a few lines on these outputs and stays outside the graph.

Without a checkpoint the detector has seeded random weights everywhere, the zero-initialised key
projections and head outputs included, so the check exercises every head.
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
from tma2.sim.ranges import rows_for
from tma2.types.generated.tma import DetectorConfig, DetectorVariant

from .detector import Detector, features

OPSET = 17
TOL = 1e-5
MAX_LOAD_S = 60.0
MAX_WASM_S_PER_WINDOW = 1.0  # Annex A §A.4: the browser viewer, a 360-row window
INPUTS = ("bearing", "valid", "ox", "oy", "own_course", "own_speed", "t", "window")
OUTPUTS = ("p_change", "w_change", "p_kind")
FIXTURE = Path("tests/fixtures/gitma/phase4-seed777")


class DetectorExport(nn.Module):
    def __init__(self, model: Detector) -> None:
        super().__init__()
        self.model = model
        self.late = model.cfg.variant == DetectorVariant.time_late

    def forward(
        self,
        bearing: Tensor,
        valid: Tensor,
        ox: Tensor,
        oy: Tensor,
        own_course: Tensor,
        own_speed: Tensor,
        t: Tensor,
        window: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        own = torch.stack([ox, oy, own_course, own_speed], dim=2)
        v = valid * window
        x = features(bearing, v, own, t, window)
        r = bearing.shape[1]
        last = (window.sum(dim=1) - 1.0).to(torch.int64)  # [B]
        if self.late:
            query = last.unsqueeze(1)
        else:
            idx = torch.arange(r, device=bearing.device).unsqueeze(0)
            query = torch.where(idx <= last.unsqueeze(1), idx, torch.full_like(idx, -1))
        out = self.model(x, window, query)
        return out.p_change, out.w_change, out.p_kind


def seeded_detector(cfg: DetectorConfig, seed: int) -> Detector:
    torch.manual_seed(seed)
    model = Detector(cfg)
    g = torch.Generator().manual_seed(seed + 1)
    with torch.no_grad():
        for p in (
            model.now_head[2].weight,
            model.now_head[2].bias,
            model.w_head.k.weight,
            model.w_head.k.bias,
            model.kind_head.k.weight,
            model.kind_head.k.bias,
        ):
            p.copy_(0.1 * torch.randn(p.shape, generator=g))
        model.w_head.bias.fill_(-1.0)  # weights in (0, 1), some above the export threshold
    return model


def golden_batch(fixture: Path, r_max: int, n: int = 4) -> dict[str, np.ndarray]:
    cols: dict[str, list[np.ndarray]] = {name: [] for name in INPUTS}
    for i, (_, meta, own, _tgt, obs) in enumerate(iter_pack_raw(fixture / "test.f32pack")):
        if i >= n:
            break
        s = int(meta["samples"])

        def pad(a: np.ndarray) -> np.ndarray:
            out = np.zeros(r_max)
            out[:s] = a[:s]
            return out

        cols["bearing"].append(pad(obs[:, 1].astype(np.float64)))
        cols["valid"].append(pad((obs[:, 2] != 0).astype(np.float64)))
        cols["ox"].append(pad(own[:, 1].astype(np.float64)))
        cols["oy"].append(pad(own[:, 2].astype(np.float64)))
        cols["own_course"].append(pad(own[:, 3].astype(np.float64)))
        cols["own_speed"].append(pad(own[:, 4].astype(np.float64)))
        cols["t"].append(pad(own[:, 0].astype(np.float64)))
        cols["window"].append(pad(np.ones(s)))
    return {name: np.stack(v).astype(np.float64) for name, v in cols.items()}


def export(model: Detector, out_dir: Path, r_max: int, fixture: Path = FIXTURE) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    model = model.double().eval()
    wrapper = DetectorExport(model).eval()
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
                "max_s_per_window": MAX_WASM_S_PER_WINDOW,
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
    record = {
        "max_rel_diff": diffs,
        "tol": TOL,
        "dtype": "float64",
        "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "runtime": f"onnxruntime {ort.__version__} (Python)",
        "nodes": len(graph.node),
        "ops": ops,
        "load_s": load_s,
        "run_s": run_s,
        "run_s_per_window": run_s / batch["bearing"].shape[0],
        "window_rows": r_max,
        "variant": DetectorVariant(model.cfg.variant).value,
    }
    (out_dir / "python_leg.json").write_text(json.dumps(record, indent=2))
    return record


def architecture(cfg: DetectorConfig, r_max: int, source: str) -> dict[str, Any]:
    late = cfg.variant == DetectorVariant.time_late
    return {
        "config": json.loads(cfg.model_dump_json(exclude_none=True)),
        "window_rows": r_max,
        "inputs": {
            "bearing": "[B, R] true bearing, rad, clockwise from north",
            "valid": "[B, R] 1 where the bearing is present",
            "ox": "[B, R] ownship x (east), m",
            "oy": "[B, R] ownship y (north), m",
            "own_course": "[B, R] ownship course, rad",
            "own_speed": "[B, R] ownship speed, m/s",
            "t": "[B, R] time, s",
            "window": "[B, R] 1 inside the window (rows 0 … samples − 1), 0 on padding",
        },
        "outputs": {
            "p_change": "[B, R] P(manoeuvre in progress or begun within 60 s) at each row",
            "w_change": "[B, 1, R] the last row's changepoint weights"
            if late
            else "[B, R, R] row k's changepoint weights over rows j ≤ k",
            "p_kind": "same shape: P(course change) of a changepoint at j",
        },
        "dtype": "float64",
        "opset": OPSET,
        "weights": source,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--model", default="gd-conformance")
    ap.add_argument("--variant", choices=[v.value for v in DetectorVariant], default="causal")
    ap.add_argument("--checkpoint")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    from .detector_config import detector_config
    from .detector_predict import load_detector
    from .detector_train import detector_from_plan
    from .train import load_plan

    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        if a.plan:
            plan, _ = load_plan(a.plan)
            cfg = detector_from_plan(plan, a.model)
        else:
            if a.checkpoint:
                ap.error("--checkpoint needs --plan")
            cfg = detector_config(a.model, variant=DetectorVariant(a.variant))
        r_max = rows_for(json.loads((FIXTURE / "ranges.json").read_text()))
        if a.checkpoint:
            model = load_detector(a.plan, a.model, a.checkpoint)
            source = str(a.checkpoint)
        else:
            model = seeded_detector(cfg, a.seed)
            source = f"seeded random (seed {a.seed}, zero-initialised layers perturbed)"
        out = Path(a.out)
        record = export(model, out, r_max)
        (out / "architecture.json").write_text(
            json.dumps(architecture(cfg, r_max, source), indent=2)
        )
    finally:
        torch.set_default_dtype(default)
    print(json.dumps(record))
    bad = {k: v for k, v in record["max_rel_diff"].items() if v > TOL}
    if bad or record["load_s"] > MAX_LOAD_S:
        print(f"python leg fails: diffs {bad}, load {record['load_s']:.1f} s", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
