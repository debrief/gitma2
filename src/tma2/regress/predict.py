"""Prediction rows from a trained regressor (spec 012 research R6): the scorer's prefixes (G5
rows) of each σ = 1° scenario of a split, in the existing per-row prediction format."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.gate2.predict import _row
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment.score import g5_rows, iter_selected

from .frame import features, to_state
from .model import Regressor, RegressorConfig


def load_model(cfg: RegressorConfig, weights: Path) -> Regressor:
    from safetensors.torch import load_file

    model = Regressor(cfg)
    model.load_state_dict(load_file(str(weights)))
    model.eval()
    return model


def predict_scenarios(
    model: Regressor, data: list[BearingData], rows: list[list[int]]
) -> list[list[dict[str, Any]]]:
    """One prediction row per (scenario, prefix row k). Each k is read from a pass whose folding
    offset makes k the last row of a token, so the output at k reads rows ≤ k only."""
    cfg = model.cfg
    r, patch = cfg.max_rows, model.patch
    b = len(data)
    t = np.zeros((b, r), dtype=np.float32)
    own = np.zeros((b, r, 2))
    z = np.zeros((b, r), dtype=np.float32)
    valid = np.zeros((b, r), dtype=bool)
    mask = np.zeros((b, r), dtype=bool)
    for i, d in enumerate(data):
        n = min(d.n, r)
        t[i, :n], z[i, :n] = d.t[:n], d.z[:n]
        own[i, :n, 0], own[i, :n, 1] = d.ox[:n], d.oy[:n]
        valid[i, :n] = d.valid[:n] > 0
        mask[i, :n] = True
    sigma = np.array([d.sigma for d in data], dtype=np.float32)
    f, th = features(t, own, z, valid, mask, sigma, cfg.inputs == "ownship_only")
    outs: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    with torch.no_grad():
        for off in sorted({(k + 1) % patch for ks in rows for k in ks}):
            mean, logvar = model(torch.from_numpy(f), off)
            outs[off] = (mean.double().numpy(), logvar.double().numpy())
    res: list[list[dict[str, Any]]] = []
    for i, (d, ks) in enumerate(zip(data, rows, strict=True)):
        out = []
        for k in ks:
            off = (k + 1) % patch
            j = (k + 1 - off) // patch - 1
            ok = 0 <= j < outs[off][0].shape[1] and k < r
            if not ok:
                continue
            pred = outs[off][0][i, j]
            # the direction to the target: the last valid bearing at or before k
            vk = np.flatnonzero(d.valid[: k + 1] > 0)
            if vk.size == 0 or not np.isfinite(pred).all():
                continue
            st, rcs = to_state(pred, float(th[i]), float(d.z[vk[-1]]), (d.ox[k], d.oy[k]))
            row = _row(d, k, st, rcs, True)
            sd = np.exp(0.5 * outs[off][1][i, j])
            row["sd_log_range"] = float(sd[0])
            row["sd_speed_mps"] = float(10.0 * math.hypot(sd[1], sd[2]) / math.sqrt(2.0))
            out.append(row)
        res.append(out)
    return res


def predict_split(
    model: Regressor, path: str, start: int, count: int, batch: int = 64
) -> list[tuple[int, int, list[dict[str, Any]]]]:
    recs: list[tuple[int, int, list[dict[str, Any]]]] = []
    buf: list[tuple[int, dict[str, Any], BearingData, list[int]]] = []

    def flush() -> None:
        if not buf:
            return
        rows = predict_scenarios(model, [d for _, _, d, _ in buf], [ks for *_, ks in buf])
        recs.extend((j, int(m["index"]), rr) for (j, m, _, _), rr in zip(buf, rows, strict=True))
        buf.clear()

    for j, m, own, _tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if ks:
            buf.append((j, m, d, ks))
        if len(buf) >= batch:
            flush()
    flush()
    return recs
