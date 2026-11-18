"""Time-late windows that carry the previous window as a prior (spec 027).

``solve_window2`` is ``carry.solve_window`` (copied, so that spec 026's bound module stays
untouched; ``tests/unit/test_long_carry2.py`` asserts its ``ctl`` and ``ctl-carry`` equal the
original's) with one more system:

* ``ctl-prior``: the same evidence search, from C″'s answer and from its own chain's carried
  start, under ``v3`` and ``broad``, each **with the carried prior** in the fit and the evidence
  (``carried.CarriedPrior``); pooled, declared at margin 1 with quiet probability 0.01; then the
  guard: if the carried prior adds more misfit than χ²(4) allows at level ``alpha``, the window
  is declared as its ``ctl-carry`` answer instead. ``ctl-prior-noguard`` is the declared answer
  before the guard (the guarded chain's, not a chain of its own). Where nothing is carried (a
  chain's first window, or no usable hand-over) ``ctl-prior`` is ``ctl``.

``run_chain2`` keeps two chains on one window sequence: ``ctl-carry`` hands its declared history
on as a start (spec 026), ``ctl-prior`` hands its guarded answer on as a start and as a prior
(``carried.hand_on`` → ``widen`` → ``to_frame``). Each window records what it was handed.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.timelate.periods import Period

from .carried import (
    CHI2_4,
    CarriedPrior,
    elimination_path_c,
    evidence_search_c,
    guard,
    hand_on,
    to_frame,
    widen,
)
from .carry import MARGIN, QUIET, Carried, _carry_start
from .sim import Engagement
from .timelate import period_of

SYSTEMS2 = ("ctl-d1-q0.01", "ctl-carry", "ctl-prior", "ctl-prior-noguard", "c2", "history-map")


def _declare2(problem: Any, cands: list[Any], priors: dict[str, Any], cp: Any) -> tuple[Any, str]:
    from tma2.timelate.hedge import declared

    h0, tag0 = cands[0]
    key = tag0.split("/")[1]
    path = elimination_path_c(problem, h0, priors[key], cp)
    return path[declared(path, MARGIN, QUIET)], key


def solve_window2(
    p: Period,
    priors: dict[str, Any],
    c_params: Any,
    c2: dict[str, Any],
    settings: dict[str, Any],
    carry: Carried | None,
    carry_p: Carried | None,
    cp: CarriedPrior | None,
    alpha: float,
) -> dict[str, Any]:
    from tma2.timelate.arc import fit_arc, solve_arc
    from tma2.timelate.corr import MIN_SHARE, edited, effective, estimate
    from tma2.timelate.hedge import pool
    from tma2.timelate.run import nominal_starts
    from tma2.timelate.run2 import reference
    from tma2.timelate.search import candidate_set
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
        "tracks": {s: nan for s in SYSTEMS2},
        "declared": {},
        "bearings": int(v.sum()),
        "hist": {},
        "guard": None,
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
    pe, n_edit = edited(pb)
    share_e, tau_e = estimate(pe)
    px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
    out["edited"] = int(n_edit)
    out["px"] = px
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
    starts["carry-p"] = None
    if carry_p is not None and cp is not None:
        start_track, spans_c = _carry_start(p, carry_p, cc.states, spc, t)
        if np.isfinite(start_track).all():
            fc, _, _ = solve_arc(tt, oxx, oyy, zz, vv, ss, spans_c, start_track)
            starts["carry-p"] = (fc.theta, spans_c)
    took["starts"] = time.perf_counter() - t1
    for name in ("c2", "none", "carry"):
        st = starts[name]
        for key in ("v3", "broad"):
            if st is None:
                seen[(name, key)] = []
                continue
            t1 = time.perf_counter()
            seen[(name, key)] = evidence_search_c(px, st[0], st[1], priors[key], None, most, steps)[
                1
            ]
            took[f"{name}/{key}"] = time.perf_counter() - t1

    def cands(names: tuple[str, ...], pool_of: dict[tuple[str, str], list[Any]]) -> list[Any]:
        sets = []
        for key in ("v3", "broad"):
            hs = [h for n in names for h in pool_of[(n, key)]]
            sets.append([(h, f"ctl/{key}") for h, _p in candidate_set(hs, top=top)])
        return pool(sets, top)

    pri = {"v3": priors["v3"], "broad": priors["broad"]}
    t1 = time.perf_counter()
    plain = cands(("c2", "none"), seen)
    if plain:
        h, key = _declare2(px, plain, pri, None)
        out["tracks"]["ctl-d1-q0.01"] = h.fit.states
        out["declared"]["ctl-d1-q0.01"] = h.fit.spans
        out["hist"]["ctl-d1-q0.01"] = (h, key, None)
    carried = cands(("c2", "carry" if starts["carry"] is not None else "none"), seen)
    if carried:
        h, key = _declare2(px, carried, pri, None)
        out["tracks"]["ctl-carry"] = h.fit.states
        out["declared"]["ctl-carry"] = h.fit.spans
        out["hist"]["ctl-carry"] = (h, key, None)
    took["declare"] = time.perf_counter() - t1
    # ctl-prior: the search under the carried prior, then the guard
    if cp is None:
        for s in ("ctl-prior", "ctl-prior-noguard"):
            out["tracks"][s] = out["tracks"]["ctl-d1-q0.01"]
            if "ctl-d1-q0.01" in out["declared"]:
                out["declared"][s] = out["declared"]["ctl-d1-q0.01"]
        if "ctl-d1-q0.01" in out["hist"]:
            out["hist"]["ctl-prior"] = out["hist"]["ctl-d1-q0.01"]
    else:
        seen_p: dict[tuple[str, str], list[Any]] = {}
        for name in ("c2", "carry-p"):
            st = starts[name]
            for key in ("v3", "broad"):
                if st is None:
                    seen_p[(name, key)] = []
                    continue
                t1 = time.perf_counter()
                seen_p[(name, key)] = evidence_search_c(
                    px, st[0], st[1], priors[key], cp, most, steps
                )[1]
                took[f"prior-{name}/{key}"] = time.perf_counter() - t1
        t1 = time.perf_counter()
        withp = cands(("c2", "carry-p"), seen_p)
        if withp:
            h, key = _declare2(px, withp, pri, cp)
            out["tracks"]["ctl-prior-noguard"] = h.fit.states
            out["declared"]["ctl-prior-noguard"] = h.fit.spans
            d = guard(px, h, pri[key], cp)
            back = not (np.isfinite(d) and d <= CHI2_4[alpha])
            out["guard"] = {"D": float(d), "fell_back": bool(back), "key": key}
            if back and "ctl-carry" in out["hist"]:
                out["tracks"]["ctl-prior"] = out["tracks"]["ctl-carry"]
                out["declared"]["ctl-prior"] = out["declared"]["ctl-carry"]
                out["hist"]["ctl-prior"] = out["hist"]["ctl-carry"]
            elif not back:
                out["tracks"]["ctl-prior"] = h.fit.states
                out["declared"]["ctl-prior"] = h.fit.spans
                out["hist"]["ctl-prior"] = (h, key, cp)
        took["declare-prior"] = time.perf_counter() - t1
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
    out["search_s"] = {
        n: float(sum(v for k, v in took.items() if k.startswith(f"{n}/")))
        for n in ("c2", "none", "carry", "prior-c2", "prior-carry-p")
    }
    return out


def _carried_of(res: dict[str, Any], s: str, a: int, rows: int, p: Period, every: int) -> Any:
    ox0, oy0 = p.meta["window_origin_m"]
    t0 = float(p.meta["window_t0_s"])
    tr = res["tracks"][s]
    dec = res["declared"].get(s)
    if not np.isfinite(tr).all():
        return None
    st = tr.copy()
    st[:, 0] += ox0
    st[:, 1] += oy0
    pick = np.arange(0, rows, every)
    return Carried(a + pick, st[pick], (np.zeros((0, 2)) if dec is None else dec) + t0)


def run_chain2(
    e: Engagement,
    chain: list[tuple[int, int]],
    settings: dict[str, Any],
    priors: dict[str, Any],
    c_params: Any,
    c2: dict[str, Any],
    carry_settings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Every window of the chain in order, carrying ``ctl-carry``'s declared history as a start
    and ``ctl-prior``'s guarded answer as a start and a prior."""
    every = int(settings["score_every"])
    scale, tail_s = float(carry_settings["scale"]), float(carry_settings["tail_s"])
    alpha = float(carry_settings["alpha"])
    carry: Carried | None = None
    carry_p: Carried | None = None
    prev: dict[str, Any] | None = None  # what ctl-prior's last window hands on
    out = []
    for j, (a, rows) in enumerate(chain):
        p = period_of(e, a, rows, j)
        ox0, oy0 = p.meta["window_origin_m"]
        t0 = float(p.meta["window_t0_s"])
        cp = None
        handed: dict[str, Any] = {"row": int(a)}
        t1 = time.perf_counter()
        if prev is not None:
            ho = hand_on(prev["px"], prev["hist"], prev["prior"], prev["cp"], t0 - prev["t0"])
            if ho is not None:
                cov, info = widen(ho, prev["prior"], scale, tail_s)
                mean = to_frame(ho.mean, prev["origin"], [ox0, oy0])
                cp = CarriedPrior(mean, cov)
                handed.update(
                    {
                        "mean": (mean + np.array([ox0, oy0, 0.0, 0.0])).tolist(),
                        "cov_raw": ho.cov.tolist(),
                        "cov": cov.tolist(),
                        "t_last_s": ho.t_last + prev["t0"],
                        **info,
                    }
                )
        handed["hand_on_s"] = time.perf_counter() - t1
        res = solve_window2(
            p, priors, c_params, c2, settings, carry, carry_p if cp else None, cp, alpha
        )
        carry = _carried_of(res, "ctl-carry", a, rows, p, every)
        carry_p = _carried_of(res, "ctl-prior", a, rows, p, every)
        prev = None
        if "ctl-prior" in res["hist"] and carry_p is not None:
            h, key, cp_used = res["hist"]["ctl-prior"]
            prev = {
                "px": res["px"],
                "hist": h,
                "prior": priors[key],
                "cp": cp_used,
                "t0": t0,
                "origin": [ox0, oy0],
            }
        pick = np.arange(0, rows, every)
        tracks = {}
        for s in SYSTEMS2:
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
                "handed": handed,
                "guard": res["guard"],
                "seconds": float(res["seconds"]["total"]),
                "parts": {k: round(float(x), 2) for k, x in res["seconds"].items()},
                "search_s": res.get("search_s", {}),
                "bearings": res["bearings"],
            }
        )
    return out
