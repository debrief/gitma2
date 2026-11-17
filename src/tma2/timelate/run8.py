"""One shard of spec 025: the standing control on several periods of one target.

Per engagement (``layout``: two or three periods with gaps), the control ``ctl`` declared at
margin 1 with a 1% quiet probability (spec 016's ``ctl-d1-q0.01``, ``run4`` unchanged) is run
three ways on the same bearings:

* ``alone``: each period by itself (the standing system);
* ``joint``: the whole span with the gaps' bearings marked missing (research R1);
* ``full``: the whole span with every bearing (what the gaps cost; a reading).

Beside, from the same calls: C″ and one leg per period (``c2``, ``one-leg``), and the true
history fitted with the prior (``history-best``) per period (``ref-alone``) and across the
masked span (``ref-span``).

Each period is scored at rows 30 s apart from its own start (``score_every`` rows). Arrays per
scored row: ``eng``, ``period`` (index in the engagement), ``bound_span`` [3] (the
known-history bound from the masked span's bearings: the rows are chosen by it, R2),
``bound_own`` [3] (from the period's own bearings), ``true_range``, and ``err_<system>`` [4].
Where the joint solve gives no track the period's own answer is used and counted
(``joint_fell_back``).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .layout import Layout, layout, period, span
from .periods import Period
from .prior import ManoeuvrePrior
from .run4 import run_shard4
from .score import row_errors, truth_rows

CTL = "ctl-d1-q0.01"
SYSTEMS = ("alone", "joint", "full", "c2", "one-leg", "ref-alone", "ref-span")


def control_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """``run4``'s settings for the control alone, its tracks kept at every row."""
    return {
        **settings,
        "systems": ["ctl"],
        "score_every": 1,
        "store_tracks": 1 << 62,
        "temperatures": [],
        "margins": [1.0],
        "quiets": [0.01],
    }


def layout_options(settings: dict[str, Any]) -> dict[str, Any]:
    """The plan's ``settings.layout`` (period and gap ranges in seconds, period counts)."""
    lo = settings.get("layout") or {}
    out: dict[str, Any] = {}
    if "period_s" in lo:
        out["period_s"] = (float(lo["period_s"][0]), float(lo["period_s"][1]))
    if "gap_s" in lo:
        out["gap_s"] = (float(lo["gap_s"][0]), float(lo["gap_s"][1]))
    if "counts" in lo:
        out["counts"] = tuple(int(k) for k in lo["counts"])
    return out


def _tracks(arr: dict[str, np.ndarray], recs: list[dict[str, Any]]) -> list[dict[str, np.ndarray]]:
    """Per period of one ``run_shard4`` call: its tracks at every row."""
    out, at = [], 0
    for r in recs:
        n = int(r["rows"])
        out.append(
            {k[4:]: arr[k][at : at + n].astype(np.float64) for k in arr if k.startswith("trk_")}
        )
        at += n
    return out


def _seconds(x: Period, lay: Layout, a: int, n: int) -> list[float]:
    t = x.own[:, 0].astype(np.float64)
    t0 = float(t[lay.first])
    return [float(t[a] - t0), float(t[a + n - 1] - t0)]


def gap_events(x: Period, lay: Layout, declared: list[list[float]]) -> list[dict[str, Any]]:
    """Per gap: its length, the true manoeuvres overlapping it and the declared ones (spans in
    the span's seconds) overlapping it."""
    out = []
    t = x.own[:, 0].astype(np.float64)
    t0 = float(t[lay.first])
    for a, n in lay.gaps():
        lo, hi = float(t[a] - t0), float(t[a + n - 1] - t0)
        true = [
            s
            for s in x.meta.get("manoeuvres") or []
            if int(s["end_index"]) >= a and int(s["start_index"]) <= a + n - 1
        ]
        dec = [d for d in declared if d[1] >= lo and d[0] <= hi]
        out.append(
            {
                "seconds": [lo, hi],
                "length_s": hi - lo + x.dt,
                "true": len(true),
                "true_kinds": [s["kind"] for s in true],
                "declared": len(dec),
            }
        )
    return out


def run_shard8(
    engagements: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``engagements``: whole engagements (``iter_periods(..., whole=True)``)."""
    every = int(settings["score_every"])
    cs = control_settings(settings)
    keep = int(settings.get("store_tracks", 0))
    cols: dict[str, list[np.ndarray]] = {
        k: [] for k in ("eng", "period", "bound_span", "bound_own", "true_range")
    }
    errs: dict[str, list[np.ndarray]] = {s: [] for s in SYSTEMS}
    figs: dict[str, list[np.ndarray]] = {}
    recs: list[dict[str, Any]] = []
    for x in engagements:
        seed = np.uint64(int(x.meta["seed"]))
        lay = layout(seed, x.rows, x.dt, **layout_options(settings))
        rec: dict[str, Any] = {"ordinal": int(x.ordinal)}
        if lay is None:
            rec["skipped"] = "no two-period layout fits"
            recs.append(rec)
            continue
        pieces = [period(x, a, n) for a, n in lay.periods]
        joint, full = span(x, lay, masked=True), span(x, lay, masked=False)
        took: dict[str, float] = {}
        t0 = time.perf_counter()
        arr_a, rec_a = run_shard4(pieces, priors, c_params, c2, cs)
        took["alone"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        arr_j, rec_j = run_shard4([joint], priors, c_params, c2, cs)
        took["joint"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        arr_f, rec_f = run_shard4([full], priors, c_params, c2, cs)
        took["full"] = time.perf_counter() - t0
        tr_a = _tracks(arr_a, rec_a)
        (tr_j,), (tr_f,) = _tracks(arr_j, rec_j), _tracks(arr_f, rec_f)
        bound_span = arr_j["bound"].astype(np.float64)
        fell_back = []
        own_turns = []
        for i, (a, n) in enumerate(lay.periods):
            p = pieces[i]
            tr = truth_rows(p)
            pick = np.arange(0, n, every)
            off = a - lay.first
            js = tr_j[CTL][off : off + n]
            fb = not np.isfinite(js[:, :2]).all()
            fell_back.append(fb)
            tracks = {
                "alone": tr_a[i][CTL],
                "joint": tr_a[i][CTL] if fb else js,
                "full": tr_f[CTL][off : off + n],
                "c2": tr_a[i]["c2"],
                "one-leg": tr_a[i]["one-leg"],
                "ref-alone": tr_a[i]["history-best"],
                "ref-span": tr_j["history-best"][off : off + n],
            }
            for s in SYSTEMS:
                errs[s].append(row_errors(tracks[s], tr)[pick].astype(np.float32))
            own_n = int(sum(int(r["rows"]) for r in rec_a[:i]))
            cols["eng"].append(np.full(pick.size, x.ordinal, dtype=np.int64))
            cols["period"].append(np.full(pick.size, i, dtype=np.int8))
            cols["bound_span"].append(bound_span[off : off + n][pick].astype(np.float32))
            cols["bound_own"].append(arr_a["bound"][own_n : own_n + n][pick].astype(np.float32))
            cols["true_range"].append(np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])[pick])
            own_turns.append(len(p.ownship_turns()))
        if x.ordinal < keep:  # whole-span tracks for figures, every scored step
            pick = np.arange(0, lay.rows, every)
            sp_tr = truth_rows(joint)[pick]
            figs.setdefault("fig_eng", []).append(np.full(pick.size, x.ordinal, dtype=np.int64))
            figs.setdefault("fig_truth", []).append(sp_tr.astype(np.float32))
            figs.setdefault("fig_joint", []).append(tr_j[CTL][pick].astype(np.float32))
            figs.setdefault("fig_full", []).append(tr_f[CTL][pick].astype(np.float32))
            alone = np.full((lay.rows, 4), np.nan)
            for i, (a, n) in enumerate(lay.periods):
                alone[a - lay.first : a - lay.first + n] = tr_a[i][CTL]
            figs.setdefault("fig_alone", []).append(alone[pick].astype(np.float32))
        hist_j = rec_j[0]["histories"].get(CTL, {}).get("spans", [])
        rec.update(
            {
                "layout": {
                    "first": lay.first,
                    "periods": [list(q) for q in lay.periods],
                    "gaps": [list(g) for g in lay.gaps()],
                    "period_seconds": [_seconds(x, lay, a, n) for a, n in lay.periods],
                },
                "own_turns": own_turns,
                "joint_fell_back": fell_back,
                "true": rec_j[0]["true"],
                "true_kinds": rec_j[0]["true_kinds"],
                "joint": hist_j,
                "full": rec_f[0]["histories"].get(CTL, {}).get("spans", []),
                "alone": [r["histories"].get(CTL, {}).get("spans", []) for r in rec_a],
                "alone_true": [r["true"] for r in rec_a],
                "gaps": gap_events(x, lay, hist_j),
                "reference_flagged": {
                    "span": rec_j[0]["reference_flagged"],
                    "alone": [r["reference_flagged"] for r in rec_a],
                },
                "history_converged": {
                    "span": rec_j[0]["history_converged"],
                    "alone": [r["history_converged"] for r in rec_a],
                },
                "edited": {"span": rec_j[0]["edited"], "alone": [r["edited"] for r in rec_a]},
                "seconds": {k: round(v, 2) for k, v in took.items()},
            }
        )
        recs.append(rec)
    if not cols["eng"]:
        raise ValueError("no engagement in this shard holds a two-period layout")
    arrays: dict[str, np.ndarray] = {
        "eng": np.concatenate(cols["eng"]),
        "period": np.concatenate(cols["period"]),
        "bound_span": np.concatenate(cols["bound_span"]),
        "bound_own": np.concatenate(cols["bound_own"]),
        "true_range": np.concatenate(cols["true_range"]).astype(np.float32),
    }
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    arrays.update({k: np.concatenate(v) for k, v in figs.items()})
    return arrays, recs
