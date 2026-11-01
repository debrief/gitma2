"""``tma2-tune``: re-tune the EKF and IMM on the CV validation split and freeze them (spec 003
FR-019; research R6). Criterion: median relative range error at zig + 5 min on σ = 1° rows of the
first ``--scenarios`` validation scenarios (non-converged rows count as +∞); ties go to the
earlier grid entry. Writes grid.csv, choice.json and the experiment manifest."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.f32pack import iter_pack_raw, read_pack_header
from tma2.eval.experiment import Check, Experiment
from tma2.references.classical import bearing_data_from_arrays
from tma2.references.ekf import ekf_name, ekf_predict
from tma2.references.imm import ImmParams, imm_name, imm_predict
from tma2.types import dump_record

GATE_S = 300.0
SIGMA_1 = math.radians(1.0)
# Research R6: on constant-velocity data the coordinated-turn branch rarely carries weight, so
# its rate parameters are fixed at the phase-4 values (gitma decision 29). The first grid put
# every choice on an edge (lowest process noise, largest R scale), so both axes reach one step
# past it: no frozen setting may sit on a grid edge.
R_SCALES = (1.0, 2.0, 8.0, 16.0, 32.0)
IMM_GRID = [
    ImmParams(cv, 0.03, 0.01, sw, 4.0, r)
    for cv, sw, r in itertools.product((0.0003, 0.001, 0.003, 0.01, 0.03), (0.001, 0.01), R_SCALES)
]
EKF_GRID = [
    (sa, 4.0, r)
    for sa, r in itertools.product((0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03, 0.1), R_SCALES)
]


def _load(path: str, limit: int) -> list[Any]:
    out = []
    for _, meta, own, tgt, obs in iter_pack_raw(path):
        if abs(float(meta["parameters"]["noise_sigma_rad"]) - SIGMA_1) > 1e-6:
            continue
        zig = int(meta["zig_index"])
        k = zig + int(round(GATE_S / float(meta["parameters"]["dt_s"])))
        if k >= int(meta["samples"]):
            continue
        out.append((meta, own, tgt, obs, k))
        if len(out) >= limit:
            break
    return out


def _score(job: tuple[str, Any, str, int]) -> tuple[str, str, float]:
    kind, params, path, limit = job
    errs = []
    for meta, own, tgt, obs, k in _load(path, limit):
        d = bearing_data_from_arrays(meta, own, obs)
        pred = imm_predict(d, params) if kind == "imm" else ekf_predict(d, *params)
        t = float(own[k, 0])
        row = next((r for r in pred["rows"] if abs(r["timestamp_s"] - t) < 1e-3), None)
        tr = math.hypot(float(tgt[k, 1] - own[k, 1]), float(tgt[k, 2] - own[k, 2]))
        errs.append(abs(row["range_m"] - tr) / tr if row and row["converged"] else math.inf)
    name = imm_name(params) if kind == "imm" else ekf_name(*params)
    return kind, name, float(np.median(errs)) if errs else math.inf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-tune")
    ap.add_argument("--validation", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--scenarios", type=int, default=2000, help="σ = 1° scenarios used")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    folder = Path(a.experiment)
    exp = Experiment(id=folder.name, folder=folder)
    exp.command_lines.append("tma2-tune " + " ".join(sys.argv[1:]))
    exp.add_dataset(a.validation, dump_record(read_pack_header(a.validation)))
    jobs: list[tuple[str, Any, str, int]] = [
        ("imm", p, a.validation, a.scenarios) for p in IMM_GRID
    ]
    jobs += [("ekf", p, a.validation, a.scenarios) for p in EKF_GRID]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        results = list(pool.map(_score, jobs))
    lines = ["filter,name,median_range_rel_zig300"]
    best: dict[str, tuple[str, float, Any]] = {}
    for (kind, name, med), job in zip(results, jobs, strict=True):
        lines.append(f"{kind},{name},{med!r}")
        if kind not in best or med < best[kind][1]:
            best[kind] = (name, med, job[1])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "grid.csv").write_text("\n".join(lines) + "\n")
    imm_p: ImmParams = best["imm"][2]
    sa, p0, r = best["ekf"][2]
    choice = {
        "imm": {
            "name": best["imm"][0],
            "median_range_rel_zig300": best["imm"][1],
            **imm_p.__dict__,
        },
        "ekf": {
            "name": best["ekf"][0],
            "median_range_rel_zig300": best["ekf"][1],
            "sigma_a": sa,
            "p0_scale": p0,
            "r_scale": r,
        },
        "criterion": "median relative range error at zig + 5 min, σ = 1° validation rows",
        "scenarios": a.scenarios,
    }
    (folder / "choice.json").write_text(json.dumps(choice, indent=2, sort_keys=True) + "\n")
    for kind in ("imm", "ekf"):
        exp.add_estimator(best[kind][0], choice[kind])
        exp.checks.append(
            Check(
                f"tuned-{kind}",
                "pass",
                f"{best[kind][0]}: {best[kind][1]:.4f}",
                value=best[kind][1],
            )
        )
    exp.write("G1")
    print(json.dumps({k: choice[k]["name"] for k in ("imm", "ekf")}))
    return 0
