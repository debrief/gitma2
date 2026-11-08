"""The classical calibration control: log-scales per slice, in the head's form (spec 008 R8).

Cells cross the declared slice keys (``minute``: the G5 time; ``open``: the row ends inside an
open transition). Each cell's s minimises the same β-NLL as the head over the cell's usable rows
(fitted on validation tuning ordinals). A cell with no usable rows gets s = 0 (the raw
covariance).
"""

from __future__ import annotations

import numpy as np
import torch

from tma2.types.generated.tma import TemperatureConfig

from .data import CalData
from .head import outputs
from .loss import beta_nll


def cells(d: CalData, keys: list[str]) -> list[str]:
    """Each row's cell label, e.g. ``minute=10|open=False``."""
    cols = {"minute": d.minute, "open": d.open}
    return ["|".join(f"{k}={cols[k][i]}" for k in keys) for i in range(len(d))]


def fit(cfg: TemperatureConfig, d: CalData, steps: int = 500) -> dict[str, list[float]]:
    """{cell: s} fitted by Adam on each cell's β-NLL; s has one value (scalar) or four (local)."""
    keys = list(cfg.slices or [])
    lab = np.array(cells(d, keys))
    out: dict[str, list[float]] = {}
    m_out = outputs(cfg.form)
    for c in sorted(set(lab.tolist())):
        m = (lab == c) & d.usable
        if not m.any():
            out[c] = [0.0] * m_out
            continue
        u, w = torch.tensor(d.u[m]), torch.tensor(d.w[m])
        s = torch.zeros(m_out, dtype=torch.float64, requires_grad=True)
        opt = torch.optim.Adam([s], lr=0.05)
        for _ in range(steps):
            loss = beta_nll(s.unsqueeze(0).expand(len(u), -1), u, w, cfg.beta, cfg.cap)
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
        out[c] = [float(v) for v in s.detach()]
    return out


def apply(temps: dict[str, list[float]], d: CalData, keys: list[str]) -> np.ndarray:
    """[N, m] s per row from its cell (0 for a cell not fitted)."""
    m = len(next(iter(temps.values()))) if temps else 1
    return np.array([temps.get(c, [0.0] * m) for c in cells(d, keys)], dtype=np.float64)
