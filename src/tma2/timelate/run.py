"""One shard of the time-late systems (spec 013): for each period, C″ read as a track, the
evidence search from two starts with its candidate tracks, and the true history fitted with
and without the prior (the reference; the only use of the truth in a solve). Errors are taken
at every ``score_every``-th row."""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.references.ekf import ekf_predict
from tma2.references.imm import ImmParams, imm_predict
from tma2.types.generated.tma import SegmentParameters

from .arc import fit_arc, fit_arc_search, solve_arc, start_from_track
from .bound import period_bound
from .periods import Period
from .points import fixed_points
from .prior import ManoeuvrePrior
from .retest import Problem, Structure, joint_fit, log_evidence
from .score import row_errors, truth_rows
from .search import candidate_set, evidence_search
from .systems import solve_systems

SYSTEMS = (
    "c2",
    "search",
    "search-c2",
    "search-none",
    "history-fixed",
    "history-fit",
    "history-map",
    "truth-fit",
    "truth-map",
    "one-leg",
    "imm",
    "ekf",
)
POINT_ROWS = 2
NOMINAL_RANGE_M = 8000.0
NOMINAL_SPEED = 5.0


def nominal_starts(pb: Problem) -> list[np.ndarray]:
    """Four states that use nothing but the first bearing: a nominal range along it, a nominal
    speed, and a course in each quadrant."""
    _t, ox, oy, z, v, _sigma = pb
    z0 = float(z[v][0]) if v.any() else 0.0
    return [
        np.array(
            [
                ox[0] + NOMINAL_RANGE_M * np.sin(z0),
                oy[0] + NOMINAL_RANGE_M * np.cos(z0),
                c0,
                NOMINAL_SPEED,
            ]
        )
        for c0 in (0.0, 1.57, 3.14, 4.71)
    ]


def history_reference(
    pb: Problem, spans: np.ndarray, kinds: np.ndarray, prior: ManoeuvrePrior
) -> tuple[np.ndarray, Structure, Structure]:
    """The reference: the true manoeuvre history (when, how long, which changes) and nothing
    else of the truth. Fitted to the bearings from the nominal starts (lowest cost kept) with
    the times held, which is exactly what the known-history bound assumes (the first track
    returned: the soundness check); then with every time free, to the bearings alone and to
    the posterior. Not started at the true state: a fit started there returns it on rows the
    bearings determine weakly (Gate T's first validation run)."""
    t, ox, oy, z, v, sigma = pb
    m = spans.shape[0]
    best = None
    for q0 in nominal_starts(pb):
        th0 = np.concatenate([q0, np.zeros(2 * m)])
        for i in range(m):  # a change the history has starts off zero
            th0[4 + 2 * i] = 0.5 if kinds[i, 0] else 0.0
            th0[5 + 2 * i] = 1.0 if (kinds[i, 1] and not kinds[i, 0]) else 0.0
        f, _n = fit_arc_search(t, ox, oy, z, v, sigma, spans, th0, kinds if m else None)
        if best is None or f.cost < best.cost:
            best = f
    assert best is not None
    fit = joint_fit(pb, best.theta, spans, free_changes=kinds)
    post = joint_fit(pb, fit.theta, fit.spans, free_changes=kinds, prior=prior)
    return best.states, fit, post


def _filter_track(rows: list[dict[str, Any]], first_point: int, n_rows: int) -> np.ndarray:
    """A causal filter's rows (one per 10-second point from ``first_point``) as a track at the
    period's 5-second rows; NaN where the filter gives no state. A point's state is held for
    its two rows (the point's time is their mean: at most 2.5 s of motion)."""
    out = np.full((n_rows, 4), np.nan)
    for k, r in enumerate(rows):
        if not r.get("converged"):
            continue
        c, sp = float(r["course_rad"]), float(r["speed_mps"])
        a = (first_point + k) * POINT_ROWS
        out[a : a + POINT_ROWS] = [float(r["x_m"]), float(r["y_m"]), sp * np.sin(c), sp * np.cos(c)]
    return out


def run_shard(
    periods: list[Period],
    prior: ManoeuvrePrior,
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
    imm: ImmParams | None = None,
    ekf: tuple[float, float, float] | None = None,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """(arrays: ``period`` and ``bound`` at the scored rows and ``err_<system>`` [rows, 4];
    one record per period: true and found histories, candidates with evidence)."""
    every = int(settings["score_every"])
    res = solve_systems(periods, ["c2-end-nofade", "one-leg"], c_params, c2)
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
        tracks["one-leg"] = res["one-leg"][i].states
        pts = fixed_points(x, POINT_ROWS).data
        if imm is not None:
            tracks["imm"] = _filter_track(imm_predict(pts, imm)["rows"], pts.zig_index + 1, x.rows)
        if ekf is not None:
            tracks["ekf"] = _filter_track(ekf_predict(pts, *ekf)["rows"], pts.zig_index + 1, x.rows)
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
        fixed, hf, hm = history_reference(pb, spt, kt, prior)
        tracks["history-fixed"] = fixed
        tracks["history-fit"], tracks["history-map"] = hf.states, hm.states
        rec: dict[str, Any] = {
            "ordinal": int(x.ordinal),
            "first_row": int(x.first),
            "rows": int(x.rows),
            "bearings": int(v.sum()),
            "true": spt.tolist(),
            "truth_evidence": float(log_evidence(pb, fm, kt, prior)["total"]),
            "history_evidence": float(log_evidence(pb, hm, kt, prior)["total"]),
            "history_cost": float(hf.cost),
            "truth_start_cost": float(ft.cost),
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
        for q0 in nominal_starts(pb):  # no layer, no truth
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
