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


def _information_prefix(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    valid: np.ndarray,
    sigma: float,
) -> np.ndarray:
    """Fisher information of (x0, y0, vx, vy) from valid bearings 0 … k, for every k: [R, 4, 4]."""
    dx = tx - ox
    dy = ty - oy
    rho2 = np.maximum(dx * dx + dy * dy, 1e-12)
    g = np.stack([dy / rho2, -dx / rho2, t * dy / rho2, -t * dx / rho2], axis=1)
    g = g * valid[:, None]
    return np.asarray(np.cumsum(g[:, :, None] * g[:, None, :], axis=0) / max(sigma, 1e-4) ** 2)


def _bound(info: np.ndarray, tk: float) -> np.ndarray | None:
    d = np.sqrt(np.maximum(np.diag(info), 1e-300))
    scaled = info / np.outer(d, d)
    w, v = np.linalg.eigh(scaled)
    if w[0] <= w[-1] / SINGULAR_COND:
        return None
    cov = (v / w) @ v.T / np.outer(d, d)
    gmap = np.array([[1, 0, tk, 0], [0, 1, 0, tk], [0, 0, 1, 0], [0, 0, 0, 1.0]])
    return np.asarray(gmap @ cov @ gmap.T)


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
) -> RowBatch:
    """Scored rows for every (scenario, draw); the same rows for every draw of a scenario."""
    rows = {s: choose_rows(batch, s, rng, per_scenario, all_rows) for s in range(len(batch))}
    src, ks, grid, truth, cov, since = [], [], [], [], [], []
    infos: dict[int, np.ndarray] = {}
    for j in range(tensors.bearing.shape[0]):
        s = int(tensors.scenario[j])
        if s not in infos:
            tx = batch.tgt[s, :, 0].astype(np.float64)
            ty = batch.tgt[s, :, 1].astype(np.float64)
            infos[s] = _information_prefix(
                tensors.t[j],
                tensors.ox[j],
                tensors.oy[j],
                tx,
                ty,
                tensors.valid[j],
                float(tensors.sigma[j]),
            )
        valid_u8 = tensors.valid[j].astype(np.uint8)
        for k in rows[s]:
            bound = _bound(infos[s][k], float(tensors.t[j, k]))
            if bound is None:
                continue
            found, th = lsq.grid_start(
                tensors.t[j], tensors.ox[j], tensors.oy[j], tensors.bearing[j], valid_u8, k + 1
            )
            if not found:
                continue
            c = float(batch.tgt[s, k, 2])
            v = float(batch.tgt[s, k, 3])
            src.append(j)
            ks.append(k)
            grid.append(np.asarray(th, dtype=np.float64))
            truth.append(
                [
                    float(batch.tgt[s, k, 0]),
                    float(batch.tgt[s, k, 1]),
                    v * math.sin(c),
                    v * math.cos(c),
                ]
            )
            cov.append(bound)
            since.append(float(batch.since_zig_s[s, k]))
    return RowBatch(
        source=np.asarray(src, dtype=np.int64),
        k=np.asarray(ks, dtype=np.int64),
        theta_grid=np.asarray(grid, dtype=np.float64).reshape(-1, 4),
        truth=np.asarray(truth, dtype=np.float64).reshape(-1, 4),
        bound_cov=np.asarray(cov, dtype=np.float64).reshape(-1, 4, 4),
        since_zig_s=np.asarray(since, dtype=np.float64),
    )
