"""One shard of spec 015's systems: spec 014's runner with its three repairs. The searches
use prior version 3 (``search3``, ``search3-flat``, ``search3-mix``), with spec 014's
``search2`` beside for the before-and-after; the true-history reference is held to the true
times where it drifts into another history, and flagged; the refit control falls back to
C″'s own track when its fit is not one a system would accept. ``run2.py`` is untouched."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .arc import arc_states, start_from_track
from .bound import period_bound
from .controls import c2_refit
from .match import cut_flags, same_history
from .periods import Period
from .prior import ManoeuvrePrior
from .retest import Problem, Structure, joint_fit, log_evidence
from .run import nominal_starts
from .run2 import _history, _search, consistent, reference
from .score import row_errors, strata_of, truth_rows
from .search import History
from .systems import solve_systems

BASE = ("c2", "one-leg", "history-fixed", "history-fit", "history-map", "history-best")
SEARCHES = (
    ("search2", "v2"),
    ("search3", "v3"),
    ("search3-flat", "flat3"),
    ("search3-mix", "mix3"),
)
OPTIONAL = tuple(n for n, _ in SEARCHES) + ("c2-refit",)
MATCH_S = 120.0
WORSE = 9.0  # a refit may cost this much more than the track it started from, no more
SPEED_MAX = 2.0  # ... and its speed stays within this multiple of the prior's fastest


def track_cost(pb: Problem, states: np.ndarray) -> float:
    """χ² of the bearings against a track given at the problem's rows."""
    _t, ox, oy, z, v, sigma = pb
    b = np.arctan2(states[:, 0] - ox, states[:, 1] - oy)
    r = ((z - b + np.pi) % (2 * np.pi) - np.pi)[v.astype(bool)] / sigma
    return float(r @ r)


def refit_acceptable(
    pb: Problem, fit: Structure, c_states: np.ndarray, prior: ManoeuvrePrior
) -> bool:
    """Whether a refit of C″'s transitions is kept (research R4; no truth): finite, at a
    speed and range a target could have, and either fitting the bearings as well as their
    noise allows or no worse than C″'s own track by more than ``WORSE``. (The chord track has
    four free unknowns a manoeuvre, so a sound arc refit may cost more than it: the first
    form of this rule, cost against the track alone, fell back in 26 of 200 development
    periods.)"""
    if not np.isfinite(fit.states).all() or not np.isfinite(c_states).all():
        return False
    speed = float(np.hypot(fit.states[:, 2], fit.states[:, 3]).max())
    rng = float(np.hypot(fit.states[:, 0] - pb[1], fit.states[:, 1] - pb[2]).max())
    if speed > SPEED_MAX * prior.speed[1] or rng > 16.0 * prior.range0[1]:
        return False
    n = int(pb[4].sum())
    return consistent(float(fit.cost), n) or fit.cost <= track_cost(pb, c_states) + WORSE


def run_shard3(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: "v2" (spec 014's), "v3", "flat3", "mix3". Arrays and records as
    ``run_shard2``, with ``true_cut`` (the one rule's flags), ``reference_flagged`` and
    ``refit_fell_back`` per period, and ``candidates`` from ``search3``."""
    every = int(settings["score_every"])
    chosen = [s for s in OPTIONAL if s in settings.get("systems", OPTIONAL)]
    names = list(BASE) + chosen
    t_layer = time.perf_counter()
    res = solve_systems(periods, ["c2-end-nofade", "one-leg"], c_params, c2)
    t_layer = (time.perf_counter() - t_layer) / max(len(periods), 1)
    p3 = priors["v3"]
    errs: dict[str, list[np.ndarray]] = {s: [] for s in names}
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
        cut = cut_flags(x)
        if len(cut) != len(sp):
            raise ValueError(f"period {x.ordinal}: cut flags and manoeuvres disagree")
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)
        hist: dict[str, Any] = {"c2": {"spans": spc.tolist()}}
        rec: dict[str, Any] = {
            "ordinal": int(x.ordinal),
            "first_row": int(x.first),
            "rows": int(x.rows),
            "seconds_long": float(t[-1]),
            "bearings": int(v.sum()),
            "true": spt.tolist(),
            "true_kinds": kt.tolist(),
            "true_cut": cut,
            "ownship_turns": len(x.ownship_turns()),
        }
        t0 = time.perf_counter()
        held, hf, hm = reference(pb, spt, kt, p3)
        took["reference"] = time.perf_counter() - t0
        tracks["history-fixed"] = held.states
        tracks["history-fit"], tracks["history-map"] = hf.states, hm.states
        true_ev = float(log_evidence(pb, hm, kt, p3)["total"])
        best_true = hm
        rec["history_cost"] = float(hf.cost)
        rec["history_converged"] = consistent(float(hf.cost), int(v.sum()))
        cands3: list[tuple[History, float]] = []
        for name, key in SEARCHES:
            if name not in chosen:
                continue
            t0 = time.perf_counter()
            cands, n_seen = _search(pb, priors[key], cc.states, spc, settings)
            took[name] = time.perf_counter() - t0
            if not cands:
                continue
            top = cands[0][0]
            tracks[name] = top.fit.states
            hist[name] = _history(top.fit.spans, top.kinds, top.evidence)
            listed = [
                {**_history(h.fit.spans, h.kinds, h.evidence), "theta": h.fit.theta.tolist()}
                for h, _p in cands
            ]
            if name == "search3":
                cands3 = cands
                rec["histories_evaluated"] = n_seen
                rec["candidates"] = listed
            elif name == "search2":
                rec["candidates2"] = listed
        if "c2-refit" in chosen:
            t0 = time.perf_counter()
            fell = True
            try:
                g, kinds, ev = c2_refit(pb, spc, cc.states, p3, nominal_starts(pb))
                if refit_acceptable(pb, g, cc.states, p3):
                    tracks["c2-refit"] = g.states
                    hist["c2-refit"] = _history(g.spans, kinds, ev["total"])
                    fell = False
            except ValueError:
                pass
            if fell:  # C″'s own track stands
                tracks["c2-refit"] = cc.states
                hist["c2-refit"] = {"spans": spc.tolist()}
            rec["refit_fell_back"] = fell
            took["c2-refit"] = time.perf_counter() - t0
        if cands3:  # the true structure again, started from the search's own best track
            th = start_from_track(cands3[0][0].fit.states, t, spt)
            th[4:][~kt.reshape(-1)] = 0.0
            for j in range(spt.shape[0]):
                for c in range(2):
                    if kt[j, c] and th[4 + 2 * j + c] == 0.0:
                        th[4 + 2 * j + c] = 0.5 if c == 0 else 1.0
            alt = joint_fit(pb, th, spt, free_changes=kt, prior=p3)
            e = float(log_evidence(pb, alt, kt, p3)["total"])
            if np.isfinite(e) and (not np.isfinite(true_ev) or e > true_ev):
                true_ev, best_true = e, alt
        flagged = not same_history(spt, best_true.spans, MATCH_S, None)
        if flagged:  # it drifted into another history: hold it to the true times
            fixed = joint_fit(pb, held.theta, spt, free_changes=kt, free_times=False, prior=p3)
            best_true = Structure(fixed.theta, spt, fixed.cost, arc_states(fixed.theta, t, spt))
            true_ev = float(log_evidence(pb, best_true, kt, p3)["total"])
        tracks["history-best"] = best_true.states
        rec["reference_flagged"] = bool(flagged)
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
