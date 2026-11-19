"""One shard of spec 028: spec 027's systems and the carried prior across gaps.

Per engagement, ``run9.run_shard9`` (unchanged: ``ctl`` alone, the joint solve, every bearing,
the carried start, the references) and then the carried prior (``cprior``): each period in
order; the first is ``ctl`` alone; each later one is ``ctl`` with (a) a Gaussian prior on its
starting state from the previous period's declared state and Laplace covariance, propagated
through the gap with Annex B's manoeuvre noise, applied under both of ``ctl``'s priors, and
(b) its search started from that carried state.

Arrays: ``run9``'s plus ``err_cprior`` [rows, 4] in the same row order.

Refinements (settings ``cprior_variants``, a list of ``{"name", "inflate", "w"}``; development
only): the carried covariance multiplied by ``inflate``², and a two-part prior on the starting
state: the carried Gaussian with weight ``w`` and the standing prior with ``1 - w``. A mixture
prior's posterior is held by one part, so each later period is solved under both (``ctl`` alone
is the standing part) and the part with the larger ``log weight + evidence`` is declared; its
state and covariance are carried on. Arrays ``err_cv-<name>``; records ``cv[<name>]``.
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


def _end(out: tuple[History, Any, ManoeuvrePrior]) -> np.ndarray | None:
    h, px, pr = out
    try:
        cv = end_state_covariance(px, h.fit, h.kinds, pr)
    except (np.linalg.LinAlgError, ValueError):
        return None
    ok = bool(np.isfinite(cv).all() and np.isfinite(h.fit.states[-1]).all())
    return cv if ok else None


def cprior_chain(
    pieces: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
    inflate: float = 1.0,
    w: float = 1.0,
    alone: list[tuple[History, Any, ManoeuvrePrior] | None] | None = None,
) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    if w < 1.0 and alone is None:
        raise ValueError("a mixture needs ctl alone's solves")
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
            if inflate != 1.0:
                cov = cov * (inflate * inflate)
            use = {k: carried_prior(v, theta, cov) for k, v in priors.items()}
            rec["prior_sd"] = [float(u) for u in np.sqrt(np.clip(np.diag(cov), 0.0, None))]
            rec["prior_mean"] = [float(u) for u in theta]
            rec["prior_cov"] = cov.tolist()
        with carried_evidence():
            out = _solve(pb, use, cc.states, spc, settings, theta)
            if carried is not None and w < 1.0:
                assert alone is not None
                a = alone[i]
                ev_c = out[0].evidence + np.log(w) if out is not None else -np.inf
                ev_a = a[0].evidence + np.log1p(-w) if a is not None else -np.inf
                rec["log_odds_carried"] = float(ev_c - ev_a)
                if ev_a > ev_c:
                    out = a
                rec["chose_carried"] = bool(ev_c >= ev_a)
            if out is None:
                states = np.full((p.rows, 4), np.nan)
                carried = None
                rec["spans_abs_s"] = []
            else:
                h = out[0]
                states = h.fit.states
                rec["spans_abs_s"] = (h.fit.spans + float(t_abs[0])).tolist()
                cv_end = _end(out)
                carried = (
                    (float(t_abs[-1]), states[-1].copy(), cv_end) if cv_end is not None else None
                )
                rec["end_sd_xy_m"] = (
                    [float(np.sqrt(max(cv_end[0, 0], 0.0))), float(np.sqrt(max(cv_end[1, 1], 0.0)))]
                    if cv_end is not None
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
    variants = [
        {"name": "cprior", "inflate": 1.0, "w": 1.0},
        *({**v, "name": f"cv-{v['name']}"} for v in settings.get("cprior_variants", [])),
    ]
    mix = any(float(v["w"]) < 1.0 for v in variants)
    errs: dict[str, list[np.ndarray]] = {v["name"]: [] for v in variants}
    for x in engagements:
        lay = layout(np.uint64(int(x.meta["seed"])), x.rows, x.dt, **layout_options(settings))
        if lay is None:
            continue
        pieces = [period(x, a, n) for a, n in lay.periods]
        rec = next(r for r in recs if r["ordinal"] == int(x.ordinal))
        alone = None
        if mix:
            t0 = time.perf_counter()
            alone = _alone(pieces, priors, c_params, c2, settings)
            rec["seconds"]["cv-alone"] = round(time.perf_counter() - t0, 2)
        for v in variants:
            t0 = time.perf_counter()
            tracks, crecs = cprior_chain(
                pieces, priors, c_params, c2, settings, float(v["inflate"]), float(v["w"]), alone
            )
            rec["seconds"][v["name"]] = round(time.perf_counter() - t0, 2)
            for p, c in zip(pieces, crecs, strict=True):  # FR-004: is the truth inside?
                if "prior_mean" in c:
                    tr = truth_rows(p)[0]  # x, y, course, speed at the period's first row
                    d = np.array(tr[:4]) - np.array(c["prior_mean"])
                    d[2] = (d[2] + np.pi) % (2 * np.pi) - np.pi
                    cov = np.array(c["prior_cov"]) + np.diag([25.0, 25.0, 1e-6, 1e-4])
                    c["truth_md2"] = float(d @ np.linalg.solve(cov, d))
                    c["truth_md2_xy"] = float(d[:2] @ np.linalg.solve(cov[:2, :2], d[:2]))
            if v["name"] == "cprior":
                rec["cprior"] = crecs
            else:
                rec.setdefault("cv", {})[v["name"][3:]] = crecs
            for i, p in enumerate(pieces):
                pick = np.arange(0, p.rows, every)
                errs[v["name"]].append(
                    row_errors(tracks[i], truth_rows(p))[pick].astype(np.float32)
                )
    for name, e in errs.items():
        err = np.concatenate(e)
        if err.shape[0] != arr["eng"].shape[0]:
            raise ValueError(f"{name} rows do not match run9's")
        arr[f"err_{name}"] = err
    return arr, recs


def _alone(
    pieces: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> list[tuple[History, Any, ManoeuvrePrior] | None]:
    """``ctl`` alone on each period (the standing part of a mixture), with its problem and prior."""
    res = solve_systems(pieces, ["c2-end-nofade"], c_params, c2)
    out: list[tuple[History, Any, ManoeuvrePrior] | None] = []
    for i, p in enumerate(pieces):
        pb, _t_abs = _problem(p)
        t = pb[0]
        cc = res["c2-end-nofade"][i]
        spc = np.array(
            [[t[max(a - 1, 0)], t[b]] for a, b in cc.transitions if b > a], dtype=np.float64
        ).reshape(-1, 2)
        out.append(_solve(pb, priors, cc.states, spc, settings, None))
    return out
