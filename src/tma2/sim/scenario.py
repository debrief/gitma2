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
table ``tm[MAX_TM, TM_COLS]`` (kind, start_time_s, change, rate, change2, rate2). Truth
indices live in an int64 array
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
    R_KIND_COURSE,
    R_KIND_SPEED,
    R_LEG_MEAN,
    R_LEG_MIN,
    R_LEG_SD,
    R_LOS_MAX,
    R_LOS_MIN,
    R_MIN_RANGE,
    R_N_SIGMA,
    R_N_WEIGHTS,
    R_OSC_AMP_MAX,
    R_OSC_AMP_MIN,
    R_OSC_PERIOD_MAX,
    R_OSC_PERIOD_MIN,
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
    R_WANDER_CLIP,
    R_WANDER_SD,
    R_WANDER_TAU,
    R_WEIGHT0,
    R_WINDOW_MAX,
    R_WINDOW_MIN,
    R_WW_NONE,
    R_WW_OSC,
    R_WW_WANDER,
    R_ZIG2_DELAY_MAX,
    R_ZIG2_DELAY_MIN,
    R_ZIG_ABS_MAX,
    R_ZIG_ABS_MIN,
    R_ZIG_FRAC_MAX,
    R_ZIG_FRAC_MIN,
)

MAX_REDRAWS = 1000
MAX_TM = 32  # 0.5.0: ≤ 3 course + 1 speed change; 0.6.0: validated as window max / leg min + 1

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
# Generator 0.6.0 (SRD Annex B, MAN2); NaN when absent.
P_WANDER_KIND = 19  # 0 none, 1 wander, 2 oscillation, 3 both
P_W_SD = 20
P_W_TAU = 21
P_W_CLIP = 22
P_OSC_AMP = 23
P_OSC_PERIOD = 24
P_OSC_PHASE = 25
P_ZIG_ON_MAN = 26  # 1.0 when the ownship turn rows [turn start, zig) share a row with a span
P_LEN = 27

# Manoeuvre table columns.
TM_KIND = 0  # 0 course, 1 speed, 2 both (generator 0.6.0)
TM_START = 1
TM_CHANGE = 2
TM_RATE = 3
TM_CHANGE2 = 4  # kind 2: the speed change that accompanies the turn
TM_RATE2 = 5  # kind 2: its acceleration
TM_COLS = 6

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
        change2 = 0.0
        rate2 = 0.0
        dur_c = dur
        dur_v = 0.0
        if kind == 2:
            change2 = tm[j, TM_CHANGE2]
            rate2 = tm[j, TM_RATE2]
            dur_v = abs(change2) / rate2
            if dur_v > dur:
                dur = dur_v
            end = k + turn_rows(dur, dt)
        spans[n_spans, 0] = kind
        spans[n_spans, 1] = k + 1
        spans[n_spans, 2] = end  # may lie beyond the window: the change is still in progress
        n_spans += 1
        sign = -1.0 if change < 0 else 1.0
        stop = end if end < samples else samples
        bx = xs
        by = ys
        b_t = 0.0
        for i in range(k + 1, stop):
            tau = (i - k) * dt
            if kind == 2:
                bx, by, bc, bv = both_continue(
                    bx, by, b_t, c, v, sign * rate, dur_c, change2, rate2, dur_v, tau
                )
                b_t = tau
                tgt_x[i] = bx
                tgt_y[i] = by
                tgt_c[i] = bc
                tgt_v[i] = bv
            elif kind == 0:
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
        if kind == 2:
            bx, by, _bc, _bv = both_continue(
                bx, by, b_t, c, v, sign * rate, dur_c, change2, rate2, dur_v, dur
            )
            x = bx
            y = by
            c = wrap2pi(c + change)
            v = v + change2
        elif kind == 0:
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
def both_state(
    x0: float,
    y0: float,
    c0: float,
    v0: float,
    omega: float,
    dur_c: float,
    dv: float,
    acc: float,
    dur_v: float,
    tau: float,
) -> tuple[float, float, float, float]:
    """State ``tau`` seconds into a combined manoeuvre (generator 0.6.0 kind "both"): the course
    turns at ``omega`` for ``dur_c`` s while the speed changes by ``dv`` at ``acc`` for ``dur_v``
    s. Course and speed are exact; position is integrated with 1 s midpoint steps."""
    return both_continue(x0, y0, 0.0, c0, v0, omega, dur_c, dv, acc, dur_v, tau)


@njit(cache=True)
def both_continue(
    x0: float,
    y0: float,
    t_from: float,
    c0: float,
    v0: float,
    omega: float,
    dur_c: float,
    dv: float,
    acc: float,
    dur_v: float,
    tau: float,
) -> tuple[float, float, float, float]:
    """``both_state`` resumed from position (x0, y0) at ``t_from`` s into the manoeuvre (c0, v0
    are its start course and speed). With ``t_from`` on the integration's 1 s grid, as every row
    time is, the steps and their sums are exactly those of one integration from 0, so the
    generator can advance row by row in linear time."""
    sgn = -1.0 if dv < 0 else 1.0
    x = x0
    y = y0
    t = t_from
    while t < tau:
        h = 1.0 if tau - t > 1.0 else tau - t
        tmid = t + 0.5 * h
        cm = c0 + omega * (tmid if tmid < dur_c else dur_c)
        vm = v0 + sgn * acc * (tmid if tmid < dur_v else dur_v)
        x += vm * math.sin(cm) * h
        y += vm * math.cos(cm) * h
        t += h
    c_end = c0 + omega * (tau if tau < dur_c else dur_c)
    v_end = v0 + sgn * acc * (tau if tau < dur_v else dur_v)
    return x, y, wrap2pi(c_end), v_end


@njit(cache=True)
def plan_target_legs(
    scenario_seed: uint64, attempt: int, R: np.ndarray, P: np.ndarray, tm: np.ndarray
) -> int:
    """Generator 0.6.0 target legs (SRD Annex B, MAN2), drawn from their own stream so that no
    0.5.0 draw moves. Legs ~ N(mean, sd) clipped at min are laid end to end; the first change
    comes after a uniform fraction of the first leg. Each leg ends in a course change, a speed
    change or both, by weight. Every leg draws the same values in the same order whatever its
    kind (sign, angle, turn rate, speed sign, Δv, acceleration, next leg length). A speed change
    that fits neither sign becomes a course change. Changes are planned until one would start at
    or after the window's end. Returns and stores the number planned (``P[P_N_TM]``)."""
    s2 = create_rng(derive_seed(scenario_seed, 2 + 2 * attempt))
    dt = P[P_DT]
    samples = js_round(P[P_WINDOW] / dt)
    mean = R[R_LEG_MEAN]
    sd = R[R_LEG_SD]
    lo = R[R_LEG_MIN]
    pc = R[R_KIND_COURSE]
    ps = R[R_KIND_SPEED]
    has_speed = not math.isnan(R[R_DV_MIN]) and not math.isnan(R[R_ACC_MIN])
    v = P[P_TGT_SPEED]
    leg = mean + sd * gaussian(s2)
    if leg < lo:
        leg = lo
    t = uniform01(s2) * leg
    n = 0
    while n < MAX_TM:
        u_kind = uniform01(s2)
        sign_c = -1.0 if uniform01(s2) < 0.5 else 1.0
        angle = uniform(s2, R[R_TM_ANGLE_MIN], R[R_TM_ANGLE_MAX])
        rate_c = uniform(s2, R[R_TM_RATE_MIN], R[R_TM_RATE_MAX])
        sign_v = -1.0 if uniform01(s2) < 0.5 else 1.0
        dv = uniform(s2, R[R_DV_MIN], R[R_DV_MAX]) if has_speed else 0.0
        acc = uniform(s2, R[R_ACC_MIN], R[R_ACC_MAX]) if has_speed else 0.0
        nxt = mean + sd * gaussian(s2)
        if nxt < lo:
            nxt = lo
        k = js_round(t / dt)
        if k < 1:
            k = 1
        if k >= samples - 1:  # a change on the last row would leave no row inside it
            break
        kind = 0 if u_kind < pc else (1 if u_kind < pc + ps else 2)
        dvs = 0.0
        if kind != 0:
            if not has_speed:
                kind = 0
            elif v + sign_v * dv >= R[R_TGT_SPEED_MIN] and v + sign_v * dv <= R[R_TGT_SPEED_MAX]:
                dvs = sign_v * dv
            elif v - sign_v * dv >= R[R_TGT_SPEED_MIN] and v - sign_v * dv <= R[R_TGT_SPEED_MAX]:
                dvs = -sign_v * dv
            else:
                kind = 0
        for c in range(TM_COLS):
            tm[n, c] = 0.0
        tm[n, TM_KIND] = float(kind)
        tm[n, TM_START] = f32(k * dt)
        if kind == 1:
            tm[n, TM_CHANGE] = f32(dvs)
            tm[n, TM_RATE] = f32(acc)
            dur = abs(dvs) / acc
            v = v + dvs
        else:
            tm[n, TM_CHANGE] = f32(sign_c * angle)
            tm[n, TM_RATE] = f32(rate_c)
            dur = angle / rate_c
            if kind == 2:
                tm[n, TM_CHANGE2] = f32(dvs)
                tm[n, TM_RATE2] = f32(acc)
                dv_dur = abs(dvs) / acc
                if dv_dur > dur:
                    dur = dv_dur
                v = v + dvs
        n += 1
        t = k * dt + dur + nxt
    P[P_N_TM] = float(n)
    return n


@njit(cache=True)
def target_position(P: np.ndarray, tm: np.ndarray, k: int, rmax: int) -> tuple[float, float]:
    """The target's position at row ``k`` with its planned manoeuvres (generator 0.6.0)."""
    tgt_x = np.empty(rmax)
    tgt_y = np.empty(rmax)
    tgt_c = np.empty(rmax)
    tgt_v = np.empty(rmax)
    TI = np.full(TI_LEN, -1, dtype=np.int64)
    spans = np.empty((MAX_TM, 3), dtype=np.int64)
    dt = P[P_DT]
    samples = js_round(P[P_WINDOW] / dt)
    TI[TI_SAMPLES] = samples
    tx0 = P[P_RANGE0] * math.sin(P[P_BEARING0])
    ty0 = P[P_RANGE0] * math.cos(P[P_BEARING0])
    tvx = P[P_TGT_SPEED] * math.sin(P[P_TGT_COURSE])
    tvy = P[P_TGT_SPEED] * math.cos(P[P_TGT_COURSE])
    for i in range(samples):
        tgt_x[i] = tx0 + tvx * i * dt
        tgt_y[i] = ty0 + tvy * i * dt
        tgt_c[i] = P[P_TGT_COURSE]
        tgt_v[i] = P[P_TGT_SPEED]
    target_manoeuvres(P, tm, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
    if k >= samples:
        k = samples - 1
    return tgt_x[k], tgt_y[k]


@njit(cache=True)
def apply_wander(
    scenario_seed: uint64,
    attempt: int,
    R: np.ndarray,
    P: np.ndarray,
    own_x: np.ndarray,
    own_y: np.ndarray,
    own_c: np.ndarray,
    samples: int,
) -> None:
    """Generator 0.6.0 ownship course wander (SRD Annex B FR-006), from its own stream: helm
    wander (an AR(1) course error, clipped) and/or autopilot oscillation (a sinusoid), on steady
    rows only (a row whose planned course equals the previous row's). Positions are re-integrated
    from the recorded course: steady rows by the trapezoid rule, turn rows by the planned arc's own
    displacement, so the recorded track is the true track. Records the kind and parameters in
    ``P``. Draws: kind, amplitude, period, phase, then one innovation per row."""
    s3 = create_rng(derive_seed(scenario_seed, 3 + 2 * attempt))
    u = uniform01(s3)
    has_osc = not math.isnan(R[R_OSC_AMP_MIN])
    amp = uniform(s3, R[R_OSC_AMP_MIN], R[R_OSC_AMP_MAX]) if has_osc else 0.0
    period = (
        uniform(s3, R[R_OSC_PERIOD_MIN], R[R_OSC_PERIOD_MAX])
        if not math.isnan(R[R_OSC_PERIOD_MIN])
        else 1.0
    )
    phase = uniform(s3, 0.0, TWO_PI)
    kind = 0
    if u < R[R_WW_NONE]:
        kind = 0
    elif u < R[R_WW_NONE] + R[R_WW_WANDER]:
        kind = 1
    elif u < R[R_WW_NONE] + R[R_WW_WANDER] + R[R_WW_OSC]:
        kind = 2
    else:
        kind = 3
    has_ar = not math.isnan(R[R_WANDER_SD])
    if (kind == 1 or kind == 3) and not has_ar:
        kind = 2 if has_osc else 0
    if (kind == 2 or kind == 3) and not has_osc:
        kind = 1 if has_ar else 0
    P[P_WANDER_KIND] = float(kind)
    if kind == 0:
        return
    dt = P[P_DT]
    v = P[P_OWN_SPEED]
    use_ar = kind == 1 or kind == 3
    use_osc = kind == 2 or kind == 3
    sd = R[R_WANDER_SD] if use_ar else 0.0
    tau = R[R_WANDER_TAU] if use_ar else 1.0
    clip = R[R_WANDER_CLIP] if use_ar else 0.0
    # the course is driven by the float32-rounded values that are recorded, so the header's
    # ownship_wander reproduces the recorded course exactly (the generator's rounding rule)
    sd = f32(sd)
    tau = f32(tau)
    clip = f32(clip)
    amp = f32(amp)
    period = f32(period)
    phase = f32(phase)
    if use_ar:
        P[P_W_SD] = sd
        P[P_W_TAU] = tau
        P[P_W_CLIP] = clip
    if use_osc:
        P[P_OSC_AMP] = amp
        P[P_OSC_PERIOD] = period
        P[P_OSC_PHASE] = phase
    rho = math.exp(-dt / tau)
    innov = sd * math.sqrt(1.0 - rho * rho)
    e = sd * gaussian(s3) if use_ar else 0.0
    planned_x = own_x.copy()
    planned_y = own_y.copy()
    planned_c = own_c.copy()
    for i in range(samples):
        if i > 0:
            g = gaussian(s3)
            if use_ar:
                e = rho * e + innov * g
        err = 0.0
        if use_ar:
            err = e if abs(e) <= clip else (clip if e > 0 else -clip)
        if use_osc:
            err += amp * math.sin(TWO_PI * i * dt / period + phase)
        steady = i == 0 or planned_c[i] == planned_c[i - 1]
        if i + 1 < samples and planned_c[i + 1] != planned_c[i]:
            steady = False  # the row before a turn keeps the planned course
        own_c[i] = wrap2pi(planned_c[i] + err) if steady else planned_c[i]
        if i == 0:
            own_x[i] = planned_x[i]
            own_y[i] = planned_y[i]
        elif planned_c[i - 1] == planned_c[i]:
            # a straight step (including the row before a turn, whose course is the planned one):
            # the trapezoid of the recorded courses, so the track is the integral of the course
            own_x[i] = own_x[i - 1] + 0.5 * v * dt * (math.sin(own_c[i - 1]) + math.sin(own_c[i]))
            own_y[i] = own_y[i - 1] + 0.5 * v * dt * (math.cos(own_c[i - 1]) + math.cos(own_c[i]))
        else:
            own_x[i] = own_x[i - 1] + (planned_x[i] - planned_x[i - 1])
            own_y[i] = own_y[i - 1] + (planned_y[i] - planned_y[i - 1])


@njit(cache=True)
def zig_on_manoeuvre(TI: np.ndarray, spans: np.ndarray) -> bool:
    """Whether the ownship's turn rows [turn start, zig) share a row with a target manoeuvre span
    [start_index, end_index); both intervals are half-open, start included and end excluded, and
    both start on the first row after the motion starts changing (the generator's convention for
    spans and for the ownship turn). Without a rate-limited turn the zig is the single row
    ``zig``."""
    if TI[TI_TURN_START] != -1:
        a = TI[TI_TURN_START]
        b = TI[TI_ZIG]
    else:
        a = TI[TI_ZIG]
        b = TI[TI_ZIG] + 1
    for j in range(max(TI[TI_N_SPANS], 0)):
        if spans[j, 1] < b and spans[j, 2] > a:
            return True
    return False


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
def plan_manoeuvres(s: np.ndarray, R: np.ndarray, P: np.ndarray, tm: np.ndarray, rmax: int) -> None:
    """Generator 0.3.0 draws: across-LOS offsets and the second zig; updates ``P`` in place.

    With the 0.6.0 leg model the target's legs are planned first (own stream), so the target
    position at a zig row is taken from its simulated track, not from its initial constant
    velocity; ``tm`` holds that plan. Before 0.6.0 ``P[P_N_TM]`` is −1 here and ``tm`` is unused."""
    legs = not math.isnan(R[R_LEG_MEAN])
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
        if legs:
            tx, ty = target_position(P, tm, k, rmax)
        else:
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
        simulate_truth(P, tm, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
        k2 = TI[TI_ZIG] + js_round(delay / P[P_DT])
        if k2 < TI[TI_SAMPLES]:
            if legs:
                tx, ty = tgt_x[k2], tgt_y[k2]
            else:
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
    tm = np.empty((MAX_TM, TM_COLS))
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
    cand = np.empty((MAX_TM, TM_COLS))
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
    tm_none = np.empty((MAX_TM, TM_COLS))
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
    scenario_seed: uint64,
    attempt: int,
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
    if not math.isnan(R[R_LEG_MEAN]):
        plan_target_legs(scenario_seed, attempt, R, P, tm)
    plan_manoeuvres(s, R, P, tm, rmax)
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
        if not draw_scenario(s, R, P, tm, n_course, speed_change, rmax, seed, redraws):
            continue
        simulate_truth(P, tm, own_x, own_y, own_c, tgt_x, tgt_y, tgt_c, tgt_v, TI, spans)
        samples = TI[TI_SAMPLES]
        if TI[TI_TURN_START] != -1 and TI[TI_ZIG] >= samples:
            continue
        if TI[TI_ZIG2] != -1 and TI[TI_ZIG2] >= samples:
            continue
        if not math.isnan(R[R_WW_NONE]):
            apply_wander(seed, redraws, R, P, own_x, own_y, own_c, samples)
        if not math.isnan(R[R_LEG_MEAN]):
            P[P_ZIG_ON_MAN] = 1.0 if zig_on_manoeuvre(TI, spans) else 0.0
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
    return -1
