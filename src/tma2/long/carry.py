"""Time-late windows that carry state (spec 024, recommendation 1 of note 12).

Spec 023 ran the standing control ``ctl`` on each 2-hour window cold: its evidence search starts
from C″'s answer and from nothing (``run2._search``), under Annex B's prior and the broadened one,
on the edited (and, where estimated, correlation-widened) bearings; the pooled candidates' best
is declared at margin 1 with quiet probability 0.01 (``hedge.declared``). This module computes,
from the same pieces and on the same problem:

* ``ctl``: exactly that (checked against ``run4``'s ``ctl-d1-q0.01`` on a window);
* ``ctl-carry``: the same search, with the start from nothing replaced by a start from the
  previous window: its declared track on the rows the windows share, its declared manoeuvres
  that lie inside the overlap, and C″'s answer after it. The first window of a chain has no
  previous window and equals ``ctl``.

Both are solved on every window of a chain, in order, so ``ctl-carry`` can hand its declared
history on. Shards of a chain begin one window early (a warm-up window, run and not recorded).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.timelate.periods import Period

from .sim import Engagement
from .timelate import period_of

SYSTEMS = ("ctl-d1-q0.01", "ctl-carry", "c2", "history-map")
MARGIN, QUIET = 1.0, 0.01


@dataclass
class Carried:
    """What a window hands on: its declared track (engagement frame) at its absolute rows and its
    declared manoeuvres in seconds from the engagement's start."""

    rows: np.ndarray
    states: np.ndarray
    spans_s: np.ndarray


def _declare(problem: Any, cands: list[Any], priors: dict[str, Any]) -> Any:
    from tma2.timelate.hedge import declared, elimination_path

    h0, tag0 = cands[0]
    key = tag0.split("/")[1]
    path = elimination_path(problem, h0, priors[key])
    return path[declared(path, MARGIN, QUIET)]


def solve_window(
    p: Period,
    priors: dict[str, Any],
    c_params: Any,
    c2: dict[str, Any],
    settings: dict[str, Any],
    carry: Carried | None,
) -> dict[str, Any]:
    from tma2.timelate.arc import fit_arc, solve_arc
    from tma2.timelate.corr import MIN_SHARE, edited, effective, estimate
    from tma2.timelate.hedge import pool
    from tma2.timelate.run import nominal_starts
    from tma2.timelate.run2 import reference
    from tma2.timelate.search import candidate_set, evidence_search
    from tma2.timelate.systems import solve_systems

    t0w = time.perf_counter()
    took: dict[str, float] = {}
    a, b = p.first, p.first + p.rows
    t = p.own[a:b, 0].astype(np.float64) - float(p.own[a, 0])
    ox, oy = p.own[a:b, 1].astype(np.float64), p.own[a:b, 2].astype(np.float64)
    z, v = p.obs[a:b, 1].astype(np.float64), p.obs[a:b, 2] != 0
    sigma = float(p.meta["parameters"]["noise_sigma_rad"])
    pb = (t, ox, oy, z, v, sigma)
    nan = np.full((p.rows, 4), np.nan)
    out: dict[str, Any] = {
        "tracks": {s: nan for s in SYSTEMS},
        "declared": {},
        "bearings": int(v.sum()),
    }
    if v.sum() < 60:  # under five minutes of bearings: nothing to solve
        out["seconds"] = {"total": time.perf_counter() - t0w}
        return out
    t1 = time.perf_counter()
    cc = solve_systems([p], ["c2-end-nofade"], c_params, c2)["c2-end-nofade"][0]
    took["c2"] = time.perf_counter() - t1
    spc = np.array(
        [[t[max(r0 - 1, 0)], t[r1]] for r0, r1 in cc.transitions if r1 > r0], dtype=np.float64
    ).reshape(-1, 2)
    out["tracks"]["c2"] = cc.states
    out["declared"]["c2"] = spc
    # the problem ctl solves: wild bearings edited, then a correlation-widened sd if estimated
    pe, n_edit = edited(pb)
    share_e, tau_e = estimate(pe)
    px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
    out["edited"] = int(n_edit)
    tt, oxx, oyy, zz, vv, ss = px
    steps, most = int(settings["steps"]), int(settings["max_manoeuvres"])
    top = int(settings["candidates"])
    none = np.zeros((0, 2))
    seen: dict[tuple[str, str], list[Any]] = {}
    starts: dict[str, tuple[np.ndarray, np.ndarray] | None] = {}
    t1 = time.perf_counter()
    starts["c2"] = None
    if np.isfinite(cc.states).all():
        f0, _, _ = solve_arc(tt, oxx, oyy, zz, vv, ss, spc, cc.states)
        starts["c2"] = (f0.theta, spc)
    b0 = None
    for q0 in nominal_starts(px):
        f = fit_arc(tt, oxx, oyy, zz, vv, ss, none, q0)
        if b0 is None or f.cost < b0.cost:
            b0 = f
    assert b0 is not None
    starts["none"] = (b0.theta, none)
    starts["carry"] = None
    if carry is not None:
        start_track, spans_c = _carry_start(p, carry, cc.states, spc, t)
        if np.isfinite(start_track).all():
            fc, _, _ = solve_arc(tt, oxx, oyy, zz, vv, ss, spans_c, start_track)
            starts["carry"] = (fc.theta, spans_c)
    took["starts"] = time.perf_counter() - t1
    for name, st in starts.items():
        for key in ("v3", "broad"):
            if st is None:
                seen[(name, key)] = []
                continue
            t1 = time.perf_counter()
            seen[(name, key)] = evidence_search(px, st[0], st[1], priors[key], most, steps)[1]
            took[f"{name}/{key}"] = time.perf_counter() - t1

    def cands(names: tuple[str, ...]) -> list[Any]:
        sets = []
        for key in ("v3", "broad"):
            hs = [h for n in names for h in seen[(n, key)]]
            sets.append([(h, f"ctl/{key}") for h, _p in candidate_set(hs, top=top)])
        return pool(sets, top)

    pri = {"v3": priors["v3"], "broad": priors["broad"]}
    t1 = time.perf_counter()
    plain = cands(("c2", "none"))
    if plain:
        h = _declare(px, plain, pri)
        out["tracks"]["ctl-d1-q0.01"] = h.fit.states
        out["declared"]["ctl-d1-q0.01"] = h.fit.spans
    carried = cands(("c2", "carry" if starts["carry"] is not None else "none"))
    if carried:
        h = _declare(px, carried, pri)
        out["tracks"]["ctl-carry"] = h.fit.states
        out["declared"]["ctl-carry"] = h.fit.spans
    took["declare"] = time.perf_counter() - t1
    # the true-history fit with the prior, times free (a reference, told the history)
    t1 = time.perf_counter()
    sp = [s for s in p.spans() if s["end_index"] > s["start_index"]]
    spt = np.array([[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp]).reshape(
        -1, 2
    )
    kt = np.array(
        [[s["kind"] in ("course", "both"), s["kind"] in ("speed", "both")] for s in sp], dtype=bool
    ).reshape(-1, 2)
    try:
        _held, _fit, hm = reference(pb, spt, kt, priors["v3"])
        out["tracks"]["history-map"] = hm.states
    except (ValueError, np.linalg.LinAlgError):
        pass
    took["reference"] = time.perf_counter() - t1
    out["true"] = spt
    took["total"] = time.perf_counter() - t0w
    out["seconds"] = took
    # what took the cold start's place: the searches from nothing against those from the carry
    out["search_s"] = {
        n: float(sum(v for k, v in took.items() if k.startswith(f"{n}/")))
        for n in ("c2", "none", "carry")
    }
    return out


def _carry_start(
    p: Period, carry: Carried, c2_states: np.ndarray, spc: np.ndarray, t: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """A start track [rows, 4] in the window's frame and its manoeuvre spans (s from the
    window's start): the previous window's declared track where the two windows overlap and
    C″'s answer after; its declared manoeuvres inside the overlap and C″'s after."""
    ox0, oy0 = p.meta["window_origin_m"]
    first = int(p.meta["window_first"])
    t0 = float(p.meta["window_t0_s"])
    track = c2_states.copy()
    q = carry.rows - first
    ok = (q >= 0) & (q < p.rows) & np.isfinite(carry.states).all(axis=1)
    if ok.any():
        sel = carry.states[ok].copy()
        sel[:, 0] -= ox0
        sel[:, 1] -= oy0
        # carried rows are every few rows: fill the overlap by holding each carried state's
        # velocity over the rows up to the next one
        qs = q[ok]
        for j in range(qs.size):
            r0 = int(qs[j])
            r1 = int(qs[j + 1]) if j + 1 < qs.size else r0 + 1
            dtt = t[r0:r1] - t[r0]
            track[r0:r1, 0] = sel[j, 0] + sel[j, 2] * dtt
            track[r0:r1, 1] = sel[j, 1] + sel[j, 3] * dtt
            track[r0:r1, 2] = sel[j, 2]
            track[r0:r1, 3] = sel[j, 3]
        overlap_end = float(t[int(qs.max())])
    else:
        overlap_end = 0.0
    spans = [s - t0 for s in carry.spans_s.reshape(-1, 2)]
    spans = [s for s in spans if s[0] >= 0.0 and s[1] <= overlap_end]
    spans += [s for s in spc.reshape(-1, 2) if s[0] > overlap_end]
    arr = np.array(sorted(spans, key=lambda s: s[0]), dtype=np.float64).reshape(-1, 2)
    return track, arr


def run_chain(
    e: Engagement,
    chain: list[tuple[int, int]],
    lo: int,
    hi: int,
    settings: dict[str, Any],
    priors: dict[str, Any],
    c_params: Any,
    c2: dict[str, Any],
) -> list[dict[str, Any]]:
    """Windows ``lo`` … ``hi − 1`` of the chain in order, carrying ``ctl-carry``'s declared
    history; a shard that does not start the chain runs window ``lo − 1`` first as a warm-up."""
    every = int(settings["score_every"])
    carry: Carried | None = None
    out = []
    for j in range(max(0, lo - 1), hi):
        a, rows = chain[j]
        p = period_of(e, a, rows, j)
        res = solve_window(p, priors, c_params, c2, settings, carry)
        ox0, oy0 = p.meta["window_origin_m"]
        t0 = float(p.meta["window_t0_s"])
        tr = res["tracks"]["ctl-carry"]
        dec = res["declared"].get("ctl-carry")
        carry = None
        if np.isfinite(tr).all():
            st = tr.copy()
            st[:, 0] += ox0
            st[:, 1] += oy0
            pick = np.arange(0, rows, every)
            carry = Carried(a + pick, st[pick], (np.zeros((0, 2)) if dec is None else dec) + t0)
        if j < lo:
            continue
        pick = np.arange(0, rows, every)
        tracks = {}
        for s in SYSTEMS:
            x = res["tracks"][s][pick].astype(np.float64).copy()
            x[:, 0] += ox0
            x[:, 1] += oy0
            tracks[s] = x
        out.append(
            {
                "index": j,
                "first": a,
                "rows": rows,
                "rows_abs": a + pick,
                "tracks": tracks,
                "declared": {
                    s: [[float(x + t0), float(y + t0)] for x, y in np.asarray(v).reshape(-1, 2)]
                    for s, v in res["declared"].items()
                },
                "true": [
                    [float(x + t0), float(y + t0)]
                    for x, y in np.asarray(res.get("true", np.zeros((0, 2)))).reshape(-1, 2)
                ],
                "seconds": float(res["seconds"]["total"]),
                "parts": {k: round(float(x), 2) for k, x in res["seconds"].items()},
                "search_s": res.get("search_s", {}),
                "bearings": res["bearings"],
            }
        )
    return out
