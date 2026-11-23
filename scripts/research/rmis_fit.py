"""Spec 037: fit the interval scales and the temperature control on validation rows.

    uv run python scripts/research/rmis_fit.py --rows <off>/interval-rows.npz <all-central>/interval-rows.npz \
        --systems ft-s1,ft-s2,ft-s3 --stated-scale 1,1,1 --out interval-fit.json

Reads the per-row terms ``tma2-rmread`` wrote for the named conditions (the protocol allows off
and all-central only), pools the systems, and writes one multiplier of the head's sd per quantity
and the control's half-widths. Reads no test data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tma2.regress import mread


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", required=True)
    ap.add_argument("--systems", required=True)
    ap.add_argument("--stated-scale", default="1,1,1", help="the scales the rows were stated at")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    systems = a.systems.split(",")
    est, err, half = [], [], []
    for path in a.rows:
        z = np.load(path)
        for s in systems:
            est.append(z[f"{s}__est_range_m"])
            err.append(z[f"{s}__err"])
            half.append(z[f"{s}__half"])
    est_a, err_a, half_a = np.concatenate(est), np.concatenate(err), np.concatenate(half)
    at = [float(v) for v in a.stated_scale.split(",")]
    scale = [at[c] * mread.fit_scale(err_a[:, c], half_a[:, c]) for c in range(3)]
    out = {
        "record": "interval-fit",
        "rows_files": a.rows,
        "systems": systems,
        "rows": int(np.isfinite(est_a).sum()),
        "interval_scale": scale,
        "interval_scale_order": ["range", "course", "speed"],
        "course_stated_share": float(np.isfinite(half_a[:, 1]).mean()),
        "temperature": mread.fit_temperature(est_a, err_a),
    }
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["interval_scale"]), out["temperature"]["half_widths"])


if __name__ == "__main__":
    main()
