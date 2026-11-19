"""Spec 027 panel (reviewer 2, finding 1): the rule without constructed ties.

    uv run python scripts/research/cp_ties.py > experiments/20261119-cp/ties.json

A window whose previous window handed nothing on (``handed`` has no ``mean``: too few bearings
before the hand-over, the previous window unanswered, or a failed fit) has ``ctl-prior`` equal
to ``ctl`` by construction, and the registered estimand counts it as a tie. This prints, per
split and quantity, the registered estimate beside the same estimand over windows that were
handed a prior only, with the engagement-chain bootstrap (as registered) and, for the weak
split, clustered by engagement (both contacts of an engagement in one unit). Decides nothing.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tma2.long.study import _boot, engagements
from tma2.long.study27 import QUANTITIES, _splits, load27, ratio

ROOT = Path(__file__).resolve().parents[2]
CFG = (ROOT / "configs/long/cp-test.json").resolve()
RAW = ROOT / "experiments/20261119-cp/raw"


def main() -> int:
    loads: list[dict[str, Any]] = []
    for contact in (1, 2):
        for e in engagements(CFG, contact):
            c = load27(RAW, f"{CFG.stem}-c{contact}", e, contact)
            if c is not None:
                c["engagement"] = e.index
                loads.append(c)
    sp = _splits()
    out: dict[str, Any] = {"no_hand_over": {}}
    for name in ("weak", "other", "contact1", "contact2"):
        keep = sp[name]
        n_all = sum(1 for c in loads for w in c["windows"] if w["index"] > 0 and keep(c, w))
        n_none = sum(
            1
            for c in loads
            for w in c["windows"]
            if w["index"] > 0 and keep(c, w) and w["carried"] is None
        )
        out["no_hand_over"][name] = {"windows": n_all, "without_hand_over": n_none}
        handed = lambda c, w, k=keep: k(c, w) and w["carried"] is not None  # noqa: E731
        out[name] = {
            q: {
                "registered": ratio(loads, "ctl-d1-q0.01", "ctl-prior", q, keep),
                "handed_only": ratio(loads, "ctl-d1-q0.01", "ctl-prior", q, handed),
            }
            for q in QUANTITIES
        }
    # the weak split clustered by engagement
    weak = sp["weak"]
    for label, extra in (("all", None), ("handed_only", True)):
        units: dict[int, list[float]] = {}
        for c in loads:
            for w in c["windows"]:
                if w["index"] == 0 or not weak(c, w):
                    continue
                if extra and w["carried"] is None:
                    continue
                a, b = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["ctl-prior"]["range"]
                if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
                    units.setdefault(c["engagement"], []).append(math.log(a / b))
        us = [np.array(v) for v in units.values()]

        def gm(x: list[np.ndarray]) -> float:
            return float(np.exp(np.concatenate(x).mean())) if x else math.nan

        est, lo, hi = _boot(us, gm, 27)
        out[f"weak_by_engagement_{label}"] = {
            "engagements": len(us),
            "gm": est,
            "interval": [lo, hi],
        }
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
