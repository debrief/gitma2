"""Steady-leg trial, part 2 (docs/research/07): alarms → knots → physics layer at G5 rows.

For the first N σ = 1° scenarios: the window-local split statistic (W rows) is thresholded at the
value matching a held-leg G5 false-alarm fraction (tuned on the same scenarios, so in-sample).
Alarm episodes (runs less than 60 s apart merged) each give one knot at the split row found at
the episode's strongest row. A G5 row k uses the knots whose alarm came at or before k (causal).
Kinds are unknown: either no speed prior, or the prior on every knot as for a course change.
Median relative range error over the G5 rows, against batch least squares (the same layer with no
knots), the frozen IMM and the oracle (truth spans, speed prior).

    uv run python scripts/research/steady_leg_downstream.py --validation data/gd-val/validation.f32pack \
        --scenarios 500 --window 36 --far 0.01 0.05
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any

import numpy as np
import torch

from tma2.cli.controls import held_g5_rows
from tma2.cli.oracle import run_layer
from tma2.data.f32pack import iter_pack_raw
from tma2.detect.controls import parse_imm_name, tune_threshold
from tma2.detect.matching import episodes
from tma2.detect.steady_leg import split_stat, window_fits
from tma2.eval.errors import Truth, row_error
from tma2.eval.rows import G5_GATE_MIN
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, oracle_inputs, trivial_inputs
from tma2.references.classical import bearing_data_from_arrays
from tma2.references.imm import imm_predict

IMM = "imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    ap.add_argument("--scenarios", type=int, default=500)
    ap.add_argument("--window", type=int, default=36)
    ap.add_argument("--far", type=float, nargs="+", default=[0.01, 0.05])
    ap.add_argument("--out")
    a = ap.parse_args()
    torch.set_default_dtype(torch.float64)
    scen: list[Any] = []
    for _, meta, own, tgt, obs in iter_pack_raw(a.validation):
        if abs(float(meta["parameters"]["noise_sigma_rad"]) - math.pi / 180) > 1e-6:
            continue
        d = bearing_data_from_arrays(meta, own, obs)
        z0 = np.zeros(d.n, dtype=np.int64)  # unrestricted windows
        st, ok, _mis = window_fits(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, a.window, z0)
        lam, where = split_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, a.window, z0)
        scen.append((meta, d, Truth.from_block(meta, own, tgt), lam, where))
        if len(scen) >= a.scenarios:
            break
    imm = parse_imm_name(IMM)
    held = np.array([float(lam[k]) for meta, _d, _t, lam, _w in scen for k in held_g5_rows(meta)])
    layer = PhysicsLayer()
    r_max = max(d.n for _m, d, _t, _l, _w in scen)
    results: dict[str, Any] = {"scenarios": len(scen), "window": a.window}

    def g5(meta: dict[str, Any], d: Any) -> list[int]:
        ks = [
            d.zig_index + int(round(m * 60 / float(meta["parameters"]["dt_s"])))
            for m in G5_GATE_MIN
        ]
        return [k for k in ks if k < d.n]

    def score(name: str, make: Any) -> float:
        items, keys = [], []
        for meta, d, tr, lam, where in scen:
            for k in g5(meta, d):
                inp = make(meta, d, lam, where, k)
                if inp is not None:
                    items.append((d, k, inp))
                    keys.append((tr, d, k))
        errs = []
        for s in range(0, len(items), 256):
            out = run_layer(layer, items[s : s + 256], r_max)
            for j, (tr, d, k) in enumerate(keys[s : s + 256]):
                st = out.state[j].numpy()
                row = {
                    "timestamp_s": float(d.t[k]),
                    "range_m": float(out.range[j]),
                    "course_rad": float(out.course[j]),
                    "speed_mps": float(out.speed[j]),
                    "x_m": float(st[0]),
                    "y_m": float(st[1]),
                    "converged": bool(out.plausible[j]),
                }
                errs.append(row_error(tr, row, "plausible").range_rel)
        med = float(np.median(errs))
        results[name] = {"median_range_rel": med, "rows": len(errs)}
        print(f"{name:34s} median range error {med:.4f}  ({len(errs)} rows)")
        return med

    def triv(meta: Any, d: Any, lam: Any, where: Any, k: int) -> LayerInputs | None:
        return trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)

    def orc(meta: Any, d: Any, lam: Any, where: Any, k: int) -> LayerInputs | None:
        return oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, meta.get("manoeuvres"), True)

    score("least_squares (layer, no knots)", triv)
    score("oracle (truth spans, speed prior)", orc)
    # IMM at the same rows
    ierr = []
    for meta, d, tr, _l, _w in scen:
        rows = {round(float(r["timestamp_s"]), 3): r for r in imm_predict(d, imm)["rows"]}
        for k in g5(meta, d):
            r = rows.get(round(float(d.t[k]), 3))
            ierr.append(row_error(tr, r, "plausible").range_rel if r else math.inf)
    results["imm"] = {"median_range_rel": float(np.median(ierr)), "rows": len(ierr)}
    print(f"{'imm (frozen)':34s} median range error {np.median(ierr):.4f}  ({len(ierr)} rows)")

    for far in a.far:
        h, got = tune_threshold(held, far)
        knots_by = {}
        for meta, d, _t, lam, where in scen:
            al = lam > h
            ks = []
            for e0, e1 in episodes(al, float(meta["parameters"]["dt_s"])):
                peak = e0 + int(np.argmax(lam[e0 : e1 + 1]))
                if where[peak] > 0:
                    ks.append((e0, int(where[peak])))  # (alarm row, knot row)
            knots_by[id(d)] = ks
        # localisation and false knots
        loc, false_k, total_k = [], 0, 0
        for meta, d, _t, _l, _w in scen:
            bounds = [
                int(x)
                for sp in meta.get("manoeuvres") or []
                for x in (sp["start_index"], sp["end_index"])
            ]
            for _alarm, row in knots_by[id(d)]:
                total_k += 1
                if bounds:
                    dist = min(abs(row - b) for b in bounds)
                    loc.append(dist)
                    false_k += int(dist > 18)
                else:
                    false_k += 1
        loc_a = np.asarray(loc, dtype=float) * 10.0
        print(
            f"  knots {total_k}, false (> 180 s from any boundary) {false_k / max(total_k, 1):.2f}, "
            f"localisation median {np.median(loc_a):.0f} s, P75 {np.percentile(loc_a, 75):.0f} s"
        )
        results[f"knots_far{far}"] = {
            "total": total_k,
            "false_share": false_k / max(total_k, 1),
            "loc_median_s": float(np.median(loc_a)),
        }

        def detected_truth(meta: Any, d: Any, lam: Any, where: Any, k: int) -> Any:
            """Truth knots, but only for spans with an alarm by row k inside [start − 1, end + 30]."""
            alarms = [al for al, _r in knots_by[id(d)] if al <= k]  # noqa: B023 (called in the loop)
            spans = [
                sp
                for sp in meta.get("manoeuvres") or []
                if any(
                    int(sp["start_index"]) - 1 <= al <= int(sp["end_index"]) + 30 for al in alarms
                )
            ]
            return oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, spans, True)

        score(f"truth knots for detected spans @{far:.0%}", detected_truth)
        for delay in (0, 12, 18, 30):

            def relocated(
                meta: Any, d: Any, lam: Any, where: Any, k: int, delay: int = delay
            ) -> Any:
                """Each alarm's knot taken from the split found by the window ending ``delay`` rows
                after the alarm (never after k), speed prior on every knot."""
                base = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
                if base is None:
                    return None
                cp = np.zeros(d.n)
                for alarm, _row in knots_by[id(d)]:  # noqa: B023
                    if alarm > k:
                        continue
                    r = min(alarm + delay, k)
                    row = int(where[r])
                    if 0 < row <= k:
                        cp[row] = 1.0
                return LayerInputs(cp, cp.copy(), base.log_weight, base.theta0, cp.copy())

            score(f"knots relocated +{delay * 10} s @{far:.0%} +prior", relocated)
        for prior in (False, True):

            def det(meta: Any, d: Any, lam: Any, where: Any, k: int, prior: bool = prior) -> Any:
                base = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
                if base is None:
                    return None
                cp = np.zeros(d.n)
                for alarm, row in knots_by[id(d)]:  # noqa: B023
                    if alarm <= k and 0 < row <= k:
                        cp[row] = 1.0
                sw = cp.copy() if prior else np.zeros(d.n)
                return LayerInputs(cp, sw, base.log_weight, base.theta0, sw)

            score(f"steady-leg knots @{far:.0%} FA{' +prior' if prior else ''}", det)
        results[f"threshold_far{far}"] = {"threshold": h, "achieved": got}
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
