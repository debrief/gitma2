"""One shard of spec 028: spec 027's systems and the carried prior across gaps.

Per engagement, ``run9.run_shard9`` (unchanged: ``ctl`` alone, the joint solve, every bearing,
the carried start, the references) and then the carried prior (``cprior``): each period in
order; the first is ``ctl`` alone; each later one is ``ctl`` with (a) a Gaussian prior on its
starting state from the previous period's declared state and Laplace covariance, propagated
through the gap with Annex B's manoeuvre noise, applied under both of ``ctl``'s priors, and
(b) its search started from that carried state.

Arrays: ``run9``'s plus ``err_cprior`` [rows, 4] in the same row order.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .carry import _search
from .corr import MIN_SHARE, edited, effective, estimate
from .cprior import carried_evidence, carried_prior, end_state_covariance, propagate
from .hedge import declared, elimination_path, pool
from .layout import layout, period
from .periods import Period
from .prior import ManoeuvrePrior
from .run8 import layout_options
from .run9 import _problem, run_shard9
from .score import row_errors, truth_rows
from .search import History
from .systems import solve_systems

MARGIN, QUIET = 1.0, 0.01


def _solve(
    pb: Any,
    priors: dict[str, ManoeuvrePrior],
    c_states: np.ndarray,
    spc: np.ndarray,
    settings: dict[str, Any],
    theta_carry: np.ndarray | None,
) -> tuple[History, Any, ManoeuvrePrior] | None:
    """``carry.solve_ctl``'s pipeline, returning the declared history, the problem it was
    fitted on and the prior it was declared under."""
    pe, n_edit = edited(pb)
    share_e, tau_e = estimate(pe)
    px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
    which = "ctl" if share_e >= MIN_SHARE else ("edit" if n_edit else "plain")
    top = int(settings["candidates"])
    s = {**settings, "candidates": top}
    sets = [
        [(h, f"{which}/{key}") for h, _p in _search(px, priors[key], c_states, spc, s, theta_carry)]
        for key in ("v3", "broad")
    ]
    cands = pool(sets, top)
    if not cands:
        return None
    h0, tag0 = cands[0]
    prior = priors[tag0.split("/")[1]]
    path = elimination_path(px, h0, prior)
    return path[declared(path, MARGIN, QUIET)], px, prior


def cprior_chain(
    pieces: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    res = solve_systems(pieces, ["c2-end-nofade"], c_params, c2)
    tracks: list[np.ndarray] = []
    recs: list[dict[str, Any]] = []
    carried: tuple[float, np.ndarray, np.ndarray] | None = None  # (t_abs, state, cov)
    for i, p in enumerate(pieces):
        t0 = time.perf_counter()
        pb, t_abs = _problem(p)
        t = pb[0]
        cc = res["c2-end-nofade"][i]
        spc = np.array(
            [[t[max(a - 1, 0)], t[b]] for a, b in cc.transitions if b > a], dtype=np.float64
        ).reshape(-1, 2)
        rec: dict[str, Any] = {"carried": carried is not None}
        use = priors
        theta = None
        if carried is not None:
            ts, st, cv = carried
            theta, cov = propagate(st, cv, float(t_abs[0]) - ts, priors["v3"])
            use = {k: carried_prior(v, theta, cov) for k, v in priors.items()}
            rec["prior_sd"] = [float(u) for u in np.sqrt(np.clip(np.diag(cov), 0.0, None))]
            rec["prior_mean"] = [float(u) for u in theta]
            rec["prior_cov"] = cov.tolist()
        with carried_evidence():
            out = _solve(pb, use, cc.states, spc, settings, theta)
            if out is None:
                states = np.full((p.rows, 4), np.nan)
                carried = None
                rec["spans_abs_s"] = []
            else:
                h, px, pr = out
                states = h.fit.states
                rec["spans_abs_s"] = (h.fit.spans + float(t_abs[0])).tolist()
                try:
                    cv_end = end_state_covariance(px, h.fit, h.kinds, pr)
                    ok = bool(np.isfinite(cv_end).all() and np.isfinite(states[-1]).all())
                except (np.linalg.LinAlgError, ValueError):
                    ok = False
                carried = (float(t_abs[-1]), states[-1].copy(), cv_end) if ok else None
                rec["end_sd_xy_m"] = (
                    [float(np.sqrt(max(cv_end[0, 0], 0.0))), float(np.sqrt(max(cv_end[1, 1], 0.0)))]
                    if ok
                    else None
                )
        rec["seconds"] = round(time.perf_counter() - t0, 2)
        tracks.append(states)
        recs.append(rec)
    return tracks, recs


def run_shard10(
    engagements: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    every = int(settings["score_every"])
    arr, recs = run_shard9(engagements, priors, c_params, c2, settings)
    errs: list[np.ndarray] = []
    for x in engagements:
        lay = layout(np.uint64(int(x.meta["seed"])), x.rows, x.dt, **layout_options(settings))
        if lay is None:
            continue
        pieces = [period(x, a, n) for a, n in lay.periods]
        t0 = time.perf_counter()
        tracks, crecs = cprior_chain(pieces, priors, c_params, c2, settings)
        rec = next(r for r in recs if r["ordinal"] == int(x.ordinal))
        rec["seconds"]["cprior"] = round(time.perf_counter() - t0, 2)
        for p, c in zip(pieces, crecs, strict=True):  # FR-004: is the truth inside?
            if "prior_mean" in c:
                tr = truth_rows(p)[0]  # x, y, course, speed at the period's first row
                d = np.array(tr[:4]) - np.array(c["prior_mean"])
                d[2] = (d[2] + np.pi) % (2 * np.pi) - np.pi
                cov = np.array(c["prior_cov"]) + np.diag([25.0, 25.0, 1e-6, 1e-4])
                c["truth_md2"] = float(d @ np.linalg.solve(cov, d))
                c["truth_md2_xy"] = float(d[:2] @ np.linalg.solve(cov[:2, :2], d[:2]))
        rec["cprior"] = crecs
        for i, p in enumerate(pieces):
            pick = np.arange(0, p.rows, every)
            errs.append(row_errors(tracks[i], truth_rows(p))[pick].astype(np.float32))
    err = np.concatenate(errs)
    if err.shape[0] != arr["eng"].shape[0]:
        raise ValueError("cprior rows do not match run9's")
    arr["err_cprior"] = err
    return arr, recs
