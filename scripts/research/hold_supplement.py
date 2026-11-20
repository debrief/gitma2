"""Spec 029 panel: readings beside the registered rule (experiments/20261119-hold/), decided by
nothing.

    uv run python scripts/research/hold_supplement.py > experiments/20261119-hold/supplement.json

ctl ÷ ctl-prior per window (median range error), held and one-turn classes, bootstrap over
engagements (2,000 resamples, seed 29):

* ``ties``: windows with no hand-over counted as ties (ratio 1) where both systems answer;
* ``per_engagement``: each engagement's geometric mean weighted equally, the median engagement
  and the share of engagements above 1;
* ``range_bands``: by the window's median true range (< 15, 15–25, > 25 km);
* ``gap``: hand-overs whose previous coverage ended more than 5 s before the hand-over, against
  contiguous ones;
* ``no_hand_over``: the held windows that were not handed on (count, median range, answered).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tma2.long.study import _boot, _truth, engagements
from tma2.long.study27 import load27
from tma2.long.study29 import klass, turns_in

ROOT = Path(__file__).resolve().parents[2]
CFG = (ROOT / "configs/long/hold-test.json").resolve()
RAW = ROOT / "experiments/20261119-hold/raw"


def gm(us: list[np.ndarray]) -> float:
    return float(np.exp(np.concatenate(us).mean())) if us else math.nan


def boot(units: list[np.ndarray]) -> dict[str, Any]:
    est, lo, hi = _boot(units, gm, 29)
    return {"windows": int(sum(u.size for u in units)), "gm": est, "interval": [lo, hi]}


def main() -> int:
    loads = []
    for e in engagements(CFG, 1):
        c = load27(RAW, f"{CFG.stem}-c1", e, 1)
        if c is None:
            continue
        z = np.load(RAW / f"{CFG.stem}-c1-carry2-{e.index}.npz")
        for w in c["windows"]:
            w["klass"] = klass(turns_in(e, int(w["first"]), int(w["rows"])))
            rows = z[f"w{w['index']}_rows"]
            tr = _truth(e, rows)
            w["range_km"] = (
                float(np.median(np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5]))) / 1e3
            )
            h = w["carried"]["h"] if w["carried"] else None
            w["gap_s"] = float(h["gap_s"]) if h else math.nan
        loads.append(c)

    def logr(w: dict[str, Any]) -> float | None:
        a, b = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["ctl-prior"]["range"]
        if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
            return math.log(a / b)
        return None

    def units(keep: Any, ties: bool = False) -> list[np.ndarray]:
        out = []
        for c in loads:
            r = []
            for w in c["windows"]:
                if w["index"] == 0 or not keep(w):
                    continue
                if w["carried"] is None:
                    if ties:
                        a, b = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["ctl-prior"]["range"]
                        if np.isfinite(a) and np.isfinite(b):
                            r.append(0.0)
                    continue
                x = logr(w)
                if x is not None:
                    r.append(x)
            if r:
                out.append(np.array(r))
        return out

    res: dict[str, Any] = {}
    for k in ("held", "one"):
        kk = lambda w, k=k: w["klass"] == k  # noqa: E731
        us = units(kk)
        per = np.array([float(u.mean()) for u in us])
        est, lo, hi = _boot([np.array([p]) for p in per], gm, 29)
        res[k] = {
            "registered": boot(us),
            "ties": boot(units(kk, ties=True)),
            "per_engagement": {
                "engagements": int(per.size),
                "equal_weight_gm": est,
                "interval": [lo, hi],
                "median_engagement": float(np.exp(np.median(per))),
                "share_above_1": float((per > 0).mean()),
            },
            "range_bands": {
                name: boot(
                    units(lambda w, k=k, a=a, b=b: w["klass"] == k and a <= w["range_km"] < b)
                )
                for name, a, b in (("<15", 0, 15), ("15-25", 15, 25), (">25", 25, 1e9))
            },
            "gap": {
                "after_gap": boot(units(lambda w, k=k: w["klass"] == k and w["gap_s"] > 5.0)),
                "contiguous": boot(units(lambda w, k=k: w["klass"] == k and w["gap_s"] <= 5.0)),
            },
        }
    nh = [
        w
        for c in loads
        for w in c["windows"]
        if w["index"] > 0 and w["klass"] == "held" and w["carried"] is None
    ]
    res["no_hand_over_held"] = {
        "windows": len(nh),
        "median_range_km": float(np.median([w["range_km"] for w in nh])) if nh else None,
        "ctl_answered": int(sum(np.isfinite(w["med"]["ctl-d1-q0.01"]["range"]) for w in nh)),
    }
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
