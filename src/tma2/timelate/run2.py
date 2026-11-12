"""One shard of spec 014's systems. Gate T's runner (``run.py``) is untouched; this one adds
the corrected prior's search (``search2``), the flat-prior search, C″ refitted with the arc
model and prior, and the true history's evidence fitted without the true states, from which
wrong-history periods are classed at scoring. Systems are chosen by ``settings["systems"]``."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .arc import arc_states, fit_arc, fit_arc_search, solve_arc, start_from_track
from .bound import period_bound
from .controls import c2_refit
from .periods import Period
from .prior import ManoeuvrePrior
from .retest import Problem, Structure, joint_fit, log_evidence
from .run import nominal_starts
from .score import row_errors, strata_of, truth_rows
from .search import History, candidate_set, evidence_search
from .systems import solve_systems
from .thin import thin

BASE = ("c2", "one-leg", "history-fixed", "history-fit", "history-map", "history-best")
OPTIONAL = ("search", "search2", "search-flat", "c2-refit")


def consistent(cost: float, n: int) -> bool:
    """A fit whose cost is what the bearing noise explains (within five sd of χ²(n))."""
    return bool(cost <= n + 5.0 * np.sqrt(2.0 * n))


def _search(
    pb: Problem,
    prior: ManoeuvrePrior,
    c_states: np.ndarray,
    spc: np.ndarray,
    settings: dict[str, Any],
) -> tuple[list[tuple[History, float]], int]:
    """Gate T's search from its two starts (C″'s answer and nothing) under ``prior``."""
    t, ox, oy, z, v, sigma = pb
    steps, most = int(settings["steps"]), int(settings["max_manoeuvres"])
    seen: list[History] = []
    if np.isfinite(c_states).all():
        f0, _, _ = solve_arc(t, ox, oy, z, v, sigma, spc, c_states)
        seen += evidence_search(pb, f0.theta, spc, prior, most, steps)[1]
    none = np.zeros((0, 2))
    b0 = None
    for q0 in nominal_starts(pb):
        f = fit_arc(t, ox, oy, z, v, sigma, none, q0)
        if b0 is None or f.cost < b0.cost:
            b0 = f
    assert b0 is not None
    seen += evidence_search(pb, b0.theta, none, prior, most, steps)[1]
    return candidate_set(seen, top=int(settings["candidates"])), len(seen)


def reference(
    pb: Problem, spans: np.ndarray, kinds: np.ndarray, prior: ManoeuvrePrior
) -> tuple[Structure, Structure, Structure]:
    """Gate T's ``history_reference`` returning the fits themselves (times held; times free;
    to the posterior), so their tracks can be read at rows the fit did not see."""
    t, ox, oy, z, v, sigma = pb
    m = spans.shape[0]
    best = None
    for q0 in nominal_starts(pb):
        th0 = np.concatenate([q0, np.zeros(2 * m)])
        for i in range(m):
            th0[4 + 2 * i] = 0.5 if kinds[i, 0] else 0.0
            th0[5 + 2 * i] = 1.0 if (kinds[i, 1] and not kinds[i, 0]) else 0.0
        f, _n = fit_arc_search(t, ox, oy, z, v, sigma, spans, th0, kinds if m else None)
        if best is None or f.cost < best.cost:
            best = f
    assert best is not None
    held = Structure(best.theta, spans, float(best.cost), best.states)
    fit = joint_fit(pb, best.theta, spans, free_changes=kinds)
    post = joint_fit(pb, fit.theta, fit.spans, free_changes=kinds, prior=prior)
    return held, fit, post


def _history(spans: np.ndarray, kinds: np.ndarray, evidence: float) -> dict[str, Any]:
    return {"spans": spans.tolist(), "kinds": kinds.tolist(), "evidence": float(evidence)}


def run_shard2(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: "v1" (Gate T's), "v2" (corrected) and "flat". Arrays: ``period``, ``bound``,
    ``stratum`` and ``true_range`` at the scored rows and ``err_<system>`` [rows, 4]. One
    record per period: the true history, each system's history, ``search2``'s candidates, the
    true history's evidence under the corrected prior, and run times."""
    every = int(settings["score_every"])
    chosen = [s for s in OPTIONAL if s in settings.get("systems", OPTIONAL)]
    names = list(BASE) + chosen
    t_layer = time.perf_counter()
    res = solve_systems(periods, ["c2-end-nofade", "one-leg"], c_params, c2)
    t_layer = (time.perf_counter() - t_layer) / max(len(periods), 1)
    p2 = priors["v2"]
    errs: dict[str, list[np.ndarray]] = {s: [] for s in names}
    bounds, owner, strata, ranges, recs = [], [], [], [], []
    for i, x in enumerate(periods):
        a, b = x.first, x.first + x.rows
        t = x.own[a:b, 0].astype(np.float64) - float(x.own[a, 0])
        ox, oy = x.own[a:b, 1].astype(np.float64), x.own[a:b, 2].astype(np.float64)
        z, v = x.obs[a:b, 1].astype(np.float64), x.obs[a:b, 2] != 0
        sigma = float(x.meta["parameters"]["noise_sigma_rad"])
        full: Problem = (t, ox, oy, z, v, sigma)
        pb = thin(full, str(settings.get("thinning", "none")))
        at = np.clip(np.searchsorted(t, pb[0]), 0, x.rows - 1)  # the fit's rows in the period

        def track(s: Structure, t: np.ndarray = t) -> np.ndarray:
            out: np.ndarray = arc_states(s.theta, t, s.spans)
            return out

        tr = truth_rows(x)
        pick = np.arange(0, x.rows, every)
        nan = np.full((x.rows, 4), np.nan)
        tracks: dict[str, np.ndarray] = {s: nan for s in names}
        took: dict[str, float] = {"layer": t_layer}
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
        edge = [bool(s["began_before"]) or int(s["end_index"]) >= x.rows - 1 for s in sp]
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)
        hist: dict[str, Any] = {"c2": {"spans": spc.tolist()}}
        rec: dict[str, Any] = {
            "ordinal": int(x.ordinal),
            "first_row": int(x.first),
            "rows": int(x.rows),
            "bearings": int(v.sum()),
            "true": spt.tolist(),
            "true_kinds": kt.tolist(),
            "true_edge": edge,
            "ownship_turns": len(x.ownship_turns()),
        }
        # the reference: the true history's structure, never its states
        t0 = time.perf_counter()
        held, hf, hm = reference(pb, spt, kt, p2)
        took["reference"] = time.perf_counter() - t0
        tracks["history-fixed"] = track(held)
        tracks["history-fit"], tracks["history-map"] = track(hf), track(hm)
        true_ev = float(log_evidence(pb, hm, kt, p2)["total"])
        best_true = hm
        rec["history_cost"] = float(hf.cost)
        rec["history_converged"] = consistent(float(hf.cost), int(pb[4].sum()))
        rec["fit_points"] = int(pb[4].sum())
        cands2: list[tuple[History, float]] = []
        for name, key in (("search", "v1"), ("search2", "v2"), ("search-flat", "flat")):
            if name not in chosen:
                continue
            t0 = time.perf_counter()
            cands, n_seen = _search(pb, priors[key], cc.states[at], spc, settings)
            took[name] = time.perf_counter() - t0
            if not cands:
                continue
            top = cands[0][0]
            tracks[name] = track(top.fit)
            hist[name] = _history(top.fit.spans, top.kinds, top.evidence)
            if name == "search2":
                cands2 = cands
                rec["histories_evaluated"] = n_seen
                rec["candidates"] = [
                    {**_history(h.fit.spans, h.kinds, h.evidence), "theta": h.fit.theta.tolist()}
                    for h, _p in cands
                ]
        if "c2-refit" in chosen:
            t0 = time.perf_counter()
            try:
                g, kinds, ev = c2_refit(pb, spc, cc.states[at], p2, nominal_starts(pb))
                tracks["c2-refit"] = track(g)
                hist["c2-refit"] = _history(g.spans, kinds, ev["total"])
            except ValueError:
                pass
            took["c2-refit"] = time.perf_counter() - t0
        if cands2:  # the true structure again, started from the search's own best track
            th = start_from_track(cands2[0][0].fit.states, pb[0], spt)
            th[4:][~kt.reshape(-1)] = 0.0
            for j in range(spt.shape[0]):
                for c in range(2):
                    if kt[j, c] and th[4 + 2 * j + c] == 0.0:
                        th[4 + 2 * j + c] = 0.5 if c == 0 else 1.0
            alt = joint_fit(pb, th, spt, free_changes=kt, prior=p2)
            e = float(log_evidence(pb, alt, kt, p2)["total"])
            if np.isfinite(e) and (not np.isfinite(true_ev) or e > true_ev):
                true_ev, best_true = e, alt
        tracks["history-best"] = track(best_true)
        rec["true_evidence"] = true_ev
        rec["true_fit_spans"] = best_true.spans.tolist()
        rec["histories"] = hist
        rec["seconds"] = {k: round(float(s), 2) for k, s in took.items()}
        bd = period_bound(x)
        bounds.append(bd[pick])
        owner.append(np.full(pick.size, x.ordinal, dtype=np.int64))
        strata.append(strata_of(x, x.rows)[pick])
        ranges.append(np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])[pick].astype(np.float32))
        for s in names:
            errs[s].append(row_errors(tracks[s], tr)[pick].astype(np.float32))
        recs.append(rec)
    arrays: dict[str, np.ndarray] = {
        "period": np.concatenate(owner),
        "bound": np.concatenate(bounds).astype(np.float32),
        "stratum": np.concatenate(strata),
        "true_range": np.concatenate(ranges),
    }
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    return arrays, recs
