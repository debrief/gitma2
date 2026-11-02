"""Steady-leg trial, step 3 (docs/research/07): nominate knots from the window-local split
statistic, then confirm and place each by the physics layer's whole-history cost.

For each scenario, alarm episodes of Λ (unrestricted W-row windows) are taken in time order. At
an episode's first row a, the layer solves the history [0, a] with the knots accepted so far,
and once more with each candidate knot c in the window (every ``--step`` rows of
[a − W + 1, a], none within ``--step`` rows of an accepted knot). The candidate with the lowest
cost is accepted if it lowers the cost by more than τ (the cost is Σ (r/σ)², so τ is a χ² value
with 2 degrees of freedom, the velocity increment). An accepted knot is used from row a on.

The thresholds here are tuned on the rows they score (validation), so the numbers are a pilot,
not a result. Scored at σ = 1° G5 rows against batch least squares (the layer, no knots), the
oracle (truth spans) and the frozen IMM, all on the same rows.

    uv run python scripts/research/steady_leg_confirm.py --validation data/gd-val/validation.f32pack \
        --scenarios 500 --out experiments/<id>/steady_leg_confirm.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from typing import Any

import numpy as np
import torch

from tma2.cli.oracle import run_layer
from tma2.data.f32pack import iter_pack_raw
from tma2.detect.controls import parse_imm_name
from tma2.detect.matching import episodes
from tma2.detect.steady_leg import split_stat, window_fits
from tma2.eval.errors import Truth, row_error
from tma2.eval.rows import G5_GATE_MIN, settled_row
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, oracle_inputs, trivial_inputs
from tma2.references.classical import bearing_data_from_arrays
from tma2.references.imm import imm_predict

IMM = "imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16"
BATCH = 256


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    ap.add_argument("--scenarios", type=int, default=500)
    ap.add_argument("--window", type=int, default=36)
    ap.add_argument("--step", type=int, default=3)
    ap.add_argument("--far", default="0.01,0.03,0.05,0.1")
    ap.add_argument("--tau", default="6,9.21,13.8")
    ap.add_argument("--out")
    a = ap.parse_args()
    torch.set_default_dtype(torch.float64)
    w = a.window
    scen: list[tuple[dict[str, Any], Any, Truth, np.ndarray]] = []
    for _, meta, own, tgt, obs in iter_pack_raw(a.validation):
        if abs(meta["parameters"]["noise_sigma_rad"] - math.pi / 180) > 1e-6:
            continue
        d = bearing_data_from_arrays(meta, own, obs)
        z0 = np.zeros(d.n, dtype=np.int64)  # unrestricted windows
        st, ok, _mis = window_fits(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, w, z0)
        lam, _where = split_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, w, z0)
        scen.append((meta, d, Truth.from_block(meta, own, tgt), lam))
        if len(scen) >= a.scenarios:
            break
    held = np.array(
        [lam[k] for meta, d, _t, lam in scen for k in range(w, d.n) if settled_row(meta, k)]
    )
    layer = PhysicsLayer()
    r_max = max(d.n for _m, d, _t, _l in scen)

    def g5(meta: dict[str, Any], d: Any) -> list[int]:
        rows = (d.zig_index + int(round(x * 60 / float(d.t[1] - d.t[0]))) for x in G5_GATE_MIN)
        return [k for k in rows if k < d.n]

    def knot_inputs(d: Any, k: int, knots: list[int], prior: bool) -> LayerInputs | None:
        base = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
        if base is None:
            return None
        cp = np.zeros(d.n)
        for r in knots:
            if 0 < r <= k:
                cp[r] = 1.0
        sw = cp.copy() if prior else np.zeros(d.n)
        return LayerInputs(cp, sw, base.log_weight, base.theta0, sw.copy())

    def costs(items: list[tuple[Any, int, LayerInputs]]) -> list[float]:
        out: list[float] = []
        for s in range(0, len(items), BATCH):
            res = run_layer(layer, items[s : s + BATCH], r_max)
            out.extend(float(c) for c in res.cost)
        return out

    def score(make: Any) -> dict[str, Any]:
        items: list[tuple[Any, int, LayerInputs]] = []
        keys: list[tuple[Truth, Any, int, bool]] = []
        missing: list[bool] = []
        for i, (meta, d, tr, _l) in enumerate(scen):
            for k in g5(meta, d):
                inp = make(i, meta, d, k)
                st = settled_row(meta, k)
                if inp is None:
                    missing.append(st)
                    continue
                items.append((d, k, inp))
                keys.append((tr, d, k, st))
        errs: list[tuple[float, float, float, bool]] = []
        for s in range(0, len(items), BATCH):
            out = run_layer(layer, items[s : s + BATCH], r_max)
            for j, (tr, d, k, st) in enumerate(keys[s : s + BATCH]):
                x = out.state[j].numpy()
                row = {
                    "timestamp_s": float(d.t[k]),
                    "range_m": float(out.range[j]),
                    "course_rad": float(out.course[j]),
                    "speed_mps": float(out.speed[j]),
                    "x_m": float(x[0]),
                    "y_m": float(x[1]),
                    "converged": bool(out.plausible[j]),
                }
                e = row_error(tr, row, "plausible")
                errs.append((e.range_rel, e.course_deg, e.speed_kt, st))
        errs.extend((math.inf, math.inf, math.inf, st) for st in missing)
        return summarise(errs)

    def summarise(errs: list[tuple[float, float, float, bool]]) -> dict[str, Any]:
        arr = np.array([e[:3] for e in errs])
        sett = np.array([e[:3] for e in errs if e[3]])
        return {
            "rows": len(errs),
            "range": float(np.median(arr[:, 0])),
            "course_deg": float(np.median(arr[:, 1])),
            "speed_kt": float(np.median(arr[:, 2])),
            "settled_rows": len(sett),
            "settled_range": float(np.median(sett[:, 0])) if len(sett) else math.nan,
        }

    def confirm(h: float, tau: float) -> list[list[tuple[int, int]]]:
        eps = [[e0 for e0, _e1 in episodes(lam > h, 10.0, merge_s=0.0)] for *_x, lam in scen]
        acc: list[list[tuple[int, int]]] = [[] for _ in scen]
        for p in range(max((len(e) for e in eps), default=0)):
            items: list[tuple[Any, int, LayerInputs]] = []
            meta_: list[tuple[int, int, int]] = []
            for i, (_m, d, _t, _l) in enumerate(scen):
                if p >= len(eps[i]):
                    continue
                al = eps[i][p]
                cur = [r for _a, r in acc[i]]
                cands = [
                    c
                    for c in range(max(1, al - w + 1), al + 1, a.step)
                    if all(abs(c - r) > a.step for r in cur)
                ]
                base = knot_inputs(d, al, cur, False)
                if base is None or not cands:
                    continue
                items.append((d, al, base))
                meta_.append((i, al, -1))
                for c in cands:
                    inp = knot_inputs(d, al, [*cur, c], False)
                    assert inp is not None
                    items.append((d, al, inp))
                    meta_.append((i, al, c))
            best: dict[int, dict[str, float]] = {}
            for (i, al, c), cst in zip(meta_, costs(items), strict=True):
                b = best.setdefault(i, {})
                if c < 0:
                    b["base"] = cst
                elif cst < b.get("cost", math.inf):
                    b.update(cost=cst, row=c, alarm=al)
            for i, b in best.items():
                if "row" in b and b["base"] - b["cost"] > tau:
                    acc[i].append((int(b["alarm"]), int(b["row"])))
        return acc

    t0 = time.time()
    results: dict[str, Any] = {"scenarios": len(scen), "window": w, "step": a.step}
    results["least_squares"] = score(lambda i, meta, d, k: knot_inputs(d, k, [], False))
    results["oracle"] = score(
        lambda i, meta, d, k: oracle_inputs(
            d.t, d.ox, d.oy, d.z, d.valid, k, meta.get("manoeuvres"), True
        )
    )
    imm = parse_imm_name(IMM)
    ierr: list[tuple[float, float, float, bool]] = []
    for meta, d, tr, _l in scen:
        rows = {round(float(r["timestamp_s"]), 3): r for r in imm_predict(d, imm)["rows"]}
        for k in g5(meta, d):
            r = rows.get(round(float(d.t[k]), 3))
            e = row_error(tr, r, "plausible") if r else None
            ierr.append(
                (e.range_rel, e.course_deg, e.speed_kt, settled_row(meta, k))
                if e
                else (math.inf, math.inf, math.inf, settled_row(meta, k))
            )
    results["imm"] = summarise(ierr)
    for name in ("least_squares", "oracle", "imm"):
        print(f"{name:14s} {results[name]}", flush=True)
    results["confirmed"] = []
    for q in (float(x) for x in a.far.split(",")):
        h = float(np.quantile(held, 1 - q))
        for tau in (float(x) for x in a.tau.split(",")):
            acc = confirm(h, tau)
            nk = sum(len(x) for x in acc)
            false = 0
            loc: list[int] = []
            for (meta, _d, _t, _l), kn in zip(scen, acc, strict=True):
                bounds = [
                    x
                    for sp in meta.get("manoeuvres") or []
                    for x in (sp["start_index"], sp["end_index"])
                ]
                for _al, r in kn:
                    dd = min((abs(r - x) for x in bounds), default=10**9)
                    if dd > 18:
                        false += 1
                    else:
                        loc.append(dd)
            rec = {
                "far": q,
                "threshold": h,
                "tau": tau,
                "knots_per_scenario": nk / len(scen),
                "false_share": false / max(nk, 1),
                "localisation_median_rows": float(np.median(loc)) if loc else math.nan,
                "no_prior": score(
                    lambda i, meta, d, k, acc=acc: knot_inputs(
                        d, k, [r for al, r in acc[i] if al <= k], False
                    )
                ),
                "prior": score(
                    lambda i, meta, d, k, acc=acc: knot_inputs(
                        d, k, [r for al, r in acc[i] if al <= k], True
                    )
                ),
            }
            results["confirmed"].append(rec)
            print(
                f"FA {q:.0%} tau {tau}: knots {rec['knots_per_scenario']:.2f} "
                f"false {rec['false_share']:.2f} loc {rec['localisation_median_rows']:.1f} | "
                f"no prior {rec['no_prior']} | prior {rec['prior']} [{time.time() - t0:.0f} s]",
                flush=True,
            )
    if a.out:
        with open(a.out, "w") as f:
            json.dump(results, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
