"""One shard of spec 026: spec 025's systems and the carry across gaps.

Per engagement, ``run8.run_shard8`` (unchanged: ``ctl`` alone per period, the joint solve, every
bearing, C″, one leg, the references) and then the carry: each period in order, solved by
``carry.solve_ctl`` on its own bearings, its start from nothing replaced by the previous
period's declared carry state at its last row run forward through the gap. The first period has
nothing to carry and is ``ctl`` alone (recomputed; its agreement with ``run8``'s alone is
recorded).

Arrays: ``run8``'s, plus ``err_carry`` [rows, 4] and ``carry_first`` (the row belongs to an
engagement's first period) in the same row order.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .carry import Carried, carried_theta, solve_ctl
from .layout import layout, period
from .periods import Period
from .prior import ManoeuvrePrior
from .run8 import layout_options, run_shard8
from .score import row_errors, truth_rows
from .systems import solve_systems


def _problem(p: Period) -> tuple[Any, np.ndarray]:
    a, b = p.first, p.first + p.rows
    t_abs = p.own[a:b, 0].astype(np.float64)
    t = t_abs - float(t_abs[0])
    ox, oy = p.own[a:b, 1].astype(np.float64), p.own[a:b, 2].astype(np.float64)
    z, v = p.obs[a:b, 1].astype(np.float64), p.obs[a:b, 2] != 0
    sigma = float(p.meta["parameters"]["noise_sigma_rad"])
    return (t, ox, oy, z, v, sigma), t_abs


def carry_chain(
    pieces: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    """The carry's declared track [rows, 4] for each period in order, and per period a record
    (spans, whether it fell back to ``ctl`` alone, time)."""
    res = solve_systems(pieces, ["c2-end-nofade"], c_params, c2)
    tracks: list[np.ndarray] = []
    recs: list[dict[str, Any]] = []
    carried: Carried | None = None
    for i, p in enumerate(pieces):
        t0 = time.perf_counter()
        pb, t_abs = _problem(p)
        t = pb[0]
        cc = res["c2-end-nofade"][i]
        spc = np.array(
            [[t[max(a - 1, 0)], t[b]] for a, b in cc.transitions if b > a], dtype=np.float64
        ).reshape(-1, 2)
        theta = carried_theta(carried, float(t_abs[0])) if carried is not None else None
        fell_back = i > 0 and theta is None
        out = solve_ctl(pb, priors, cc.states, spc, settings, theta)
        if out is None:
            states = np.full((p.rows, 4), np.nan)
            spans: list[list[float]] = []
        else:
            states, sp = out
            spans = (sp + float(t_abs[0])).tolist()  # absolute seconds
        tracks.append(states)
        last = states[-1]
        carried = Carried(float(t_abs[-1]), last.copy()) if np.isfinite(last).all() else None
        recs.append(
            {
                "carried": theta is not None,
                "fell_back": bool(fell_back),
                "spans_abs_s": spans,
                "seconds": round(time.perf_counter() - t0, 2),
            }
        )
    return tracks, recs


def run_shard9(
    engagements: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    every = int(settings["score_every"])
    parts: dict[str, list[np.ndarray]] = {}
    recs: list[dict[str, Any]] = []
    for x in engagements:
        lay = layout(np.uint64(int(x.meta["seed"])), x.rows, x.dt, **layout_options(settings))
        if lay is None:
            recs.append({"ordinal": int(x.ordinal), "skipped": "no two-period layout fits"})
            continue
        arr, (rec,) = run_shard8([x], priors, c_params, c2, settings)
        pieces = [period(x, a, n) for a, n in lay.periods]
        t0 = time.perf_counter()
        tracks, crecs = carry_chain(pieces, priors, c_params, c2, settings)
        rec["seconds"]["carry"] = round(time.perf_counter() - t0, 2)
        errs, first = [], []
        for i, p in enumerate(pieces):
            pick = np.arange(0, p.rows, every)
            errs.append(row_errors(tracks[i], truth_rows(p))[pick].astype(np.float32))
            first.append(np.full(pick.size, i == 0, dtype=bool))
        err_carry = np.concatenate(errs)
        if err_carry.shape[0] != arr["eng"].shape[0]:
            raise ValueError(f"engagement {x.ordinal}: carry rows do not match run8's")
        n0 = first[0].size  # the first period's carry is ctl alone, recomputed
        d0 = np.abs(err_carry[:n0].astype(np.float64) - arr["err_alone"][:n0].astype(np.float64))
        rec["carry_first_max_diff"] = float(np.nanmax(d0, initial=0.0))
        rec["carry"] = crecs
        arr["err_carry"] = err_carry
        arr["carry_first"] = np.concatenate(first)
        for k, v in arr.items():
            parts.setdefault(k, []).append(v)
        recs.append(rec)
    if not parts:
        raise ValueError("no engagement in this shard holds a two-period layout")
    return {k: np.concatenate(v) for k, v in parts.items()}, recs
