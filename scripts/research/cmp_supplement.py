"""Spec 031: readings beside the registered rule (experiments/20261120-cmp/), decided by nothing.

    uv run python scripts/research/cmp_supplement.py > experiments/20261120-cmp/supplement.json

On the test record's turn-free (held) and one-turn 1-hour windows (handed on in (a)), with the
registered bootstrap over engagements:

* ``prior2h_vs_ctl2h``: 2-hour ``ctl`` ÷ 2-hour ``ctl-prior`` (does the prior help on top of the
  longer window);
* ``prior2h_vs_joint``: the joint solve ÷ 2-hour ``ctl-prior`` (held only);
* each registered estimand with every engagement weighted equally (per-engagement geometric means).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tma2.long.study import _boot, engagements
from tma2.long.study27 import load27
from tma2.long.study29 import klass, turns_in
from tma2.long.study30 import _load_2h, _load_joint, _window_meds

ROOT = Path(__file__).resolve().parents[2]
CFG = (ROOT / "configs/long/cmp-test.json").resolve()
RAW = ROOT / "experiments/20261120-cmp/raw"


def gm(us: list[np.ndarray]) -> float:
    return float(np.exp(np.concatenate(us).mean())) if us else math.nan


def boot(units: list[np.ndarray]) -> dict[str, Any]:
    est, lo, hi = _boot(units, gm, 30)
    allr = np.exp(np.concatenate(units)) if units else np.zeros(0)
    return {
        "windows": int(allr.size),
        "engagements": len(units),
        "gm": est,
        "interval": [lo, hi],
        "median": float(np.median(allr)) if allr.size else None,
        "share_den_better": float((allr > 1).mean()) if allr.size else None,
    }


def main() -> int:
    stem = CFG.stem
    recs: list[dict[str, Any]] = []
    for e in engagements(CFG, 1):
        a = load27(RAW, f"{stem}-c1", e, 1)
        b = _load_2h(RAW, stem, e)
        c = _load_joint(RAW, stem, e)
        if a is None or b is None:
            continue
        for w in a["windows"]:
            if w["index"] == 0 or w["carried"] is None:
                continue
            first, n = int(w["first"]), int(w["rows"])
            sel = (b["rows"] >= first) & (b["rows"] < first + n)
            rec = {
                "e": e.index,
                "k": klass(turns_in(e, first, n)),
                "a": w["med"]["ctl-prior"]["range"],
                "b": _window_meds(b["states"]["ctl-d1-q0.01"][sel], b["rows"][sel], e)["range"],
                "bp": _window_meds(b["states"]["ctl-prior"][sel], b["rows"][sel], e)["range"],
                "c": c[w["index"]]["ctl"]["range"] if c and w["index"] in c else math.nan,
            }
            recs.append(rec)

    def units(num: str, den: str, k: str) -> list[np.ndarray]:
        by: dict[int, list[float]] = {}
        for r in recs:
            if r["k"] != k:
                continue
            x, y = r[num], r[den]
            if np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0:
                by.setdefault(r["e"], []).append(math.log(x / y))
        return [np.array(v) for v in by.values()]

    out: dict[str, Any] = {
        "prior2h_vs_ctl2h": {k: boot(units("b", "bp", k)) for k in ("held", "one")},
        "prior2h_vs_joint_held": boot(units("c", "bp", "held")),
        "equal_weight_engagements": {},
    }
    for name, num in (("D1", "b"), ("D2", "c"), ("D3", "bp")):
        us = units(num, "a", "held")
        per = [np.array([float(u.mean())]) for u in us]
        est, lo, hi = _boot(per, gm, 30)
        out["equal_weight_engagements"][name] = {
            "gm": est,
            "interval": [lo, hi],
            "engagements": len(us),
        }
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
