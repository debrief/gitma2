"""Training and scoring rows from generated CV batches (spec 003 FR-005, FR-006, FR-012).

A scenario batch from :func:`tma2.features.batch.generate_batch` is turned into:

* scenario tensors, one per (scenario, noise draw): bearings re-drawn from the stored truth with
  the scenario's σ and dropout pattern, from a seeded stream that is a pure function of
  (seed, scenario index, draw); draw 0 keeps the generator's own bearings;
* scored rows: per scenario, the gate rows zig + 5 min and zig + 10 min when the window reaches
  them, plus random post-zig rows up to ``rows_per_scenario``; each with the classical grid start,
  the truth state and the full-window Cramér–Rao bound on (x, y, vx, vy) at the row. Rows whose
  bound is singular are dropped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numba import njit, prange

from tma2.features.batch import Batch
from tma2.references import lsq

GATE_ROWS_S = (300.0, 600.0)  # zig + 5 min (range, course), zig + 10 min (speed)
SINGULAR_COND = 1e12
TWO_PI = 2.0 * math.pi


@dataclass
class ScenarioTensors:
    """Per (scenario, draw): float64 arrays [S, R] and [S]."""

    scenario: np.ndarray  # [S] index into the source batch
    draw: np.ndarray  # [S]
    bearing: np.ndarray  # [S, R]
    valid: np.ndarray  # [S, R] float 0/1
    ox: np.ndarray  # [S, R]
    oy: np.ndarray  # [S, R]
    t: np.ndarray  # [S, R]
    sigma: np.ndarray  # [S]


@dataclass
class RowBatch:
    """One entry per scored row."""

    source: np.ndarray  # [N] index into ScenarioTensors
    k: np.ndarray  # [N] row index
    theta_grid: np.ndarray  # [N, 4] classical grid start (window-start state)
    truth: np.ndarray  # [N, 4] (x, y, vx, vy) at row k
    bound_cov: np.ndarray  # [N, 4, 4] Cramér–Rao bound on (x, y, vx, vy) at row k
    since_zig_s: np.ndarray  # [N]


def renoise(batch: Batch, seed: int, draw: int) -> np.ndarray:
    """Bearings for one noise draw: draw 0 is the generator's; otherwise truth + σ·N(0, 1) from
    a stream seeded by (seed, scenario index, draw), wrapped to [0, 2π) and float32-rounded like
    the generator's. The dropout pattern is the scenario's own."""
    if draw == 0:
        return batch.bearing.astype(np.float64)
    out = np.zeros(batch.bearing.shape, dtype=np.float64)
    dx = batch.tgt[..., 0].astype(np.float64) - batch.own[..., 0].astype(np.float64)
    dy = batch.tgt[..., 1].astype(np.float64) - batch.own[..., 1].astype(np.float64)
    truth = np.arctan2(dx, dy)
    for s in range(len(batch)):
        rng = np.random.default_rng([seed, int(batch.index[s]), draw])
        noise = rng.standard_normal(batch.bearing.shape[1]) * float(batch.sigma[s])
        z = np.mod(truth[s] + noise, TWO_PI).astype(np.float32).astype(np.float64)
        out[s] = np.where(batch.valid[s], z, 0.0)
    return out


@njit(parallel=True, cache=True)
def _row_kernel(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    sigma: np.ndarray,
    src: np.ndarray,
    ks: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per row (source j, row k): the classical grid start on samples [0, k] and the full-window
    Cramér–Rao bound on (x, y, vx, vy) at k; ok = 0 where no valid bearing or the bound is
    singular (scaled condition above 1e12). ``ok``: 0 no valid bearing up to k, 1 grid start but
    singular bound, 2 both. Parallel over rows; each row's arithmetic is serial."""
    n = src.shape[0]
    grid = np.zeros((n, 4))
    cov = np.full((n, 4, 4), np.nan)
    ok = np.zeros(n, dtype=np.uint8)
    for q in prange(n):
        j = src[q]
        k = ks[q]
        vu8 = valid[j].astype(np.uint8)
        found, th = lsq.grid_start(t[j], ox[j], oy[j], z[j], vu8, k + 1)
        if not found:
            continue
        grid[q] = th
        ok[q] = 1
        info = np.zeros((4, 4))
        s2 = max(sigma[j], 1e-4) ** 2
        for i in range(k + 1):
            if valid[j, i] == 0:
                continue
            dx = tx[j, i] - ox[j, i]
            dy = ty[j, i] - oy[j, i]
            rho2 = max(dx * dx + dy * dy, 1e-12)
            g0 = dy / rho2
            g1 = -dx / rho2
            g2 = t[j, i] * dy / rho2
            g3 = -t[j, i] * dx / rho2
            gv = (g0, g1, g2, g3)
            for a in range(4):
                for b in range(4):
                    info[a, b] += gv[a] * gv[b] / s2
        d = np.empty(4)
        for a in range(4):
            d[a] = math.sqrt(max(info[a, a], 1e-300))
        m = np.empty((4, 4))
        inv = np.zeros((4, 4))
        for a in range(4):
            inv[a, a] = 1.0
            for b in range(4):
                m[a, b] = info[a, b] / (d[a] * d[b])
        # Gauss–Jordan on the Jacobi-scaled matrix (unit diagonal, eigenvalues ≤ 4): a pivot at
        # or below 1/SINGULAR_COND means the bound is singular.
        singular = False
        for col in range(4):
            piv = m[col, col]
            if piv <= 1.0 / SINGULAR_COND:
                singular = True
                break
            for b in range(4):
                m[col, b] /= piv
                inv[col, b] /= piv
            for a in range(4):
                if a != col:
                    f = m[a, col]
                    for b in range(4):
                        m[a, b] -= f * m[col, b]
                        inv[a, b] -= f * inv[col, b]
        if singular:
            continue
        c = np.empty((4, 4))
        for a in range(4):
            for b in range(4):
                c[a, b] = inv[a, b] / (d[a] * d[b])
        tk = t[j, k]
        # state map at k: x = x0 + vx t, y = y0 + vy t (explicit products: no BLAS in numba)
        gm = np.zeros((4, 4))
        for a in range(4):
            gm[a, a] = 1.0
        gm[0, 2] = tk
        gm[1, 3] = tk
        for a in range(4):
            for b in range(4):
                acc = 0.0
                for u in range(4):
                    for w in range(4):
                        acc += gm[a, u] * c[u, w] * gm[b, w]
                cov[q, a, b] = acc
        ok[q] = 2
    return grid, cov, ok


def scenario_tensors(batch: Batch, seed: int, draws: int) -> ScenarioTensors:
    zs = [renoise(batch, seed, d) for d in range(draws)]
    n = len(batch)
    rep = np.tile(np.arange(n), draws)
    return ScenarioTensors(
        scenario=rep,
        draw=np.repeat(np.arange(draws), n),
        bearing=np.concatenate(zs, axis=0),
        valid=np.tile(batch.valid.astype(np.float64), (draws, 1)),
        ox=np.tile(batch.own[..., 0].astype(np.float64), (draws, 1)),
        oy=np.tile(batch.own[..., 1].astype(np.float64), (draws, 1)),
        t=np.tile(batch.t.astype(np.float64), (draws, 1)),
        sigma=np.tile(batch.sigma.astype(np.float64), draws),
    )


def choose_rows(
    batch: Batch, s: int, rng: np.random.Generator, per_scenario: int, all_rows: bool
) -> list[int]:
    """The scored rows of scenario s: every post-zig row (``all_rows``), or the gate rows plus
    random post-zig rows up to ``per_scenario``."""
    n = int(batch.samples[s])
    zig = int(batch.zig_index[s])
    post = list(range(zig + 1, n))
    if all_rows or not post:
        return post
    dt = float(batch.t[s, 1] - batch.t[s, 0]) if n > 1 else 10.0
    gate = [zig + int(round(sec / dt)) for sec in GATE_ROWS_S]
    chosen = [k for k in gate if k < n]
    rest = [k for k in post if k not in chosen]
    extra = max(per_scenario - len(chosen), 0)
    if rest and extra:
        chosen += [int(v) for v in rng.choice(rest, size=min(extra, len(rest)), replace=False)]
    return sorted(chosen)


def row_batch(
    batch: Batch,
    tensors: ScenarioTensors,
    rng: np.random.Generator,
    per_scenario: int = 4,
    all_rows: bool = False,
    keep_singular: bool = False,
) -> RowBatch:
    """Scored rows for every (scenario, draw); the same rows for every draw of a scenario.
    ``keep_singular`` keeps rows whose bound is singular (prediction scores every row; the bound
    is then NaN). Rows without a valid bearing up to k are always dropped."""
    rows = {s: choose_rows(batch, s, rng, per_scenario, all_rows) for s in range(len(batch))}
    src_l: list[int] = []
    ks_l: list[int] = []
    for j in range(tensors.bearing.shape[0]):
        for k in rows[int(tensors.scenario[j])]:
            src_l.append(j)
            ks_l.append(k)
    src = np.asarray(src_l, dtype=np.int64)
    ks = np.asarray(ks_l, dtype=np.int64)
    scen = tensors.scenario[src] if src.size else src
    tx = batch.tgt[..., 0].astype(np.float64)[tensors.scenario]
    ty = batch.tgt[..., 1].astype(np.float64)[tensors.scenario]
    grid, cov, ok = _row_kernel(
        tensors.t,
        tensors.ox,
        tensors.oy,
        tensors.bearing,
        tensors.valid,
        tx,
        ty,
        tensors.sigma,
        src,
        ks,
    )
    keep = (ok == 2) | (keep_singular & (ok == 1))
    src, ks, scen, grid, cov = src[keep], ks[keep], scen[keep], grid[keep], cov[keep]
    c = batch.tgt[scen, ks, 2].astype(np.float64)
    v = batch.tgt[scen, ks, 3].astype(np.float64)
    truth = (
        np.stack(
            [
                batch.tgt[scen, ks, 0].astype(np.float64),
                batch.tgt[scen, ks, 1].astype(np.float64),
                v * np.sin(c),
                v * np.cos(c),
            ],
            axis=1,
        )
        if src.size
        else np.zeros((0, 4))
    )
    return RowBatch(
        source=src,
        k=ks,
        theta_grid=grid.reshape(-1, 4),
        truth=truth.reshape(-1, 4),
        bound_cov=cov.reshape(-1, 4, 4),
        since_zig_s=batch.since_zig_s[scen, ks].astype(np.float64) if src.size else np.zeros(0),
    )
