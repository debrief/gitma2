"""Spec 039: a classical read-out told the generator's priors.

For one (scenario, row, segmentation) item the robust solve's cost is profiled over the target's
range at the row: each grid point is a refit with the range held (one tight prior row on the
state at the row, ``regress.hybrid.HybridLayer``; ``physics/layer.py`` is not edited) under the
whiteners the unconstrained robust solve ended with. The profile is weighted by the generator's
distribution of ln range at scored rows and its support for speed, and the read-out is the
posterior median of range with the velocity interpolated between the neighbouring refits.

It reads no truth: on the true segmentation it is a reference told the priors, on C″'s a causal
control. A profile is not a marginal (the other parameters' volume is ignored), and under
bearing errors the stated sd makes it too narrow; ``temper`` divides the cost by the variance
inflation the robust solve's own fitted error model implies for a mean.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tma2.headroom.estimators import (
    Item,
    RobustSettings,
    _unweight,
    _whiteners,
    robust_model,
    used,
)
from tma2.headroom.gls import solve
from tma2.physics.layer import PhysicsOutputs
from tma2.regress.hybrid import HybridLayer, prior_rows, set_prior

HOLD_SD = 0.002  # the range is held to 0.2%
REFINE = (-2.5, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.5)  # in sds of ln range about the mode


@dataclass(frozen=True)
class ProfileSettings:
    prior: str  # the prior table (JSON: ln_range_edges, density, speed_mps)
    grid: int = 20
    range_m: tuple[float, float] = (1000.0, 80000.0)
    temper: str = "none"  # "none" | "effective"
    speed_edge: float = 0.1  # softness of the speed support's edges, as a fraction of the edge
    flat: bool = False  # ignore the table and the speed support (a likelihood median: a test)

    def __post_init__(self) -> None:
        if self.temper not in ("none", "effective"):
            raise ValueError(f"temper: {self.temper!r} (none or effective)")
        if self.grid < 5:
            raise ValueError("grid: at least 5 points")


@dataclass(frozen=True)
class Prior:
    edges: np.ndarray  # [n + 1] ln range (m)
    density: np.ndarray  # [n] per unit ln range
    speed: tuple[float, float]

    @staticmethod
    def load(path: str | Path) -> Prior:
        d = json.loads(Path(path).read_text())
        return Prior(
            np.asarray(d["ln_range_edges"], dtype=np.float64),
            np.asarray(d["density"], dtype=np.float64),
            (float(d["speed_mps"][0]), float(d["speed_mps"][1])),
        )

    def log_range(self, x: np.ndarray) -> np.ndarray:
        """ln density of ln range, floored at 1e-4 of the peak outside the table's support."""
        j = np.clip(np.searchsorted(self.edges, x, side="right") - 1, 0, self.density.size - 1)
        inside = (x >= self.edges[0]) & (x <= self.edges[-1])
        floor = 1e-4 * float(self.density.max())
        out: np.ndarray = np.log(np.maximum(np.where(inside, self.density[j], 0.0), floor))
        return out

    def log_speed(self, s: np.ndarray, edge: float) -> np.ndarray:
        lo, hi = self.speed
        below = np.minimum(s - lo, 0.0) / (edge * lo)
        above = np.maximum(s - hi, 0.0) / (edge * hi)
        out: np.ndarray = -0.5 * (below * below + above * above)
        return out


def weighted_median(x: np.ndarray, lw: np.ndarray) -> tuple[float, int, float]:
    """The median of a density given by ln values ``lw`` at sorted points ``x`` (trapezoid rule
    on the density): (median, index i of the interval [x[i], x[i + 1]] holding it, fraction)."""
    w = np.exp(lw - lw.max())
    area = 0.5 * (w[1:] + w[:-1]) * np.diff(x)
    cum = np.concatenate([[0.0], np.cumsum(area)])
    if not cum[-1] > 0.0:
        i = int(np.argmax(w))
        return float(x[i]), min(i, x.size - 2), 0.0 if i < x.size - 1 else 1.0
    half = 0.5 * cum[-1]
    i = int(np.clip(np.searchsorted(cum, half, side="right") - 1, 0, x.size - 2))
    # inside the interval the density is linear: solve the quadratic for the fraction
    a, b, h = w[i], w[i + 1], x[i + 1] - x[i]
    need = half - cum[i]
    if abs(b - a) < 1e-12 * max(a, b, 1e-300):
        f = need / (a * h) if a > 0 else 0.5
    else:
        f = (-a + math.sqrt(max(a * a + 2.0 * (b - a) * need / h, 0.0))) / (b - a)
    f = float(min(max(f, 0.0), 1.0))
    return float(x[i] + f * h), i, f


def inflation(model: Any, dt: float) -> float:
    """The factor by which a white-noise variance of a mean understates this error model's."""
    var = float(model.marginal_var)
    if not var > 0.0 or float(model.sigma_c) <= 0.0 or float(model.tau_c) <= 0.0:
        return 1.0
    share = float(model.sigma_c) ** 2 / var
    rho = math.exp(-dt / float(model.tau_c))
    return (1.0 - share) + share * (1.0 + rho) / (1.0 - rho)


def profile_estimate(
    layer: HybridLayer,
    items: list[Item],
    r_max: int,
    settings: RobustSettings,
    cfg: ProfileSettings,
    prior: Prior,
) -> tuple[PhysicsOutputs, list[dict[str, Any] | None]]:
    """(the unconstrained robust solve's outputs, per item the read-out or None where it falls
    back to that solve). A read-out: range_m, course_rad, speed_mps, x_m, y_m and diagnostics."""
    layer.prior = None
    n_items = len(items)
    none: list[np.ndarray | None] = [None] * n_items
    from tma2.headroom.cov import ErrorModel

    models = [ErrorModel(d.sigma) for d, _, _ in items]
    out, raw = solve(layer, items, _whiteners(items, models, none), r_max)
    extras: list[np.ndarray | None] = none
    for _ in range(settings.outer):
        fitted = [
            robust_model(r, used(d, k, inp), float(d.t[1] - d.t[0]), d.sigma, settings)
            for r, (d, k, inp) in zip(_unweight(items, raw), items, strict=True)
        ]
        models = [m for m, _ in fitted]
        extras = [e for _, e in fitted]
        out, raw = solve(layer, items, _whiteners(items, models, extras), r_max)
    w = _whiteners(items, models, extras)

    def chi2(raw_b: np.ndarray, b: int) -> float:
        n = w[b].shape[0]
        v = w[b] @ raw_b[:n]
        return float(v @ v)

    mode_r = out.range.numpy()
    cov = out.cov.numpy()
    state0 = out.state.numpy()
    base = np.geomspace(cfg.range_m[0], cfg.range_m[1], cfg.grid)
    grids = []
    for b, (d, k, _) in enumerate(items):
        own = np.array([d.ox[k], d.oy[k]])
        g: list[float] = [float(v) for v in base]
        r0 = float(mode_r[b])
        if math.isfinite(r0) and r0 > 1.0 and np.isfinite(cov[b]).all():
            u = (state0[b, :2] - own) / r0
            s = math.sqrt(max(float(u @ cov[b, :2, :2] @ u), 0.0)) / r0
            s = min(max(s, 0.01), 0.5)
            g += [r0 * math.exp(c * s) for c in REFINE] + [r0]
        else:
            g += [float(np.sqrt(base[0] * base[-1]))] * (len(REFINE) + 1)
        grids.append(np.asarray(g))
    n_g = len(grids[0])
    rng = np.full((n_items, n_g), np.nan)
    cost = np.full((n_items, n_g), np.nan)
    vel = np.full((n_items, n_g, 2), np.nan)
    pos = np.full((n_items, n_g, 2), np.nan)
    for j in range(n_g):
        rows = [
            prior_rows(d, k, None, 1.0, (math.log(float(grids[b][j])), HOLD_SD))
            for b, (d, k, _) in enumerate(items)
        ]
        set_prior(layer, items, rows)
        o, rw = solve(layer, items, w, r_max)
        st = o.state.numpy()
        for b in range(n_items):
            if rows[b][2] and np.isfinite(st[b]).all():
                rng[b, j] = float(o.range[b])
                cost[b, j] = chi2(rw[b], b)
                vel[b, j] = st[b, 2:]
                pos[b, j] = st[b, :2]
    layer.prior = None
    res: list[dict[str, Any] | None] = []
    for b, (d, k, _) in enumerate(items):
        ok = np.isfinite(rng[b]) & np.isfinite(cost[b]) & (rng[b] > 1.0)
        if int(ok.sum()) < 5:
            res.append(None)
            continue
        order = np.argsort(rng[b][ok])
        x = np.log(rng[b][ok][order])
        c = cost[b][ok][order]
        v = vel[b][ok][order]
        p = pos[b][ok][order]
        keep = np.concatenate([[True], np.diff(x) > 1e-9])
        x, c, v, p = x[keep], c[keep], v[keep], p[keep]
        temp = inflation(models[b], float(d.t[1] - d.t[0])) if cfg.temper == "effective" else 1.0
        lw = -0.5 * (c - c.min()) / temp
        if not cfg.flat:
            lw = (
                lw
                + prior.log_range(x)
                + prior.log_speed(np.hypot(v[:, 0], v[:, 1]), cfg.speed_edge)
            )
        if x.size < 5 or not np.isfinite(lw).any():
            res.append(None)
            continue
        med, i, f = weighted_median(x, lw)
        vv = (1.0 - f) * v[i] + f * v[i + 1]
        own = np.array([d.ox[k], d.oy[k]])
        near = p[i] if f < 0.5 else p[i + 1]
        u = (near - own) / max(float(np.hypot(*(near - own))), 1e-9)
        r_hat = math.exp(med)
        xy = own + r_hat * u
        dens = np.exp(lw - lw.max())
        area = 0.5 * (dens[1:] + dens[:-1]) * np.diff(x)
        mean = float(np.sum(area * 0.5 * (x[1:] + x[:-1])) / max(float(area.sum()), 1e-300))
        var = float(
            np.sum(area * (0.5 * (x[1:] + x[:-1]) - mean) ** 2) / max(float(area.sum()), 1e-300)
        )
        res.append(
            {
                "range_m": r_hat,
                "course_rad": float(math.atan2(vv[0], vv[1]) % (2.0 * math.pi)),
                "speed_mps": float(math.hypot(vv[0], vv[1])),
                "x_m": float(xy[0]),
                "y_m": float(xy[1]),
                "profile_sd_log_range": math.sqrt(max(var, 0.0)),
                "profile_shift": float(med - math.log(max(float(mode_r[b]), 1.0))),
                "profile_temper": temp,
            }
        )
    return out, res
