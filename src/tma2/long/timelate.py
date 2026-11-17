"""Time-late tracks over a long engagement (spec 023): the standing classical control ``ctl``
(spec 016, declared at margin 1, quiet probability 0.01) run on a chain of overlapping windows
and stitched into one track.

The control was built and decided on periods of 20 to 120 minutes. Its search adds or removes one
manoeuvre at a time and refits the whole period at each step, so its cost grows faster than the
period's length (``scaling``); a 48-hour engagement holds about 100 target manoeuvres against the
ten the search allows (``max_manoeuvres``). The chain keeps every window at the size the control
was decided on. Each row of the long track comes from the window whose centre is nearest, so the
seams sit in the middle of the overlaps, where both neighbours have bearings on either side.

A window may not start inside a target manoeuvre (its truth would have no initial leg), so its
start moves forward to the manoeuvre's end; the chain's step absorbs the shift.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from tma2.timelate.periods import Period

from .sim import Engagement
from .windows import in_manoeuvre, window

ROOT = Path(__file__).resolve().parents[3]
PLAN = "configs/timelate/tl-e.json"  # spec 016's registered settings for the control
SYSTEMS = ("ctl-d1-q0.01", "c2", "history-best")


def settings_and_priors() -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    from tma2.timelate.prior import ManoeuvrePrior
    from tma2.timelate.systems import c_parameters

    plan = json.loads((ROOT / PLAN).read_text())
    priors = {
        "v3": ManoeuvrePrior.from_ranges(json.loads((ROOT / plan["prior"]).read_text()), 3),
        "broad": ManoeuvrePrior.from_ranges(
            json.loads((ROOT / plan["prior_broad"]).read_text()), 3
        ),
    }
    c_params, c2 = c_parameters(ROOT / plan["gh_plan"])
    s = dict(plan["settings"])
    s.update({"systems": ["ctl"], "temperatures": [], "margins": [1], "quiets": [0.01]})
    s["store_tracks"] = 1 << 30
    return s, priors, c_params, c2


def chain(e: Engagement, window_s: float, overlap_s: float) -> list[tuple[int, int]]:
    """(first, rows) of each window, covering the engagement."""
    dt = e.dt
    w, step = int(round(window_s / dt)), int(round((window_s - overlap_s) / dt))
    out: list[tuple[int, int]] = []
    a = 0
    while True:
        end = in_manoeuvre(e, a)
        if end is not None:
            a = end + 1
        rows = min(w, e.samples - a)
        out.append((a, rows))
        if a + rows >= e.samples:
            return out
        a += step


def period_of(e: Engagement, first: int, rows: int, ordinal: int) -> Period:
    w = window(e, first, rows, "first")
    return Period(ordinal, w.meta, w.own, w.tgt, w.obs, 0, w.samples, w.dt)


def run_windows(
    e: Engagement,
    spans: list[tuple[int, int]],
    settings: dict[str, Any],
    priors: dict[str, Any],
    c_params: Any,
    c2: dict[str, Any],
) -> list[dict[str, Any]]:
    """The control on each window: its tracks at every ``score_every``-th row, its declared
    manoeuvres (seconds from the engagement's start) and how long it took."""
    from tma2.timelate.run4 import run_shard4

    out = []
    for j, (a, rows) in enumerate(spans):
        p = period_of(e, a, rows, j)
        t1 = time.perf_counter()
        arrays, recs = run_shard4([p], priors, c_params, c2, settings)
        took = time.perf_counter() - t1
        rec = recs[0]
        t0 = float(p.meta["window_t0_s"])
        ox, oy = p.meta["window_origin_m"]
        every = int(settings["score_every"])
        rows_abs = a + np.arange(0, rows, every)
        tracks = {}
        for s in SYSTEMS:
            st = arrays[f"trk_{s}"].astype(np.float64)
            st[:, 0] += ox
            st[:, 1] += oy
            tracks[s] = st
        hist = rec["histories"]
        out.append(
            {
                "first": a,
                "rows": rows,
                "rows_abs": rows_abs,
                "tracks": tracks,
                "declared": {
                    s: [[x + t0, y + t0] for x, y in hist.get(s, {}).get("spans", [])]
                    for s in ("ctl-d1-q0.01", "c2")
                },
                "true": [[x + t0, y + t0] for x, y in rec["true"]],
                "seconds": took,
                "parts": rec["seconds"],
                "bearings": rec["bearings"],
            }
        )
    return out


def stitch(e: Engagement, wins: list[dict[str, Any]], every: int) -> dict[str, Any]:
    """One long track per system: each row from the window whose centre is nearest."""
    rows = np.arange(0, e.samples, every)
    centres = np.array([w["first"] + w["rows"] / 2 for w in wins])
    states = {s: np.full((rows.size, 4), np.nan) for s in SYSTEMS}
    owner = np.full(rows.size, -1)
    for q, k in enumerate(rows):
        cand = [j for j, w in enumerate(wins) if w["first"] <= k < w["first"] + w["rows"]]
        if not cand:
            continue
        j = min(cand, key=lambda j: abs(centres[j] - k))
        w = wins[j]
        at = np.flatnonzero(w["rows_abs"] == k)
        if at.size != 1:
            continue
        owner[q] = j
        for s in SYSTEMS:
            states[s][q] = w["tracks"][s][at[0]]
    declared: dict[str, list[list[float]]] = {}
    dt = e.dt
    for s in ("ctl-d1-q0.01", "c2"):
        keep = []
        for j, w in enumerate(wins):
            for a, b in w["declared"][s]:
                mid = int(round(0.5 * (a + b) / dt))
                near = [i for i, x in enumerate(wins) if x["first"] <= mid < x["first"] + x["rows"]]
                if near and min(near, key=lambda i: abs(centres[i] - mid)) == j:
                    keep.append([a, b])
        declared[s] = sorted(keep)
    truth = np.stack(
        [
            e.tgt[rows, 1],
            e.tgt[rows, 2],
            e.tgt[rows, 3],
            e.tgt[rows, 4],
            e.own[rows, 1],
            e.own[rows, 2],
        ],
        axis=1,
    )
    return {"rows": rows, "owner": owner, "states": states, "declared": declared, "truth": truth}


def scaling(
    e: Engagement,
    lengths_s: list[float],
    start_s: float,
    settings: dict[str, Any],
    priors: dict[str, Any],
    c_params: Any,
    c2: dict[str, Any],
) -> list[dict[str, Any]]:
    """The control's run time on one period of each length, all starting at ``start_s``."""
    from tma2.timelate.run4 import run_shard4

    out = []
    a = int(round(start_s / e.dt))
    end = in_manoeuvre(e, a)
    if end is not None:
        a = end + 1
    for L in lengths_s:
        rows = int(round(L / e.dt))
        p = period_of(e, a, rows, 0)
        t1 = time.perf_counter()
        _arr, recs = run_shard4([p], priors, c_params, c2, settings)
        out.append(
            {
                "seconds_long": L,
                "true_manoeuvres": len(recs[0]["true"]),
                "declared": len(recs[0]["histories"]["ctl-d1-q0.01"]["spans"]),
                "run_s": time.perf_counter() - t1,
                "parts": recs[0]["seconds"],
            }
        )
    return out
