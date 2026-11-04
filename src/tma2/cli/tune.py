"""``tma2-tune``: re-tune the EKF and IMM on a validation split and freeze them.

``--criterion zig300`` (spec 003 FR-019, research R6; constant-velocity data): median relative
range error at zig + 5 min on σ = 1° rows of the first ``--scenarios`` validation scenarios
(non-converged rows count as +∞), over the CV grid.

``--criterion g5`` (spec 004 FR-026, research R7; manoeuvring data): median relative range error
over every G5 row (σ = 1°, zig + 5/10/15/20 min where reached, ``eval/rows.py``) of the first
``--scenarios`` σ = 1° scenarios that contribute one, over a grid around P0's phase-4 setting.
Rows count as converged under spec 004's one definition (``errors.plausible_row``).

Ties go to the earlier grid entry. Writes grid.csv, choice.json and the experiment manifest."""

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
from tma2.eval.errors import plausible_row
from tma2.eval.experiment import Check, Experiment
from tma2.eval.g1 import GATE_S as _GATE_S  # the gate's rows (one definition)
from tma2.eval.g1 import SIGMA_1
from tma2.eval.rows import G5_GATE_MIN
from tma2.references.classical import bearing_data_from_arrays
from tma2.references.ekf import ekf_name, ekf_predict
from tma2.references.imm import ImmParams, imm_name, imm_predict
from tma2.types import dump_record

GATE_S = _GATE_S["range_rel"]
# Research R6: on constant-velocity data the coordinated-turn branch rarely carries weight, so
# its rate parameters are fixed at the phase-4 values (gitma decision 29). The first grid put
# every choice on an edge (lowest process noise, largest R scale, lowest switch rate), so every
# axis reaches past it: a frozen setting on an edge must sit on a plateau (recorded in R6).
R_SCALES = (1.0, 2.0, 8.0, 16.0, 32.0)
IMM_GRID = [
    ImmParams(cv, 0.03, 0.01, sw, 4.0, r)
    for cv, sw, r in itertools.product(
        (0.0003, 0.001, 0.003, 0.01, 0.03), (1e-5, 1e-4, 0.001, 0.01), R_SCALES
    )
]
EKF_GRID = [
    (sa, 4.0, r)
    for sa, r in itertools.product((0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03, 0.1), R_SCALES)
]
# Research R7 (spec 004): around P0's phase-4 setting imm-cv0.01-ct0.03-w0.01-s0.001-p4-r8.
G5_R_SCALES = (2.0, 8.0, 16.0)
G5_IMM_GRID = [
    ImmParams(cv, ct, w, sw, 4.0, r)
    for cv, ct, w, sw, r in itertools.product(
        (0.003, 0.01, 0.03),
        (0.01, 0.03, 0.1),
        (0.003, 0.01, 0.03),
        (0.0003, 0.001, 0.003),
        G5_R_SCALES,
    )
]
# The first pass on seed 304 chose cv 0.003, ω 0.003, r 16: three edges with the error still
# falling (ω 0.01 → 0.003: 0.1003 → 0.0970; r 8 → 16: 0.0985 → 0.0970), so each of those axes
# reaches past its edge at the interior values of the others (ct 0.03, switch 0.001; spec 003's
# rule, research R7). Earlier grid entries keep priority on ties.
_G5_EXT = [
    ImmParams(cv, 0.03, w, 0.001, 4.0, r)
    for cv, w, r in itertools.product(
        (0.0003, 0.001, 0.003), (0.0003, 0.001, 0.003), (16.0, 32.0, 64.0)
    )
]
G5_IMM_GRID += [p for p in _G5_EXT if p not in G5_IMM_GRID]
G5_EKF_GRID = [
    (sa, 4.0, r)
    for sa, r in itertools.product((0.0003, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3), G5_R_SCALES)
]
# MAN2 pass 2 (spec 006 T032): the first pass on seed 314 chose imm-cv0.03-ct0.1-w0.01-s0.0003-p4-r2
# and ekf-sa0.0003-p4-r2, every axis but ω on an edge with the error still falling (cv 0.01 → 0.03:
# 0.5913 → 0.5852; ct 0.03 → 0.1: 0.5876 → 0.5852; r 8 → 2: 0.601 → 0.585; switch 0.001 → 0.0003:
# 0.5858 → 0.5852; sa 0.001 → 0.0003: 0.5886 → 0.5833). Each axis reaches past its edge (spec
# 003's rule), with the first pass's choices included so the comparison is on the same rows.
MAN2_PASS2_IMM_GRID = [
    ImmParams(cv, ct, 0.01, sw, 4.0, r)
    for cv, ct, sw, r in itertools.product(
        (0.03, 0.1, 0.3), (0.1, 0.3, 1.0), (0.0003, 0.0001), (2.0, 1.0)
    )
]
MAN2_PASS2_EKF_GRID = [
    (sa, 4.0, r) for sa, r in itertools.product((0.0003, 0.0001, 0.00003), (2.0, 1.0))
]
GRIDS = {"default": None, "man2-pass2": (MAN2_PASS2_IMM_GRID, MAN2_PASS2_EKF_GRID)}

CRITERIA = {
    "zig300": "median relative range error at zig + 5 min, σ = 1° validation rows",
    "g5": "median relative range error over all σ = 1° G5 rows (zig + 5/10/15/20 min), validation",
}


def _load(path: str, limit: int, criterion: str = "zig300") -> list[Any]:
    """(meta, own, tgt, obs, rows) for the first ``limit`` σ = 1° scenarios with a scored row."""
    out = []
    for _, meta, own, tgt, obs in iter_pack_raw(path):
        if abs(float(meta["parameters"]["noise_sigma_rad"]) - SIGMA_1) > 1e-6:
            continue
        zig = int(meta["zig_index"])
        dt = float(meta["parameters"]["dt_s"])
        offsets = [GATE_S] if criterion == "zig300" else [60.0 * m for m in G5_GATE_MIN]
        ks = [zig + int(round(s / dt)) for s in offsets]
        ks = [k for k in ks if k < int(meta["samples"])]
        if not ks:
            continue
        out.append((meta, own, tgt, obs, ks))
        if len(out) >= limit:
            break
    return out


def _score(job: tuple[str, Any, str, int, str]) -> tuple[str, str, float]:
    kind, params, path, limit, criterion = job
    errs = []
    for meta, own, tgt, obs, ks in _load(path, limit, criterion):
        d = bearing_data_from_arrays(meta, own, obs)
        pred = imm_predict(d, params) if kind == "imm" else ekf_predict(d, *params)
        by_t = {round(float(r["timestamp_s"]), 3): r for r in pred["rows"]}
        for k in ks:
            row = by_t.get(round(float(own[k, 0]), 3))
            tr = math.hypot(float(tgt[k, 1] - own[k, 1]), float(tgt[k, 2] - own[k, 2]))
            if criterion == "zig300":
                ok = row is not None and bool(row["converged"])
            else:
                ok = row is not None and plausible_row(row)
            errs.append(abs(row["range_m"] - tr) / tr if ok and row is not None else math.inf)
    name = imm_name(params) if kind == "imm" else ekf_name(*params)
    return kind, name, float(np.median(errs)) if errs else math.inf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-tune")
    ap.add_argument("--validation", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--scenarios", type=int, default=2000, help="σ = 1° scenarios used")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--allow-dirty", action="store_true", help="exploration only: not frozen")
    ap.add_argument("--criterion", choices=sorted(CRITERIA), default="zig300")
    ap.add_argument(
        "--grid",
        choices=sorted(GRIDS),
        default="default",
        help="man2-pass2: the second pass past the MAN2 first pass's edges (g5 only)",
    )
    ap.add_argument(
        "--shard",
        metavar="I/N",
        help="score only grid entries I, I + N, … and write grid-part-I.csv (no choice); "
        "a long tune split over several runners",
    )
    ap.add_argument(
        "--from-parts",
        nargs="+",
        metavar="CSV",
        help="score nothing: read the shards' grid-part files and choose as the whole grid would "
        "(the same order, so ties still go to the earlier entry)",
    )
    a = ap.parse_args(argv)
    folder = Path(a.experiment)
    exp = Experiment(id=folder.name, folder=folder)
    if exp.git()[1] and not a.allow_dirty:
        # The frozen references must come from a committed tree (constitution II).
        print(
            "tma2-tune: the working tree is dirty; commit first (or --allow-dirty)", file=sys.stderr
        )
        return 2
    exp.command_lines.append("tma2-tune " + " ".join(sys.argv[1:]))
    exp.add_dataset(a.validation, dump_record(read_pack_header(a.validation)))
    imm_grid, ekf_grid = (
        (IMM_GRID, EKF_GRID) if a.criterion == "zig300" else (G5_IMM_GRID, G5_EKF_GRID)
    )
    chosen = GRIDS[a.grid]
    if chosen is not None:
        if a.criterion != "g5":
            print("tma2-tune: --grid man2-pass2 needs --criterion g5", file=sys.stderr)
            return 2
        imm_grid, ekf_grid = chosen
        exp.command_lines.append(f"grid: {a.grid}")
    jobs: list[tuple[str, Any, str, int, str]] = [
        ("imm", p, a.validation, a.scenarios, a.criterion) for p in imm_grid
    ]
    jobs += [("ekf", p, a.validation, a.scenarios, a.criterion) for p in ekf_grid]
    if a.shard:
        i, n = (int(x) for x in a.shard.split("/"))
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            part = list(pool.map(_score, jobs[i::n]))
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"grid-part-{i}.csv").write_text(
            "".join(f"{pk},{pn},{pm!r}\n" for pk, pn, pm in part)
        )
        return 0
    if a.from_parts:
        scored: dict[tuple[str, str], float] = {}
        for f in a.from_parts:
            for line in Path(f).read_text().splitlines():
                k_s, n_s, m_s = line.split(",")
                scored[(k_s, n_s)] = float(m_s)
        results: list[tuple[str, str, float]] = []
        for job_kind, params, *_ in jobs:
            nm = imm_name(params) if job_kind == "imm" else ekf_name(*params)
            if (job_kind, nm) not in scored:
                print(f"tma2-tune: {job_kind} {nm} missing from the parts", file=sys.stderr)
                return 2
            results.append((job_kind, nm, scored[(job_kind, nm)]))
        exp.command_lines.append("parts: " + " ".join(a.from_parts))
    else:
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            results = list(pool.map(_score, jobs))
    lines = [f"filter,name,median_range_rel_{a.criterion}"]
    best: dict[str, tuple[str, float, Any]] = {}
    for (kind, name, med), job in zip(results, jobs, strict=True):
        lines.append(f"{kind},{name},{med!r}")
        if kind not in best or med < best[kind][1]:
            best[kind] = (name, med, job[1])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "grid.csv").write_text("\n".join(lines) + "\n")
    key = "median_range_rel_zig300" if a.criterion == "zig300" else "median_range_rel_g5"
    imm_p: ImmParams = best["imm"][2]
    sa, p0, r = best["ekf"][2]
    choice = {
        "imm": {
            "name": best["imm"][0],
            key: best["imm"][1],
            **imm_p.__dict__,
        },
        "ekf": {
            "name": best["ekf"][0],
            key: best["ekf"][1],
            "sigma_a": sa,
            "p0_scale": p0,
            "r_scale": r,
        },
        "criterion": CRITERIA[a.criterion],
        "criterion_id": a.criterion,
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
    exp.write("G1" if a.criterion == "zig300" else "GD")
    print(json.dumps({k: choice[k]["name"] for k in ("imm", "ekf")}))
    return 0
