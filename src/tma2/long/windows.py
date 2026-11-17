"""Windows of a long engagement (spec 023).

Every estimator the project has was built for one window of 40 to 120 minutes with one ownship
zig: the real-time model E's exported graph takes exactly 720 rows (2 hours at 10 s), C's tests
and the zig veto read one ``zig_index``, and the time-late search's cost grows with the number of
manoeuvres a period holds. A long engagement is therefore read through windows cut from it, each
a self-contained engagement in the pack's form: arrays sliced (and optionally thinned), time
rebased to start at 0, the truth's manoeuvres and the ownship's turns re-indexed.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.references.classical import BearingData
from tma2.sim.geometry import turn_rows

from .sim import Engagement


def thinned(e: Engagement, step: int) -> Engagement:
    """Every ``step``-th sample (the real-time model runs at MAN2's 10 s; the data are 5 s)."""
    if step == 1:
        return e
    dt = e.dt * step
    m = dict(e.meta)
    m["parameters"] = {**e.meta["parameters"], "dt_s": dt}
    m["samples"] = int((e.samples + step - 1) // step)
    m["manoeuvres"] = _respan(e.meta["parameters"]["target_manoeuvres"], 0.0, dt, m["samples"])
    m["ownship_turns"] = [[a // step, -(-b // step)] for a, b in e.meta["ownship_turns"]]
    m["zig_index"] = m["ownship_turns"][0][1] if m["ownship_turns"] else 0
    m["turn_start_index"] = m["ownship_turns"][0][0] if m["ownship_turns"] else 0
    return Engagement(e.index, m, e.own[::step].copy(), e.tgt[::step].copy(), e.obs[::step].copy())


def _respan(plan: list[dict[str, Any]], t0: float, dt: float, rows: int) -> list[dict[str, Any]]:
    out = []
    for m in plan:
        ts = float(m["start_time_s"]) - t0
        if ts < 0:
            continue
        k = int(round(ts / dt))
        if k >= rows:
            break
        dur = abs(m["change"]) / m["rate"]
        if m["kind"] == "both":
            dur = max(dur, abs(m["change2"]) / m["rate2"])
        out.append({"kind": m["kind"], "start_index": k + 1, "end_index": k + turn_rows(dur, dt)})
    return out


def in_manoeuvre(e: Engagement, row: int) -> int | None:
    """The end row of a target manoeuvre in progress at ``row`` (None if the target is on a
    leg). A window that starts inside a manoeuvre has no initial leg for the bound to start from."""
    for s in e.meta["manoeuvres"]:
        if s["start_index"] - 1 < row <= s["end_index"]:
            return int(s["end_index"])
    return None


def window(e: Engagement, first: int, rows: int, zig: str = "first") -> Engagement:
    """Rows ``first`` … ``first + rows − 1`` as an engagement of their own. ``zig``: which
    ownship turn in the window becomes its ``zig_index`` ("first", or "last" ending at least
    five minutes before the window's end, as a real-time estimate at the last row would read
    it). Target manoeuvres in progress at the window's start are left out of the truth tables
    (call ``in_manoeuvre`` first where that matters)."""
    last = min(first + rows, e.samples)
    rows = last - first
    dt = e.dt
    t0 = float(e.own[first, 0])
    own = e.own[first:last].copy()
    tgt = e.tgt[first:last].copy()
    obs = e.obs[first:last].copy()
    for a in (own, tgt, obs):
        a[:, 0] -= t0
    origin = (float(own[0, 1]), float(own[0, 2]))  # positions relative to the ownship at the start
    for a in (own, tgt):
        a[:, 1] -= origin[0]
        a[:, 2] -= origin[1]
    plan = [
        {**m, "start_time_s": float(m["start_time_s"]) - t0}
        for m in e.meta["parameters"]["target_manoeuvres"]
        if t0 <= float(m["start_time_s"]) < t0 + rows * dt
    ]
    turns = [
        [max(a - first, 0), min(b - first, rows - 1)]
        for a, b in e.meta["ownship_turns"]
        if b >= first and a < last
    ]
    m: dict[str, Any] = {
        **{k: v for k, v in e.meta.items() if k not in ("manoeuvres", "ownship_turns")},
        "parameters": {**e.meta["parameters"], "target_manoeuvres": plan},
        "samples": rows,
        "window_first": first,
        "window_t0_s": t0,
        "window_origin_m": list(origin),
        "manoeuvres": _respan(plan, 0.0, dt, rows),
        "ownship_turns": turns,
    }
    if zig == "last":
        late = [tr for tr in turns if tr[1] <= rows - 1 - int(round(300 / dt))]
        tr = late[-1] if late else (turns[0] if turns else [0, 0])
    else:
        tr = turns[0] if turns else [0, 0]
    m["turn_start_index"], m["zig_index"] = int(tr[0]), int(tr[1])
    # the Period's ownship_turns() reads the first and second turns
    if len(turns) > 1:
        m["turn2_start_index"], m["zig2_index"] = int(turns[1][0]), int(turns[1][1])
    return Engagement(e.index, m, own, tgt, obs)


def bearing_data(e: Engagement) -> BearingData:
    return BearingData(
        t=e.own[:, 0].astype(np.float64),
        ox=e.own[:, 1].astype(np.float64),
        oy=e.own[:, 2].astype(np.float64),
        z=e.obs[:, 1].astype(np.float64),
        valid=(e.obs[:, 2] != 0).astype(np.uint8),
        zig_index=int(e.meta["zig_index"]),
        sigma=float(e.meta["parameters"]["noise_sigma_rad"]),
        index=int(e.index),
    )


def turns_veto(d: BearingData, turns: list[list[int]], width: int) -> np.ndarray:
    """C″'s zig veto (``gate2.predict.zig_veto_evidence``) at *every* ownship turn in the window,
    not only one: the one change C″ needs to run on a window with several ownship legs."""
    e = np.zeros(d.n)
    for _a, z in turns:
        e[max(0, z - width) : min(d.n, z + width + 1)] = 1.0e3
    return e
