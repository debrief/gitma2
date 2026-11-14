"""One shard of spec 018: the standing control exactly as registered (``run4``), and beside
it controls whose manoeuvre prior is chosen from a family, a hedged track with a spread,
and the readings that say where any gain comes from.

On the bearings the control sees (edited; an effective sd when the errors look correlated),
two searches (under the family's busiest and quietest members) give one set of candidate
histories; every member refits and scores that set.

* ``fam-<member>``: the history declared under that member's prior by the control's rule
  (margin and quiet probability the first of the settings'). One per member: what each
  fixed prior gives, and the material for choosing a member by a group of periods.
* ``ada-dM-qQ``: the member chosen by this period's evidence alone, declared.
* ``ada-hT``: the mean track of every member's candidates at temperature T, with the
  mixture's sd of range (arrays ``hrange_ada-hT`` and ``spread_ada-hT``, metres);
* ``ada-aP``: per period, the declared history when the mixture's first candidate has
  probability at least P, the hedged track otherwise (a rule that reads no truth);
* ``true``: the search told the split's own statistics, declared by the same rule (what a
  right prior is worth; not a bound);
* ``ref-full``: the true history, times held, fitted with Annex B's prior (told the true
  times; not a bound), and each true manoeuvre's ``detectability`` (spec 017), read only
  to class periods.

Arrays also carry ``logz`` [periods in the shard, members] and ``logz_period``; the record
of a period gains the member posterior, the member chosen and the histories.
"""

from __future__ import annotations

import math
import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .adapt import hedged_spread, log_sum, mixture, rate_posterior, rescore, union
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

FAMILY = "L"  # the family's members' keys start with this


def members(priors: dict[str, ManoeuvrePrior]) -> list[str]:
    return [k for k in priors if k.startswith(FAMILY)]


def extra_names(settings: dict[str, Any], keys: list[str]) -> list[str]:
    names = [f"fam-{k}" for k in keys]
    names += [f"ada-h{t:g}" for t in settings["temperatures"]]
    names += [f"ada-d{m:g}-q{q:g}" for m in settings["margins"][:1] for q in settings["quiets"][:1]]
    names += [f"ada-a{p:g}" for p in settings.get("auto_thresholds", [])]
    return names + ["true", "ref-full"]


def run_shard6(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: study L's "v3" and "broad", "true" (the split's own statistics; absent on
    a quiet split) and the family's members. ``settings["member_weights"]`` gives a member's
    weight beforehand (equal when absent); ``settings["search_members"]`` names the members
    whose searches supply the candidates."""
    arrays, recs = run_shard4(periods, priors, c_params, c2, settings)
    every = int(settings["score_every"])
    margin, quiet = float(settings["margins"][0]), float(settings["quiets"][0])
    temps = [float(x) for x in settings["temperatures"]]
    autos = [float(x) for x in settings.get("auto_thresholds", [])]
    top = int(settings["candidates"])
    keys = members(priors)
    given = settings.get("member_weights") or {}
    logw = {k: math.log(float(given.get(k, 1.0))) for k in keys}
    norm = log_sum(np.array(list(logw.values())))
    logw = {k: v - norm for k, v in logw.items()}
    searched = list(settings["search_members"])
    names = extra_names(settings, keys)
    hedges = [f"ada-h{t:g}" for t in temps]
    said = f"ada-d{margin:g}-q{quiet:g}"
    p3 = priors["v3"]
    res = solve_systems(periods, ["c2-end-nofade"], c_params, c2)
    errs: dict[str, list[np.ndarray]] = {s: [] for s in names}
    extra: dict[str, list[np.ndarray]] = {
        f"{a}_{h}": [] for h in hedges for a in ("hrange", "spread")
    }
    trks: dict[str, list[np.ndarray]] = {s: [] for s in names}
    logz_rows: list[list[float]] = []
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

        found: list[list[History]] = []
        for key in searched:
            t0 = time.perf_counter()
            got, _seen = _search(px, priors[key], cc.states, spc, {**settings, "candidates": top})
            took[f"ada/search/{key}"] = time.perf_counter() - t0
            found.append([h for h, _p in got])
        shared = union(found)
        t0 = time.perf_counter()
        sets = {k: rescore(px, shared, priors[k]) for k in keys}
        took["ada/rescore"] = time.perf_counter() - t0
        logz = {k: log_sum(np.array([h.evidence for h in s])) for k, s in sets.items()}
        logz_rows.append([float(logz[k]) for k in keys])
        post = rate_posterior({k: np.array([h.evidence for h in s]) for k, s in sets.items()}, logw)
        best = max(post, key=lambda k: post[k])
        rec["member_posterior"] = {k: round(float(p), 6) for k, p in post.items()}
        rec["member_chosen"] = best
        rec["leg_inferred_s"] = float(sum(post[k] * priors[k].leg_mean for k in keys))
        rec["candidates_shared"] = len(shared)
        t0 = time.perf_counter()
        for k in keys:
            if not sets[k]:
                continue
            path = elimination_path(px, sets[k][0], priors[k])
            hd = path[declared(path, margin, quiet)]
            tracks[f"fam-{k}"] = hd.fit.states
            rec["histories"][f"fam-{k}"] = {"spans": hd.fit.spans.tolist()}
        took["ada/paths"] = time.perf_counter() - t0
        if sets[best]:
            tracks[said] = tracks[f"fam-{best}"]
            rec["histories"][said] = rec["histories"][f"fam-{best}"]
            mix = mixture(sets, logw, top, quiet)
            t0 = time.perf_counter()
            for tt in temps:
                st, mean, spread, w = hedged_spread(px, mix, priors, tt)
                name = f"ada-h{tt:g}"
                tracks[name] = st
                side[f"hrange_{name}"], side[f"spread_{name}"] = mean, spread
                if tt == temps[0]:
                    rec["mixture"] = {
                        "weights": [round(float(q), 6) for q in w],
                        "manoeuvres": [int(h.fit.spans.shape[0]) for h, _k, _s in mix],
                        "members": [k for _h, k, _s in mix],
                    }
                    for p in autos:
                        tracks[f"ada-a{p:g}"] = tracks[said] if float(w[0]) >= p else st
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
    arrays["logz"] = np.array(logz_rows, dtype=np.float64).reshape(len(periods), len(keys))
    arrays["logz_period"] = np.array([x.ordinal for x in periods], dtype=np.int64)
    if "trk_period" in arrays:
        arrays.update({f"trk_{s}": np.concatenate(e) for s, e in trks.items()})
    return arrays, recs
