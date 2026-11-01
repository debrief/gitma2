"""Per-timestep predictions of a trained model on a split (spec 003 FR-019; contracts/cli.md).

Every post-zig row of every scenario, in gitma's prediction format (estimator = the model's id,
mode per_timestep), so the evaluation tooling of spec 002 scores models and references alike. A
row is marked converged when the physics layer's solution is plausible (gitma's bounds); the
estimate is the physics layer's (or, for control (a), the direct head's).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors.torch import load_file

from tma2.eval.predictions import PredictionWriter
from tma2.sim.geometry import bearing_of, f32, f32_angle

from .batching import model_inputs, run
from .gate1 import Gate1Model
from .rows import row_batch, scenario_tensors
from .train import batch_from_pack, load_plan, model_from_plan


def load_model(plan_path: str | Path, model_id: str, checkpoint: str | Path) -> Gate1Model:
    plan, _ = load_plan(plan_path)
    cfg = model_from_plan(plan, model_id)
    torch.set_default_dtype(torch.float64)
    model = Gate1Model(cfg)
    folder = Path(checkpoint)
    weights = folder / "best.safetensors"
    if not weights.exists():
        weights = folder / "weights.safetensors"
    model.load_state_dict(load_file(str(weights)))
    model.eval()
    model.set_implicit(False)
    return model


def predict_split(
    model: Gate1Model,
    truth: str | Path,
    out: str | Path,
    limit: int | None = None,
    chunk: int = 32,
    log: Any = print,
) -> int:
    """Write predictions for the first ``limit`` scenarios (all by default); returns the count."""
    truth = Path(truth)
    batch_all = batch_from_pack(truth, limit or 10**9)
    writer = PredictionWriter(out, model.cfg.id, "per_timestep", truth)
    n = len(batch_all)
    try:
        for a in range(0, n, chunk):
            sub = _slice(batch_all, a, min(a + chunk, n))
            tens = scenario_tensors(sub, 0, 1)
            rows = row_batch(sub, tens, np.random.default_rng(0), all_rows=True, keep_singular=True)
            x = model_inputs(tens, rows, sub.samples)
            with torch.no_grad():
                o = run(model, x)
            by_s: dict[int, list[dict[str, Any]]] = {s: [] for s in range(len(sub))}
            for j in range(rows.k.shape[0]):
                s = int(rows.source[j])
                k = int(rows.k[j])
                st = o.state[j].numpy()
                okx, oky = float(sub.own[s, k, 0]), float(sub.own[s, k, 1])
                finite = bool(np.isfinite(st).all())
                by_s[s].append(
                    {
                        "timestamp_s": f32(float(sub.t[s, k])),
                        "range_m": f32(math.hypot(st[0] - okx, st[1] - oky)) if finite else 0.0,
                        "course_rad": f32_angle(bearing_of(float(st[2]), float(st[3])))
                        if finite
                        else 0.0,
                        "speed_mps": f32(math.hypot(st[2], st[3])) if finite else 0.0,
                        "x_m": f32(float(st[0])) if finite else 0.0,
                        "y_m": f32(float(st[1])) if finite else 0.0,
                        "converged": bool(o.plausible[j]) and finite,
                        "iterations": model.cfg.iterations,
                    }
                )
            for s in range(len(sub)):
                writer.write(
                    {
                        "record": "prediction",
                        "scenario_index": int(sub.index[s]),
                        "estimator": model.cfg.id,
                        "mode": "per_timestep",
                        "rows": by_s[s],
                    }
                )
            log(f"{min(a + chunk, n)}/{n}")
        writer.close()
    except BaseException:
        writer.abort()
        raise
    return n


def _slice(b: Any, a: int, z: int) -> Any:
    from dataclasses import fields, replace

    return replace(b, **{f.name: getattr(b, f.name)[a:z] for f in fields(b)})
