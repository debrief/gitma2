"""Fisher information and Cramér–Rao bounds for bearings-only estimation.

For a model in which the target position at each sample is linear in parameters θ,
pᵢ = Bᵢ θ, with independent bearing noise σ, the Fisher information from valid bearings i ≤ k at
the true trajectory is I = Σ gᵢgᵢᵀ / σ², gᵢ = Bᵢᵀ (dy/ρ², −dx/ρ²). Bounds on range, course and speed
at row k follow by the delta method: var(f) ≥ ∇fᵀ I⁻¹ ∇f, with ∇f taken through the state map.

Three models (``CrbModel``):

- *full window*: constant velocity, θ = (x0, y0, vx, vy), all bearings up to k; the bound for a
  held-course target (Gate 1).
- *known manoeuvres*: the generator's manoeuvre kinematics (an arc at constant speed for a course
  change, constant acceleration for a speed change) with θ = (x0, y0, vx0, vy0, change_1 …): each
  manoeuvre's start time, duration and kind known, its size unknown; all bearings up to k. The
  bound for an estimator that knows when and how the target manoeuvred (the oracle's regime):
  position continuity carries the earlier legs across the manoeuvre. (Leaving the positions inside
  a manoeuvre free instead decouples the legs, which is no better than per leg.) Defined inside
  manoeuvres too; the positions' Jacobian is taken by central differences.
- *per leg*: constant velocity on the current leg's bearings only. A diagnostic: it ignores the
  earlier legs, so an estimator that knows the manoeuvre times can beat it (panel round 1).

Before the zig the information is singular. Singularity is judged on the Jacobi-scaled matrix
(condition number above 1e12), and directions the bearings cannot see (a dropout inside a
manoeuvre) are allowed only when the state at k does not depend on them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numba import njit

from tma2.sim.scenario import both_state

SINGULAR_COND = 1e12
MIN_SIGMA_RAD = 1e-4


@dataclass
class CrbRow:
    sd_range_rel: float
    sd_course_deg: float
    sd_speed_kt: float
    singular: bool
    # Bound on the covariance of (x, y, vx, vy) at the row, for losses normalised per component.
    state_cov: np.ndarray | None = None


def _information(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    valid: np.ndarray,
    start: int,
    k: int,
    t_ref: float,
    sigma: float,
) -> np.ndarray:
    info = np.zeros((4, 4))
    s2 = max(sigma, MIN_SIGMA_RAD) ** 2
    for i in range(start, k + 1):
        if valid[i] == 0:
            continue
        dx = tx[i] - ox[i]
        dy = ty[i] - oy[i]
        rho2 = dx * dx + dy * dy
        tau = t[i] - t_ref
        g = np.array([dy / rho2, -dx / rho2, tau * dy / rho2, -tau * dx / rho2])
        info += np.outer(g, g) / s2
    return info


def crb_at_row(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    tvx: float,
    tvy: float,
    valid: np.ndarray,
    start: int,
    k: int,
    sigma: float,
) -> CrbRow:
    """Bounds at row k from bearings in [start, k], anchored at t[start] (truth given)."""
    t_ref = float(t[start])
    info = _information(t, ox, oy, tx, ty, valid, start, k, t_ref, sigma)
    tau = float(t[k]) - t_ref
    # state map: p_k = (x0 + vx τ, y0 + vy τ), u_k = (vx, vy)
    g = np.array([[1.0, 0.0, tau, 0.0], [0.0, 1.0, 0.0, tau], [0.0, 0.0, 1.0, 0.0], [0, 0, 0, 1.0]])
    return _bound(info, g, tx[k] - ox[k], ty[k] - oy[k], tvx, tvy)


def _bound(info: np.ndarray, g: np.ndarray, dx: float, dy: float, tvx: float, tvy: float) -> CrbRow:
    """Delta-method bounds at row k from the information ``info`` [P,P] and the state map ``g``
    [4,P] (∂(p_k, u_k)/∂θ), at the true relative position (dx, dy) and velocity (tvx, tvy)."""
    singular = CrbRow(math.nan, math.nan, math.nan, True)
    d = np.diag(info).copy()
    if not np.all(np.isfinite(info)):
        return singular
    seen = d > 0
    if not seen.any():
        return singular
    # Parameters no bearing touches: the state must not depend on them.
    if np.any(np.abs(g[:, ~seen]) > 0):
        return singular
    sub = info[np.ix_(seen, seen)]
    scale = 1.0 / np.sqrt(d[seen])
    scaled = sub * np.outer(scale, scale)
    w, v = np.linalg.eigh(scaled)
    if w[-1] <= 0:
        return singular
    weak = w <= w[-1] / SINGULAR_COND
    gs = g[:, seen] * scale  # state map in scaled coordinates
    if weak.any():
        # Unseen combinations (e.g. a dropout inside a manoeuvre) are allowed only if the state
        # at k does not move along them.
        leak = np.abs(gs @ v[:, weak]).max()
        if leak > 1e-9 * max(np.abs(gs).max(), 1.0):
            return singular
    inv_w = np.where(weak, 0.0, 1.0 / np.where(weak, 1.0, w))
    cov_scaled = (v * inv_w) @ v.T
    cov_state = gs @ cov_scaled @ gs.T  # [4,4] covariance of (p_k, u_k)
    rng = math.hypot(dx, dy)
    speed = math.hypot(tvx, tvy)
    g_r = np.array([dx / rng, dy / rng, 0.0, 0.0])
    # course c = atan2(vx, vy): ∂c/∂vx = vy/s², ∂c/∂vy = −vx/s²
    g_c = np.array([0.0, 0.0, tvy / (speed * speed), -tvx / (speed * speed)])
    g_s = np.array([0.0, 0.0, tvx / speed, tvy / speed])
    var_r = float(g_r @ cov_state @ g_r)
    var_c = float(g_c @ cov_state @ g_c)
    var_s = float(g_s @ cov_state @ g_s)
    if min(var_r, var_c, var_s) < 0:
        return singular
    return CrbRow(
        sd_range_rel=math.sqrt(var_r) / rng,
        sd_course_deg=math.degrees(math.sqrt(var_c)),
        sd_speed_kt=math.sqrt(var_s) / (1852.0 / 3600.0),
        singular=False,
        state_cov=cov_state,
    )


Manoeuvre = tuple[str, float, float, float]
"""(kind, start s, duration s, second duration s): the second duration is the speed change's
for kind "both" (generator 0.6.0) and 0 otherwise."""


def param_kinds(mans: list[Manoeuvre]) -> list[str]:
    """The kind of each change parameter θ[4:], in order: "both" contributes a course change and
    then a speed change."""
    out: list[str] = []
    for kind, *_ in mans:
        out += ["course", "speed"] if kind == "both" else [kind]
    return out


def _pos_vel(
    theta: np.ndarray, t: float, mans: list[Manoeuvre]
) -> tuple[float, float, float, float]:
    """Target position and velocity at time t for θ = (x0, y0, vx0, vy0, change_1 …) under the
    generator's manoeuvre kinematics: a course change is an arc at constant speed, a speed change
    constant acceleration on a constant course (0.5.0), and "both" turns and accelerates at once
    (0.6.0, two parameters). ``mans`` holds ``Manoeuvre`` tuples in time order."""
    x, y = float(theta[0]), float(theta[1])
    s = math.hypot(float(theta[2]), float(theta[3]))
    c = math.atan2(float(theta[2]), float(theta[3]))
    now = 0.0
    p = 4
    for kind, ts, dur_a, dur_b in mans:
        if t <= ts:
            break
        x += s * math.sin(c) * (ts - now)
        y += s * math.cos(c) * (ts - now)
        dur = max(dur_a, dur_b) if kind == "both" else dur_a
        tau = min(t - ts, dur)
        if kind == "both":
            w = float(theta[p]) / dur_a
            dv = float(theta[p + 1])
            p += 2
            # the generator's own kinematics (1 s midpoint steps), so the bound models its truth
            x, y, c, s = both_state(x, y, c, s, w, dur_a, dv, abs(dv) / dur_b, dur_b, tau)
            now = ts + tau
            if t <= ts + dur:
                return x, y, s * math.sin(c), s * math.cos(c)
            continue
        ch = float(theta[p])
        p += 1
        if kind == "course":
            w = ch / dur
            if abs(w) < 1e-15:
                x += s * math.sin(c) * tau
                y += s * math.cos(c) * tau
            else:
                x += (s / w) * (math.cos(c) - math.cos(c + w * tau))
                y += (s / w) * (math.sin(c + w * tau) - math.sin(c))
                c += w * tau
        else:
            a = ch / dur
            dist = s * tau + 0.5 * a * tau * tau
            x += dist * math.sin(c)
            y += dist * math.cos(c)
            s += a * tau
        now = ts + tau
        if t <= ts + dur:
            return x, y, s * math.sin(c), s * math.cos(c)
    x += s * math.sin(c) * (t - now)
    y += s * math.cos(c) * (t - now)
    return x, y, s * math.sin(c), s * math.cos(c)


def manoeuvre_model(
    manoeuvres: list[dict[str, Any]], tx0: float, ty0: float, tvx0: float, tvy0: float
) -> tuple[np.ndarray, list[Manoeuvre]]:
    """θ at the truth and the ``Manoeuvre`` list from a scenario's ``parameters.target_manoeuvres``
    (duration = |change| / rate; kind "both" adds change2 / rate2 as a second parameter)."""
    mans = sorted(manoeuvres, key=lambda m: float(m["start_time_s"]))
    changes: list[float] = []
    spec: list[Manoeuvre] = []
    for m in mans:
        kind = str(m["kind"]).split(".")[-1]
        dur = abs(float(m["change"])) / float(m["rate"])
        changes.append(float(m["change"]))
        dur2 = 0.0
        if kind == "both":
            if not float(m.get("change2") or 0.0) or not float(m.get("rate2") or 0.0) > 0:
                raise ValueError("a 'both' manoeuvre needs a non-zero change2 and a positive rate2")
            changes.append(float(m["change2"]))
            dur2 = abs(float(m["change2"])) / float(m["rate2"])
        spec.append((kind, float(m["start_time_s"]), dur, dur2))
    theta = np.array([tx0, ty0, tvx0, tvy0] + changes)
    return theta, spec


_FD_STEP = (1.0, 1.0, 1e-3, 1e-3)  # m, m, m/s, m/s; changes: 1e-6 rad or 1e-4 m/s


def _model_jacobian(theta: np.ndarray, times: np.ndarray, mans: list[Manoeuvre]) -> np.ndarray:
    """∂(x, y, vx, vy)(t_i)/∂θ by central differences: [N, 4, P]."""
    n_p = theta.shape[0]
    out = np.empty((times.shape[0], 4, n_p))
    kinds = param_kinds(mans)
    for p in range(n_p):
        h = _FD_STEP[p] if p < 4 else (1e-6 if kinds[p - 4] == "course" else 1e-4)
        up = theta.copy()
        dn = theta.copy()
        up[p] += h
        dn[p] -= h
        for i, ti in enumerate(times):
            a = _pos_vel(up, float(ti), mans)
            b = _pos_vel(dn, float(ti), mans)
            out[i, :, p] = [(a[q] - b[q]) / (2 * h) for q in range(4)]
    return out


def crb_known_manoeuvres(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    tvx: np.ndarray,
    tvy: np.ndarray,
    valid: np.ndarray,
    manoeuvres: list[dict[str, Any]],
    rows: list[int],
    sigma: float,
) -> list[CrbRow]:
    """The known-manoeuvres bound (module docstring) at each of ``rows``: one pass builds the
    per-bearing information and accumulates it, so all rows of a scenario cost one Jacobian."""
    theta, mans = manoeuvre_model(
        manoeuvres, float(tx[0]), float(ty[0]), float(tvx[0]), float(tvy[0])
    )
    last = max(rows) if rows else -1
    jac = _model_jacobian(theta, t[: last + 1], mans)
    s2 = max(sigma, MIN_SIGMA_RAD) ** 2
    n_p = theta.shape[0]
    info = np.zeros((n_p, n_p))
    want = set(rows)
    out: dict[int, CrbRow] = {}
    for i in range(last + 1):
        if valid[i] != 0:
            dx = tx[i] - ox[i]
            dy = ty[i] - oy[i]
            rho2 = dx * dx + dy * dy
            gi = (dy / rho2) * jac[i, 0] - (dx / rho2) * jac[i, 1]
            info += np.outer(gi, gi) / s2
        if i in want:
            out[i] = _bound(
                info, jac[i], tx[i] - ox[i], ty[i] - oy[i], float(tvx[i]), float(tvy[i])
            )
    return [out[k] for k in rows]


def leg_start(spans: list[dict[str, Any]], k: int) -> int:
    """First row of the current leg: 0, or the end of the last manoeuvre that ended at or before k.
    A manoeuvre in progress at k makes the leg start at k (no information yet)."""
    start = 0
    for s in spans:
        if s["start_index"] <= k < s["end_index"]:
            return k
        if s["end_index"] <= k:
            start = max(start, int(s["end_index"]))
    return start


def crb_rows(
    own: np.ndarray,
    tgt: np.ndarray,
    obs: np.ndarray,
    sigma: float,
    zig_index: int,
    spans: list[dict[str, Any]] | None,
    rows: list[int],
    model: str | bool = "full_window",
    target_manoeuvres: list[dict[str, Any]] | None = None,
) -> list[CrbRow]:
    """Bounds at the given rows from pack arrays own/tgt [S,5] and obs [S,3]."""
    t = own[:, 0].astype(np.float64)
    ox = own[:, 1].astype(np.float64)
    oy = own[:, 2].astype(np.float64)
    tx = tgt[:, 1].astype(np.float64)
    ty = tgt[:, 2].astype(np.float64)
    course = tgt[:, 3].astype(np.float64)
    speed = tgt[:, 4].astype(np.float64)
    valid = (obs[:, 2] != 0).astype(np.uint8)
    out = []
    if isinstance(model, bool):  # legacy flag: per_leg
        model = "per_leg" if model else "full_window"
    if model not in ("full_window", "known_manoeuvres", "per_leg"):
        raise ValueError(f"unknown CRB model {model}")
    if model == "known_manoeuvres":
        if spans and not target_manoeuvres:
            # Data with manoeuvres but no drawn plan (generator 0.4.0's single turn): the bound
            # would silently be the constant-velocity one (P0 panel round 2).
            raise ValueError("known_manoeuvres needs the scenario's target_manoeuvres plan")
        tvx = speed * np.sin(course)
        tvy = speed * np.cos(course)
        # the numba path (tested equal to the Python reference, test_crb_fast): with generator
        # 0.6.0's ~25 manoeuvres per scenario the reference is too slow for whole splits
        codes = {"course": 0.0, "speed": 1.0, "both": 2.0}
        plan = list(target_manoeuvres or [])
        table = np.array(
            [
                [
                    codes[str(m["kind"]).split(".")[-1]],
                    float(m["start_time_s"]),
                    float(m["change"]),
                    float(m["rate"]),
                    float(m.get("change2") or 0.0),
                    float(m.get("rate2") or 0.0),
                ]
                for m in plan
            ],
            dtype=np.float64,
        ).reshape(len(plan), 6)
        if not plan:
            return crb_known_manoeuvres(t, ox, oy, tx, ty, tvx, tvy, valid, [], rows, sigma)
        return crb_known_manoeuvres_fast(t, ox, oy, tx, ty, tvx, tvy, valid, table, rows, sigma)
    for k in rows:
        vx = speed[k] * math.sin(course[k])
        vy = speed[k] * math.cos(course[k])
        start = leg_start(spans or [], k) if model == "per_leg" else 0
        out.append(crb_at_row(t, ox, oy, tx, ty, vx, vy, valid, start, k, sigma))
    return out


# --- numba port of the known-manoeuvres bound's Jacobian and information (spec 004 R5) ---------
# Same arithmetic as ``_pos_vel`` / ``_model_jacobian`` / the information loop above, for the
# training loss (two rows per scenario). Manoeuvres as a table [M, 5] (kind 0 course / 1 speed /
# 2 both, start s, duration s, change, second duration s), sorted by start time.


@njit(cache=True)
def _segment_nb(
    kind: float,
    x: float,
    y: float,
    c: float,
    s: float,
    p: int,
    theta: np.ndarray,
    dur_a: float,
    dur_b: float,
    tau: float,
) -> tuple[float, float, float, float]:
    """State ``tau`` s into one manoeuvre starting from (x, y, c, s); its parameters are θ[p] (and
    θ[p + 1] for kind 2)."""
    if kind == 2.0:
        dv = theta[p + 1]
        return both_state(x, y, c, s, theta[p] / dur_a, dur_a, dv, abs(dv) / dur_b, dur_b, tau)
    ch = theta[p]
    if kind == 0.0:
        w = ch / dur_a
        if abs(w) < 1e-15:
            return x + s * math.sin(c) * tau, y + s * math.cos(c) * tau, c, s
        return (
            x + (s / w) * (math.cos(c) - math.cos(c + w * tau)),
            y + (s / w) * (math.sin(c + w * tau) - math.sin(c)),
            c + w * tau,
            s,
        )
    a = ch / dur_a
    dist = s * tau + 0.5 * a * tau * tau
    return x + dist * math.sin(c), y + dist * math.cos(c), c, s + a * tau


@njit(cache=True)
def _manoeuvre_states_nb(
    theta: np.ndarray, mans: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """For θ: each manoeuvre's state at its start and at its end [M, 4] (x, y, course, speed), its
    duration [M] and its first parameter index [M]. Computed once per θ, so a time inside or
    after a manoeuvre costs at most that manoeuvre's own integration, not every earlier one's."""
    m_n = mans.shape[0]
    starts = np.zeros((m_n, 4))
    ends = np.zeros((m_n, 4))
    durs = np.zeros(m_n)
    pidx = np.zeros(m_n, dtype=np.int64)
    x, y = theta[0], theta[1]
    s = math.hypot(theta[2], theta[3])
    c = math.atan2(theta[2], theta[3])
    now = 0.0
    p = 4
    for j in range(m_n):
        kind = mans[j, 0]
        ts = mans[j, 1]
        dur = max(mans[j, 2], mans[j, 4]) if kind == 2.0 else mans[j, 2]
        x += s * math.sin(c) * (ts - now)
        y += s * math.cos(c) * (ts - now)
        starts[j, 0], starts[j, 1], starts[j, 2], starts[j, 3] = x, y, c, s
        pidx[j] = p
        x, y, c, s = _segment_nb(kind, x, y, c, s, p, theta, mans[j, 2], mans[j, 4], dur)
        ends[j, 0], ends[j, 1], ends[j, 2], ends[j, 3] = x, y, c, s
        durs[j] = dur
        p += 2 if kind == 2.0 else 1
        now = ts + dur
    return starts, ends, durs, pidx


@njit(cache=True)
def _pos_vel_nb(
    theta: np.ndarray,
    t: float,
    mans: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
    durs: np.ndarray,
    pidx: np.ndarray,
) -> tuple[float, float, float, float]:
    """Target position and velocity at t (as ``_pos_vel``), from ``_manoeuvre_states_nb``."""
    last = -1
    for j in range(mans.shape[0]):
        if t <= mans[j, 1]:
            break
        last = j
    if last < 0:
        s = math.hypot(theta[2], theta[3])
        c = math.atan2(theta[2], theta[3])
        x = theta[0] + s * math.sin(c) * t
        y = theta[1] + s * math.cos(c) * t
        return x, y, s * math.sin(c), s * math.cos(c)
    ts = mans[last, 1]
    if t <= ts + durs[last]:
        x, y, c, s = _segment_nb(
            mans[last, 0],
            starts[last, 0],
            starts[last, 1],
            starts[last, 2],
            starts[last, 3],
            pidx[last],
            theta,
            mans[last, 2],
            mans[last, 4],
            t - ts,
        )
        return x, y, s * math.sin(c), s * math.cos(c)
    x, y, c, s = ends[last, 0], ends[last, 1], ends[last, 2], ends[last, 3]
    rest = t - (ts + durs[last])
    x += s * math.sin(c) * rest
    y += s * math.cos(c) * rest
    return x, y, s * math.sin(c), s * math.cos(c)


@njit(cache=True)
def known_manoeuvre_information(
    theta: np.ndarray,
    mans: np.ndarray,
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    valid: np.ndarray,
    rows: np.ndarray,
    sigma: float,
) -> tuple[np.ndarray, np.ndarray]:
    """(information [Q, P, P] accumulated up to each of ``rows`` (ascending), state map
    [Q, 4, P] at each row): the inputs of ``_bound``."""
    n_p = theta.shape[0]
    q_n = rows.shape[0]
    last = rows[q_n - 1]
    s2 = max(sigma, MIN_SIGMA_RAD) ** 2
    info = np.zeros((n_p, n_p))
    out_i = np.zeros((q_n, n_p, n_p))
    out_g = np.zeros((q_n, 4, n_p))
    jac = np.zeros((4, n_p))
    up = theta.copy()
    dn = theta.copy()
    pk = np.zeros(max(n_p - 4, 1))  # 0 course-like step, 1 speed-like step, per change parameter
    m = 0
    for j in range(mans.shape[0]):
        if mans[j, 0] == 2.0:
            pk[m] = 0.0
            pk[m + 1] = 1.0
            m += 2
        else:
            pk[m] = mans[j, 0]
            m += 1
    # Jacobian at every row, one parameter at a time, so each perturbed θ's manoeuvre states are
    # computed once (a "both" manoeuvre is integrated numerically; spec 006 review).
    jac_all = np.zeros((last + 1, 4, n_p))
    for p in range(n_p):
        if p < 4:
            h = 1.0 if p < 2 else 1e-3
        else:
            h = 1e-6 if pk[p - 4] == 0.0 else 1e-4
        up[p] = theta[p] + h
        dn[p] = theta[p] - h
        su, eu, du, iu = _manoeuvre_states_nb(up, mans)
        sd_, ed, dd, id_ = _manoeuvre_states_nb(dn, mans)
        for i in range(last + 1):
            a = _pos_vel_nb(up, t[i], mans, su, eu, du, iu)
            b = _pos_vel_nb(dn, t[i], mans, sd_, ed, dd, id_)
            jac_all[i, 0, p] = (a[0] - b[0]) / (2 * h)
            jac_all[i, 1, p] = (a[1] - b[1]) / (2 * h)
            jac_all[i, 2, p] = (a[2] - b[2]) / (2 * h)
            jac_all[i, 3, p] = (a[3] - b[3]) / (2 * h)
        up[p] = theta[p]
        dn[p] = theta[p]
    q = 0
    for i in range(last + 1):
        jac[:, :] = jac_all[i]
        if valid[i] != 0:
            dx = tx[i] - ox[i]
            dy = ty[i] - oy[i]
            rho2 = dx * dx + dy * dy
            for a_ in range(n_p):
                ga = (dy / rho2) * jac[0, a_] - (dx / rho2) * jac[1, a_]
                for b_ in range(n_p):
                    gb = (dy / rho2) * jac[0, b_] - (dx / rho2) * jac[1, b_]
                    info[a_, b_] += ga * gb / s2
        while q < q_n and rows[q] == i:
            out_i[q] = info
            out_g[q] = jac
            q += 1
    return out_i, out_g


def crb_known_manoeuvres_fast(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    tvx: np.ndarray,
    tvy: np.ndarray,
    valid: np.ndarray,
    tm: np.ndarray,
    rows: list[int],
    sigma: float,
) -> list[CrbRow]:
    """``crb_known_manoeuvres`` with the manoeuvres as the generator's table ``tm`` [M, ≥ 4]
    (kind 0 course / 1 speed / 2 both, start_time_s, change, rate[, change2, rate2]) and the
    Jacobian in numba."""
    order = np.argsort(tm[:, 1], kind="stable")
    tms = tm[order]
    both = tms[:, 0] == 2.0
    dur2 = np.zeros(tms.shape[0])
    if both.any():
        if tms.shape[1] < 6:
            raise ValueError("a 'both' manoeuvre needs the six-column table (change2, rate2)")
        if np.any(tms[both, 4] == 0.0) or np.any(tms[both, 5] <= 0.0):
            raise ValueError("a 'both' manoeuvre needs a non-zero change2 and a positive rate2")
        dur2[both] = np.abs(tms[both, 4]) / tms[both, 5]
    mans = np.stack([tms[:, 0], tms[:, 1], np.abs(tms[:, 2]) / tms[:, 3], tms[:, 2], dur2], axis=1)
    changes: list[float] = []
    for r in range(tms.shape[0]):
        changes.append(float(tms[r, 2]))
        if both[r]:
            changes.append(float(tms[r, 4]))
    theta = np.concatenate([[tx[0], ty[0], tvx[0], tvy[0]], changes]).astype(np.float64)
    want = sorted(set(rows))
    info, g = known_manoeuvre_information(
        theta,
        np.ascontiguousarray(mans, dtype=np.float64),
        t.astype(np.float64),
        ox.astype(np.float64),
        oy.astype(np.float64),
        tx.astype(np.float64),
        ty.astype(np.float64),
        valid.astype(np.float64),
        np.asarray(want, dtype=np.int64),
        float(sigma),
    )
    by_row = {
        k: _bound(info[q], g[q], tx[k] - ox[k], ty[k] - oy[k], float(tvx[k]), float(tvy[k]))
        for q, k in enumerate(want)
    }
    return [by_row[k] for k in rows]
