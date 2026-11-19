"""Spec 028: readings beside the registered rule (experiments/20261119-cp/), decided by nothing.

    uv run python scripts/research/cp_supplement.py > experiments/20261119-cp/supplement.json

Per split (weak, other, contact 1, contact 2), on ctl ÷ ctl-prior per window (median range
error, chains' first windows excluded):

* the geometric mean trimmed at both ends (10% each), and the shares better, twice as good and
  twice as bad (spec 019's review: never drop one end only);
* the same split by whether ``ctl`` and ``ctl-prior`` declared the same number of manoeuvres
  in the window (structure agreed) or not, with window counts and engagement intervals.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tma2.long.study import _boot, engagements
from tma2.long.study27 import _splits, load27

ROOT = Path(__file__).resolve().parents[2]
CFG = (ROOT / "configs/long/cp-test.json").resolve()
RAW = ROOT / "experiments/20261119-cp/raw"


def main() -> int:
    loads: list[dict[str, Any]] = []
    for contact in (1, 2):
        for e in engagements(CFG, contact):
            c = load27(RAW, f"{CFG.stem}-c{contact}", e, contact)
            if c is None:
                continue
            head = json.loads((RAW / f"{CFG.stem}-c{contact}-carry2-{e.index}.json").read_text())
            dec = {w["index"]: w["declared"] for w in head["windows"]}
            for w in c["windows"]:
                d = dec[w["index"]]
                w["agree"] = len(d.get("ctl-d1-q0.01", [])) == len(d.get("ctl-prior", []))
            loads.append(c)
    sp = _splits()
    out: dict[str, Any] = {}
    for name in ("weak", "other", "contact1", "contact2"):
        keep = sp[name]
        rec: dict[str, Any] = {}
        for sub, extra in (("all", None), ("agree", True), ("differ", False)):
            units = []
            for c in loads:
                r = []
                for w in c["windows"]:
                    if w["index"] == 0 or not keep(c, w):
                        continue
                    if extra is not None and w["agree"] != extra:
                        continue
                    a = w["med"]["ctl-d1-q0.01"]["range"]
                    b = w["med"]["ctl-prior"]["range"]
                    if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
                        r.append(math.log(a / b))
                if r:
                    units.append(np.array(r))

            def gm(us: list[np.ndarray]) -> float:
                return float(np.exp(np.concatenate(us).mean())) if us else math.nan

            def trimmed(us: list[np.ndarray]) -> float:
                if not us:
                    return math.nan
                x = np.sort(np.concatenate(us))
                k = int(0.1 * x.size)
                return float(np.exp(x[k : x.size - k].mean())) if x.size > 2 * k else math.nan

            est, lo, hi = _boot(units, gm, 27)
            t_est, t_lo, t_hi = _boot(units, trimmed, 27)
            allr = np.exp(np.concatenate(units)) if units else np.zeros(0)
            rec[sub] = {
                "windows": int(allr.size),
                "engagements": len(units),
                "gm": est,
                "interval": [lo, hi],
                "trimmed_10pc": t_est,
                "trimmed_interval": [t_lo, t_hi],
                "share_better": float((allr > 1).mean()) if allr.size else None,
                "share_level": float((allr == 1).mean()) if allr.size else None,
                "share_twice_better": float((allr >= 2).mean()) if allr.size else None,
                "share_twice_worse": float((allr <= 0.5).mean()) if allr.size else None,
            }
        out[name] = rec
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
