"""The hybrid (spec 037 research R7): C″'s final robust solve with the regressor as a prior.

``HybridLayer`` is ``headroom.gls.WhitenedLayer`` with up to three more residual rows per item,
linear in the layer's parameters because the state at the reported row is: the range along the
line of sight and the two velocity components, each (layer − regressor) ÷ (weight × the
regressor's stated sd). ``physics/layer.py`` is not edited; the reported state is the layer's.
An item without a usable prior has zero rows there and solves as the parent does, to rounding
(its rows carry `prior_used: false`).

Differences from the plan, recorded: the solve keeps the layer's own start (the prior pulls it;
the damping ladder is the parent's), the velocity prior is isotropic at the row's ``sd_speed_mps``
(the row does not carry the two components' sds), and the range prior is linearised along the
regressor's line of sight.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch
from torch import Tensor

from tma2.headroom.gls import WhitenedLayer
from tma2.references.classical import BearingData

PRIOR_ROWS = 3


class HybridLayer(WhitenedLayer):
    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        if self.knots == 0:
            raise ValueError("the hybrid is built for the layer with knots")
        # (tk [B], A [B, 3, 4], m [B, 3]): residual = A · state(tk) − m; None: the parent's solve
        self.prior: tuple[Tensor, Tensor, Tensor] | None = None

    def _raw(self, theta: Tensor, *args: Tensor) -> tuple[Tensor, Tensor]:
        r, jac = super()._raw(theta, *args)
        if self.prior is None:
            return r, jac
        t, _ox, _oy, _z, _sw, t_knots, c, _s, _order, _ref = args
        tk, a, m = self.prior
        n = theta.shape[0] // tk.shape[0]
        tk_r = tk.repeat_interleave(n, dim=0).unsqueeze(1)
        a_r = a.repeat_interleave(n, dim=0)
        m_r = m.repeat_interleave(n, dim=0)
        zero = torch.zeros(theta.shape[0], dtype=theta.dtype)
        one = torch.ones(theta.shape[0], dtype=theta.dtype)
        state, g, _ = self._knot_state(
            theta, t, tk_r, c, t_knots, theta[:, 0:2], theta[:, 2:4], zero, one
        )
        rp = (a_r @ state.unsqueeze(2))[..., 0] - m_r
        return torch.cat([r, rp], dim=1), torch.cat([jac, a_r @ g], dim=1)


def prior_rows(
    d: BearingData,
    k: int,
    row: dict[str, Any] | None,
    weight: float,
    static: tuple[float, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, bool]:
    """(A [3, 4], m [3], used) for one item. ``row``: the regressor's prediction row at k;
    ``static``: instead, a fixed prior on ln range (mean, sd) along the last valid bearing."""
    a, m = np.zeros((PRIOR_ROWS, 4)), np.zeros(PRIOR_ROWS)
    own = np.array([d.ox[k], d.oy[k]])
    if static is not None:
        vk = np.flatnonzero(d.valid[: k + 1] > 0)
        if vk.size == 0:
            return a, m, False
        z = float(d.z[vk[-1]])
        u = np.array([math.sin(z), math.cos(z)])
        rng = math.exp(static[0])
        sd = weight * rng * static[1]
        a[0, :2] = u / sd
        m[0] = (float(u @ own) + rng) / sd
        return a, m, True
    if row is None:
        return a, m, False
    vals = [row.get(key) for key in ("range_m", "x_m", "y_m", "course_rad", "speed_mps")]
    sds = [row.get("sd_log_range"), row.get("sd_speed_mps")]
    if any(v is None or not math.isfinite(float(v)) for v in vals + sds):
        return a, m, False
    rng, x, y, course, speed, s0, s1 = (float(v) for v in (*vals, *sds) if v is not None)
    sd_r = weight * rng * s0
    sd_v = weight * s1
    if not (rng > 0 and sd_r > 0 and sd_v > 0):
        return a, m, False
    u = (np.array([x, y]) - own) / rng
    a[0, :2] = u / sd_r
    m[0] = (float(u @ own) + rng) / sd_r
    a[1, 2] = a[2, 3] = 1.0 / sd_v
    m[1] = speed * math.sin(course) / sd_v
    m[2] = speed * math.cos(course) / sd_v
    return a, m, True


def set_prior(
    layer: HybridLayer,
    items: list[tuple[BearingData, int, Any]],
    rows: list[tuple[np.ndarray, np.ndarray, bool]],
) -> None:
    f64 = torch.float64
    layer.prior = (
        torch.tensor([float(d.t[k]) for d, k, _ in items], dtype=f64),
        torch.tensor(np.stack([a for a, _, _ in rows]), dtype=f64),
        torch.tensor(np.stack([m for _, m, _ in rows]), dtype=f64),
    )


def load_prior_rows(path: str, ordinals: set[int]) -> dict[tuple[int, float], dict[str, Any]]:
    """{(ordinal, float32 timestamp): row} of a regressor prediction file, for some ordinals."""
    import json

    out: dict[tuple[int, float], dict[str, Any]] = {}
    with open(path, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            rec = json.loads(line)
            j = int(rec["ordinal"])
            if j in ordinals:
                for x in rec["rows"]:
                    out[(j, float(x["timestamp_s"]))] = x
    return out
