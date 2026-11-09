"""Calibrated prediction files (spec 008 T024, FR-020).

Reads an E prediction file and its feature cache (the same rows) and writes a copy in which each
row's covariance is rescaled (``calibrate_row``), with ``cov_scale_log`` set to the scales.
Every other field, the point estimate included, is copied unchanged. Rows absent from the cache
(no estimate) are copied as they are. A scale with no matching prediction row is refused (the CLI
passes only the file's scenarios: ``cli.g3predict``).
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.canonical import canonical_json
from tma2.physics.uncertainty import derived_sds, local_rescale, pack_cov, unpack_cov


def calibrate_row(
    row: dict[str, Any], s: Sequence[float], own_xy: tuple[float, float] | None = None
) -> dict[str, Any]:
    """The row with its covariance rescaled: one s, e^(2s) times it (standard deviations times
    e^s); four, in local coordinates (``physics.uncertainty.local_rescale``, needs ownship at the
    row), with the standard deviations recomputed from the result."""
    out = dict(row)
    sv = [float(v) for v in s]
    if len(sv) == 1:
        if "cov_xyvv" in row:
            f = math.exp(2.0 * sv[0])
            out["cov_xyvv"] = [f * float(v) for v in row["cov_xyvv"]]
        for k in ("log_range_sd", "course_sd_rad", "speed_sd_mps"):
            if k in row:
                out[k] = float(row[k]) * math.exp(sv[0])
    elif "cov_xyvv" in row:
        if own_xy is None:
            raise ValueError("a local rescale needs ownship at the row")
        sp, cr = float(row["speed_mps"]), float(row["course_rad"])
        st = np.array([row["x_m"], row["y_m"], sp * math.sin(cr), sp * math.cos(cr)], dtype=float)
        p = local_rescale(st, unpack_cov(row["cov_xyvv"]), own_xy, np.array(sv))
        out["cov_xyvv"] = pack_cov(p)
        lr, c, v = derived_sds(st, p, own_xy)
        out.update({"log_range_sd": lr, "course_sd_rad": c, "speed_sd_mps": v})
    out["cov_scale_log"] = sv
    return out


def write_calibrated(
    pred_in: Path,
    out: Path,
    scales: dict[tuple[int, float], tuple[list[float], tuple[float, float]]],
    calibration: dict[str, Any],
) -> int:
    """Rescale each row named in ``scales`` by (ordinal, float32 timestamp) → (s, ownship at the
    row); returns how many rows were rescaled. Every scale must find its row."""
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
                sc = scales.get((j, f32(float(r["timestamp_s"]))))
                if sc is not None:
                    rows.append(calibrate_row(r, sc[0], sc[1]))
                    done += 1
                else:
                    rows.append(r)
            rec["rows"] = rows
            fo.write(canonical_json(rec) + "\n")
    if done != len(scales):
        raise ValueError(f"{len(scales) - done} cache rows have no prediction row in {pred_in}")
    return done


def write_fields(
    pred_in: Path,
    out: Path,
    fields: dict[tuple[int, float], dict[str, float]],
    calibration: dict[str, Any],
) -> int:
    """Copy a prediction file, adding ``fields`` to each row named by (ordinal, float32
    timestamp) (spec 009's statement); every other field is copied unchanged. Every entry must
    find its row."""
    from tma2.sim.geometry import f32

    done = 0
    with open(pred_in, encoding="utf-8") as fi, open(out, "w", encoding="utf-8") as fo:
        h = json.loads(fi.readline())
        h["calibration"] = calibration
        fo.write(canonical_json(h) + "\n")
        for line in fi:
            rec = json.loads(line)
            j = int(rec["ordinal"])
            new = []
            for r in rec["rows"]:
                f = fields.get((j, f32(float(r["timestamp_s"]))))
                if f is not None:
                    r = {**r, **f}
                    done += 1
                new.append(r)
            rec["rows"] = new
            fo.write(canonical_json(rec) + "\n")
    if done != len(fields):
        raise ValueError(f"{len(fields) - done} cache rows have no prediction row in {pred_in}")
    return done
