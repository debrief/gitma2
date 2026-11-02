"""Steady-leg pre-processor trial (docs/research/07): detection power at matched false alarms.

For the first N σ = 1° scenarios of a validation split, compute per row:

- the window one-leg ATAN misfit and the window-local split statistic, for W = 18 and 36 rows;
- for reference, the Gate D whole-history GLR (W = 30) and the frozen IMM's μ_CT.

For each statistic, the threshold is tuned on held-leg G5 rows to a 1% and a 5% false-alarm
fraction (as Gate D's controls were). Reported: the share of spans detected in [start − 1, end + 30]
and the median delay. Writes JSON to --out.

    uv run python scripts/research/steady_leg_trial.py --validation data/gd-val/validation.f32pack \
        --scenarios 500 --out /tmp/steady-leg-trial.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from typing import Any

import numpy as np

from tma2.cli.controls import held_g5_rows
from tma2.data.f32pack import iter_pack_raw
from tma2.detect.controls import glr_stat, imm_mode_stat, ls_states, parse_imm_name, tune_threshold
from tma2.detect.steady_leg import split_stat, window_fits
from tma2.references.classical import bearing_data_from_arrays, classical_predict

IMM = "imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16"


def detection(stats: list[tuple[dict[str, Any], np.ndarray]], far: float) -> dict[str, float]:
    held = [float(st[k]) for meta, st in stats for k in held_g5_rows(meta)]
    h, achieved = tune_threshold(np.asarray(held), far)
    det = tot = 0
    delays = []
    for meta, st in stats:
        dt = float(meta["parameters"]["dt_s"])
        n = int(meta["samples"])
        for sp in meta.get("manoeuvres") or []:
            a, b = int(sp["start_index"]) - 1, int(sp["end_index"]) + 30
            if b >= n:
                continue
            tot += 1
            hit = np.flatnonzero(st[a : b + 1] > h)
            if hit.size:
                det += 1
                delays.append(float(hit[0]) * dt)
    return {
        "threshold": h,
        "false_alarm": achieved,
        "detected": det / tot if tot else math.nan,
        "spans": tot,
        "median_delay_s": float(np.median(delays)) if delays else math.nan,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    ap.add_argument("--scenarios", type=int, default=500)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names = ["misfit18", "split18", "misfit36", "split36", "glr_global30", "imm_mu"]
    per: dict[str, list[tuple[dict[str, Any], np.ndarray]]] = {k: [] for k in names}
    imm = parse_imm_name(IMM)
    t0 = time.time()
    n = 0
    for _, meta, own, _tgt, obs in iter_pack_raw(a.validation):
        if abs(float(meta["parameters"]["noise_sigma_rad"]) - math.pi / 180) > 1e-6:
            continue
        d = bearing_data_from_arrays(meta, own, obs)
        for w in (18, 36):
            z0 = np.zeros(d.n, dtype=np.int64)  # unrestricted windows
            st, ok, mis = window_fits(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, w, z0)
            lam, _where = split_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, w, z0)
            per[f"misfit{w}"].append((meta, np.nan_to_num(mis, nan=0.0)))
            per[f"split{w}"].append((meta, lam))
        lst, lok = ls_states(d, classical_predict(d, "per_timestep")["rows"])
        per["glr_global30"].append(
            (meta, glr_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, lst, lok, 30))
        )
        per["imm_mu"].append((meta, imm_mode_stat(d, imm)))
        n += 1
        if n >= a.scenarios:
            break
    out: dict[str, Any] = {"scenarios": n, "seconds": time.time() - t0}
    for k in names:
        out[k] = {f"far{f}": detection(per[k], f) for f in (0.01, 0.05)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    for k in names:
        r1, r5 = out[k]["far0.01"], out[k]["far0.05"]
        print(
            f"{k:14s} 1%: {r1['detected']:.3f} (delay {r1['median_delay_s']:.0f} s)   "
            f"5%: {r5['detected']:.3f} (delay {r5['median_delay_s']:.0f} s)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
