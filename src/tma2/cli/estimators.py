"""Estimator CLIs: ``tma2-solve``, ``tma2-track``, ``tma2-naive``, ``tma2-crb``.

Each reads a split (``.f32pack`` or ``.ndjson``), writes a prediction file in gitma's format
bound to the truth file by digest, and prints a JSON summary. Exit 2 on usage errors.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.f32pack import iter_pack_raw, read_pack_header
from tma2.data.io import file_digest
from tma2.data.ndjson import iter_ndjson_raw, read_ndjson_header
from tma2.eval.predictions import PredictionWriter
from tma2.references.classical import CLASSICAL, bearing_data_from_arrays, classical_predict
from tma2.references.crb import crb_rows
from tma2.references.ekf import ekf_name, ekf_predict
from tma2.references.imm import ImmParams, imm_name, imm_predict
from tma2.references.naive import NAIVE, fit_naive, naive_predict
from tma2.types import DatasetHeader

Block = tuple[int, dict[str, Any], np.ndarray, np.ndarray, np.ndarray]


def _record_arrays(record: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    own = np.array(
        [
            [s["timestamp_s"], s["x_m"], s["y_m"], s["course_rad"], s["speed_mps"]]
            for s in record["ownship"]["states"]
        ],
        dtype=np.float32,
    )
    tgt = np.array(
        [
            [s["timestamp_s"], s["x_m"], s["y_m"], s["course_rad"], s["speed_mps"]]
            for s in record["target"]["states"]
        ],
        dtype=np.float32,
    )
    obs = np.array(
        [
            [o["timestamp_s"], o["bearing_rad"], 1.0 if o["valid"] else 0.0]
            for o in record["observations"]
        ],
        dtype=np.float32,
    )
    return own, tgt, obs


def open_split(path: str | Path) -> tuple[DatasetHeader, Iterator[Block]]:
    """Header and block iterator for either file format."""
    p = Path(path)
    if p.suffix == ".f32pack":
        header = read_pack_header(p)
        return header, iter_pack_raw(p)
    header = read_ndjson_header(p)

    def blocks() -> Iterator[Block]:
        for i, (_, rec) in enumerate(iter_ndjson_raw(p, header)):
            own, tgt, obs = _record_arrays(rec)
            yield i, rec["metadata"], own, tgt, obs

    return header, blocks()


def _write(
    out: str, estimator: str, mode: str, truth: str, predictions: Iterator[dict[str, Any]]
) -> dict[str, Any]:
    t0 = time.perf_counter()
    w = PredictionWriter(out, estimator, mode, truth)
    try:
        n = 0
        non_converged = 0
        for p in predictions:
            w.write(p)
            n += 1
            non_converged += sum(1 for r in p["rows"] if not r["converged"])
        w.close()
    except BaseException:
        w.abort()
        raise
    return {
        "out": out,
        "estimator": estimator,
        "scenarios": n,
        "non_converged_rows": non_converged,
        "seconds": time.perf_counter() - t0,
    }


def solve_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="tma2-solve", description="Batch least-squares bearings-only solver."
    )
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-timestep", action="store_true")
    ap.add_argument("--max-iter", type=int, default=50)
    a = ap.parse_args(argv)
    if a.max_iter <= 0:
        print("tma2-solve: --max-iter must be > 0", file=sys.stderr)
        return 2
    mode = "per_timestep" if a.per_timestep else "final"
    _, blocks = open_split(a.inp)

    def preds() -> Iterator[dict[str, Any]]:
        for _, meta, own, _tgt, obs in blocks:
            yield classical_predict(bearing_data_from_arrays(meta, own, obs), mode, a.max_iter)

    print(json.dumps(_write(a.out, CLASSICAL, mode, a.inp, preds())))
    return 0


def track_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="tma2-track", description="EKF or IMM tracker (gitma's references)."
    )
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--filter", required=True, choices=["ekf", "imm"])
    ap.add_argument("--sigma-a", type=float)
    ap.add_argument("--sigma-cv", type=float)
    ap.add_argument("--sigma-ct", type=float)
    ap.add_argument("--sigma-omega", type=float)
    ap.add_argument("--switch", type=float)
    ap.add_argument("--p0-scale", type=float, default=1.0)
    ap.add_argument("--r-scale", type=float, default=1.0)
    a = ap.parse_args(argv)
    if a.p0_scale <= 0 or a.r_scale <= 0:
        print("tma2-track: scales must be > 0", file=sys.stderr)
        return 2
    _, blocks = open_split(a.inp)
    if a.filter == "ekf":
        if a.sigma_a is None or a.sigma_a < 0:
            print("tma2-track: --filter ekf needs --sigma-a ≥ 0", file=sys.stderr)
            return 2
        name = ekf_name(a.sigma_a, a.p0_scale, a.r_scale)

        def preds_ekf() -> Iterator[dict[str, Any]]:
            for _, meta, own, _tgt, obs in blocks:
                yield ekf_predict(
                    bearing_data_from_arrays(meta, own, obs), a.sigma_a, a.p0_scale, a.r_scale
                )

        print(json.dumps(_write(a.out, name, "per_timestep", a.inp, preds_ekf())))
        return 0
    if None in (a.sigma_cv, a.sigma_ct, a.sigma_omega, a.switch):
        print(
            "tma2-track: --filter imm needs --sigma-cv --sigma-ct --sigma-omega --switch",
            file=sys.stderr,
        )
        return 2
    params = ImmParams(a.sigma_cv, a.sigma_ct, a.sigma_omega, a.switch, a.p0_scale, a.r_scale)

    def preds_imm() -> Iterator[dict[str, Any]]:
        for _, meta, own, _tgt, obs in blocks:
            yield imm_predict(bearing_data_from_arrays(meta, own, obs), params)

    print(json.dumps(_write(a.out, imm_name(params), "per_timestep", a.inp, preds_imm())))
    return 0


def naive_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="tma2-naive", description="Naive baseline: training-set means."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit")
    f.add_argument("--train", required=True)
    f.add_argument("--out", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--model", required=True)
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--per-timestep", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "fit":
        _, blocks = open_split(a.train)
        model = fit_naive(blocks, file_digest(a.train))
        Path(a.out).write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
        print(
            json.dumps(
                {
                    "out": a.out,
                    "n_final": model["final"]["n"],
                    "n_per_timestep": model["per_timestep"]["n"],
                }
            )
        )
        return 0
    model = json.loads(Path(a.model).read_text())
    mode = "per_timestep" if a.per_timestep else "final"
    _, blocks = open_split(a.inp)

    def preds() -> Iterator[dict[str, Any]]:
        for _, meta, own, _tgt, obs in blocks:
            yield naive_predict(meta, own, obs, model, mode)

    print(json.dumps(_write(a.out, NAIVE, mode, a.inp, preds())))
    return 0


def crb_main(argv: list[str] | None = None) -> int:
    """Per-row Cramér–Rao bounds for every scored row (zig_index + 1 … end) of each scenario."""
    ap = argparse.ArgumentParser(prog="tma2-crb", description="Cramér–Rao bounds at the truth.")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-leg", action="store_true", help="anchor at the last completed manoeuvre")
    a = ap.parse_args(argv)
    _, blocks = open_split(a.inp)
    from tma2.data.canonical import canonical_json
    from tma2.data.io import AtomicFile

    out = AtomicFile(a.out)
    header = {
        "record": "header",
        "kind": "crb",
        "per_leg": a.per_leg,
        "dataset_digest": file_digest(a.inp),
    }
    out.write((canonical_json(header) + "\n").encode())
    n = 0
    try:
        for _, meta, own, tgt, obs in blocks:
            rows = list(range(int(meta["zig_index"]) + 1, int(meta["samples"])))
            bounds = crb_rows(
                own,
                tgt,
                obs,
                float(meta["parameters"]["noise_sigma_rad"]),
                int(meta["zig_index"]),
                meta.get("manoeuvres"),
                rows,
                a.per_leg,
            )
            rec = {
                "record": "crb",
                "scenario_index": int(meta["index"]),
                "first_row": rows[0] if rows else int(meta["samples"]),
                "sd_range_rel": [None if b.singular else b.sd_range_rel for b in bounds],
                "sd_course_deg": [None if b.singular else b.sd_course_deg for b in bounds],
                "sd_speed_kt": [None if b.singular else b.sd_speed_kt for b in bounds],
            }
            out.write((canonical_json(rec) + "\n").encode())
            n += 1
        out.commit()
    except BaseException:
        out.abort()
        raise
    print(json.dumps({"out": a.out, "scenarios": n, "per_leg": a.per_leg}))
    return 0
