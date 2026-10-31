"""The generator-0.5.0 algorithm, ported from gitma ``packages/sim/src/scenario.ts`` (d0aec60).

Every function here is a numba ``njit`` over scalars and arrays, so a scenario is a pure function
of (dataset seed, index, ranges) and batches can run in parallel. The port keeps gitma's draw
order exactly, including draws that are consumed and discarded, and gitma's float32 rounding
points. Mapping to the source (gitma function → here):

| gitma (scenario.ts)       | here                      |
| ------------------------- | ------------------------- |
| ``drawManoeuvreCount``    | ``draw_manoeuvre_count``  |
| ``drawScenario``          | ``draw_scenario``         |
| ``planManoeuvres``        | ``plan_manoeuvres``       |
| ``planTargetManoeuvre``   | ``plan_target_manoeuvre`` |
| ``planTargetManoeuvres``  | ``plan_target_manoeuvres``|
| ``acrossLosTurn``         | ``across_los_turn``       |
| ``targetAt``              | ``target_at``             |
| ``simulateTwoLegs``       | ``simulate_two_legs``     |
| ``ownshipZig2``           | ``ownship_zig2``          |
| ``targetManoeuvre``       | ``target_manoeuvre``      |
| ``targetManoeuvres``      | ``target_manoeuvres``     |
| ``simulateTruth``         | ``simulate_truth``        |
| ``ranges`` (mean/min)     | ``range_stats``           |
| ``observe``               | ``observe``               |
| ``generateScenario``      | ``generate_into``         |

Parameters live in a float64 array ``P`` (``P_*`` indices; NaN = key absent) plus a manoeuvre
table ``tm[MAX_TM, 4]`` (kind, start_time_s, change, rate). Truth indices live in an int64 array
``TI`` (``TI_*`` indices; −1 = null) plus ``spans[MAX_TM, 3]`` (kind, start_index, end_index).
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit, uint64

from .geometry import (
    TWO_PI,
    arc_position,
    bearing_of,
    f32,
    f32_angle,
    js_round,
    turn_rows,
    wrap2pi,
    wrap_pi,
)
from .prng import create_rng, derive_seed, gaussian, log_uniform, uniform, uniform01, uniform_int
from .ranges import (
    R_ACC_MAX,
    R_ACC_MIN,
    R_ACROSS_LOS,
    R_DROPOUT_MAX,
    R_DROPOUT_MIN,
    R_DT,
    R_DV_MAX,
    R_DV_MIN,
    R_LOS_MAX,
    R_LOS_MIN,
    R_MIN_RANGE,
    R_N_SIGMA,
    R_N_WEIGHTS,
    R_OWN_SPEED_MAX,
    R_OWN_SPEED_MIN,
    R_RANGE0_MAX,
    R_RANGE0_MIN,
    R_RANGE_LOG_UNIFORM,
    R_SIGMA0,
    R_SPEED_CHANGE_FRACTION,
    R_TGT_SPEED_MAX,
    R_TGT_SPEED_MIN,
    R_TM_AFTER,
    R_TM_ANGLE_MAX,
    R_TM_ANGLE_MIN,
    R_TM_FRACTION,
    R_TM_MARGIN,
    R_TM_RATE_MAX,
    R_TM_RATE_MIN,
    R_TM_SPACING,
    R_TURN_RATE_MAX,
    R_TURN_RATE_MIN,
    R_WEIGHT0,
    R_WINDOW_MAX,
    R_WINDOW_MIN,
    R_ZIG2_DELAY_MAX,
    R_ZIG2_DELAY_MIN,
    R_ZIG_ABS_MAX,
    R_ZIG_ABS_MIN,
    R_ZIG_FRAC_MAX,
    R_ZIG_FRAC_MIN,
)

MAX_REDRAWS = 1000
MAX_TM = 4  # at most 3 course changes + 1 speed change

# Parameter array layout (ScenarioParameters); NaN means the optional key is absent.
P_WINDOW = 0
P_DT = 1
P_OWN_SPEED = 2
P_COURSE0 = 3
P_ZIG = 4
P_ZIG_FRAC = 5
P_RANGE0 = 6
P_BEARING0 = 7
P_TGT_SPEED = 8
P_TGT_COURSE = 9
P_SIGMA = 10
P_DROPOUT = 11
P_TURN_RATE = 12
P_ZIG2_DELAY = 13
P_ZIG2_ANGLE = 14
P_TM_TIME = 15  # generator 0.4.0 single turn
P_TM_ANGLE = 16
P_TM_RATE = 17
P_N_TM = 18  # generator 0.5.0: −1 key absent, else number of planned manoeuvres
P_LEN = 19

# Manoeuvre table columns.
TM_KIND = 0  # 0 course, 1 speed
TM_START = 1
TM_CHANGE = 2
TM_RATE = 3

# Truth index array layout; −1 means null.
TI_SAMPLES = 0
TI_ZIG = 1
TI_TURN_START = 2
TI_ZIG2 = 3
TI_TURN2_START = 4
TI_M_START = 5
TI_M_INDEX = 6
TI_N_SPANS = 7  # −1: manoeuvres key absent (older ranges); ≥ 0: number of spans
TI_LEN = 8


@njit(cache=True)
def draw_manoeuvre_count(scenario_seed: uint64, R: np.ndarray) -> tuple[int, bool]:
    """How many target course changes, and whether there is a speed change (own stream)."""
    n_w = int(R[R_N_WEIGHTS])
    s = create_rng(derive_seed(scenario_seed, 1))
    u = uniform01(s)
    course_changes = n_w - 1
    acc = 0.0
    for k in range(n_w):
        acc += R[R_WEIGHT0 + k]
        if u < acc:
            course_changes = k
            break
    speed_change = uniform01(s) < R[R_SPEED_CHANGE_FRACTION]
    return course_changes, speed_change


@njit(cache=True)
def target_at(P: np.ndarray, t: float) -> tuple[float, float]:
    """Target position at time t (constant velocity from its start)."""
    x = P[P_RANGE0] * math.sin(P[P_BEARING0]) + P[P_TGT_SPEED] * math.sin(P[P_TGT_COURSE]) * t
    y = P[P_RANGE0] * math.cos(P[P_BEARING0]) + P[P_TGT_SPEED] * math.cos(P[P_TGT_COURSE]) * t
    return x, y


@njit(cache=True)
def across_los_turn(
    ox: float, oy: float, course: float, tx: float, ty: float, offset: float
) -> float:
    """The across-the-line-of-sight turn: the target ends up ``offset`` off the other bow."""
    brg = bearing_of(tx - ox, ty - oy)
    rel = wrap_pi(brg - course)
    side = -1.0 if rel < 0 else 1.0
    return float(wrap_pi(brg + side * offset - course))


@njit(cache=True)
def simulate_two_legs(
    P: np.ndarray,
    own_x: np.ndarray,
    own_y: np.ndarray,
    own_c: np.ndarray,
    tgt_x: np.ndarray,
    tgt_y: np.ndarray,
    tgt_c: np.ndarray,
    tgt_v: np.ndarray,
    TI: np.ndarray,
) -> None:
    """Ownship two-leg motion and constant-velocity target (gitma ``simulateTwoLegs``)."""
    dt = P[P_DT]
    samples = js_round(P[P_WINDOW] / dt)
    zig_index = js_round(P[P_ZIG_FRAC] * samples)
    t_zig = zig_index * dt
    c0 = P[P_COURSE0]
    c1 = wrap2pi(c0 + P[P_ZIG])
    v = P[P_OWN_SPEED]
    zx = v * math.sin(c0) * t_zig
    zy = v * math.cos(c0) * t_zig
    tx0 = P[P_RANGE0] * math.sin(P[P_BEARING0])
    ty0 = P[P_RANGE0] * math.cos(P[P_BEARING0])
    tvx = P[P_TGT_SPEED] * math.sin(P[P_TGT_COURSE])
    tvy = P[P_TGT_SPEED] * math.cos(P[P_TGT_COURSE])
    for i in range(TI_LEN):
        TI[i] = -1
    TI[TI_SAMPLES] = samples
    TI[TI_ZIG] = zig_index
    for i in range(samples):
        t = i * dt
        tgt_x[i] = tx0 + tvx * t
        tgt_y[i] = ty0 + tvy * t
        tgt_c[i] = P[P_TGT_COURSE]
        tgt_v[i] = P[P_TGT_SPEED]
    rate = 0.0 if math.isnan(P[P_TURN_RATE]) else P[P_TURN_RATE]
    if not (rate > 0):
        for i in range(samples):
            t = i * dt
            if i < zig_index:
                own_x[i] = v * math.sin(c0) * t
                own_y[i] = v * math.cos(c0) * t
                own_c[i] = c0
            else:
                own_x[i] = zx + v * math.sin(c1) * (t - t_zig)
                own_y[i] = zy + v * math.cos(c1) * (t - t_zig)
                own_c[i] = c1
        return
    omega = (-1.0 if P[P_ZIG] < 0 else 1.0) * rate
    turn_s = abs(P[P_ZIG]) / rate
    ex, ey, _ec = arc_position(zx, zy, c0, v, omega, turn_s)
    leg2 = zig_index + 1
    while (leg2 - zig_index) * dt < turn_s:
        leg2 += 1
    TI[TI_TURN_START] = zig_index + 1
    TI[TI_ZIG] = leg2
    for i in range(samples):
        t = i * dt
        tau = t - t_zig
        if i <= zig_index:
            own_x[i] = v * math.sin(c0) * t
            own_y[i] = v * math.cos(c0) * t
            own_c[i] = c0
        elif i < leg2:
            ax, ay, ac = arc_position(zx, zy, c0, v, omega, tau)
            own_x[i] = ax
            own_y[i] = ay
            own_c[i] = ac
        else:
            own_x[i] = ex + v * math.sin(c1) * (tau - turn_s)
            own_y[i] = ey + v * math.cos(c1) * (tau - turn_s)
            own_c[i] = c1


@njit(cache=True)
def ownship_zig2(
    P: np.ndarray, own_x: np.ndarray, own_y: np.ndarray, own_c: np.ndarray, TI: np.ndarray
) -> None:
    """The second zig (generator 0.3.0) on a two-leg truth; unchanged when there is none."""
    if math.isnan(P[P_ZIG2_ANGLE]) or math.isnan(P[P_ZIG2_DELAY]):
        return
    zig2 = P[P_ZIG2_ANGLE]
    dt = P[P_DT]
    v = P[P_OWN_SPEED]
    samples = TI[TI_SAMPLES]
    k2 = TI[TI_ZIG] + js_round(P[P_ZIG2_DELAY] / dt)
    TI[TI_ZIG2] = k2
    if k2 >= samples:
        return
    t2 = k2 * dt
    x2 = own_x[k2]
    y2 = own_y[k2]
    c1 = own_c[k2]
    c2 = wrap2pi(c1 + zig2)
    rate = 0.0 if math.isnan(P[P_TURN_RATE]) else P[P_TURN_RATE]
    if not (rate > 0):
        for i in range(k2, samples):
            tau = i * dt - t2
            own_x[i] = x2 + v * math.sin(c2) * tau
            own_y[i] = y2 + v * math.cos(c2) * tau
            own_c[i] = c2
        return
    omega = (-1.0 if zig2 < 0 else 1.0) * rate
    turn_s = abs(zig2) / rate
    ex, ey, _ec = arc_position(x2, y2, c1, v, omega, turn_s)
    leg3 = k2 + 1
    while (leg3 - k2) * dt < turn_s:
        leg3 += 1
    TI[TI_TURN2_START] = k2 + 1
    TI[TI_ZIG2] = leg3
    for i in range(k2 + 1, samples):
        tau = i * dt - t2
        if i < leg3:
            ax, ay, ac = arc_position(x2, y2, c1, v, omega, tau)
            own_x[i] = ax
            own_y[i] = ay
            own_c[i] = ac
        else:
            own_x[i] = ex + v * math.sin(c2) * (tau - turn_s)
            own_y[i] = ey + v * math.cos(c2) * (tau - turn_s)
            own_c[i] = c2


@njit(cache=True)
def target_manoeuvre(
    P: np.ndarray, tgt_x: np.ndarray, tgt_y: np.ndarray, tgt_c: np.ndarray, TI: np.ndarray
) -> None:
    """The target's single course change (generator 0.4.0)."""
    time = P[P_TM_TIME]
    angle = P[P_TM_ANGLE]
    rate = P[P_TM_RATE]
    if math.isnan(time) or math.isnan(angle) or math.isnan(rate) or not (rate > 0):
        return
    dt = P[P_DT]
    samples = TI[TI_SAMPLES]
    k = js_round(time / dt)
    if k >= samples:
        return
    v = P[P_TGT_SPEED]
    c0 = P[P_TGT_COURSE]
    c1 = wrap2pi(c0 + angle)
    omega = (-1.0 if angle < 0 else 1.0) * rate
    turn_s = abs(angle) / rate
    x0 = tgt_x[k]
    y0 = tgt_y[k]
    ex, ey, _ec = arc_position(x0, y0, c0, v, omega, turn_s)
    leg = k + turn_rows(turn_s, dt)
    TI[TI_M_START] = k + 1
    TI[TI_M_INDEX] = leg
    for i in range(k + 1, samples):
        tau = (i - k) * dt
        if i < leg:
            ax, ay, ac = arc_position(x0, y0, c0, v, omega, tau)
            tgt_x[i] = ax
            tgt_y[i] = ay
            tgt_c[i] = ac
        else:
            tgt_x[i] = ex + v * math.sin(c1) * (tau - turn_s)
            tgt_y[i] = ey + v * math.cos(c1) * (tau - turn_s)
            tgt_c[i] = c1


@njit(cache=True)
def target_manoeuvres(
    P: np.ndarray,
    tm: np.ndarray,
    tgt_x: np.ndarray,
    tgt_y: np.ndarray,
    tgt_c: np.ndarray,
    tgt_v: np.ndarray,
    TI: np.ndarray,
    spans: np.ndarray,
) -> None:
    """The target's manoeuvres in order (generator 0.5.0): arcs and constant accelerations."""
    n_tm = int(P[P_N_TM])
    if n_tm < 0:
        return
    TI[TI_N_SPANS] = 0
    dt = P[P_DT]
    samples = TI[TI_SAMPLES]
    x = tgt_x[0]
    y = tgt_y[0]
    c = P[P_TGT_COURSE]
    v = P[P_TGT_SPEED]
    t0 = 0.0
    frm = 0
    n_spans = 0
    for j in range(n_tm):
        k = js_round(tm[j, TM_START] / dt)
        if k >= samples:
            break
        for i in range(frm, k + 1):
            tau = i * dt - t0
            tgt_x[i] = x + v * math.sin(c) * tau
            tgt_y[i] = y + v * math.cos(c) * tau
            tgt_c[i] = c
            tgt_v[i] = v
        ts = k * dt
        xs = x + v * math.sin(c) * (ts - t0)
        ys = y + v * math.cos(c) * (ts - t0)
        change = tm[j, TM_CHANGE]
        rate = tm[j, TM_RATE]
        dur = abs(change) / rate
        end = k + turn_rows(dur, dt)
        kind = int(tm[j, TM_KIND])
        spans[n_spans, 0] = kind
        spans[n_spans, 1] = k + 1
        spans[n_spans, 2] = end
        n_spans += 1
        sign = -1.0 if change < 0 else 1.0
        stop = end if end < samples else samples
        for i in range(k + 1, stop):
            tau = (i - k) * dt
            if kind == 0:
                ax, ay, ac = arc_position(xs, ys, c, v, sign * rate, tau)
                tgt_x[i] = ax
                tgt_y[i] = ay
                tgt_c[i] = ac
                tgt_v[i] = v
            else:
                d = v * tau + 0.5 * sign * rate * tau * tau
                tgt_x[i] = xs + math.sin(c) * d
                tgt_y[i] = ys + math.cos(c) * d
                tgt_c[i] = c
                tgt_v[i] = v + sign * rate * tau
        if kind == 0:
            ax, ay, _ac = arc_position(xs, ys, c, v, sign * rate, dur)
            x = ax
            y = ay
            c = wrap2pi(c + change)
        else:
            x = xs + math.sin(c) * (v * dur + 0.5 * change * dur)
            y = ys + math.cos(c) * (v * dur + 0.5 * change * dur)
            v = v + change
        t0 = ts + dur
        frm = end
    for i in range(frm, samples):
        tau = i * dt - t0
        tgt_x[i] = x + v * math.sin(c) * tau
        tgt_y[i] = y + v * math.cos(c) * tau
        tgt_c[i] = c
        tgt_v[i] = v
    TI[TI_N_SPANS] = n_spans
    if n_spans > 0:
        TI[TI_M_START] = spans[0, 1]
        TI[TI_M_INDEX] = spans[n_spans - 1, 2]


@njit(cache=True)
def simulate_truth(
    P: np.ndarray,
    tm: np.ndarray,
    own_x: np.ndarray,
    own_y: np.ndarray,
    own_c: np.ndarray,
    tgt_x: np.ndarray,
    tgt_y: np.ndarray,
    tgt_c: np.ndarray,
    tgt_v: np.ndarray,
    TI: np.ndarray,
    spans: np.ndarray,
) -> None:
    """Full truth: two legs, second zig, 0.4.0 turn, 0.5.0 manoeuvres (gitma ``simulateTruth``)."""
    simulate_two_legs(P, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI)
    ownship_zig2(P, own_x, own_y, own_c, TI)
    target_manoeuvre(P, tgt_x, tgt_y, tgt_c, TI)
    target_manoeuvres(P, tm, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)


@njit(cache=True)
def plan_manoeuvres(s: np.ndarray, R: np.ndarray, P: np.ndarray, rmax: int) -> None:
    """Generator 0.3.0 draws: across-LOS offsets and the second zig; updates ``P`` in place."""
    across = R[R_ACROSS_LOS] > 0
    has_delay = not math.isnan(R[R_ZIG2_DELAY_MIN])
    if not across and not has_delay:
        return
    offset1 = uniform(s, R[R_LOS_MIN], R[R_LOS_MAX]) if across else 0.0
    delay = f32(uniform(s, R[R_ZIG2_DELAY_MIN], R[R_ZIG2_DELAY_MAX])) if has_delay else math.nan
    zig2_drawn = 0.0
    if has_delay:
        if across:
            zig2_drawn = uniform(s, R[R_LOS_MIN], R[R_LOS_MAX])
        else:
            ab = uniform(s, R[R_ZIG_ABS_MIN], R[R_ZIG_ABS_MAX])
            zig2_drawn = (-1.0 if uniform01(s) < 0.5 else 1.0) * ab
    if across:
        k = js_round(P[P_ZIG_FRAC] * js_round(P[P_WINDOW] / P[P_DT]))
        t = k * P[P_DT]
        c0 = P[P_COURSE0]
        v = P[P_OWN_SPEED]
        tx, ty = target_at(P, t)
        P[P_ZIG] = f32(
            across_los_turn(v * math.sin(c0) * t, v * math.cos(c0) * t, c0, tx, ty, offset1)
        )
    if not has_delay:
        return
    zig2 = zig2_drawn
    if across:
        own_x = np.empty(rmax)
        own_y = np.empty(rmax)
        own_c = np.empty(rmax)
        tgt_x = np.empty(rmax)
        tgt_y = np.empty(rmax)
        tgt_c = np.empty(rmax)
        tgt_v = np.empty(rmax)
        TI = np.empty(TI_LEN, dtype=np.int64)
        spans = np.empty((MAX_TM, 3), dtype=np.int64)
        tm = np.empty((MAX_TM, 4))
        simulate_truth(P, tm, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
        k2 = TI[TI_ZIG] + js_round(delay / P[P_DT])
        if k2 < TI[TI_SAMPLES]:
            tx, ty = target_at(P, k2 * P[P_DT])
            zig2 = across_los_turn(own_x[k2], own_y[k2], own_c[k2], tx, ty, zig2_drawn)
    P[P_ZIG2_DELAY] = delay
    P[P_ZIG2_ANGLE] = f32(zig2)


@njit(cache=True)
def plan_target_manoeuvre(s: np.ndarray, R: np.ndarray, P: np.ndarray, rmax: int) -> bool:
    """Generator 0.4.0 draws (four, always); returns whether the window fits the turn."""
    fraction = R[R_TM_FRACTION]
    if math.isnan(fraction):
        return True
    turns = uniform01(s) < fraction
    angle = f32(
        (-1.0 if uniform01(s) < 0.5 else 1.0) * uniform(s, R[R_TM_ANGLE_MIN], R[R_TM_ANGLE_MAX])
    )
    rate = f32(uniform(s, R[R_TM_RATE_MIN], R[R_TM_RATE_MAX]))
    where = uniform01(s)
    dt = P[P_DT]
    samples = js_round(P[P_WINDOW] / dt)
    own_x = np.empty(rmax)
    own_y = np.empty(rmax)
    own_c = np.empty(rmax)
    tgt_x = np.empty(rmax)
    tgt_y = np.empty(rmax)
    tgt_c = np.empty(rmax)
    tgt_v = np.empty(rmax)
    TI = np.empty(TI_LEN, dtype=np.int64)
    spans = np.empty((MAX_TM, 3), dtype=np.int64)
    tm = np.empty((MAX_TM, 4))
    simulate_truth(P, tm, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
    lo = TI[TI_ZIG] + int(math.ceil(R[R_TM_AFTER] / dt))
    hi = samples - 1 - int(math.ceil(R[R_TM_MARGIN] / dt)) - turn_rows(abs(angle) / rate, dt)
    if hi < lo:
        return False
    start = lo + min(hi - lo, int(math.floor(where * (hi - lo + 1))))
    if not turns:
        return True
    P[P_TM_TIME] = f32(start * dt)
    P[P_TM_ANGLE] = angle
    P[P_TM_RATE] = rate
    return True


@njit(cache=True)
def plan_target_manoeuvres(
    s: np.ndarray,
    R: np.ndarray,
    P: np.ndarray,
    tm: np.ndarray,
    n_course: int,
    speed_change: bool,
    rmax: int,
) -> bool:
    """Generator 0.5.0 draws (all consumed whatever is used); returns whether the plan fits."""
    n_w = int(R[R_N_WEIGHTS])
    if n_w == 0:
        return True
    max_course = n_w - 1
    has_speed = not math.isnan(R[R_DV_MIN]) and not math.isnan(R[R_ACC_MIN])
    # Candidate course changes: sign, |angle|, rate for every possible one.
    cand = np.empty((MAX_TM, 4))
    for k in range(max_course):
        sign = -1.0 if uniform01(s) < 0.5 else 1.0
        change = f32(sign * uniform(s, R[R_TM_ANGLE_MIN], R[R_TM_ANGLE_MAX]))
        rate = f32(uniform(s, R[R_TM_RATE_MIN], R[R_TM_RATE_MAX]))
        cand[k, TM_KIND] = 0.0
        cand[k, TM_START] = 0.0
        cand[k, TM_CHANGE] = change
        cand[k, TM_RATE] = rate
    speed_ok = True
    have_speed = False
    sp_change = 0.0
    sp_rate = 0.0
    if has_speed:
        sign = -1.0 if uniform01(s) < 0.5 else 1.0
        dv = uniform(s, R[R_DV_MIN], R[R_DV_MAX])
        sp_rate = f32(uniform(s, R[R_ACC_MIN], R[R_ACC_MAX]))
        lo_v = R[R_TGT_SPEED_MIN]
        hi_v = R[R_TGT_SPEED_MAX]
        v = P[P_TGT_SPEED]
        d1 = sign * dv
        d2 = -sign * dv
        if v + d1 >= lo_v and v + d1 <= hi_v:
            have_speed = True
            sp_change = f32(d1)
        elif v + d2 >= lo_v and v + d2 <= hi_v:
            have_speed = True
            sp_change = f32(d2)
        else:
            speed_ok = not speed_change
    place = uniform01(s)
    slack = np.empty(MAX_TM)
    for k in range(max_course + 1):
        slack[k] = uniform01(s)
    if not speed_ok:
        return False
    # The plan: the first n_course candidates, with the speed change inserted at `place`.
    n_plan = n_course
    for k in range(n_course):
        for c in range(4):
            tm[k, c] = cand[k, c]
    if speed_change and have_speed:
        pos = int(math.floor(place * (n_plan + 1)))
        if pos > n_plan:
            pos = n_plan
        for k in range(n_plan, pos, -1):
            for c in range(4):
                tm[k, c] = tm[k - 1, c]
        tm[pos, TM_KIND] = 1.0
        tm[pos, TM_START] = 0.0
        tm[pos, TM_CHANGE] = sp_change
        tm[pos, TM_RATE] = sp_rate
        n_plan += 1
    dt = P[P_DT]
    samples = js_round(P[P_WINDOW] / dt)
    own_x = np.empty(rmax)
    own_y = np.empty(rmax)
    own_c = np.empty(rmax)
    tgt_x = np.empty(rmax)
    tgt_y = np.empty(rmax)
    tgt_c = np.empty(rmax)
    tgt_v = np.empty(rmax)
    TI = np.empty(TI_LEN, dtype=np.int64)
    spans = np.empty((MAX_TM, 3), dtype=np.int64)
    tm_none = np.empty((MAX_TM, 4))
    P[P_N_TM] = -1.0  # simulate without manoeuvres, as gitma's simulateTruth(p) before the plan
    simulate_truth(P, tm_none, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
    lo = TI[TI_ZIG] + int(math.ceil(R[R_TM_AFTER] / dt))
    hi_end = samples - 1 - int(math.ceil(R[R_TM_MARGIN] / dt))
    gap = int(math.ceil(R[R_TM_SPACING] / dt))
    rows = np.empty(MAX_TM, dtype=np.int64)
    total = 0
    for j in range(n_plan):
        rows[j] = turn_rows(abs(tm[j, TM_CHANGE]) / tm[j, TM_RATE], dt)
        total += rows[j]
    if n_plan > 1:
        total += (n_plan - 1) * gap
    free = hi_end - lo - total
    if n_plan > 0 and free < 0:
        return False
    offsets = np.empty(MAX_TM, dtype=np.int64)
    for j in range(n_plan):
        o = int(math.floor(slack[j] * (free + 1)))
        offsets[j] = free if o > free else o
    # Sort ascending (insertion sort, n ≤ 4).
    for a in range(1, n_plan):
        key = offsets[a]
        b = a - 1
        while b >= 0 and offsets[b] > key:
            offsets[b + 1] = offsets[b]
            b -= 1
        offsets[b + 1] = key
    used = 0
    for j in range(n_plan):
        start = lo + offsets[j] + used
        used += rows[j] + gap
        tm[j, TM_START] = f32(start * dt)
    P[P_N_TM] = n_plan
    return True


@njit(cache=True)
def draw_scenario(
    s: np.ndarray,
    R: np.ndarray,
    P: np.ndarray,
    tm: np.ndarray,
    n_course: int,
    speed_change: bool,
    rmax: int,
) -> bool:
    """One parameter draw (gitma ``drawScenario``); fills ``P``/``tm``; returns ``fits``."""
    dt = R[R_DT]
    min_samples = int(math.ceil(R[R_WINDOW_MIN] / dt))
    max_samples = int(math.floor(R[R_WINDOW_MAX] / dt))
    samples = min_samples + uniform_int(s, max_samples - min_samples + 1)
    ownship_speed = uniform(s, R[R_OWN_SPEED_MIN], R[R_OWN_SPEED_MAX])
    course0 = uniform(s, 0.0, TWO_PI)
    zig_abs = uniform(s, R[R_ZIG_ABS_MIN], R[R_ZIG_ABS_MAX])
    zig_sign = -1.0 if uniform01(s) < 0.5 else 1.0
    zig_fraction = uniform(s, R[R_ZIG_FRAC_MIN], R[R_ZIG_FRAC_MAX])
    if R[R_RANGE_LOG_UNIFORM] > 0:
        range0 = log_uniform(s, R[R_RANGE0_MIN], R[R_RANGE0_MAX])
    else:
        range0 = uniform(s, R[R_RANGE0_MIN], R[R_RANGE0_MAX])
    bearing0 = uniform(s, 0.0, TWO_PI)
    target_speed = uniform(s, R[R_TGT_SPEED_MIN], R[R_TGT_SPEED_MAX])
    target_course = uniform(s, 0.0, TWO_PI)
    n_sigma = int(R[R_N_SIGMA])
    sigma = R[R_SIGMA0 + uniform_int(s, n_sigma)]
    dropout = uniform(s, R[R_DROPOUT_MIN], R[R_DROPOUT_MAX])
    for i in range(P_LEN):
        P[i] = math.nan
    P[P_N_TM] = -1.0
    if not math.isnan(R[R_TURN_RATE_MIN]):
        P[P_TURN_RATE] = f32(uniform(s, R[R_TURN_RATE_MIN], R[R_TURN_RATE_MAX]))
    P[P_WINDOW] = f32(samples * dt)
    P[P_DT] = f32(dt)
    P[P_OWN_SPEED] = f32(ownship_speed)
    P[P_COURSE0] = f32_angle(course0)
    P[P_ZIG] = f32(zig_sign * zig_abs)
    P[P_ZIG_FRAC] = f32(zig_fraction)
    P[P_RANGE0] = f32(range0)
    P[P_BEARING0] = f32_angle(bearing0)
    P[P_TGT_SPEED] = f32(target_speed)
    P[P_TGT_COURSE] = f32_angle(target_course)
    P[P_SIGMA] = f32(sigma)
    P[P_DROPOUT] = f32(dropout)
    plan_manoeuvres(s, R, P, rmax)
    if not plan_target_manoeuvre(s, R, P, rmax):
        return False
    return bool(plan_target_manoeuvres(s, R, P, tm, n_course, speed_change, rmax))


@njit(cache=True)
def range_stats(
    samples: int,
    own_x: np.ndarray,
    own_y: np.ndarray,
    tgt_x: np.ndarray,
    tgt_y: np.ndarray,
) -> tuple[float, float]:
    """Mean and minimum ownship–target range over the window."""
    total = 0.0
    mn = math.inf
    for i in range(samples):
        r = math.hypot(tgt_x[i] - own_x[i], tgt_y[i] - own_y[i])
        total += r
        if r < mn:
            mn = r
    return total / samples, mn


@njit(cache=True)
def observe(
    s: np.ndarray,
    P: np.ndarray,
    samples: int,
    own_x: np.ndarray,
    own_y: np.ndarray,
    tgt_x: np.ndarray,
    tgt_y: np.ndarray,
    bearing: np.ndarray,
    valid: np.ndarray,
) -> None:
    """Bearings with Gaussian noise and dropouts; draws noise and dropout for every sample."""
    for i in range(samples):
        noise = gaussian(s) * P[P_SIGMA]
        dropped = uniform01(s) < P[P_DROPOUT]
        b = bearing_of(tgt_x[i] - own_x[i], tgt_y[i] - own_y[i])
        if dropped:
            bearing[i] = 0.0
            valid[i] = False
        else:
            bearing[i] = f32_angle(b + noise)
            valid[i] = True


@njit(cache=True)
def generate_into(
    dataset_seed: uint64,
    index: int,
    R: np.ndarray,
    rmax: int,
    own: np.ndarray,
    tgt: np.ndarray,
    bearing: np.ndarray,
    valid: np.ndarray,
    P: np.ndarray,
    tm: np.ndarray,
    TI: np.ndarray,
    spans: np.ndarray,
    stats: np.ndarray,
) -> int:
    """Generate scenario ``index`` into the given arrays; returns the redraw count.

    ``own``/``tgt`` are ``[rmax, 4]`` (x, y, course, speed) and hold float32-rounded values; rows
    beyond ``samples`` are zero. ``bearing``/``valid`` are ``[rmax]``. ``stats`` receives
    (zig_time_s, mean_range_m, min_range_m), float32-rounded. Raises after ``MAX_REDRAWS``.
    """
    seed = derive_seed(dataset_seed, index)
    s = create_rng(seed)
    n_course = 0
    speed_change = False
    if int(R[R_N_WEIGHTS]) > 0:
        n_course, speed_change = draw_manoeuvre_count(seed, R)
    own_x = np.empty(rmax)
    own_y = np.empty(rmax)
    own_c = np.empty(rmax)
    tgt_x = np.empty(rmax)
    tgt_y = np.empty(rmax)
    tgt_c = np.empty(rmax)
    tgt_v = np.empty(rmax)
    for redraws in range(MAX_REDRAWS + 1):
        if not draw_scenario(s, R, P, tm, n_course, speed_change, rmax):
            continue
        simulate_truth(P, tm, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
        samples = TI[TI_SAMPLES]
        if TI[TI_TURN_START] != -1 and TI[TI_ZIG] >= samples:
            continue
        if TI[TI_ZIG2] != -1 and TI[TI_ZIG2] >= samples:
            continue
        mean_r, min_r = range_stats(samples, own_x, own_y, tgt_x, tgt_y)
        if min_r < R[R_MIN_RANGE]:
            continue
        observe(s, P, samples, own_x, own_y, tgt_x, tgt_y, bearing, valid)
        for i in range(rmax):
            if i < samples:
                own[i, 0] = f32(own_x[i])
                own[i, 1] = f32(own_y[i])
                own[i, 2] = f32_angle(own_c[i])
                own[i, 3] = P[P_OWN_SPEED]
                tgt[i, 0] = f32(tgt_x[i])
                tgt[i, 1] = f32(tgt_y[i])
                tgt[i, 2] = f32_angle(tgt_c[i])
                tgt[i, 3] = f32(tgt_v[i])
            else:
                for c in range(4):
                    own[i, c] = 0.0
                    tgt[i, c] = 0.0
                bearing[i] = 0.0
                valid[i] = False
        stats[0] = f32(TI[TI_ZIG] * P[P_DT])
        stats[1] = f32(mean_r)
        stats[2] = f32(min_r)
        return redraws
    raise ValueError("no valid geometry after the maximum number of redraws")
