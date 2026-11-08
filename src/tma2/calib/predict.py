"""Calibrated prediction files (spec 008 T024, FR-020).

Reads an E prediction file and its feature cache (the same rows) and writes a copy in which each
row's covariance is scaled by e^(2s) and its standard deviations by e^s, with ``cov_scale_log``
set to s. Every other field, the point estimate included, is copied unchanged. Rows absent from
the cache (no estimate) are copied as they are. A cache row with no matching prediction row is
refused.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from tma2.data.canonical import canonical_json


def calibrate_row(row: dict[str, Any], s: float) -> dict[str, Any]:
    out = dict(row)
    if "cov_xyvv" in row:
        f = math.exp(2.0 * s)
        out["cov_xyvv"] = [f * float(v) for v in row["cov_xyvv"]]
    for k in ("log_range_sd", "course_sd_rad", "speed_sd_mps"):
        if k in row:
            out[k] = float(row[k]) * math.exp(s)
    out["cov_scale_log"] = s
    return out


def write_calibrated(
    pred_in: Path,
    out: Path,
    scales: dict[tuple[int, float], float],
    calibration: dict[str, Any],
) -> int:
    """Scale each row named in ``scales`` by (ordinal, float32 timestamp); returns how many rows
    were scaled. Every scale must find its row."""
    from tma2.sim.geometry import f32

    done = 0
    with open(pred_in, encoding="utf-8") as fi, open(out, "w", encoding="utf-8") as fo:
        h = json.loads(fi.readline())
        h["calibration"] = calibration
        fo.write(canonical_json(h) + "\n")
        for line in fi:
            rec = json.loads(line)
            j = int(rec["ordinal"])
            rows = []
            for r in rec["rows"]:
                s = scales.get((j, f32(float(r["timestamp_s"]))))
                if s is not None:
                    rows.append(calibrate_row(r, float(s)))
                    done += 1
                else:
                    rows.append(r)
            rec["rows"] = rows
            fo.write(canonical_json(rec) + "\n")
    if done != len(scales):
        raise ValueError(f"{len(scales) - done} cache rows have no prediction row in {pred_in}")
    return done
