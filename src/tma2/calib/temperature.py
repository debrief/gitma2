"""The classical calibration control: one log-scale per slice (spec 008 research R8, FR-023).

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
from .loss import beta_nll


def cells(d: CalData, keys: list[str]) -> list[str]:
    """Each row's cell label, e.g. ``minute=10|open=False``."""
    cols = {"minute": d.minute, "open": d.open}
    return ["|".join(f"{k}={cols[k][i]}" for k in keys) for i in range(len(d))]


def fit(cfg: TemperatureConfig, d: CalData, steps: int = 500) -> dict[str, float]:
    """{cell: s} fitted by Adam on each cell's β-NLL."""
    keys = list(cfg.slices or [])
    lab = np.array(cells(d, keys))
    out: dict[str, float] = {}
    for c in sorted(set(lab.tolist())):
        m = (lab == c) & d.usable
        if not m.any():
            out[c] = 0.0
            continue
        q = torch.tensor(d.q[m])
        s = torch.zeros(1, dtype=torch.float64, requires_grad=True)
        opt = torch.optim.Adam([s], lr=0.05)
        for _ in range(steps):
            loss = beta_nll(s.expand_as(q), q, cfg.beta, cfg.cap)
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
        out[c] = float(s.detach())
    return out


def apply(temps: dict[str, float], d: CalData, keys: list[str]) -> np.ndarray:
    """[N] s per row from its cell (0 for a cell not fitted)."""
    return np.array([temps.get(c, 0.0) for c in cells(d, keys)])
