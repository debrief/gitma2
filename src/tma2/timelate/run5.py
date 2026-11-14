"""One shard of spec 017: study L's control exactly as registered (``run4``), and beside it
the readings that say what the gap to the true history is made of.

* ``ref-full``: the true history, times held, fitted with the prior (threshold 0);
  ``ref-dT``: the same told only the manoeuvres whose detectability is at least T;
* ``true``: the control's search on the control's bearings with the split's own manoeuvre
  statistics as the prior, declared by the control's rule;
* ``imm`` and ``ekf``: the tuned filters read as tracks (constitution; study L left them out);
* ``ref-full-edit`` and ``ref-dT-edit``: the references fitted to the edited bearings
  (study L's panel: under outliers a reference fitted to the bearings as given is no
  yardstick).

Per period the record gains ``detectability`` (one value per true manoeuvre), its cut
flags, and the history of ``true``.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from tma2.references.ekf import ekf_predict
from tma2.references.imm import ImmParams, imm_predict
from tma2.types.generated.tma import SegmentParameters

from .corr import MIN_SHARE, edited, effective, estimate
from .detect import detectability, detectable_reference
from .hedge import declared, elimination_path
from .periods import Period
from .points import fixed_points
from .prior import ManoeuvrePrior
from .retest import Problem
from .run import _filter_track
from .run2 import _history, _search
from .run4 import run_shard4
from .score import row_errors, truth_rows
from .systems import POINT_ROWS, solve_systems


def extra_names(settings: dict[str, Any]) -> list[str]:
    th = [float(x) for x in settings["detect_thresholds"]]
    names = ["ref-full"] + [f"ref-d{x:g}" for x in th] + ["true", "imm", "ekf"]
    if settings.get("edited_reference"):
        names += ["ref-full-edit"] + [f"ref-d{x:g}-edit" for x in th]
    return names


def run_shard5(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
    imm: ImmParams,
    ekf: tuple[float, float, float],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: study L's "v3" and "broad", and "true" (the split's own statistics).
    Arrays and records are ``run_shard4``'s for the control's systems with the readings
    above appended at the same rows."""
    arrays, recs = run_shard4(periods, priors, c_params, c2, settings)
    every = int(settings["score_every"])
    margin, quiet = float(settings["margins"][0]), float(settings["quiets"][0])
    thresholds = [float(x) for x in settings["detect_thresholds"]]
    names = extra_names(settings)
    p3 = priors["v3"]
    res = solve_systems(periods, ["c2-end-nofade"], c_params, c2)
    errs: dict[str, list[np.ndarray]] = {s: [] for s in names}
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
        took: dict[str, float] = {}
        spt = np.array(rec["true"], dtype=np.float64).reshape(-1, 2)
        kt = np.array(rec["true_kinds"], dtype=bool).reshape(-1, 2)

        t0 = time.perf_counter()
        det, full_cost = detectability(pb, spt, kt)
        took["detectability"] = time.perf_counter() - t0
        rec["detectability"] = [float(d) for d in det]
        rec["true_history_cost"] = float(full_cost)
        t0 = time.perf_counter()
        for name, th in [("ref-full", 0.0)] + [(f"ref-d{x:g}", x) for x in thresholds]:
            tracks[name] = detectable_reference(pb, spt, kt, det, th, p3).states
        took["references"] = time.perf_counter() - t0

        pe, _n = edited(pb)
        share_e, tau_e = estimate(pe)
        px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
        if settings.get("edited_reference"):
            det_e, _c = detectability(pe, spt, kt)
            rec["detectability_edited"] = [float(d) for d in det_e]
            for name, th in [("ref-full", 0.0)] + [(f"ref-d{x:g}", x) for x in thresholds]:
                tracks[f"{name}-edit"] = detectable_reference(pe, spt, kt, det_e, th, p3).states

        cc = res["c2-end-nofade"][i]
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)
        t0 = time.perf_counter()
        cands, _seen = _search(px, priors["true"], cc.states, spc, settings)
        took["true"] = time.perf_counter() - t0
        if cands:
            path = elimination_path(px, cands[0][0], priors["true"])
            h = path[declared(path, margin, quiet)]
            tracks["true"] = h.fit.states
            rec["histories"]["true"] = _history(h.fit.spans, h.kinds, h.evidence)

        pts = fixed_points(x, POINT_ROWS).data
        tracks["imm"] = _filter_track(imm_predict(pts, imm)["rows"], pts.zig_index + 1, x.rows)
        tracks["ekf"] = _filter_track(ekf_predict(pts, *ekf)["rows"], pts.zig_index + 1, x.rows)
        rec["seconds"].update({k: round(float(s), 2) for k, s in took.items()})
        for s in names:
            errs[s].append(row_errors(tracks[s], tr)[pick].astype(np.float32))
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    return arrays, recs
