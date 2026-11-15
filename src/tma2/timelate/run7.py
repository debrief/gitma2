"""One shard of spec 019's diagnostic (development work on used periods): the standing
control as registered (``run4``), and the search, each time a search of its own, under a
ladder of priors from the broadened prior to the split's own statistics.

The parts of a manoeuvre prior, in the ladder's order: ``legs`` (leg mean, spread and
minimum), ``angle`` (turn sizes), ``rate`` (turn rates), ``speed`` (speed changes and their
rates), ``kinds`` (the weights of turn, speed change and both).

* ``lad-0`` is the broadened prior; ``lad-k`` has the first k parts from the true prior;
  ``lad-5`` is the true prior.
* ``one-<part>``: that part alone from the true prior on the broadened prior
  (``one-legs`` is ``lad-1`` and is not run twice).
* ``mem-<key>``: the family member nearest the truth (spec 018's key) with its own search.

Every system is declared by the control's rule under its own prior, on the bearings the
control sees.
"""

from __future__ import annotations

import dataclasses
import time
from typing import Any

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from .corr import MIN_SHARE, edited, effective, estimate
from .hedge import declared, elimination_path
from .periods import Period
from .prior import ManoeuvrePrior
from .retest import Problem
from .run2 import _history, _search
from .run4 import run_shard4
from .score import row_errors, truth_rows
from .systems import solve_systems

PARTS: dict[str, tuple[str, ...]] = {
    "legs": ("leg_mean", "leg_sd", "leg_min"),
    "angle": ("angle",),
    "rate": ("turn_rate",),
    "speed": ("dv", "acc"),
    "kinds": ("w_course", "w_speed", "w_both"),
}
ORDER = ("legs", "angle", "rate", "speed", "kinds")


def with_parts(
    base: ManoeuvrePrior, true: ManoeuvrePrior, parts: tuple[str, ...]
) -> ManoeuvrePrior:
    """``base`` with the named parts' fields taken from ``true``."""
    fields = {f: getattr(true, f) for p in parts for f in PARTS[p]}
    return dataclasses.replace(base, **fields)


def ladder(base: ManoeuvrePrior, true: ManoeuvrePrior) -> dict[str, ManoeuvrePrior]:
    """The cumulative rungs and the single-part rungs, keyed by system name."""
    out = {f"lad-{k}": with_parts(base, true, ORDER[:k]) for k in range(len(ORDER) + 1)}
    out.update({f"one-{p}": with_parts(base, true, (p,)) for p in ORDER[1:]})
    return out


def run_shard7(
    periods: list[Period],
    priors: dict[str, ManoeuvrePrior],
    c_params: SegmentParameters,
    c2: dict[str, Any],
    settings: dict[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """``priors``: study L's "v3" and "broad", and every system's own prior under its name
    (``lad-*``, ``one-*``, ``mem-*``)."""
    arrays, recs = run_shard4(periods, priors, c_params, c2, settings)
    every = int(settings["score_every"])
    margin, quiet = float(settings["margins"][0]), float(settings["quiets"][0])
    names = [k for k in priors if k.startswith(("lad-", "one-", "mem-"))]
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
        pe, _n = edited(pb)
        share_e, tau_e = estimate(pe)
        px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
        cc = res["c2-end-nofade"][i]
        spc = np.array(
            [[t[max(p - 1, 0)], t[q]] for p, q in cc.transitions if q > p], dtype=np.float64
        ).reshape(-1, 2)
        took: dict[str, float] = {}
        for name in names:
            track = nan
            t0 = time.perf_counter()
            cands, _seen = _search(px, priors[name], cc.states, spc, settings)
            if cands:
                path = elimination_path(px, cands[0][0], priors[name])
                h = path[declared(path, margin, quiet)]
                track = h.fit.states
                rec["histories"][name] = _history(h.fit.spans, h.kinds, h.evidence)
            took[name] = time.perf_counter() - t0
            errs[name].append(row_errors(track, tr)[pick].astype(np.float32))
        rec["seconds"].update({k: round(float(s), 2) for k, s in took.items()})
    arrays.update({f"err_{s}": np.concatenate(e) for s, e in errs.items()})
    return arrays, recs
