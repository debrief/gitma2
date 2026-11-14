"""One shard of spec 018: the standing control exactly as registered (``run4``), and beside
it a control whose manoeuvre prior adapts to the period, a hedged track with a spread, and
the readings that say where any gain comes from.

On the bearings the control sees (edited; an effective sd when the errors look correlated):

* ``ada``: the first candidate under the inferred rate; ``ada-dM-qQ``: the history declared
  under that rate's prior by the control's rule (margin M, quiet probability Q);
* ``ada-hT``: the mean track of the candidates of every rate at temperature T, with the
  mixture's sd of range (arrays ``hrange_ada-hT`` and ``spread_ada-hT``, metres);
* ``ada-aP``: per period, the declared history when the mixture's first candidate has
  probability at least P, the hedged track otherwise (a rule that reads no truth);
* ``true``: the search told the split's own statistics, declared by the same rule (what a
  right prior is worth; not a bound);
* ``ref-full``: the true history, times held, fitted with Annex B's prior (told the true
  times; not a bound), and each true manoeuvre's ``detectability`` (spec 017), read only
  to class periods.

Per period the record gains the rate posterior, the inferred leg length and the histories.
"""

from __future__ import annotations

import math
import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .adapt import hedged_spread, mixture, rate_posterior
from .corr import MIN_SHARE, edited, effective, estimate
from .detect import detectability, detectable_reference
from .hedge import declared, elimination_path
from .periods import Period
from .prior import ManoeuvrePrior
from .retest import Problem
from .run2 import _history, _search
from .run4 import run_shard4
from .score import row_errors, truth_rows
from .search import History
from .systems import solve_systems


def extra_names(settings: dict[str, Any]) -> list[str]:
    names = ["ada"]
    names += [f"ada-h{t:g}" for t in settings["temperatures"]]
    names += [f"ada-d{m:g}-q{q:g}" for m in settings["margins"] for q in settings["quiets"]]
    names += [f"ada-a{p:g}" for p in settings.get("auto_thresholds", [])]
    return names + ["true", "ref-full"]


def run_shard6(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: study L's "v3" and "broad", "true" (the split's own statistics) and the
    rate grid's members (keys starting ``rate``). ``settings["rate_weights"]`` gives each
    member's weight beforehand (equal when absent)."""
    arrays, recs = run_shard4(periods, priors, c_params, c2, settings)
    every = int(settings["score_every"])
    margin, quiet = float(settings["margins"][0]), float(settings["quiets"][0])
    temps = [float(x) for x in settings["temperatures"]]
    autos = [float(x) for x in settings.get("auto_thresholds", [])]
    top = int(settings["candidates"])
    grid = {k: p for k, p in priors.items() if k.startswith("rate")}
    given = settings.get("rate_weights") or {}
    logw = {k: math.log(float(given.get(k, 1.0))) for k in grid}
    norm = math.log(sum(math.exp(v) for v in logw.values()))
    logw = {k: v - norm for k, v in logw.items()}
    names = extra_names(settings)
    hedges = [f"ada-h{t:g}" for t in temps]
    p3 = priors["v3"]
    res = solve_systems(periods, ["c2-end-nofade"], c_params, c2)
    errs: dict[str, list[np.ndarray]] = {s: [] for s in names}
    extra: dict[str, list[np.ndarray]] = {
        f"{a}_{h}": [] for h in hedges for a in ("hrange", "spread")
    }
    trks: dict[str, list[np.ndarray]] = {s: [] for s in names}
    keep = int(settings.get("store_tracks", 0))
    for i, (x, rec) in enumerate(zip(periods, recs, strict=True)):
        a, b = x.first, x.first + x.rows
        t = x.own[a:b, 0].astype(np.float64) - float(x.own[a, 0])
        ox, oy = x.own[a:b, 1].astype(np.float64), x.own[a:b, 2].astype(np.float64)
        z, v = x.obs[a:b, 1].astype(np.float64), x.obs[a:b, 2] != 0
        sigma = float(x.meta["parameters"]["noise_sigma_rad"])
        pb: Problem = (t, ox, oy, z, v, sigma)
        tr = truth_rows(x)
        pick = np.arange(0, x.rows, every)
        nan = np.full((x.rows, 4), np.nan)
        tracks: dict[str, np.ndarray] = {s: nan for s in names}
        side = {k: np.full(x.rows, np.nan) for k in extra}
        took: dict[str, float] = {}
        spt = np.array(rec["true"], dtype=np.float64).reshape(-1, 2)
        kt = np.array(rec["true_kinds"], dtype=bool).reshape(-1, 2)

        t0 = time.perf_counter()
        det, full_cost = detectability(pb, spt, kt)
        rec["detectability"] = [float(d) for d in det]
        rec["true_history_cost"] = float(full_cost)
        tracks["ref-full"] = detectable_reference(pb, spt, kt, det, 0.0, p3).states
        took["detectability"] = time.perf_counter() - t0

        pe, _n = edited(pb)
        share_e, tau_e = estimate(pe)
        px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
        cc = res["c2-end-nofade"][i]
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)

        cands: list[tuple[History, float]] = []
        if "true" in priors:
            t0 = time.perf_counter()
            cands, _seen = _search(px, priors["true"], cc.states, spc, settings)
            took["true"] = time.perf_counter() - t0
        if cands:
            path = elimination_path(px, cands[0][0], priors["true"])
            h = path[declared(path, margin, quiet)]
            tracks["true"] = h.fit.states
            rec["histories"]["true"] = _history(h.fit.spans, h.kinds, h.evidence)

        sets = {}
        for key, prior in grid.items():
            t0 = time.perf_counter()
            found, _seen = _search(px, prior, cc.states, spc, {**settings, "candidates": top})
            took[f"ada/{key}"] = time.perf_counter() - t0
            sets[key] = [h for h, _p in found]
        post = rate_posterior({k: np.array([h.evidence for h in s]) for k, s in sets.items()}, logw)
        best = max(post, key=lambda k: post[k])
        rec["rate_posterior"] = {k: float(p) for k, p in post.items()}
        rec["rate_inferred"] = best
        rec["leg_inferred_s"] = float(sum(post[k] * grid[k].leg_mean for k in grid))
        if sets[best]:
            top_h = sets[best][0]
            tracks["ada"] = top_h.fit.states
            t0 = time.perf_counter()
            path = elimination_path(px, top_h, grid[best])
            took["ada/path"] = time.perf_counter() - t0
            entry = _history(top_h.fit.spans, top_h.kinds, top_h.evidence)
            entry["prior"] = best
            rec["histories"]["ada"] = entry
            said: dict[str, np.ndarray] = {}
            for mg in settings["margins"]:
                for q in settings["quiets"]:
                    hd = path[declared(path, float(mg), float(q))]
                    name = f"ada-d{float(mg):g}-q{float(q):g}"
                    tracks[name] = said[name] = hd.fit.states
                    rec["histories"][name] = {"spans": hd.fit.spans.tolist()}
            mix = mixture(sets, logw, top)
            t0 = time.perf_counter()
            for tt in temps:
                st, mean, spread, w = hedged_spread(px, mix, grid, tt)
                name = f"ada-h{tt:g}"
                tracks[name] = st
                side[f"hrange_{name}"], side[f"spread_{name}"] = mean, spread
                if tt == temps[0]:
                    rec["mixture"] = {
                        "weights": [float(q) for q in w],
                        "manoeuvres": [int(h.fit.spans.shape[0]) for h, _k, _s in mix],
                        "rates": [k for _h, k, _s in mix],
                    }
                    first = f"ada-d{margin:g}-q{quiet:g}"
                    for p in autos:
                        tracks[f"ada-a{p:g}"] = said[first] if float(w[0]) >= p else st
                        rec.setdefault("auto", {})[f"{p:g}"] = bool(float(w[0]) >= p)
            took["ada/hedge"] = time.perf_counter() - t0
        rec["seconds"].update({k: round(float(s), 2) for k, s in took.items()})
        for s in names:
            errs[s].append(row_errors(tracks[s], tr)[pick].astype(np.float32))
        for k, val in side.items():
            extra[k].append(val[pick].astype(np.float32))
        if x.ordinal < keep:
            for s in names:
                trks[s].append(tracks[s][pick].astype(np.float32))
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    arrays.update({k: np.concatenate(e) for k, e in extra.items()})
    if "trk_period" in arrays:
        arrays.update({f"trk_{s}": np.concatenate(e) for s, e in trks.items()})
    return arrays, recs
