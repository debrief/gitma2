"""``tma2-oracle``: the physics layer with truth segmentation, as a per-timestep estimator.

Rows are scored at the G5 times by default (zig + 5/10/15/20 min) or every row with ``--all-rows``;
rows without an estimate (no valid bearing) are written non-converged, like gitma's estimators.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import numpy as np
import torch

from tma2.eval.predictions import PredictionWriter
from tma2.eval.rows import G5_GATE_MIN
from tma2.physics.layer import PhysicsInputs, PhysicsLayer
from tma2.physics.reference import ITERATIONS
from tma2.physics.segmentation import LayerInputs, oracle_inputs, trivial_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.sim.geometry import f32, f32_angle

from .estimators import open_split

ORACLE = "oracle-physics"


def rows_for(meta: dict[str, Any], all_rows: bool) -> list[int]:
    n = int(meta["samples"])
    if all_rows:
        return list(range(int(meta["zig_index"]) + 1, n))
    dt = float(meta["parameters"]["dt_s"])
    out = []
    for minutes in G5_GATE_MIN:
        k = int(meta["zig_index"]) + int(round(minutes * 60 / dt))
        if k < n:
            out.append(k)
    return out


def _pad(a: np.ndarray, r: int, fill: float = 0.0) -> np.ndarray:
    out = np.full(r, fill, dtype=np.float64)
    out[: a.shape[0]] = a
    return out


def inputs_for(items: list[tuple[BearingData, int, LayerInputs]], r_max: int) -> PhysicsInputs:
    """Padded batch inputs for (data, row, inputs) items, in double whatever the default dtype
    (results must not depend on what ran before; P0 panel round 2)."""
    f64 = torch.float64

    def t(a: Any) -> torch.Tensor:
        return torch.tensor(np.asarray(a, dtype=np.float64), dtype=f64)

    return PhysicsInputs(
        bearing=t(np.stack([_pad(d.z, r_max) for d, _, _ in items])),
        valid=t(np.stack([_pad(d.valid.astype(np.float64), r_max) for d, _, _ in items])),
        own=t(np.stack([np.stack([_pad(d.ox, r_max), _pad(d.oy, r_max)], 1) for d, _, _ in items])),
        t=t(np.stack([_pad(d.t, r_max) for d, _, _ in items])),
        sigma=t([d.sigma for d, _, _ in items]),
        k=torch.tensor([k for _, k, _ in items], dtype=torch.int64),
        changepoint=t(np.stack([_pad(i.changepoint, r_max) for _, _, i in items])),
        speed_weight=t(np.stack([_pad(i.speed_weight, r_max) for _, _, i in items])),
        log_weight=t(np.stack([_pad(i.log_weight, r_max) for _, _, i in items])),
        theta0=t(np.stack([i.theta0 for _, _, i in items])),
        speed_skip=t(
            np.stack(
                [
                    _pad(i.speed_skip if i.speed_skip is not None else np.zeros(1), r_max)
                    for _, _, i in items
                ]
            )
        ),
    )


def run_layer(
    layer: PhysicsLayer, items: list[tuple[BearingData, int, LayerInputs]], r_max: int
) -> Any:
    """Batched forward for (data, row, inputs) items; returns PhysicsOutputs."""
    x = inputs_for(items, r_max)
    with torch.no_grad():
        return layer(x)


def row_from_output(d: BearingData, k: int, out: Any, b: int) -> dict[str, Any]:
    st = out.state[b].numpy()
    return {
        "timestamp_s": f32(float(d.t[k])),
        "range_m": f32(float(out.range[b])),
        "course_rad": f32_angle(float(out.course[b])),
        "speed_mps": f32(float(out.speed[b])),
        "x_m": f32(float(st[0])),
        "y_m": f32(float(st[1])),
        "converged": bool(out.plausible[b]),
        "iterations": 0,
    }


def empty_row(d: BearingData, k: int) -> dict[str, Any]:
    return {
        "timestamp_s": f32(float(d.t[k])),
        "range_m": 0.0,
        "course_rad": 0.0,
        "speed_mps": 0.0,
        "x_m": 0.0,
        "y_m": 0.0,
        "converged": False,
        "iterations": 0,
    }


def predict_split(
    truth: str,
    out: str,
    speed_prior: bool,
    all_rows: bool,
    iterations: int,
    knots: int,
    batch: int = 256,
    trivial: bool = False,
    mask_turns: bool = False,
) -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    header, blocks = open_split(truth)
    r_max = int(np.floor(header.parameter_ranges.window_s.max / header.parameter_ranges.dt_s))
    layer = PhysicsLayer(iterations=iterations, knots=knots)
    name = (
        "classical-physics"
        if trivial
        else ORACLE + ("-sp" if speed_prior else "") + ("-masked" if mask_turns else "")
    )
    writer = PredictionWriter(out, name, "per_timestep", truth)
    t0 = time.perf_counter()
    n_scen = 0
    pending: list[tuple[BearingData, int, LayerInputs]] = []
    pending_meta: list[
        tuple[dict[str, Any], list[tuple[int, int | None]]]
    ] = []  # per scenario: rows and item idx

    def flush() -> None:
        if not pending:
            return
        o = run_layer(layer, pending, r_max)
        base = 0
        for d_meta, rows in pending_meta:
            pred_rows = []
            for k, j in rows:
                dd = pending[j][0] if j is not None else None
                if j is None:
                    pred_rows.append(empty_row(d_cache[d_meta["index"]], k))
                else:
                    assert dd is not None
                    pred_rows.append(row_from_output(dd, k, o, j))
            writer.write(
                {
                    "record": "prediction",
                    "scenario_index": int(d_meta["index"]),
                    "estimator": name,
                    "mode": "per_timestep",
                    "rows": pred_rows,
                }
            )
            base += len(rows)
        pending.clear()
        pending_meta.clear()
        d_cache.clear()

    d_cache: dict[int, BearingData] = {}
    try:
        for _, meta, own, _tgt, obs in blocks:
            d = bearing_data_from_arrays(meta, own, obs)
            d_cache[d.index] = d
            rows: list[tuple[int, int | None]] = []
            for k in rows_for(meta, all_rows):
                inp = (
                    trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
                    if trivial
                    else oracle_inputs(
                        d.t,
                        d.ox,
                        d.oy,
                        d.z,
                        d.valid,
                        k,
                        meta.get("manoeuvres"),
                        speed_prior,
                        mask_turns,
                    )
                )
                if inp is None:
                    rows.append((k, None))
                else:
                    pending.append((d, k, inp))
                    rows.append((k, len(pending) - 1))
            pending_meta.append((meta, rows))
            n_scen += 1
            if len(pending) >= batch:
                flush()
        flush()
        writer.close()
    except BaseException:
        writer.abort()
        raise
    return {"out": out, "estimator": name, "scenarios": n_scen, "seconds": time.perf_counter() - t0}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-oracle")
    ap.add_argument("--truth", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed-prior", action="store_true")
    ap.add_argument("--all-rows", action="store_true")
    ap.add_argument(
        "--trivial", action="store_true", help="no knots: the physics layer as batch least squares"
    )
    ap.add_argument(
        "--mask-turns",
        action="store_true",
        help="diagnostic: zero weight on bearings inside each manoeuvre span",
    )
    ap.add_argument("--iterations", type=int, default=ITERATIONS)
    ap.add_argument("--knots", type=int, default=8)
    a = ap.parse_args(argv)
    try:
        print(
            json.dumps(
                predict_split(
                    a.truth,
                    a.out,
                    a.speed_prior,
                    a.all_rows,
                    a.iterations,
                    a.knots,
                    trivial=a.trivial,
                    mask_turns=a.mask_turns,
                )
            )
        )
    except (OSError, ValueError) as e:
        print(f"tma2-oracle: {e}", file=sys.stderr)
        return 2
    return 0
