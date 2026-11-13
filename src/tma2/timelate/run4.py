"""One shard of spec 016's classical controls (research R1 to R5, R13), beside the standing
search (spec 015's ``search3``: Annex B's prior, version 3, the bearings as given).

Single-factor controls, each the same search with one thing changed:

* ``edit``: wild bearings edited out;
* ``corr``: an effective bearing sd from the estimated error correlation;
* ``broad``: a broadened manoeuvre prior; ``mix2``: ``search3`` and ``broad`` pooled.

The combined control ``ctl`` is what a system that is not told the conditions would run:
edit, then estimate the correlation (used only above ``corr.MIN_SHARE``), then search under
both priors and pool. For every search ``X``: ``X`` is its first candidate's track,
``X-hT`` the hedged track at temperature T, and for ``search3`` and ``ctl``
``X-dM-qQ`` the declared history at margin M and quiet probability Q.

The true-history reference is given three ways (``history-fixed``: bearings only, times
held; ``history-map``: fitted with the prior, times free; ``history-held``: fitted with the
prior, times held) and as ``history-best`` (free unless it drifted, spec 015's rule).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .bound import period_bound
from .corr import MIN_SHARE, edited, effective, estimate
from .hedge import declared, elimination_path, hedged, pool
from .learned import arc_readout
from .match import cut_flags, same_history
from .periods import Period
from .prior import ManoeuvrePrior
from .retest import Problem, joint_fit
from .run2 import _history, _search, consistent, reference
from .run3 import refit_acceptable
from .score import row_errors, strata_of, truth_rows
from .search import History
from .systems import solve_systems

BASE = ("c2", "one-leg", "history-fixed", "history-map", "history-held", "history-best")
SEARCHES = ("search3", "edit", "corr", "broad", "mix2", "ctl")
DECLARED = ("search3", "ctl")
MATCH_S = 120.0


def system_names(settings: dict[str, Any]) -> list[str]:
    chosen = [s for s in SEARCHES if s in settings.get("systems", SEARCHES)]
    names = list(BASE)
    for s in chosen:
        names.append(s)
        names += [f"{s}-h{t:g}" for t in settings.get("temperatures", [])]
        if s in DECLARED:
            names += [
                f"{s}-d{m:g}-q{q:g}"
                for m in settings.get("margins", [])
                for q in settings.get("quiets", [])
            ]
    return names


def run_shard4(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
    learned: dict[str, dict[str, np.ndarray]] | None = None,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: "v3" (Annex B) and "broad". ``learned``: per model name, the arrays of a
    ``tma2-tlpredict`` shard for these periods; each gives two systems, ``<name>`` (the
    model's own track) and ``<name>-arc`` (the declared read-out: the arc model with Annex
    B's prior fitted to the bearings ``ctl`` sees, at the model's manoeuvres, started from
    the model's track; the model's own track where that fit fails or is not acceptable by
    spec 015's rule for a refit).
    Arrays: ``period``, ``bound``, ``stratum``,
    ``true_range`` and ``err_<system>`` at every ``score_every``-th row; for periods with
    ordinal below ``store_tracks``, ``trk_period``, ``trk_truth`` and ``trk_<system>`` at
    the same rows."""
    every = int(settings["score_every"])
    chosen = [s for s in SEARCHES if s in settings.get("systems", SEARCHES)]
    names = system_names(settings)
    learned = learned or {}
    for ln in learned:
        names += [ln, f"{ln}-arc"]
    temps = [float(x) for x in settings.get("temperatures", [])]
    margins = [float(x) for x in settings.get("margins", [])]
    quiets = [float(x) for x in settings.get("quiets", [])]
    keep = int(settings.get("store_tracks", 0))
    top = int(settings["candidates"])
    res = solve_systems(periods, ["c2-end-nofade", "one-leg"], c_params, c2)
    p3 = priors["v3"]
    errs: dict[str, list[np.ndarray]] = {s: [] for s in names}
    trks: dict[str, list[np.ndarray]] = {s: [] for s in names}
    trk_owner: list[np.ndarray] = []
    trk_truth: list[np.ndarray] = []
    bounds, owner, strata, ranges, recs = [], [], [], [], []
    for i, x in enumerate(periods):
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
        took: dict[str, float] = {}
        cc = res["c2-end-nofade"][i]
        tracks["c2"], tracks["one-leg"] = cc.states, res["one-leg"][i].states
        sp = [s for s in x.spans() if s["end_index"] > s["start_index"]]
        spt = np.array(
            [[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp], dtype=np.float64
        ).reshape(-1, 2)
        kt = np.array(
            [[s["kind"] in ("course", "both"), s["kind"] in ("speed", "both")] for s in sp],
            dtype=bool,
        ).reshape(-1, 2)
        cut = cut_flags(x)
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)
        hist: dict[str, Any] = {"c2": {"spans": spc.tolist()}}
        rec: dict[str, Any] = {
            "ordinal": int(x.ordinal),
            "rows": int(x.rows),
            "seconds_long": float(t[-1]),
            "bearings": int(v.sum()),
            "true": spt.tolist(),
            "true_kinds": kt.tolist(),
            "true_cut": cut,
        }
        t0 = time.perf_counter()
        held, _hf, hm = reference(pb, spt, kt, p3)
        hh = joint_fit(pb, held.theta, spt, free_changes=kt, free_times=False, prior=p3)
        took["reference"] = time.perf_counter() - t0
        flagged = not same_history(spt, hm.spans, MATCH_S, cut)
        tracks["history-fixed"], tracks["history-map"] = held.states, hm.states
        tracks["history-held"] = hh.states
        tracks["history-best"] = hh.states if flagged else hm.states
        rec["reference_flagged"] = bool(flagged)
        rec["history_converged"] = consistent(float(held.cost), int(v.sum()))

        pe, n_edit = edited(pb)
        share, tau = estimate(pb)
        share_e, tau_e = estimate(pe)
        pc = effective(pb, share, tau)
        px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
        rec["edited"] = n_edit
        rec["corr_estimate"] = [share, tau]
        rec["ctl_corr_estimate"] = [share_e, tau_e, bool(share_e >= MIN_SHARE)]
        problems = {"plain": pb, "edit": pe, "corr": pc, "ctl": px}
        cache: dict[tuple[str, str], list[tuple[History, str]]] = {}

        def search(which: str, key: str) -> list[tuple[History, str]]:
            # ``ctl``'s problem is ``edit``'s when no correlation is used, and the plain
            # one when nothing was edited either: one search serves both
            if which == "ctl" and share_e < MIN_SHARE:  # noqa: B023
                which = "edit"
            if which == "edit" and n_edit == 0:  # noqa: B023
                which = "plain"
            if (which, key) not in cache:  # noqa: B023
                t1 = time.perf_counter()
                c, _n = _search(
                    problems[which],  # noqa: B023
                    priors[key],
                    cc.states,  # noqa: B023
                    spc,  # noqa: B023
                    {**settings, "candidates": top},
                )
                took[f"{which}/{key}"] = time.perf_counter() - t1  # noqa: B023
                cache[(which, key)] = [(h, f"{which}/{key}") for h, _p in c]  # noqa: B023
            return cache[(which, key)]  # noqa: B023

        for name in chosen:
            if name == "search3":
                cands = search("plain", "v3")
            elif name in ("edit", "corr"):
                cands = search(name, "v3")
            elif name == "broad":
                cands = search("plain", "broad")
            elif name == "mix2":
                cands = pool([search("plain", "v3"), search("plain", "broad")], top)
            else:
                cands = pool([search("ctl", "v3"), search("ctl", "broad")], top)
            if not cands:
                continue
            h0, tag0 = cands[0]
            tracks[name] = h0.fit.states
            ev = np.array([h.evidence for h, _ in cands])
            for tt in temps:
                tracks[f"{name}-h{tt:g}"] = hedged([h.fit.states for h, _ in cands], ev, tt)
            entry = _history(h0.fit.spans, h0.kinds, h0.evidence)
            entry["prior"] = tag0
            entry["candidates"] = [
                {**_history(h.fit.spans, h.kinds, h.evidence), "prior": g} for h, g in cands[:5]
            ]
            if name in ("mix2", "ctl"):  # Bayes factor, broad prior over Annex B's
                best = {k: -np.inf for k in ("v3", "broad")}
                for h, g in cands:
                    k = g.split("/")[1]
                    best[k] = max(best[k], h.evidence)
                entry["log_bayes_broad"] = float(best["broad"] - best["v3"])
            if name in DECLARED and margins:
                which, key = tag0.split("/")
                t1 = time.perf_counter()
                path = elimination_path(problems[which], h0, priors[key])
                took[f"{name}/path"] = time.perf_counter() - t1
                entry["path"] = [_history(h.fit.spans, h.kinds, h.evidence) for h in path]
                grid = {}
                for mg in margins:
                    for q in quiets:
                        j = declared(path, mg, q)
                        tracks[f"{name}-d{mg:g}-q{q:g}"] = path[j].fit.states
                        grid[f"d{mg:g}-q{q:g}"] = j
                        hist[f"{name}-d{mg:g}-q{q:g}"] = {"spans": path[j].fit.spans.tolist()}
                entry["declared"] = grid
            hist[name] = entry
        for ln, arr in learned.items():
            at = np.flatnonzero(arr["ordinal"] == x.ordinal)
            if at.size != 1 or int(arr["rows"][at[0]]) != x.rows:
                raise ValueError(f"period {x.ordinal}: no (or another) period in {ln}'s shard")
            direct = arr["learned"][arr["row_period"] == x.ordinal].astype(np.float64)
            spans = arr["spans"][arr["span_period"] == x.ordinal].astype(np.float64).reshape(-1, 2)
            tracks[ln] = direct
            hist[ln] = {"spans": spans.tolist()}
            t1 = time.perf_counter()
            try:
                fit, kinds_l, ev_l = arc_readout(px, direct, spans, p3)
                if not refit_acceptable(px, fit, direct, p3):  # spec 015's rule, no truth
                    raise ValueError("the read-out is not a fit a system would accept")
                tracks[f"{ln}-arc"] = fit.states
                hist[f"{ln}-arc"] = _history(fit.spans, kinds_l, float(ev_l["total"]))
            except ValueError:  # no acceptable fit: the model's own track stands
                tracks[f"{ln}-arc"] = direct
                hist[f"{ln}-arc"] = {"spans": spans.tolist(), "fell_back": True}
            took[f"{ln}/arc"] = time.perf_counter() - t1
        rec["histories"] = hist
        rec["seconds"] = {k: round(float(s), 2) for k, s in took.items()}
        bounds.append(period_bound(x)[pick])
        owner.append(np.full(pick.size, x.ordinal, dtype=np.int64))
        strata.append(strata_of(x, x.rows)[pick])
        ranges.append(np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])[pick].astype(np.float32))
        for s in names:
            errs[s].append(row_errors(tracks[s], tr)[pick].astype(np.float32))
        if x.ordinal < keep:
            trk_owner.append(np.full(pick.size, x.ordinal, dtype=np.int64))
            trk_truth.append(tr[pick].astype(np.float32))
            for s in names:
                trks[s].append(tracks[s][pick].astype(np.float32))
        recs.append(rec)
    arrays: dict[str, np.ndarray] = {
        "period": np.concatenate(owner),
        "bound": np.concatenate(bounds).astype(np.float32),
        "stratum": np.concatenate(strata),
        "true_range": np.concatenate(ranges),
    }
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    if trk_owner:
        arrays["trk_period"] = np.concatenate(trk_owner)
        arrays["trk_truth"] = np.concatenate(trk_truth)
        arrays.update({f"trk_{s}": np.concatenate(e) for s, e in trks.items()})
    return arrays, recs
