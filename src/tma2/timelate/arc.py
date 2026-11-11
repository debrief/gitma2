"""The arc-model solve (spec 013, owner decision 2026-11-11 after the first checkpoint).

A classical least-squares fit of a whole period's bearings to a target that holds course and
speed on legs and, between each manoeuvre's two times, changes course at a constant rate and
speed at a constant rate (Annex B's manoeuvres; the generator's, with a "both" manoeuvre's two
changes sharing one duration). The unknowns are the state at the period's start (position,
course, speed) and, per manoeuvre, a course change and a speed change: two per manoeuvre where
the physics layer's chord has four. ``free`` says which of the two each manoeuvre may use, so a
manoeuvre told (or judged) to be a turn costs one unknown, as in the Cramér–Rao bound's model.

NumPy, documentation of record; nothing here is trained. The fit is Levenberg–Marquardt with a
finite-difference Jacobian from a start the caller supplies (usually the chord solve's track).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SUB = 5  # midpoint steps per row for the position integral
_STEP = (1.0, 1.0, 1e-6, 1e-4)  # m, m, rad, m/s
MIN_SPEED = 0.05  # m/s; the speed profile is floored here so course stays defined
MAX_TURN = 3.0  # rad: a manoeuvre's course change stays below half a turn (Annex B: at most 120°)
MAX_SPEED_CHANGE = 6.0  # m/s per manoeuvre (Annex B: at most 6 kt, about 3.1 m/s)
MAX_ANGLE_STEP = 0.5  # rad per iteration, on any course parameter (stops a turn winding round)


@dataclass
class ArcFit:
    theta: np.ndarray  # [4 + 2M]: x0, y0, course0, speed0, then (Δcourse, Δspeed) per manoeuvre
    cost: float  # Σ (residual / σ)² over valid bearings
    states: np.ndarray  # [N, 4] x, y, vx, vy at the fit's times
    iterations: int


def arc_states(theta: np.ndarray, times: np.ndarray, spans: np.ndarray) -> np.ndarray:
    """[N, 4] target states at ``times`` (ascending, ``times[0]`` is where θ's position holds)
    for manoeuvres ``spans`` [M, 2] (start s, end s; end > start)."""
    m = spans.shape[0]
    d = theta[4:].reshape(m, 2)
    n = times.shape[0]
    frac = (np.arange(SUB) + 0.5) / SUB
    mid = (times[:-1, None] + np.diff(times)[:, None] * frac[None, :]).ravel()
    tt = np.concatenate([times, mid])
    if m:
        ramp = np.clip((tt[:, None] - spans[None, :, 0]) / (spans[:, 1] - spans[:, 0]), 0.0, 1.0)
        c = theta[2] + ramp @ d[:, 0]
        s = theta[3] + ramp @ d[:, 1]
    else:
        c = np.full(tt.shape, theta[2])
        s = np.full(tt.shape, theta[3])
    s = np.maximum(s, MIN_SPEED)
    vx, vy = s * np.sin(c), s * np.cos(c)
    w = np.repeat(np.diff(times) / SUB, SUB)
    px = np.concatenate([[0.0], np.cumsum((vx[n:] * w).reshape(n - 1, SUB).sum(axis=1))])
    py = np.concatenate([[0.0], np.cumsum((vy[n:] * w).reshape(n - 1, SUB).sum(axis=1))])
    out: np.ndarray = np.stack([theta[0] + px, theta[1] + py, vx[:n], vy[:n]], axis=1)
    return out


def start_from_track(states: np.ndarray, times: np.ndarray, spans: np.ndarray) -> np.ndarray:
    """θ from any track [N, 4]: the state at the first row and, per manoeuvre, the change in
    course and speed between the rows at its two times."""

    def cs(i: int) -> tuple[float, float]:
        return (
            float(np.arctan2(states[i, 2], states[i, 3])),
            float(np.hypot(states[i, 2], states[i, 3])),
        )

    c0, s0 = cs(0)
    th = [float(states[0, 0]), float(states[0, 1]), c0, max(s0, MIN_SPEED)]
    for a, b in spans:
        ia = int(np.searchsorted(times, a, side="right")) - 1
        ib = min(int(np.searchsorted(times, b, side="left")), times.shape[0] - 1)
        ca, sa = cs(max(ia, 0))
        cb, sb = cs(ib)
        th += [(cb - ca + np.pi) % (2 * np.pi) - np.pi, sb - sa]
    return np.array(th, dtype=np.float64)


def _allowed(theta: np.ndarray) -> bool:
    """Bounds: speed positive on every leg, turns below half a turn, speed changes bounded."""
    speeds = theta[3] + np.concatenate([[0.0], np.cumsum(theta[5::2])])
    return bool(
        float(speeds.min()) > MIN_SPEED
        and float(np.abs(theta[4::2]).max(initial=0.0)) < MAX_TURN
        and float(np.abs(theta[5::2]).max(initial=0.0)) < MAX_SPEED_CHANGE
    )


def fit_arc(
    times: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    spans: np.ndarray,
    theta0: np.ndarray,
    free: np.ndarray | None = None,
    iterations: int = 40,
) -> ArcFit:
    """Least squares from ``theta0``. ``free`` [M, 2] (bool) marks the changes that may move;
    the others stay at their ``theta0`` values (0 for a change the manoeuvre does not have)."""
    m = spans.shape[0]
    mask = np.ones(4 + 2 * m, dtype=bool)
    if free is not None:
        mask[4:] = free.reshape(-1)
    idx = np.flatnonzero(mask)
    steps = np.array(list(_STEP) + [1e-6, 1e-4] * m)
    angle = np.zeros(4 + 2 * m, dtype=bool)
    angle[2] = True
    angle[4::2] = True
    v = valid.astype(bool)

    def resid(th: np.ndarray) -> np.ndarray:
        st = arc_states(th, times, spans)
        b = np.arctan2(st[:, 0] - ox, st[:, 1] - oy)
        out: np.ndarray = ((z - b + np.pi) % (2 * np.pi) - np.pi)[v] / sigma
        return out

    theta = theta0.astype(np.float64).copy()
    theta[3] = max(theta[3], 2 * MIN_SPEED)
    theta[4::2] = np.clip(theta[4::2], -0.95 * MAX_TURN, 0.95 * MAX_TURN)
    theta[5::2] = np.clip(theta[5::2], -0.95 * MAX_SPEED_CHANGE, 0.95 * MAX_SPEED_CHANGE)
    low = theta[3] + np.cumsum(theta[5::2])
    if low.size and float(low.min()) <= 2 * MIN_SPEED:  # a start that stops the target: no changes
        theta[5::2] = 0.0
    r = resid(theta)
    cost = float(r @ r)
    lam = 1e-3
    done = 0
    for it in range(1, iterations + 1):
        done = it
        jac = np.empty((r.size, idx.size))
        for q, p in enumerate(idx):
            up, dn = theta.copy(), theta.copy()
            up[p] += steps[p]
            dn[p] -= steps[p]
            jac[:, q] = (resid(up) - resid(dn)) / (2 * steps[p])
        a = jac.T @ jac
        g = -jac.T @ r
        dg = np.maximum(np.diag(a), 1e-30)
        gain = -1.0
        for _ in range(8):
            try:
                step = np.linalg.solve(a + lam * np.diag(dg), g)
            except np.linalg.LinAlgError:
                lam *= 10
                continue
            big = float(np.abs(step[angle[idx]]).max(initial=0.0))
            if big > MAX_ANGLE_STEP:
                step = step * (MAX_ANGLE_STEP / big)
            trial = theta.copy()
            trial[idx] += step
            if _allowed(trial):
                r2 = resid(trial)
                c2 = float(r2 @ r2)
                if np.isfinite(c2) and c2 <= cost:
                    gain = cost - c2
                    theta, r, cost = trial, r2, c2
                    lam = max(lam / 10, 1e-12)
                    break
            lam *= 10
        if gain < 0 or gain < 1e-9 * max(cost, 1.0):
            break
    return ArcFit(theta, cost, arc_states(theta, times, spans), done)


def select_changes(
    times: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    spans: np.ndarray,
    full: ArcFit,
    threshold: float,
) -> tuple[ArcFit, np.ndarray]:
    """Backward elimination from the two-change fit: drop a manoeuvre's speed change (or its
    course change) while the cheapest drop raises the cost by less than ``threshold`` (a
    likelihood-ratio test on one parameter). Each manoeuvre keeps at least one change."""
    m = spans.shape[0]
    free = np.ones((m, 2), dtype=bool)
    best = full
    while True:
        cands = []
        for i in range(m):
            if not free[i].all():
                continue
            for j in (1, 0):
                f = free.copy()
                f[i, j] = False
                th = best.theta.copy()
                th[4 + 2 * i + j] = 0.0
                fit = fit_arc(times, ox, oy, z, valid, sigma, spans, th, f)
                cands.append((fit.cost - best.cost, i, j, fit))
        if not cands:
            break
        rise, i, j, fit = min(cands, key=lambda x: x[0])
        if rise >= threshold:
            break
        free[i, j] = False
        best = fit
    return best, free


TURN_STARTS = (-1.75, -0.8, 0.8, 1.75)  # rad: alternative course changes tried per manoeuvre
RANGE_STARTS = (0.5, 2.0)  # alternative scalings of the start's range from the ownship


def consistent(cost: float, n_valid: int, n_sd: float = 4.0) -> bool:
    """Whether a fit's cost is what the stated bearing error allows: below its expected value
    (the number of bearings) by more than, or above it by less than, ``n_sd`` standard
    deviations of a chi-square."""
    return cost <= n_valid + n_sd * float(np.sqrt(2.0 * n_valid))


def fit_arc_search(
    times: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    spans: np.ndarray,
    theta0: np.ndarray,
    free: np.ndarray | None = None,
    sweeps: int = 2,
) -> tuple[ArcFit, int]:
    """``fit_arc`` and a search over starts, keeping the lowest cost: each manoeuvre's course
    change replaced in turn by each of ``TURN_STARTS`` not near its current value (a second
    pass only if the first improved); and, where the cost is still not consistent with the
    bearing error, the range scaled. A consistent cost does not end the turn search: a mirror
    solution with one turn's sign wrong can be consistent. Returns the fit and the fits made."""
    n_valid = int(valid.astype(bool).sum())
    args = (times, ox, oy, z, valid, sigma, spans)
    best = fit_arc(*args, theta0, free)
    fits = 1
    m = spans.shape[0]

    def turn_sweeps(best: ArcFit, fits: int) -> tuple[ArcFit, int]:
        for _ in range(sweeps):
            improved = False
            for i in range(m):
                if free is not None and not free[i, 0]:
                    continue
                for dc in TURN_STARTS:
                    if abs(dc - best.theta[4 + 2 * i]) < 0.4:
                        continue
                    th = best.theta.copy()
                    th[4 + 2 * i] = dc
                    f = fit_arc(*args, th, free)
                    fits += 1
                    if f.cost < best.cost - 1e-3:
                        best, improved = f, True
            if not improved:
                break
        return best, fits

    best, fits = turn_sweeps(best, fits)
    if not consistent(best.cost, n_valid):
        for k in RANGE_STARTS:
            th = best.theta.copy()
            th[0] = ox[0] + k * (th[0] - ox[0])
            th[1] = oy[0] + k * (th[1] - oy[0])
            th[3] *= k
            f = fit_arc(*args, th, free)
            fits += 1
            if f.cost < best.cost - 1e-3:
                best, fits = turn_sweeps(f, fits)
    return best, fits


SELECT_THRESHOLD = 6.63  # chi-square(1) at 1%: the cost a second change must save to be kept


def solve_arc(
    times: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    spans: np.ndarray,
    start: np.ndarray,
    kinds: np.ndarray | None = None,
    threshold: float = SELECT_THRESHOLD,
) -> tuple[ArcFit, np.ndarray, int]:
    """The arc solve from a starting track [N, 4]. With ``kinds`` [M, 2] (which changes each
    manoeuvre has) the fit is the search over starts. Without, the kind is judged from the
    data: every manoeuvre is first fitted as a turn (the search), then every manoeuvre is given
    both changes, then changes are dropped while the bearings do not object
    (``select_changes``). Returns the fit, the changes in use [M, 2] and the fits made."""
    args = (times, ox, oy, z, valid, sigma, spans)
    th0 = start_from_track(start, times, spans)
    m = spans.shape[0]
    if kinds is not None:
        th0[4:][~kinds.reshape(-1)] = 0.0
        fit, n = fit_arc_search(*args, th0, kinds)
        return fit, kinds, n
    turn = np.zeros((m, 2), dtype=bool)
    turn[:, 0] = True
    th0[5::2] = 0.0
    first, n = fit_arc_search(*args, th0, turn)
    if m == 0:
        return first, turn, n
    both = fit_arc(*args, first.theta)
    n += 1
    if both.cost > first.cost:  # cannot happen from a converged start; keep the better
        both = first
    sel, free = select_changes(*args, both, threshold)
    return sel, free, n
