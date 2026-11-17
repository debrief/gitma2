"""Long engagements (spec 023, issue #42): 6 to 48 hours of one target and one ownship.

The 0.6.0 kernel is not touched (its manoeuvre table holds 32 changes, enough for two hours of
Annex B legs but not for 48: about 115 changes). This module draws its own engagements from the
project's PRNG (``derive_seed(seed, index)``), so they are seeded and reproducible:

* the target follows Annex B's manoeuvre statistics, read from a ranges file (leg lengths, kind
  weights, course and speed changes and their rates, speed bounds);
* the ownship runs legs of 20 to 40 minutes with a turn at the start of each, alternating the
  side of the line of sight it puts the target on (the usual TMA practice), and keeps the target
  between two ranges by closing or opening on the next leg. It steers on the *true* target
  position: a simplification (a real ownship steers on its own solution), recorded in the spec.

Kinematics are the generator's: constant-rate turns, constant accelerations, a "both" change runs
its course and speed parts together. Course and speed are laid out analytically on a 0.5 s grid
and positions integrated by the trapezoidal rule (error well under a metre over 48 hours),
then sampled every ``dt_s``. Arrays use the pack's column order (own and tgt: t, x, y, course,
speed; obs: t, bearing, valid), so the project's estimators read them unchanged.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.sim.geometry import turn_rows
from tma2.sim.prng import create_rng, derive_seed, gaussian, log_uniform, uniform, uniform01

H = 0.5  # integration grid, s
TWO_PI = 2.0 * math.pi
KINDS = ("course", "speed", "both")
REALISM_STREAM = np.uint64(0x5EC0_24A1_7B3D_9F11)  # spec 024's realism draws: a stream of its own


@dataclass
class Engagement:
    index: int
    meta: dict[str, Any]
    own: np.ndarray  # [S, 5] t, x, y, course, speed
    tgt: np.ndarray  # [S, 5]
    obs: np.ndarray  # [S, 3] t, bearing, valid
    other: Engagement | None = None  # spec 024: the second contact (same ownship), if any

    @property
    def samples(self) -> int:
        return int(self.own.shape[0])

    @property
    def dt(self) -> float:
        return float(self.meta["parameters"]["dt_s"])


def _wrap(a: np.ndarray | float) -> Any:
    return np.mod(a, TWO_PI)


def _profile(n: int, start: float, events: list[tuple[float, float, float]]) -> np.ndarray:
    """A quantity on the fine grid: ``start`` plus each event's change applied at its rate
    from its start time (events: (t_start, change, rate > 0))."""
    t = np.arange(n) * H
    out = np.full(n, start, dtype=np.float64)
    for ts, ch, rate in events:
        if ch == 0.0 or rate <= 0.0:
            continue
        dur = abs(ch) / rate
        out += math.copysign(1.0, ch) * np.clip(t - ts, 0.0, dur) * rate
    return out


def _integrate(x0: float, y0: float, course: np.ndarray, speed: np.ndarray) -> tuple[Any, Any]:
    vx, vy = speed * np.sin(course), speed * np.cos(course)
    x = x0 + np.concatenate([[0.0], np.cumsum(0.5 * (vx[1:] + vx[:-1]) * H)])
    y = y0 + np.concatenate([[0.0], np.cumsum(0.5 * (vy[1:] + vy[:-1]) * H)])
    return x, y


def _leg(s: np.ndarray, mean: float, sd: float, lo: float) -> float:
    while True:  # Annex B: a normal leg length truncated below
        v = mean + sd * gaussian(s)
        if v >= lo:
            return float(v)


def _target_plan(
    s: np.ndarray, R: dict[str, Any], seconds: float, dt: float, v0: float
) -> list[dict[str, Any]]:
    """The target's manoeuvre table (the generator's ``target_manoeuvres`` form)."""
    leg = R["target_leg_length_s"]
    w = R["target_change_kind_weights"]
    cum = np.cumsum([w["course"], w["speed"], w["both"]])
    cum = cum / cum[-1]
    vlo, vhi = R["target_speed_mps"]["min"], R["target_speed_mps"]["max"]
    plan: list[dict[str, Any]] = []
    v = v0
    t = _leg(s, leg["mean"], leg["sd"], leg["min"])
    while True:
        ts = round(t / dt) * dt
        if ts >= seconds:
            return plan
        u = uniform01(s)
        kind = KINDS[int(np.searchsorted(cum, u, side="right"))]
        ang = uniform(
            s,
            R["target_manoeuvre_angle_abs_rad"]["min"],
            R["target_manoeuvre_angle_abs_rad"]["max"],
        )
        ang *= -1.0 if uniform01(s) < 0.5 else 1.0
        rate = uniform(s, R["target_turn_rate_rad_s"]["min"], R["target_turn_rate_rad_s"]["max"])
        dv = uniform(
            s, R["target_speed_change_abs_mps"]["min"], R["target_speed_change_abs_mps"]["max"]
        )
        dv *= -1.0 if uniform01(s) < 0.5 else 1.0
        acc = uniform(
            s,
            R["target_speed_change_rate_mps2"]["min"],
            R["target_speed_change_rate_mps2"]["max"],
        )
        if kind != "course":
            if not vlo <= v + dv <= vhi:
                dv = -dv
            if not vlo <= v + dv <= vhi:
                kind = "course"
        if kind == "course":
            m = {"kind": "course", "start_time_s": ts, "change": ang, "rate": rate}
            dur = abs(ang) / rate
        elif kind == "speed":
            m = {"kind": "speed", "start_time_s": ts, "change": dv, "rate": acc}
            dur = abs(dv) / acc
            v += dv
        else:
            m = {
                "kind": "both",
                "start_time_s": ts,
                "change": ang,
                "rate": rate,
                "change2": dv,
                "rate2": acc,
            }
            dur = max(abs(ang) / rate, abs(dv) / acc)
            v += dv
        plan.append(m)
        t = ts + dur + _leg(s, leg["mean"], leg["sd"], leg["min"])


def _target(
    plan: list[dict[str, Any]], n: int, x0: float, y0: float, c0: float, v0: float
) -> tuple[np.ndarray, ...]:
    ce, ve = [], []
    for m in plan:
        if m["kind"] == "course":
            ce.append((m["start_time_s"], m["change"], m["rate"]))
        elif m["kind"] == "speed":
            ve.append((m["start_time_s"], m["change"], m["rate"]))
        else:
            ce.append((m["start_time_s"], m["change"], m["rate"]))
            ve.append((m["start_time_s"], m["change2"], m["rate2"]))
    course = _profile(n, c0, ce)
    speed = _profile(n, v0, ve)
    x, y = _integrate(x0, y0, course, speed)
    return x, y, course, speed


def _ownship(
    s: np.ndarray,
    osc: dict[str, Any],
    n: int,
    dt: float,
    v_own: float,
    turn_rate: float,
    tx: np.ndarray,
    ty: np.ndarray,
    belief: Any = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[tuple[float, float]]]:
    """The ownship on the fine grid, leg by leg; returns x, y, course, speed and the turns
    (start, end) in seconds. ``belief(t, r, b)`` (spec 024), when given, replaces the true range
    and bearing the next leg is planned on with what the ownship believes: (range, bearing), or
    a flag saying the contact is lost; the ownship then closes on where it last believed the target
    to be, at sprint speed, to regain it. The base stream ``s``
    draws the same numbers either way, so the target and the bearing noise do not change."""
    course = np.empty(n)
    speed = np.empty(n)
    x = np.empty(n)
    y = np.empty(n)
    side = 1.0 if uniform01(s) < 0.5 else -1.0
    b0 = math.atan2(tx[0], ty[0])
    c = float(_wrap(b0 + side * uniform(s, osc["offset_rad"]["min"], osc["offset_rad"]["max"])))
    course[0], speed[0], x[0], y[0] = c, v_own, 0.0, 0.0
    turns: list[tuple[float, float]] = []
    course_target = c
    i0 = 0  # fine index the current leg starts at
    v = v_own
    while True:
        leg = uniform(s, osc["leg_s"]["min"], osc["leg_s"]["max"])
        i1 = min(n, i0 + int(round(round(leg / dt) * dt / H)))  # next leg starts on a sample
        # this leg: turn (if any) from i0, then hold
        seg = np.arange(i1 - i0) * H
        if turns and turns[-1][0] == i0 * H:
            c_from, c_to = course[i0], course_target
            d = (c_to - c_from + math.pi) % TWO_PI - math.pi
            dur = abs(d) / turn_rate
            course[i0:i1] = c_from + math.copysign(1.0, d) * np.clip(seg, 0.0, dur) * turn_rate
        else:
            course[i0:i1] = course[i0]
        speed[i0:i1] = v
        xs, ys = _integrate(x[i0], y[i0], course[i0:i1], speed[i0:i1])
        x[i0:i1], y[i0:i1] = xs, ys
        if i1 >= n:
            break
        # next leg's course, from the geometry at its start
        dx, dy = (
            tx[i1] - (xs[-1] + v * math.sin(course[i1 - 1]) * H),
            ty[i1] - (ys[-1] + v * math.cos(course[i1 - 1]) * H),
        )
        x[i1] = xs[-1] + v * math.sin(course[i1 - 1]) * H
        y[i1] = ys[-1] + v * math.cos(course[i1 - 1]) * H
        r, b = math.hypot(dx, dy), math.atan2(dx, dy)
        if belief is not None:
            r, b, lost = belief(i1 * H, r, b, x[i1], y[i1])
            if lost:  # no contact: close along the last bearing it had, at sprint speed
                r = float("inf")
        side = -side
        if r > osc["range_high_m"]:
            off = uniform(s, osc["close_offset_rad"]["min"], osc["close_offset_rad"]["max"])
            v = max(v_own, osc["sprint_speed_mps"])
        elif r < osc["range_low_m"]:
            off = uniform(s, osc["open_offset_rad"]["min"], osc["open_offset_rad"]["max"])
            v = v_own
        else:
            off = uniform(s, osc["offset_rad"]["min"], osc["offset_rad"]["max"])
            v = v_own
        course_target = float(_wrap(b + side * off))
        course[i1] = course[i1 - 1]
        d = (course_target - course[i1] + math.pi) % TWO_PI - math.pi
        turns.append((i1 * H, i1 * H + abs(d) / turn_rate))
        i0 = i1
    return x, y, _wrap(course), speed, turns


def generate(
    seed: int, index: int, hours: float, config: dict[str, Any], R: dict[str, Any]
) -> Engagement:
    """One engagement of ``hours``; ``config`` is ``configs/long/long.json``, ``R`` the target's
    ranges (Annex B)."""
    dt = float(config["dt_s"])
    seconds = hours * 3600.0
    samples = int(round(seconds / dt))
    n = int(round((samples - 1) * dt / H)) + 1
    s = create_rng(np.uint64(derive_seed(np.uint64(seed), index)))
    osc = config["ownship"]
    v_own = uniform(s, R["ownship_speed_mps"]["min"], R["ownship_speed_mps"]["max"])
    turn_rate = uniform(s, R["ownship_turn_rate_rad_s"]["min"], R["ownship_turn_rate_rad_s"]["max"])
    r0 = log_uniform(s, R["target_range0_m"]["min"], R["target_range0_m"]["max"])
    b0 = uniform(s, 0.0, TWO_PI)
    c0 = uniform(s, 0.0, TWO_PI)
    v0 = uniform(s, R["target_speed_mps"]["min"], R["target_speed_mps"]["max"])
    sigma = float(config["noise_sigma_rad"])
    dropout = uniform(s, R["dropout_fraction"]["min"], R["dropout_fraction"]["max"])
    plan = _target_plan(s, R, seconds, dt, v0)
    tx, ty, tc, tv = _target(plan, n, r0 * math.sin(b0), r0 * math.cos(b0), c0, v0)
    real = config.get("realism")
    rr = (
        create_rng(np.uint64(derive_seed(np.uint64(seed) ^ REALISM_STREAM, index)))
        if real
        else None
    )
    world = _World(rr, real, seconds, dt, sigma, R) if real else None
    if world is not None:
        world.start(r0 * math.sin(b0), r0 * math.cos(b0))
    belief = world.belief if world is not None else None
    ox, oy, oc, ov, turns = _ownship(s, osc, n, dt, v_own, turn_rate, tx, ty, belief)

    pick = np.round(np.arange(samples) * dt / H).astype(np.int64)
    t = np.arange(samples) * dt
    own = np.stack([t, ox[pick], oy[pick], oc[pick], ov[pick]], axis=1)
    tgt = np.stack([t, tx[pick], ty[pick], _wrap(tc[pick]), tv[pick]], axis=1)
    z = np.empty(samples)
    valid = np.empty(samples)
    for i in range(samples):
        g = gaussian(s)
        dropped = uniform01(s) < dropout
        b = math.atan2(tgt[i, 1] - own[i, 1], tgt[i, 2] - own[i, 2])
        z[i] = 0.0 if dropped else float(_wrap(b + sigma * g))
        valid[i] = 0.0 if dropped else 1.0
    obs = np.stack([t, z, valid], axis=1)

    spans = []
    for m in plan:
        k = int(round(m["start_time_s"] / dt))
        dur = abs(m["change"]) / m["rate"]
        if m["kind"] == "both":
            dur = max(dur, abs(m["change2"]) / m["rate2"])
        spans.append({"kind": m["kind"], "start_index": k + 1, "end_index": k + turn_rows(dur, dt)})
    own_turns = [
        [int(round(a / dt)), int(round(a / dt)) + turn_rows(b - a, dt)] for a, b in turns if b > a
    ]
    rng = np.hypot(tgt[:, 1] - own[:, 1], tgt[:, 2] - own[:, 2])
    meta: dict[str, Any] = {
        "seed": str(int(derive_seed(np.uint64(seed), index))),
        "dataset_seed": seed,
        "index": index,
        "hours": hours,
        "parameters": {
            "dt_s": dt,
            "noise_sigma_rad": sigma,
            "dropout_fraction": dropout,
            "ownship_speed_mps": v_own,
            "ownship_turn_rate_rad_s": turn_rate,
            "target_range0_m": r0,
            "target_manoeuvres": plan,
        },
        "samples": samples,
        "manoeuvres": spans,
        "ownship_turns": own_turns,
        "zig_index": own_turns[0][1] if own_turns else 0,
        "turn_start_index": own_turns[0][0] if own_turns else 0,
        "mean_range_m": float(rng.mean()),
        "min_range_m": float(rng.min()),
        "max_range_m": float(rng.max()),
    }
    if world is None:
        return Engagement(index, meta, own, tgt, obs)
    # spec 024: what the ownship's sensor would lose, and a second contact
    obs[:, 1:] = world.degrade(obs[:, 1:], rng, world.gaps[0])
    meta["realism"] = {"config": real, "gaps_s": world.gaps[0], "steering": world.steering}
    other = world.second(own, pick, n, plan_spans=_spans, dt=dt, samples=samples, meta=meta)
    swaps = world.swap(obs, other.obs) if other is not None else 0
    meta["realism"]["swapped_bearings"] = swaps
    if other is not None:
        other.meta["realism"]["swapped_bearings"] = swaps
    meta["valid_share"] = float(obs[:, 2].mean())
    return Engagement(index, meta, own, tgt, obs, other)


def _spans(plan: list[dict[str, Any]], dt: float) -> list[dict[str, Any]]:
    spans = []
    for m in plan:
        k = int(round(m["start_time_s"] / dt))
        dur = abs(m["change"]) / m["rate"]
        if m["kind"] == "both":
            dur = max(dur, abs(m["change2"]) / m["rate2"])
        spans.append({"kind": m["kind"], "start_index": k + 1, "end_index": k + turn_rows(dur, dt)})
    return spans


class _World:
    """Spec 024's realism, all drawn from the realism stream ``rr`` in a fixed order:

    * gaps: contact lost for 10–60 minutes at a Poisson rate per hour (each contact its own);
    * detection: a bearing is reported with probability 1 / (1 + exp((r − r50) / width));
    * steering: at each leg's start the ownship plans on the measured bearing (true + σ noise)
      and a range belief (true × exp(sd · N(0, 1))); with no contact it closes along the last
      bearing it measured, at sprint speed;
    * a second target (Annex B's statistics, its own start), its bearings degraded the same
      way; where both contacts are reported within ``swap_rad`` of each other, the two bearings
      are swapped with probability one half (mis-association).
    """

    def __init__(
        self,
        rr: Any,
        cfg: dict[str, Any],
        seconds: float,
        dt: float,
        sigma: float,
        R: dict[str, Any],
    ) -> None:
        self.rr, self.cfg, self.seconds, self.dt, self.sigma, self.R = (
            rr,
            cfg,
            seconds,
            dt,
            sigma,
            R,
        )
        g = cfg["gaps"]
        self.gaps = [self._gaps(g), self._gaps(g)]
        self.steering: dict[str, int] = {"planned": 0, "lost": 0}
        self.datum = (0.0, 0.0)  # where the ownship last believed the target to be

    def _gaps(self, g: dict[str, Any]) -> list[list[float]]:
        out: list[list[float]] = []
        t = 0.0
        rate = float(g["per_hour"]) / 3600.0
        while True:
            t += -math.log(max(1e-300, 1.0 - uniform01(self.rr))) / rate
            if t >= self.seconds:
                return out
            d = uniform(self.rr, float(g["min_s"]), float(g["max_s"]))
            out.append([t, min(t + d, self.seconds)])
            t += d

    def p_detect(self, r: float) -> float:
        d = self.cfg["detection"]
        return 1.0 / (1.0 + math.exp((r - float(d["r50_m"])) / float(d["width_m"])))

    def _lost(self, t: float, gaps: list[list[float]]) -> bool:
        return any(a <= t < b for a, b in gaps)

    def start(self, x: float, y: float) -> None:
        """The contact at the engagement's start (it begins held): a belief of where it is."""
        g1, g2 = gaussian(self.rr), gaussian(self.rr)
        r, b = math.hypot(x, y), math.atan2(x, y)
        sd = float(self.cfg["steering"]["range_belief_sd"])
        rb, bb = r * math.exp(sd * g1), b + self.sigma * g2
        self.datum = (rb * math.sin(bb), rb * math.cos(bb))

    def belief(
        self, t: float, r: float, b: float, ox: float, oy: float
    ) -> tuple[float, float, bool]:
        u, g1, g2 = uniform01(self.rr), gaussian(self.rr), gaussian(self.rr)  # always drawn
        if self._lost(t, self.gaps[0]) or u > self.p_detect(r):
            self.steering["lost"] += 1
            dx, dy = self.datum[0] - ox, self.datum[1] - oy
            return math.hypot(dx, dy), math.atan2(dx, dy), True
        self.steering["planned"] += 1
        sd = float(self.cfg["steering"]["range_belief_sd"])
        rb, bb = r * math.exp(sd * g1), b + self.sigma * g2
        self.datum = (ox + rb * math.sin(bb), oy + rb * math.cos(bb))
        return rb, bb, False

    def degrade(self, zv: np.ndarray, rng: np.ndarray, gaps: list[list[float]]) -> np.ndarray:
        """[S, 2] bearing, valid with gaps and range-dependent detection applied."""
        out = zv.copy()
        for i in range(out.shape[0]):
            u = uniform01(self.rr)
            if self._lost(i * self.dt, gaps) or u > self.p_detect(float(rng[i])):
                out[i] = (0.0, 0.0)
        return out

    def second(
        self,
        own: np.ndarray,
        pick: np.ndarray,
        n: int,
        plan_spans: Any,
        dt: float,
        samples: int,
        meta: dict[str, Any],
    ) -> Engagement | None:
        if not self.cfg.get("second_target"):
            return None
        R, rr = self.R, self.rr
        r0 = log_uniform(rr, R["target_range0_m"]["min"], R["target_range0_m"]["max"])
        b0, c0 = uniform(rr, 0.0, TWO_PI), uniform(rr, 0.0, TWO_PI)
        v0 = uniform(rr, R["target_speed_mps"]["min"], R["target_speed_mps"]["max"])
        dropout = uniform(rr, R["dropout_fraction"]["min"], R["dropout_fraction"]["max"])
        plan = _target_plan(rr, R, self.seconds, dt, v0)
        tx, ty, tc, tv = _target(plan, n, r0 * math.sin(b0), r0 * math.cos(b0), c0, v0)
        t = own[:, 0]
        tgt = np.stack([t, tx[pick], ty[pick], _wrap(tc[pick]), tv[pick]], axis=1)
        z = np.empty(samples)
        valid = np.empty(samples)
        for i in range(samples):
            g = gaussian(rr)
            dropped = uniform01(rr) < dropout
            b = math.atan2(tgt[i, 1] - own[i, 1], tgt[i, 2] - own[i, 2])
            z[i] = 0.0 if dropped else float(_wrap(b + self.sigma * g))
            valid[i] = 0.0 if dropped else 1.0
        rng = np.hypot(tgt[:, 1] - own[:, 1], tgt[:, 2] - own[:, 2])
        zv = self.degrade(np.stack([z, valid], axis=1), rng, self.gaps[1])
        obs = np.stack([t, zv[:, 0], zv[:, 1]], axis=1)
        m2 = {
            **meta,
            "contact": 2,
            "parameters": {
                **meta["parameters"],
                "dropout_fraction": dropout,
                "target_range0_m": r0,
                "target_manoeuvres": plan,
            },
            "manoeuvres": plan_spans(plan, dt),
            "mean_range_m": float(rng.mean()),
            "min_range_m": float(rng.min()),
            "max_range_m": float(rng.max()),
            "realism": {**meta["realism"], "gaps_s": self.gaps[1]},
            "valid_share": float(obs[:, 2].mean()),
        }
        return Engagement(int(meta["index"]), m2, own, tgt, obs)

    def swap(self, a: np.ndarray, b: np.ndarray) -> int:
        """Mis-association: swap the two contacts' bearings, with probability one half, where
        both are reported within ``swap_rad`` of each other. Returns the number swapped."""
        lim = float(self.cfg["swap_rad"])
        n = 0
        for i in range(a.shape[0]):
            u = uniform01(self.rr)  # always drawn
            if a[i, 2] == 0 or b[i, 2] == 0:
                continue
            d = (a[i, 1] - b[i, 1] + math.pi) % TWO_PI - math.pi
            if abs(d) < lim and u < 0.5:
                a[i, 1], b[i, 1] = b[i, 1], a[i, 1]
                n += 1
        return n


def generate_all(config: dict[str, Any], R: dict[str, Any]) -> list[Engagement]:
    """Every engagement the config names, indices in order of duration."""
    out = []
    i = 0
    for h in config["hours"]:
        for _ in range(int(config["engagements_per_duration"])):
            out.append(generate(int(config["seed"]), i, float(h), config, R))
            i += 1
    return out
