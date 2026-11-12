"""The full-period re-test on the arc cost (spec 013 research R6, after the owner's decision of
2026-11-11): a classical search for the manoeuvres of a whole period.

From any set of manoeuvre spans (C″'s transitions, or none) it repeats until nothing changes:

1. **Refine**: a joint least-squares fit of the arc model with every manoeuvre's start and
   duration free.
2. **Add**: a score test at candidate times on steady stretches (how much cost a small course
   or speed change there would save, given everything already fitted) picks a few candidates;
   each is fitted in full, and the best is added if it saves more than ``add_threshold``.
3. **Remove**: a manoeuvre whose removal costs less than ``add_threshold`` is removed.

Nothing is trained. The thresholds are chosen on tuning data and declared with the gate.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .arc import (
    MAX_ANGLE_STEP,
    MAX_SPEED_CHANGE,
    MAX_TURN,
    MIN_SPEED,
    TURN_STARTS,
    arc_states,
    fit_arc,
)

MIN_DURATION = 10.0  # s
MAX_DURATION = 900.0
NEW_DURATION = 90.0  # a candidate manoeuvre's starting duration
CANDIDATE_EVERY = 30.0  # s between candidate times
CLEAR = 60.0  # s a candidate keeps from existing manoeuvres and from the period's ends
TOP = 3  # candidates fitted in full per addition


@dataclass
class Structure:
    theta: np.ndarray  # [4 + 2M]
    spans: np.ndarray  # [M, 2] start s, end s
    cost: float
    states: np.ndarray
    log: list[dict[str, float | str]] = field(default_factory=list)


Problem = tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]
"""times, ownship x, ownship y, bearings, valid, sigma."""


def _resid(pb: Problem, theta: np.ndarray, spans: np.ndarray) -> np.ndarray:
    t, ox, oy, z, v, sigma = pb
    st = arc_states(theta, t, spans)
    b = np.arctan2(st[:, 0] - ox, st[:, 1] - oy)
    out: np.ndarray = ((z - b + np.pi) % (2 * np.pi) - np.pi)[v.astype(bool)] / sigma
    return out


def _unpack(x: np.ndarray, m: int) -> tuple[np.ndarray, np.ndarray]:
    theta = x[: 4 + 2 * m]
    start = x[4 + 2 * m : 4 + 3 * m]
    dur = x[4 + 3 * m :]
    return theta, np.stack([start, start + dur], axis=1).reshape(m, 2)


def _pack(theta: np.ndarray, spans: np.ndarray) -> np.ndarray:
    return np.concatenate([theta, spans[:, 0], spans[:, 1] - spans[:, 0]])


def _allowed(x: np.ndarray, m: int, t_end: float) -> bool:
    theta, spans = _unpack(x, m)
    speeds = theta[3] + np.concatenate([[0.0], np.cumsum(theta[5::2])])
    if float(speeds.min()) <= MIN_SPEED:
        return False
    if m == 0:
        return True
    dur = spans[:, 1] - spans[:, 0]
    return bool(
        float(np.abs(theta[4::2]).max()) < MAX_TURN
        and float(np.abs(theta[5::2]).max()) < MAX_SPEED_CHANGE
        and float(dur.min()) >= MIN_DURATION
        and float(dur.max()) <= MAX_DURATION
        and spans[0, 0] >= 0.0
        and spans[-1, 1] <= t_end
        and bool((spans[1:, 0] >= spans[:-1, 1]).all())
    )


def _clip(x: np.ndarray, idx: np.ndarray, step: np.ndarray, m: int) -> np.ndarray:
    """x + step with the changes and durations held just inside their bounds (a step that
    crosses a bound stops at it, where rejecting it would stall the fit)."""
    out = x.copy()
    out[idx] += step
    e = 1e-6
    out[4 : 4 + 2 * m : 2] = np.clip(out[4 : 4 + 2 * m : 2], -MAX_TURN + e, MAX_TURN - e)
    out[5 : 4 + 2 * m : 2] = np.clip(
        out[5 : 4 + 2 * m : 2], -MAX_SPEED_CHANGE + e, MAX_SPEED_CHANGE - e
    )
    out[4 + 3 * m :] = np.clip(out[4 + 3 * m :], MIN_DURATION, MAX_DURATION)
    return out


def _steps(m: int) -> np.ndarray:
    return np.array([1.0, 1.0, 1e-6, 1e-4] + [1e-6, 1e-4] * m + [0.5] * (2 * m))


def _jacobian(
    f: Callable[[np.ndarray], np.ndarray], x: np.ndarray, r: np.ndarray, idx: np.ndarray, m: int
) -> np.ndarray:
    steps = _steps(m)
    jac = np.empty((r.size, idx.size))
    for q, p in enumerate(idx):
        up = x.copy()
        up[p] += steps[p]
        jac[:, q] = (f(up) - r) / steps[p]
    return jac


def joint_fit(
    pb: Problem,
    theta0: np.ndarray,
    spans0: np.ndarray,
    free_changes: np.ndarray | None = None,
    free_times: bool = True,
    iterations: int = 30,
    prior: Any = None,
) -> Structure:
    """Least squares over the state, the changes and (``free_times``) every manoeuvre's start
    and duration, by Levenberg–Marquardt with forward differences. With ``prior`` the fit is
    to the posterior: the prior's Gaussian parts are appended as residuals
    (``prior.prior_residuals``); ``cost`` stays the bearings' cost alone."""
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
        r_data = _resid(pb, th, sp)
        if prior is None:
            return r_data
        from .prior import prior_residuals

        return np.concatenate([r_data, prior_residuals(prior, th, sp, kinds)])

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
    if prior is not None:
        rd = _resid(pb, theta, spans)
        cost = float(rd @ rd)
    return Structure(theta.copy(), spans.copy(), cost, arc_states(theta, pb[0], spans))


def candidates(pb: Problem, s: Structure) -> list[tuple[float, float]]:
    """(score, time) for candidate manoeuvre times, best first: the cost a small course and
    speed change at that time would save to first order, the fitted parameters re-adjusted."""
    t_end = float(pb[0][-1])
    m = s.spans.shape[0]
    x = _pack(s.theta, s.spans)

    def f(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return _resid(pb, th, sp)

    r = f(x)
    jac = _jacobian(f, x, r, np.arange(4 + 2 * m), m)
    q, _ = np.linalg.qr(jac)
    out = []
    for c in np.arange(CLEAR + NEW_DURATION / 2, t_end - CLEAR - NEW_DURATION / 2, CANDIDATE_EVERY):
        a, b = c - NEW_DURATION / 2, c + NEW_DURATION / 2
        if m and bool(((s.spans[:, 0] - CLEAR < b) & (s.spans[:, 1] + CLEAR > a)).any()):
            continue
        k = int(np.searchsorted(s.spans[:, 0], a)) if m else 0
        sp = np.insert(s.spans, k, [a, b], axis=0)
        cols = []
        for j, h in ((0, 1e-4), (1, 1e-3)):
            th = np.insert(s.theta, 4 + 2 * k, [0.0, 0.0])
            th[4 + 2 * k + j] = h
            cols.append((_resid(pb, th, sp) - r) / h)
        d = np.stack(cols, axis=1)
        d = d - q @ (q.T @ d)
        gram = d.T @ d
        rhs = -d.T @ r
        try:
            sol = np.linalg.solve(gram + 1e-12 * np.trace(gram) * np.eye(2), rhs)
        except np.linalg.LinAlgError:
            continue
        out.append((float(rhs @ sol), float(c)))
    return sorted(out, reverse=True)


def _insert(s: Structure, c: float, dc: float) -> tuple[np.ndarray, np.ndarray]:
    a, b = c - NEW_DURATION / 2, c + NEW_DURATION / 2
    m = s.spans.shape[0]
    k = int(np.searchsorted(s.spans[:, 0], a)) if m else 0
    return np.insert(s.theta, 4 + 2 * k, [dc, 0.0]), np.insert(s.spans, k, [a, b], axis=0)


def try_add(pb: Problem, s: Structure) -> Structure | None:
    """The best full fit with one more manoeuvre, from the top candidates of the score test
    (kept at least 2·CLEAR apart); None when there is no candidate."""
    picked: list[float] = []
    for _score, c in candidates(pb, s):
        if all(abs(c - p) >= 2 * CLEAR for p in picked):
            picked.append(c)
        if len(picked) == TOP:
            break
    best: Structure | None = None
    t, ox, oy, z, v, sigma = pb
    for c in picked:
        fixed = None
        for dc in TURN_STARTS:  # times fixed first: the new turn's size and sign
            th, sp = _insert(s, c, dc)
            g = fit_arc(t, ox, oy, z, v, sigma, sp, th)
            if fixed is None or g.cost < fixed[0].cost:
                fixed = (g, sp)
        if fixed is None:
            continue
        f = joint_fit(pb, fixed[0].theta, fixed[1])
        if f.cost > fixed[0].cost:
            f = Structure(fixed[0].theta, fixed[1], fixed[0].cost, fixed[0].states)
        if best is None or f.cost < best.cost:
            best = f
    return best


def try_remove(pb: Problem, s: Structure) -> tuple[Structure, int] | None:
    """The cheapest full fit with one manoeuvre fewer, and which."""
    best: tuple[Structure, int] | None = None
    for i in range(s.spans.shape[0]):
        th = np.delete(s.theta, [4 + 2 * i, 5 + 2 * i])
        f = joint_fit(pb, th, np.delete(s.spans, i, axis=0))
        if best is None or f.cost < best[0].cost:
            best = (f, i)
    return best


def retest(
    pb: Problem,
    theta0: np.ndarray,
    spans0: np.ndarray,
    add_threshold: float,
    max_manoeuvres: int = 12,
    rounds: int = 3,
) -> Structure:
    """The search described in the module's docstring. ``log`` records every accepted change
    (kind, time, cost saved or paid)."""
    s = joint_fit(pb, theta0, spans0)
    log: list[dict[str, float | str]] = []
    for _ in range(rounds):
        changed = False
        while s.spans.shape[0] < max_manoeuvres:
            new = try_add(pb, s)
            if new is None or s.cost - new.cost < add_threshold:
                break
            added = [float(a) for a in new.spans[:, 0] if not np.isclose(s.spans[:, 0], a).any()]
            log.append({"what": "add", "saved": s.cost - new.cost, "at": added[0] if added else -1})
            s, changed = new, True
        while s.spans.shape[0] > 0:
            rem = try_remove(pb, s)
            if rem is None or rem[0].cost - s.cost >= add_threshold:
                break
            log.append(
                {"what": "remove", "paid": rem[0].cost - s.cost, "at": float(s.spans[rem[1], 0])}
            )
            s, changed = rem[0], True
        if not changed:
            break
    s.log = log
    return s


def log_evidence(
    pb: Problem,
    s: Structure,
    kinds: np.ndarray,
    prior: Any,
) -> dict[str, float]:
    """Laplace's approximation to the log evidence of a history fitted **with the prior**
    (``joint_fit(..., prior=prior)``), by part: ``fit`` (−cost / 2), the prior's three parts
    at the fit, and ``occam`` (the volume the bearings and the prior leave). Evaluating the
    prior at a likelihood-only fit is wrong where the bearings leave a quantity loose (a
    manoeuvre's duration) and the prior is sharp (its rate)."""
    from .prior import LOG_2PI, log_prior, prior_precision, prior_residuals

    t, ox, oy, *_ = pb
    m = s.spans.shape[0]
    x = _pack(s.theta, s.spans)
    mask = np.ones(x.size, dtype=bool)
    mask[4 : 4 + 2 * m] = kinds.reshape(-1)
    idx = np.flatnonzero(mask)

    def f(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return np.concatenate([_resid(pb, th, sp), prior_residuals(prior, th, sp, kinds)])

    r = f(x)
    jac = _jacobian(f, x, r, idx, m)
    range0 = float(np.hypot(s.theta[0] - ox[0], s.theta[1] - oy[0]))
    h = jac.T @ jac + np.diag(prior_precision(prior, m, range0, float(t[-1]))[idx])
    _sign, logdet = np.linalg.slogdet(h)
    rd = _resid(pb, s.theta, s.spans)
    out = {"fit": -0.5 * float(rd @ rd)}
    out.update(log_prior(prior, s.theta, s.spans, kinds, float(t[-1]), range0))
    out["occam"] = 0.5 * idx.size * LOG_2PI - 0.5 * float(logdet)
    out["total"] = float(sum(out.values()))
    return out


def choose_kinds(
    pb: Problem, s: Structure, prior: Any
) -> tuple[Structure, np.ndarray, dict[str, float]]:
    """Each manoeuvre's kind (turn, speed change or both) by evidence, one manoeuvre at a time
    from all turns; the history refitted with the chosen changes."""
    m = s.spans.shape[0]
    kinds = np.zeros((m, 2), dtype=bool)
    kinds[:, 0] = True

    def fitted(k: np.ndarray) -> tuple[Structure, dict[str, float]]:
        th = s.theta.copy()
        th[4:][~k.reshape(-1)] = 0.0
        for i in range(m):  # a change switched on starts from a small value, not from zero
            for j in range(2):
                if k[i, j] and th[4 + 2 * i + j] == 0.0:
                    th[4 + 2 * i + j] = 0.5 if j == 0 else 1.0
        g = joint_fit(pb, th, s.spans, free_changes=k, prior=prior)
        return g, log_evidence(pb, g, k, prior)

    best, ev = fitted(kinds)
    for i in range(m):
        for alt in ((False, True), (True, True)):
            k = kinds.copy()
            k[i] = alt
            g, e = fitted(k)
            if e["total"] > ev["total"]:
                best, ev, kinds = g, e, k
    return best, kinds, ev


def ensemble(
    pb: Problem, s: Structure, prior: Any, more: int = 2
) -> tuple[list[Structure], np.ndarray, np.ndarray]:
    """Histories near a fitted one, with their posterior weights and the weighted mean track:
    the history itself, up to ``more`` further additions (taken whatever they save), and the
    history with each manoeuvre removed in turn. Kinds are chosen by evidence for each.
    A local stand-in for the posterior over histories: it holds the alternatives the bearings
    cannot rule out one step from the fit, not the whole space."""
    members: list[Structure] = [s]
    cur = s
    for _ in range(more):
        new = try_add(pb, cur)
        if new is None:
            break
        members.append(new)
        cur = new
    for i in range(s.spans.shape[0]):
        th = np.delete(s.theta, [4 + 2 * i, 5 + 2 * i])
        members.append(joint_fit(pb, th, np.delete(s.spans, i, axis=0)))
    fitted, logw = [], []
    for mem in members:
        g, _kinds, ev = choose_kinds(pb, mem, prior)
        fitted.append(g)
        logw.append(ev["total"])
    lw = np.array(logw)
    w = np.exp(lw - lw.max())
    w = w / w.sum()
    mean = np.zeros_like(fitted[0].states)
    for wi, g in zip(w, fitted, strict=True):
        mean += wi * g.states
    return fitted, w, mean
