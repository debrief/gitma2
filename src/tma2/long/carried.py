"""The previous window as a prior (spec 027, owner 2026-11-18).

Spec 026's ``ctl-carry`` handed the previous window's track on only as a starting guess, so it
could change where the search began but not what it concluded. Here the previous window hands
on an **estimate with an uncertainty**: the target's position, course and speed at the next
window's first row (the hand-over time t_o), fitted on the previous window's bearings *before*
t_o only (the next window uses those from t_o on, so nothing is counted twice), together with
the prior that window itself received. The next window's fit and evidence then carry it as a
Gaussian term in the state at its start, so it can change which manoeuvre history is declared.

Pieces:

* ``CarriedPrior``: mean and precision of (x, y, course, speed) at the window's first row, in
  the window's frame.
* ``joint_fit_c`` / ``log_evidence_c``: ``timelate.retest.joint_fit`` / ``log_evidence`` with
  the carried residuals appended (fit), the carried Gaussian's log density added (evidence) and
  its Jacobian in the Laplace Hessian. The base prior's broad state factor stays beside it
  (nearly flat against the carried one). With ``cp=None`` both equal the originals exactly.
* ``evidence_search_c`` / ``elimination_path_c``: ``timelate.search.evidence_search`` and
  ``hedge.elimination_path`` on those two functions (copied: the originals are bound by earlier
  decision records and are not edited).
* ``hand_on``, ``widen``, ``to_frame``: the carried estimate, its widening for manoeuvres the
  bearings before t_o could not show and for a gap, and its move to the next window's frame.
* ``guard``: the χ² check of the carried prior against the window's own bearings.

Classical; nothing trained. NumPy, documentation of record.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.timelate.arc import MAX_ANGLE_STEP, TURN_STARTS, arc_states, fit_arc
from tma2.timelate.retest import (
    CLEAR,
    NEW_DURATION,
    TOP,
    Problem,
    Structure,
    _allowed,
    _clip,
    _jacobian,
    _pack,
    _resid,
    _steps,
    _unpack,
    candidates,
)
from tma2.timelate.search import KINDS, History

# χ²(4) upper quantiles (no scipy here): level → quantile
CHI2_4 = {0.05: 9.487729, 0.01: 13.276704, 0.001: 18.466827, 0.0001: 23.512742, 1e-5: 28.473255}


def _wrap(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class CarriedPrior:
    """Gaussian prior on θ[:4] = (x, y, course, speed) at the window's first row."""

    mean: np.ndarray  # [4]
    cov: np.ndarray  # [4, 4]

    @property
    def root(self) -> np.ndarray:
        """Lᵀ with L Lᵀ = precision, so that ‖Lᵀ d‖² = dᵀ P d."""
        p = np.linalg.inv(0.5 * (self.cov + self.cov.T))
        out: np.ndarray = np.linalg.cholesky(0.5 * (p + p.T)).T
        return out

    def residuals(self, theta: np.ndarray) -> np.ndarray:
        d = theta[:4] - self.mean
        d[2] = _wrap(float(d[2]))
        out: np.ndarray = self.root @ d
        return out

    def log_density(self, theta: np.ndarray) -> float:
        r = self.residuals(theta)
        _s, logdet_cov = np.linalg.slogdet(self.cov)
        return float(-0.5 * (r @ r) - 0.5 * logdet_cov - 2.0 * math.log(2.0 * math.pi))


def _residuals(
    pb: Problem,
    th: np.ndarray,
    sp: np.ndarray,
    kinds: np.ndarray,
    prior: Any,
    cp: CarriedPrior | None,
) -> np.ndarray:
    r = _resid(pb, th, sp)
    parts = [r]
    if prior is not None:
        from tma2.timelate.prior import prior_residuals

        parts.append(prior_residuals(prior, th, sp, kinds))
    if cp is not None:
        parts.append(cp.residuals(th))
    return parts[0] if len(parts) == 1 else np.concatenate(parts)


def joint_fit_c(
    pb: Problem,
    theta0: np.ndarray,
    spans0: np.ndarray,
    free_changes: np.ndarray | None = None,
    free_times: bool = True,
    iterations: int = 30,
    prior: Any = None,
    cp: CarriedPrior | None = None,
) -> Structure:
    """``retest.joint_fit`` with the carried residuals appended when ``cp`` is given."""
    m = spans0.shape[0]
    t_end = float(pb[0][-1])
    x = _pack(theta0.astype(np.float64), spans0.astype(np.float64))
    mask = np.ones(x.size, dtype=bool)
    if free_changes is not None:
        mask[4 : 4 + 2 * m] = free_changes.reshape(-1)
    if not free_times:
        mask[4 + 2 * m :] = False
    idx = np.flatnonzero(mask)
    angle = np.zeros(x.size, dtype=bool)
    angle[2] = True
    angle[4 : 4 + 2 * m : 2] = True

    kinds = np.ones((m, 2), dtype=bool) if free_changes is None else free_changes

    def f(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return _residuals(pb, th, sp, kinds, prior, cp)

    r = f(x)
    cost = float(r @ r)
    lam = 1e-3
    for _ in range(iterations):
        jac = _jacobian(f, x, r, idx, m)
        a = jac.T @ jac
        g = -jac.T @ r
        dg = np.maximum(np.diag(a), 1e-30)
        gain = -1.0
        for _try in range(8):
            try:
                step = np.linalg.solve(a + lam * np.diag(dg), g)
            except np.linalg.LinAlgError:
                lam *= 10
                continue
            big = float(np.abs(step[angle[idx]]).max(initial=0.0))
            if big > MAX_ANGLE_STEP:
                step = step * (MAX_ANGLE_STEP / big)
            trial = _clip(x, idx, step, m)
            if _allowed(trial, m, t_end):
                r2 = f(trial)
                c2 = float(r2 @ r2)
                if np.isfinite(c2) and c2 <= cost:
                    gain = cost - c2
                    x, r, cost = trial, r2, c2
                    lam = max(lam / 10, 1e-12)
                    break
            lam *= 10
        if gain < 0 or gain < 1e-7 * max(cost, 1.0):
            break
    theta, spans = _unpack(x, m)
    if prior is not None or cp is not None:
        rd = _resid(pb, theta, spans)
        cost = float(rd @ rd)
    return Structure(theta.copy(), spans.copy(), cost, arc_states(theta, pb[0], spans))


def _hessian(
    pb: Problem, s: Structure, kinds: np.ndarray, prior: Any, cp: CarriedPrior | None
) -> tuple[np.ndarray, np.ndarray]:
    """The Laplace Hessian over the free parameters (``log_evidence``'s) and their indices."""
    from tma2.timelate.prior import open_precision, prior_precision

    t, ox, oy, *_ = pb
    m = s.spans.shape[0]
    x = _pack(s.theta, s.spans)
    mask = np.ones(x.size, dtype=bool)
    mask[4 : 4 + 2 * m] = kinds.reshape(-1)
    idx = np.flatnonzero(mask)

    def f(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return _residuals(pb, th, sp, kinds, prior, cp)

    r = f(x)
    jac = _jacobian(f, x, r, idx, m)
    range0 = float(np.hypot(s.theta[0] - ox[0], s.theta[1] - oy[0]))
    if getattr(prior, "version", 1) >= 3:
        stand_in = open_precision(prior, s.theta, s.spans, kinds, range0, float(t[-1]))
    else:
        stand_in = prior_precision(prior, m, range0, float(t[-1]))
    return jac.T @ jac + np.diag(stand_in[idx]), idx


def log_evidence_c(
    pb: Problem, s: Structure, kinds: np.ndarray, prior: Any, cp: CarriedPrior | None = None
) -> dict[str, float]:
    """``retest.log_evidence`` with the carried Gaussian (part ``carried``) when ``cp`` is
    given."""
    from tma2.timelate.prior import LOG_2PI, log_prior

    t, ox, oy, *_ = pb
    h, idx = _hessian(pb, s, kinds, prior, cp)
    range0 = float(np.hypot(s.theta[0] - ox[0], s.theta[1] - oy[0]))
    _sign, logdet = np.linalg.slogdet(h)
    rd = _resid(pb, s.theta, s.spans)
    out = {"fit": -0.5 * float(rd @ rd)}
    out.update(log_prior(prior, s.theta, s.spans, kinds, float(t[-1]), range0))
    if cp is not None:
        out["carried"] = cp.log_density(s.theta)
    out["occam"] = 0.5 * idx.size * LOG_2PI - 0.5 * float(logdet)
    out["total"] = float(sum(out.values()))
    return out


# --- the search (timelate.search and hedge.elimination_path on the functions above) ---------


def _score(
    pb: Problem,
    theta: np.ndarray,
    spans: np.ndarray,
    kinds: np.ndarray,
    prior: Any,
    cp: CarriedPrior | None,
) -> History:
    th = theta.copy()
    th[4:][~kinds.reshape(-1)] = 0.0
    for i in range(spans.shape[0]):
        for j in range(2):
            if kinds[i, j] and th[4 + 2 * i + j] == 0.0:
                th[4 + 2 * i + j] = 0.5 if j == 0 else 1.0
    g = joint_fit_c(pb, th, spans, free_changes=kinds, prior=prior, cp=cp)
    ev = log_evidence_c(pb, g, kinds, prior, cp)
    total = ev["total"] if np.isfinite(ev["total"]) else -np.inf
    return History(g, kinds.copy(), float(total), ev)


def _additions(pb: Problem, h: History, prior: Any, cp: CarriedPrior | None) -> list[History]:
    t, ox, oy, z, v, sigma = pb
    picked: list[float] = []
    for _s, c in candidates(pb, h.fit):
        if all(abs(c - q) >= 2 * CLEAR for q in picked):
            picked.append(c)
        if len(picked) == TOP:
            break
    out: list[History] = []
    for c in picked:
        a, b = c - NEW_DURATION / 2, c + NEW_DURATION / 2
        m = h.fit.spans.shape[0]
        k = int(np.searchsorted(h.fit.spans[:, 0], a)) if m else 0
        spans = np.insert(h.fit.spans, k, [a, b], axis=0)
        best = None
        for dc in TURN_STARTS:
            th = np.insert(h.fit.theta, 4 + 2 * k, [dc, 0.0])
            g = fit_arc(t, ox, oy, z, v, sigma, spans, th)
            if best is None or g.cost < best.cost:
                best = g
        assert best is not None
        for kind in KINDS:
            kinds = np.insert(h.kinds, k, kind, axis=0)
            out.append(_score(pb, best.theta, spans, kinds, prior, cp))
    return out


def _removals(pb: Problem, h: History, prior: Any, cp: CarriedPrior | None) -> list[History]:
    out = []
    for i in range(h.fit.spans.shape[0]):
        th = np.delete(h.fit.theta, [4 + 2 * i, 5 + 2 * i])
        out.append(
            _score(
                pb,
                th,
                np.delete(h.fit.spans, i, axis=0),
                np.delete(h.kinds, i, axis=0),
                prior,
                cp,
            )
        )
    return out


def _rekind(pb: Problem, h: History, prior: Any, cp: CarriedPrior | None) -> list[History]:
    out = []
    for i in range(h.fit.spans.shape[0]):
        for kind in KINDS:
            if tuple(bool(x) for x in h.kinds[i]) == kind:
                continue
            kinds = h.kinds.copy()
            kinds[i] = kind
            out.append(_score(pb, h.fit.theta, h.fit.spans, kinds, prior, cp))
    return out


def evidence_search_c(
    pb: Problem,
    theta0: np.ndarray,
    spans0: np.ndarray,
    prior: Any,
    cp: CarriedPrior | None,
    max_manoeuvres: int = 10,
    steps: int = 12,
) -> tuple[History, list[History]]:
    """``timelate.search.evidence_search`` under the carried prior ``cp`` (None: the original)."""
    m = spans0.shape[0]
    kinds = np.zeros((m, 2), dtype=bool)
    kinds[:, 0] = True
    cur = _score(pb, theta0, spans0, kinds, prior, cp)
    seen = [cur]
    for _ in range(steps):
        moves = _removals(pb, cur, prior, cp) + _rekind(pb, cur, prior, cp)
        if cur.fit.spans.shape[0] < max_manoeuvres:
            moves += _additions(pb, cur, prior, cp)
        seen += moves
        if not moves:
            break
        best = max(moves, key=lambda x: x.evidence)
        if best.evidence <= cur.evidence + 1e-6:
            break
        cur = best
    return cur, seen


def elimination_path_c(
    pb: Problem, top: History, prior: Any, cp: CarriedPrior | None
) -> list[History]:
    """``hedge.elimination_path`` under the carried prior."""
    path = [top]
    while path[-1].fit.spans.shape[0]:
        moves = [h for h in _removals(pb, path[-1], prior, cp) if np.isfinite(h.evidence)]
        if not moves:
            break
        path.append(max(moves, key=lambda x: x.evidence))
    return path


# --- the hand-over --------------------------------------------------------------------------


@dataclass
class HandOn:
    """The carried estimate at t_o in the previous window's frame, before widening."""

    mean: np.ndarray  # x, y, course, speed
    cov: np.ndarray
    t_o: float  # s from the previous window's start
    t_last: float  # the last valid bearing before t_o (s, same origin)


def _state4(states: np.ndarray) -> np.ndarray:
    x, y, vx, vy = (float(v) for v in states[-1])
    return np.array([x, y, math.atan2(vx, vy), math.hypot(vx, vy)])


def hand_on(
    pb: Problem,
    hist: History,
    prior: Any,
    cp: CarriedPrior | None,
    t_o: float,
) -> HandOn | None:
    """The state at ``t_o`` under the declared history ``hist``, refitted on the bearings before
    ``t_o`` with the prior the window had (``prior`` and ``cp``), and its Laplace covariance.
    Manoeuvres that start within ``MIN_DURATION`` of ``t_o`` or later are dropped; one in
    progress at ``t_o`` ends there. None when there is nothing to fit."""
    from tma2.timelate.retest import MIN_DURATION

    t, ox, oy, z, v, sigma = pb
    i_o = int(np.searchsorted(t, t_o - 1e-6))
    if i_o <= 1 or i_o >= t.shape[0]:
        return None
    sl = slice(0, i_o + 1)
    vv = v[sl].astype(bool).copy()
    vv[-1] = False  # the bearing at t_o belongs to the next window
    if int(vv.sum()) < 12:
        return None
    pbt: Problem = (t[sl], ox[sl], oy[sl], z[sl], vv, sigma)
    tt = float(t[i_o])
    keep = [i for i in range(hist.fit.spans.shape[0]) if hist.fit.spans[i, 0] < tt - MIN_DURATION]
    spans = hist.fit.spans[keep].copy().reshape(-1, 2)
    if spans.shape[0]:
        spans[:, 1] = np.minimum(spans[:, 1], tt)
        spans[:, 1] = np.maximum(spans[:, 1], spans[:, 0] + MIN_DURATION)
    kinds = hist.kinds[keep].copy().reshape(-1, 2)
    theta = np.concatenate(
        [hist.fit.theta[:4]] + [hist.fit.theta[4 + 2 * i : 6 + 2 * i] for i in keep]
    )
    try:
        s = joint_fit_c(pbt, theta, spans, free_changes=kinds, prior=prior, cp=cp)
        h, idx = _hessian(pbt, s, kinds, prior, cp)
        sig = np.linalg.pinv(0.5 * (h + h.T))
    except (ValueError, np.linalg.LinAlgError):
        return None
    m = s.spans.shape[0]
    x = _pack(s.theta, s.spans)
    steps = _steps(m)

    def g(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return _state4(arc_states(th, pbt[0], sp))

    g0 = g(x)
    jg = np.empty((4, idx.size))
    for q, p in enumerate(idx):
        up = x.copy()
        up[p] += steps[p]
        d = g(up) - g0
        d[2] = _wrap(float(d[2]))
        jg[:, q] = d / steps[p]
    cov = jg @ sig @ jg.T
    cov = 0.5 * (cov + cov.T)
    if not (np.isfinite(g0).all() and np.isfinite(cov).all()):
        return None
    before = np.flatnonzero(vv)
    return HandOn(g0, cov, tt, float(t[before[-1]]))


def widen(
    ho: HandOn, prior: Any, scale: float, tail_s: float
) -> tuple[np.ndarray, dict[str, float]]:
    """The carried covariance widened: × ``scale`` (the Laplace covariance is overconfident),
    then course and speed variance for the manoeuvres the bearings before t_o could not show
    (Annex B's rates over τ = (t_o − last bearing) + ``tail_s``), and position variance for the
    gap's length g: (v²·Δvar_course + Δvar_speed)·g²/3."""
    cov = ho.cov * float(scale)
    gap = max(ho.t_o - ho.t_last, 0.0)
    tau = gap + float(tail_s)
    rho_c = (prior.w_course + prior.w_both) / prior.leg_mean
    rho_s = (prior.w_speed + prior.w_both) / prior.leg_mean
    a0, a1 = prior.angle
    v0, v1 = prior.dv
    e_c = (a0 * a0 + a0 * a1 + a1 * a1) / 3.0
    e_s = (v0 * v0 + v0 * v1 + v1 * v1) / 3.0
    dc, ds = rho_c * tau * e_c, rho_s * tau * e_s
    out = cov.copy()
    out[2, 2] += dc
    out[3, 3] += ds
    dp = (float(ho.mean[3]) ** 2 * dc + ds) * gap * gap / 3.0
    out[0, 0] += dp
    out[1, 1] += dp
    # a tiny floor keeps the precision finite where the fit pinned a direction exactly
    out += np.diag([1.0, 1.0, 1e-8, 1e-8])
    return out, {"gap_s": gap, "tau_s": tau, "add_course": dc, "add_speed": ds, "add_pos": dp}


def to_frame(mean: np.ndarray, origin_from: list[float], origin_to: list[float]) -> np.ndarray:
    """A carried mean moved from one window's frame (positions from its origin) to another's."""
    out = mean.copy()
    out[0] += float(origin_from[0]) - float(origin_to[0])
    out[1] += float(origin_from[1]) - float(origin_to[1])
    return out


def guard(pb: Problem, h: History, prior: Any, cp: CarriedPrior) -> float:
    """D: the posterior misfit of ``h`` (fitted with ``cp``) minus that of the same history
    refitted without ``cp``; about χ²(4) where the prior agrees with the bearings."""
    from tma2.timelate.prior import prior_residuals

    s1 = joint_fit_c(pb, h.fit.theta, h.fit.spans, free_changes=h.kinds, prior=prior, cp=None)

    def base(s: Structure) -> float:
        if prior is None:
            return 0.0
        r = prior_residuals(prior, s.theta, s.spans, h.kinds)
        return float(r @ r)

    rc = cp.residuals(h.fit.theta)
    with_cp = h.fit.cost + base(h.fit) + float(rc @ rc)
    without = s1.cost + base(s1)
    return float(with_cp - without)
