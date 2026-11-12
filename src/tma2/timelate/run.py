"""One shard of the time-late systems (spec 013): for each period, C″ read as a track, the
evidence search from two starts with its candidate tracks, and the true history fitted with
and without the prior (the reference; the only use of the truth in a solve). Errors are taken
at every ``score_every``-th row."""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .arc import fit_arc, solve_arc, start_from_track
from .bound import period_bound
from .periods import Period
from .prior import ManoeuvrePrior
from .retest import joint_fit, log_evidence
from .score import row_errors, truth_rows
from .search import candidate_set, evidence_search
from .systems import solve_systems

SYSTEMS = ("c2", "search", "search-c2", "search-none", "truth-fit", "truth-map")
NOMINAL_RANGE_M = 8000.0
NOMINAL_SPEED = 5.0


def run_shard(
    periods: list[Period],
    prior: ManoeuvrePrior,
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """(arrays: ``period`` and ``bound`` at the scored rows and ``err_<system>`` [rows, 4];
    one record per period: true and found histories, candidates with evidence)."""
    every = int(settings["score_every"])
    res = solve_systems(periods, ["c2-end-nofade"], c_params, c2)
    errs: dict[str, list[np.ndarray]] = {s: [] for s in SYSTEMS}
    bounds, owner, recs = [], [], []
    for i, x in enumerate(periods):
        a, b = x.first, x.first + x.rows
        t = x.own[a:b, 0].astype(np.float64) - float(x.own[a, 0])
        ox, oy = x.own[a:b, 1].astype(np.float64), x.own[a:b, 2].astype(np.float64)
        z, v = x.obs[a:b, 1].astype(np.float64), x.obs[a:b, 2] != 0
        sigma = float(x.meta["parameters"]["noise_sigma_rad"])
        pb = (t, ox, oy, z, v, sigma)
        tr = truth_rows(x)
        pick = np.arange(0, x.rows, every)
        nan = np.full((x.rows, 4), np.nan)
        tracks: dict[str, np.ndarray] = {s: nan for s in SYSTEMS}
        cc = res["c2-end-nofade"][i]
        tracks["c2"] = cc.states
        # the reference: the true history, fitted to the bearings and then to the posterior
        tt = np.stack(
            [tr[:, 0], tr[:, 1], tr[:, 3] * np.sin(tr[:, 2]), tr[:, 3] * np.cos(tr[:, 2])], axis=1
        )
        sp = [s for s in x.spans() if s["end_index"] > s["start_index"]]
        spt = np.array(
            [[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp], dtype=np.float64
        ).reshape(-1, 2)
        kt = np.array(
            [[s["kind"] in ("course", "both"), s["kind"] in ("speed", "both")] for s in sp],
            dtype=bool,
        ).reshape(-1, 2)
        th = start_from_track(tt, t, spt)
        th[4:][~kt.reshape(-1)] = 0.0
        ft = joint_fit(pb, th, spt, free_changes=kt)
        fm = joint_fit(pb, ft.theta, ft.spans, free_changes=kt, prior=prior)
        tracks["truth-fit"], tracks["truth-map"] = ft.states, fm.states
        rec: dict[str, Any] = {
            "ordinal": int(x.ordinal),
            "first_row": int(x.first),
            "rows": int(x.rows),
            "bearings": int(v.sum()),
            "true": spt.tolist(),
            "truth_evidence": float(log_evidence(pb, fm, kt, prior)["total"]),
        }
        seen = []
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)
        if np.isfinite(cc.states).all():
            f0, _, _ = solve_arc(t, ox, oy, z, v, sigma, spc, cc.states)
            best, s1 = evidence_search(
                pb, f0.theta, spc, prior, int(settings["max_manoeuvres"]), int(settings["steps"])
            )
            tracks["search-c2"] = best.fit.states
            seen += s1
        none = np.zeros((0, 2))
        b0 = None
        z0 = float(z[v][0]) if v.any() else 0.0
        for c0 in (0.0, 1.57, 3.14, 4.71):  # no layer, no truth: a nominal state on the bearing
            q0 = np.array(
                [
                    ox[0] + NOMINAL_RANGE_M * np.sin(z0),
                    oy[0] + NOMINAL_RANGE_M * np.cos(z0),
                    c0,
                    NOMINAL_SPEED,
                ]
            )
            f = fit_arc(t, ox, oy, z, v, sigma, none, q0)
            if b0 is None or f.cost < b0.cost:
                b0 = f
        assert b0 is not None
        best, s2 = evidence_search(
            pb, b0.theta, none, prior, int(settings["max_manoeuvres"]), int(settings["steps"])
        )
        tracks["search-none"] = best.fit.states
        seen += s2
        cands = candidate_set(seen, top=int(settings["candidates"]))
        if cands:
            tracks["search"] = cands[0][0].fit.states
        rec["histories_evaluated"] = len(seen)
        rec["candidates"] = [
            {
                "evidence": h.evidence,
                "spans": h.fit.spans.tolist(),
                "kinds": h.kinds.tolist(),
                "theta": h.fit.theta.tolist(),
            }
            for h, _p in cands
        ]
        bd = period_bound(x)
        bounds.append(bd[pick])
        owner.append(np.full(pick.size, x.ordinal, dtype=np.int64))
        for s in SYSTEMS:
            errs[s].append(row_errors(tracks[s], tr)[pick].astype(np.float32))
        recs.append(rec)
    arrays: dict[str, np.ndarray] = {
        "period": np.concatenate(owner),
        "bound": np.concatenate(bounds).astype(np.float32),
    }
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    return arrays, recs
