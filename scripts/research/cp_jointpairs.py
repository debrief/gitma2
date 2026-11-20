"""Spec 028 (FR-012, reported only): spec 025's joint solve over two consecutive windows
against ``ctl-prior`` on the second window, on the tuning seed.

    uv run python scripts/research/cp_jointpairs.py [--raw experiments/20261118-cp-tuning/raw]

For each ``jointpair`` output (ctl on the union of windows pair-1 and pair, read on the second
window's rows) prints the median range error of the joint solve, of the same window's ``ctl``,
``ctl-carry`` and ``ctl-prior`` (from the ``carry2`` output of the same engagement), and the
joint solve's run time; then the geometric mean of ctl-prior ÷ joint over the pairs.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from tma2.long.study import _truth, engagements, range_error

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="experiments/20261118-cp-tuning/raw")
    ap.add_argument("--config", default="configs/long/cp-tuning.json")
    a = ap.parse_args(argv)
    raw = ROOT / a.raw
    cfg = (ROOT / a.config).resolve()
    engs = {e.index: e for e in engagements(cfg, 1)}
    rows_out = []
    for f in sorted(raw.glob(f"{cfg.stem}-c1-jointpair-*-p*.json")):
        h = json.loads(f.read_text())
        i = int(h["index"])
        e = engs[i]
        z = np.load(f.with_suffix(".npz"))
        joint = float(np.nanmedian(range_error(z["ctl-d1-q0.01"], _truth(e, z["rows"]))))
        c = json.loads((raw / f"{cfg.stem}-c1-carry2-{i}.json").read_text())
        zc = np.load(raw / f"{cfg.stem}-c1-carry2-{i}.npz")
        j = int(h["pair"])
        rows = zc[f"w{j}_rows"]
        assert int(c["windows"][j]["first"]) == int(h["second"][0])
        med = {
            s: float(np.nanmedian(range_error(zc[f"w{j}_{s}"], _truth(e, rows))))
            for s in ("ctl-d1-q0.01", "ctl-carry", "ctl-prior")
        }
        rows_out.append(
            {
                "engagement": i,
                "pair": j,
                "joint": joint,
                **med,
                "joint_s": float(h["seconds"]),
                "window_s": float(c["windows"][j]["seconds"]),
            }
        )
    ok = [r for r in rows_out if r["joint"] > 0 and r["ctl-prior"] > 0]
    gm = math.exp(float(np.mean([math.log(r["ctl-prior"] / r["joint"]) for r in ok])))
    gm_ctl = math.exp(float(np.mean([math.log(r["ctl-d1-q0.01"] / r["joint"]) for r in ok])))
    print(
        json.dumps(
            {
                "pairs": rows_out,
                "gm_ctl_prior_over_joint": gm,
                "gm_ctl_over_joint": gm_ctl,
                "median_joint_s": float(np.median([r["joint_s"] for r in rows_out])),
                "median_window_s": float(np.median([r["window_s"] for r in rows_out])),
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
