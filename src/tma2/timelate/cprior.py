"""A carried prior across a gap (spec 028, development study).

Spec 027's carry handed the next period only a *start* for its search. Here the next period's
evidence gets a *prior* on its starting state θ0 = (x, y, course, speed): a Gaussian whose
mean is the previous period's declared state at its last row run forward through the gap at
constant velocity, and whose covariance is that state's Laplace covariance (from the previous
period's posterior fit), propagated through the gap, plus process noise for a manoeuvre the
gap may hide (Annex B's rate and sizes). The period's search then starts from the carried
state too (spec 027's start).

The prior replaces the state part of the standing evidence (range log-uniform, bearing and
course uniform, the first leg's speed soft-uniform) for the four starting parameters: their
Gaussian residuals enter the posterior fit and the Laplace Hessian, their stand-in volumes are
dropped, and their log density is the Gaussian's. Everything else (legs, changes, later
speeds) is unchanged.

``ctl``'s registered code is not edited. The evidence functions in ``retest`` import
``prior_residuals``, ``log_prior`` and ``open_precision`` from ``prior`` when they run; while a
carried solve runs (``carried_evidence()``), those three names are wrapped so that a
``CarriedPrior`` adds its state term, and any other prior goes to the original function
unchanged.
"""

from __future__ import annotations

import contextlib
import dataclasses
import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import numpy as np

from . import prior as prior_mod
from .arc import arc_states
from .prior import LOG_2PI, ManoeuvrePrior, _log_position, log_soft_uniform

FLOOR = np.array([25.0, 25.0, 1e-6, 1e-4])  # variance floor on (x, y, course, speed)


@dataclass(frozen=True)
class CarriedPrior(ManoeuvrePrior):
    """A manoeuvre prior with a Gaussian prior on θ0 (``mu``, inverse Cholesky ``linv``,
    ``logdet`` = log det(2π Σ))."""

    mu: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0)
    linv: tuple[tuple[float, ...], ...] = ()
    logdet: float = 0.0


def carried_prior(base: ManoeuvrePrior, mu: np.ndarray, cov: np.ndarray) -> CarriedPrior:
    c = 0.5 * (cov + cov.T) + np.diag(FLOOR)
    chol = np.linalg.cholesky(c)
    linv = np.linalg.inv(chol)
    _s, ld = np.linalg.slogdet(2.0 * math.pi * c)
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(ManoeuvrePrior)}
    return CarriedPrior(
        **fields,
        mu=tuple(float(u) for u in mu),
        linv=tuple(tuple(float(u) for u in row) for row in linv),
        logdet=float(ld),
    )


def _state_residuals(p: CarriedPrior, theta: np.ndarray) -> np.ndarray:
    d = np.asarray(theta[:4], dtype=np.float64) - np.asarray(p.mu)
    d[2] = (d[2] + math.pi) % (2.0 * math.pi) - math.pi
    out: np.ndarray = np.asarray(p.linv) @ d
    return out


_ORIG: dict[str, Any] = {
    "prior_residuals": prior_mod.prior_residuals,
    "log_prior": prior_mod.log_prior,
    "open_precision": prior_mod.open_precision,
}


def _prior_residuals(p: Any, theta: np.ndarray, spans: np.ndarray, kinds: np.ndarray) -> np.ndarray:
    out: np.ndarray = _ORIG["prior_residuals"](p, theta, spans, kinds)
    if isinstance(p, CarriedPrior):
        out = np.concatenate([out, _state_residuals(p, theta)])
    return out


def _log_prior(
    p: Any, theta: np.ndarray, spans: np.ndarray, kinds: np.ndarray, t_end: float, range0: float
) -> dict[str, float]:
    out: dict[str, float] = _ORIG["log_prior"](p, theta, spans, kinds, t_end, range0)
    if isinstance(p, CarriedPrior):
        r = _state_residuals(p, theta)
        out = dict(out)
        out["state"] = (
            out["state"]
            - log_soft_uniform(float(theta[3]), *p.speed)
            - _log_position(p, range0)
            - 0.5 * float(r @ r)
            - 0.5 * p.logdet
        )
    return out


def _open_precision(
    p: Any, theta: np.ndarray, spans: np.ndarray, kinds: np.ndarray, range0: float, t_end: float
) -> np.ndarray:
    out: np.ndarray = _ORIG["open_precision"](p, theta, spans, kinds, range0, t_end)
    if isinstance(p, CarriedPrior):
        out = out.copy()
        out[:4] = 0.0  # the Gaussian's residuals carry these four volumes
    return out


@contextlib.contextmanager
def carried_evidence() -> Iterator[None]:
    """Within this block, the evidence functions honour a ``CarriedPrior``."""
    prior_mod.prior_residuals = _prior_residuals
    prior_mod.log_prior = _log_prior
    prior_mod.open_precision = _open_precision
    try:
        yield
    finally:
        prior_mod.prior_residuals = _ORIG["prior_residuals"]
        prior_mod.log_prior = _ORIG["log_prior"]
        prior_mod.open_precision = _ORIG["open_precision"]


def end_state_covariance(pb: Any, fit: Any, kinds: np.ndarray, p: ManoeuvrePrior) -> np.ndarray:
    """[4, 4] Laplace covariance of the declared track's last state (x, y, vx, vy): the inverse
    of the posterior Hessian (bearings, the prior's residuals and its stand-in volumes) over
    the free parameters, mapped to the last row by finite differences."""
    from .retest import _jacobian, _pack, _resid, _steps, _unpack

    t, ox, oy = pb[0], pb[1], pb[2]
    m = fit.spans.shape[0]
    x = _pack(fit.theta, fit.spans)
    mask = np.ones(x.size, dtype=bool)
    mask[4 : 4 + 2 * m] = kinds.reshape(-1)
    idx = np.flatnonzero(mask)

    def f(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return np.concatenate([_resid(pb, th, sp), prior_mod.prior_residuals(p, th, sp, kinds)])

    def last(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        out: np.ndarray = arc_states(th, t, sp)[-1]
        return out

    r = f(x)
    jac = _jacobian(f, x, r, idx, m)
    range0 = float(np.hypot(fit.theta[0] - ox[0], fit.theta[1] - oy[0]))
    stand = prior_mod.open_precision(p, fit.theta, fit.spans, kinds, range0, float(t[-1]))
    h = jac.T @ jac + np.diag(stand[idx])
    cov = np.linalg.pinv(h)
    s0 = last(x)
    g = np.empty((4, idx.size))
    steps = _steps(m)
    for q, k in enumerate(idx):
        up = x.copy()
        up[k] += steps[k]
        g[:, q] = (last(up) - s0) / steps[k]
    out: np.ndarray = g @ cov @ g.T
    return out


def propagate(
    state: np.ndarray, cov: np.ndarray, gap_s: float, p: ManoeuvrePrior
) -> tuple[np.ndarray, np.ndarray]:
    """θ0's mean and covariance (x, y, course, speed) after ``gap_s`` seconds: constant velocity,
    plus Annex B's chance of a manoeuvre in the gap as isotropic process noise."""
    x, y, vx, vy = (float(u) for u in state)
    f = np.eye(4)
    f[0, 2] = f[1, 3] = gap_s
    mean = np.array([x + vx * gap_s, y + vy * gap_s, vx, vy])
    c = f @ cov @ f.T
    pm = 1.0 - math.exp(-gap_s / p.leg_mean)
    lo, hi = p.angle
    ea2 = (lo * lo + lo * hi + hi * hi) / 3.0
    lo, hi = p.dv
    ev2 = (lo * lo + lo * hi + hi * hi) / 3.0
    speed = math.hypot(vx, vy)
    var_v = pm * ((p.w_course + p.w_both) * speed * speed * ea2 + (p.w_speed + p.w_both) * ev2)
    q = 0.5 * var_v  # per axis
    qm = np.array([[gap_s**2 / 3.0, gap_s / 2.0], [gap_s / 2.0, 1.0]]) * q
    for a in range(2):
        idx = [a, a + 2]
        c[np.ix_(idx, idx)] += qm
    spd = max(math.hypot(mean[2], mean[3]), 1e-3)
    jt = np.zeros((4, 4))  # (x, y, vx, vy) -> (x, y, course, speed)
    jt[0, 0] = jt[1, 1] = 1.0
    jt[2, 2], jt[2, 3] = mean[3] / spd**2, -mean[2] / spd**2
    jt[3, 2], jt[3, 3] = mean[2] / spd, mean[3] / spd
    theta = np.array([mean[0], mean[1], math.atan2(mean[2], mean[3]), spd])
    return theta, jt @ c @ jt.T


__all__ = [
    "LOG_2PI",
    "CarriedPrior",
    "carried_evidence",
    "carried_prior",
    "end_state_covariance",
    "propagate",
]
