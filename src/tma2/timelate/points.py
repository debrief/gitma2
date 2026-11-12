"""Normal points (spec 013 research R2, R7): a run of bearings replaced by one fitted bearing.

``fixed_points(period, n)`` folds every n consecutive rows of a period into one point: the
mean time, the mean ownship position, the circular mean of the valid bearings, and the number
of bearings it stands for. With n = 2 on 5-second data this is the 10-second input the frozen
C is given; its stated σ is σ / √2 (a point with one bearing missing is treated as a full one,
which overstates its weight by √2 on at most the dropout share of points).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from tma2.references.classical import BearingData

from .periods import Period


@dataclass
class Points:
    data: BearingData  # times from the period's first row
    count: np.ndarray  # bearings each point stands for
    n: int  # rows folded per point

    def point_of_row(self, row: int) -> int:
        return min(row // self.n, self.data.n - 1)


def fixed_points(p: Period, n: int) -> Points:
    a, b = p.first, p.first + p.rows
    t = p.own[a:b, 0].astype(np.float64) - float(p.own[a, 0])
    ox = p.own[a:b, 1].astype(np.float64)
    oy = p.own[a:b, 2].astype(np.float64)
    z = p.obs[a:b, 1].astype(np.float64)
    v = p.obs[a:b, 2] != 0
    m = p.rows // n
    if m == 0:
        raise ValueError("a period shorter than one point")
    cut = m * n

    def fold(x: np.ndarray) -> np.ndarray:
        out: np.ndarray = x[:cut].reshape(m, n)
        return out

    vv = fold(v.astype(np.float64))
    cnt = vv.sum(axis=1)
    s = (np.sin(fold(z)) * vv).sum(axis=1)
    c = (np.cos(fold(z)) * vv).sum(axis=1)
    zz = np.where(cnt > 0, np.arctan2(s, c), 0.0)
    turns = p.ownship_turns()
    zig = turns[0][1] // n if turns else 0
    sigma = float(p.meta["parameters"]["noise_sigma_rad"]) / math.sqrt(n)
    d = BearingData(
        t=fold(t).mean(axis=1),
        ox=fold(ox).mean(axis=1),
        oy=fold(oy).mean(axis=1),
        z=zz,
        valid=(cnt > 0).astype(np.uint8),
        zig_index=int(min(zig, m - 1)),
        sigma=sigma,
        index=int(p.meta["index"]),
    )
    return Points(d, cnt, n)
