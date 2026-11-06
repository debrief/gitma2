"""Gate S panel round 2: slices by zig angle and time since the zig, and the finite-row headline,
from a gate record's ``errors.npz`` (``experiments/20261105-gs-r2/slices-extra.json``).

    uv run python scripts/research/gs_slices_extra.py <errors.npz> <out.json>
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any

import numpy as np

from tma2.eval.slices import zig_band
from tma2.segment import score as sc
from tma2.segment.metrics import gap_recovered

REFS = ("one_leg", "oracle", "imm", "ekf", "naive")


def q(v: np.ndarray) -> float:
    if not v.size:
        return math.nan
    return float(np.quantile(np.where(np.isfinite(v), v, np.inf), 0.5, method="inverted_cdf"))


def main() -> None:
    z = np.load(sys.argv[1], allow_pickle=False)
    ords, ks = z["ordinal"], z["k"]
    names = [k[4:] for k in z.files if k.startswith("err_")]
    err = {n: z[f"err_{n}"][:, 0] for n in names}
    meta = {j: m for j, m, *_ in sc.iter_selected("data/gs-test/test.f32pack", 0, 5059)}
    zb = np.array(
        [zig_band(abs(math.degrees(float(meta[o]["parameters"]["zig_angle_rad"])))) for o in ords]
    )
    tz = np.array(
        [
            f"zig+{round((k - int(meta[o]['zig_index'])) * float(meta[o]['parameters']['dt_s']) / 60)}min"
            for o, k in zip(ords, ks, strict=True)
        ]
    )
    segs = [n for n in names if n not in REFS]
    out: dict[str, Any] = {"finite_rows": {}, "zig_band": {}, "time_since_zig": {}}
    allfin = np.all([np.isfinite(err[n]) for n in names], axis=0)
    masks = {
        "all": np.ones_like(allfin),
        "one_leg_answers": np.isfinite(err["one_leg"]),
        "every_estimator_answers": allfin,
    }
    for label, mask in masks.items():
        one, ora, nav = (q(err[n][mask]) for n in ("one_leg", "oracle", "naive"))
        out["finite_rows"][label] = {"rows": int(mask.sum())}
        for n in segs:
            med = q(err[n][mask])
            out["finite_rows"][label][n] = {
                "range_median": med,
                "gap_recovered": gap_recovered(one, med, ora),
                "gap_from_naive": gap_recovered(nav, med, ora),
            }
    for key, vals in (("zig_band", zb), ("time_since_zig", tz)):
        for v in sorted(set(vals.tolist())):
            mask = vals == v
            one, ora = q(err["one_leg"][mask]), q(err["oracle"][mask])
            cell: dict[str, Any] = {"rows": int(mask.sum())}
            for n in names:
                med = q(err[n][mask])
                cell[n] = {
                    "range_median": med,
                    "gross_rate": float(np.mean(~(err[n][mask] <= 0.5))),
                }
                if n in segs:
                    cell[n]["gap_recovered"] = gap_recovered(one, med, ora)
            out[key][v] = cell
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
