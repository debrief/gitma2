"""``tma2-p0``: run every pipeline-gate check and write the experiment record (spec 002 FR-016).

Checks (SRD §5, P0):
1. generator conformance: the spec-001 fixtures regenerate with gitma's digests;
2. reference reproduction: classical, EKF and IMM rows match gitma's prediction fixtures;
3. physics layer with trivial inputs equals batch least squares (converged, determined rows);
4. noise-free recovery: final-mode least squares within 0.1% range on 200 noise-free scenarios;
5. oracle ceiling (needs ``--oracle-data``): median range ratios to the frozen IMM on the G5 rows
   inside the research note's intervals, with and without the speed prior;
6. export conformance (reads ``conformance/onnx/results.json`` when present): Python and WASM
   legs within 1e-5 in double; the Java leg recorded, deferred or not.
Exit 3 when any gated check fails; ``skipped`` checks are reported but not gated.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.data.f32pack import iter_pack_raw, read_pack_header
from tma2.data.io import file_digest
from tma2.eval.errors import Truth
from tma2.eval.experiment import Check, Experiment
from tma2.eval.oracle_check import oracle_ratios
from tma2.references.classical import bearing_data_from_arrays, classical_predict
from tma2.references.ekf import ekf_predict
from tma2.references.imm import ImmParams, imm_predict
from tma2.sim.ranges import noise_free
from tma2.types import dump_record

from .estimators import open_split
from .oracle import predict_split

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "fixtures" / "gitma"
FROZEN_IMM = ImmParams(0.01, 0.03, 0.01, 0.001, 4.0, 8.0)
# docs/research/05: 97.5% intervals of the oracle / IMM median range ratio
# (seed 777, 2,400 scenarios)
NOTE_INTERVALS = {
    ("sp", "all-range"): (0.486, 0.574),
    ("sp", "settled-range"): (0.450, 0.557),
    ("nosp", "all-range"): (0.595, 0.687),
    ("nosp", "settled-range"): (0.508, 0.628),
}


def check_generator(exp: Experiment) -> None:
    for name in ("iter1-seed1", "iter4-seed777", "phase4-seed777"):
        d = FIXTURES / name
        with open(d / "test.ndjson", encoding="utf-8") as f:
            hdr = json.loads(f.readline())
        heldout = json.loads((d / "heldout-ranges.json").read_text())
        count = hdr["index_end"]
        with tempfile.TemporaryDirectory() as tmp:
            generate_dataset(
                GenerateOptions(
                    seed=np.uint64(int(hdr["dataset_seed"])),
                    count=count,
                    out_dir=Path(tmp),
                    ranges=hdr["parameter_ranges"],
                    heldout_ranges=heldout,
                    format="both",
                    created_by=hdr["created_by"],
                    generator_git_commit=hdr["generator_git_commit"],
                    generator_git_dirty=hdr["generator_git_dirty"],
                    schema_version=hdr["schema_version"],
                )
            )
            expected = json.loads((d / "digests.json").read_text())
            bad = [k for k, v in expected.items() if file_digest(Path(tmp) / k) != v]
        exp.checks.append(
            Check(
                f"generator-{name}",
                "pass" if not bad else "fail",
                f"{len(expected)} files byte-identical to gitma's" if not bad else f"differ: {bad}",
                value=float(len(expected) - len(bad)),
                threshold=float(len(expected)),
            )
        )


def _rows_equal(
    mine: dict[str, Any], theirs: dict[str, Any], tol: float = 1e-4
) -> tuple[bool, float]:
    if len(mine["rows"]) != len(theirs["rows"]):
        return False, math.inf
    worst = 0.0
    for a, b in zip(mine["rows"], theirs["rows"], strict=True):
        if a["converged"] != b["converged"]:
            return False, math.inf
        if not a["converged"]:
            continue
        for k in ("range_m", "speed_mps", "x_m", "y_m"):
            worst = max(worst, abs(a[k] - b[k]) / max(abs(b[k]), 1.0))
        worst = max(
            worst,
            abs(
                math.atan2(
                    math.sin(a["course_rad"] - b["course_rad"]),
                    math.cos(a["course_rad"] - b["course_rad"]),
                )
            ),
        )
    return worst <= tol, worst


def check_references(exp: Experiment) -> None:
    for name in ("iter4-seed777", "phase4-seed777"):
        d = FIXTURES / name
        for est in ("lsq", "ekf", "imm"):
            theirs: dict[int, dict[str, Any]] = {}
            with open(d / "predictions" / f"test-{est}.ndjson", encoding="utf-8") as f:
                f.readline()
                for line in f:
                    p = json.loads(line)
                    theirs[p["scenario_index"]] = p
            worst = 0.0
            ok = True
            for _, meta, own, _tgt, obs in iter_pack_raw(d / "test.f32pack"):
                bd = bearing_data_from_arrays(meta, own, obs)
                mine = (
                    classical_predict(bd, "per_timestep")
                    if est == "lsq"
                    else ekf_predict(bd, 0.03, 4.0, 8.0)
                    if est == "ekf"
                    else imm_predict(bd, FROZEN_IMM)
                )
                eq, w = _rows_equal(mine, theirs[meta["index"]])
                ok = ok and eq
                worst = max(worst, w)
            exp.checks.append(
                Check(
                    f"reference-{name}-{est}",
                    "pass" if ok else "fail",
                    f"flags identical; worst relative difference {worst:.1e}",
                    value=worst,
                    threshold=1e-4,
                )
            )


def check_physics_equals_ls(exp: Experiment) -> None:
    import torch

    from tma2.cli.oracle import run_layer
    from tma2.physics.layer import PhysicsLayer
    from tma2.physics.segmentation import trivial_inputs

    torch.set_default_dtype(torch.float64)
    d = FIXTURES / "phase4-seed777"
    items = []
    rows = []
    for _, meta, own, _tgt, obs in iter_pack_raw(d / "test.f32pack"):
        bd = bearing_data_from_arrays(meta, own, obs)
        pred = classical_predict(bd, "per_timestep")
        for row in pred["rows"][5::20]:
            if not row["converged"]:
                continue
            k = int(round(row["timestamp_s"] / 10))
            inp = trivial_inputs(bd.t, bd.ox, bd.oy, bd.z, bd.valid, k)
            if inp is not None:
                items.append((bd, k, inp))
                rows.append(row)
    out = run_layer(PhysicsLayer(iterations=40, knots=8), items, 360)
    worst = 0.0
    n = 0
    for b, row in enumerate(rows):
        cov = out.cov[b].numpy()
        sd_range = math.sqrt(max(cov[0, 0] + cov[1, 1], 0.0))
        if not bool(out.plausible[b]) or sd_range >= 0.5 * float(out.range[b]):
            continue
        n += 1
        worst = max(
            worst,
            abs(float(out.range[b]) - row["range_m"]) / row["range_m"],
            abs(float(out.speed[b]) - row["speed_mps"]) / max(row["speed_mps"], 1.0),
        )
    exp.checks.append(
        Check(
            "physics-equals-least-squares",
            "pass" if worst <= 1e-4 and n > 50 else "fail",
            f"{n} determined rows; worst relative difference {worst:.1e}",
            value=worst,
            threshold=1e-4,
        )
    )


def check_noise_free(exp: Experiment) -> None:
    d = FIXTURES / "iter4-seed777"
    ranges = json.loads((d / "ranges.json").read_text())
    heldout = json.loads((d / "heldout-ranges.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        generate_dataset(
            GenerateOptions(
                seed=np.uint64(42),
                count=200,
                out_dir=Path(tmp),
                ranges=noise_free(ranges),
                heldout_ranges=noise_free(heldout),
                format="f32pack",
                created_by="p0",
                generator_git_commit="p0",
                generator_git_dirty=True,
            )
        )
        worst = 0.0
        for _, meta, own, tgt, obs in iter_pack_raw(Path(tmp) / "train.f32pack"):
            bd = bearing_data_from_arrays(meta, own, obs)
            row = classical_predict(bd, "final")["rows"][-1]
            i = int(meta["samples"]) - 1
            true_range = math.hypot(tgt[i, 1] - own[i, 1], tgt[i, 2] - own[i, 2])
            worst = max(
                worst,
                abs(row["range_m"] - true_range) / true_range if row["converged"] else math.inf,
            )
    exp.checks.append(
        Check(
            "noise-free-recovery",
            "pass" if worst < 1e-3 else "fail",
            f"worst relative range error {worst:.2e} over 160 scenarios",
            value=worst,
            threshold=1e-3,
        )
    )


def check_oracle(exp: Experiment, data_dir: Path, out_dir: Path) -> None:
    truth = data_dir / "validation.f32pack"
    header = read_pack_header(truth)
    exp.add_dataset(truth, dump_record(header))
    out_dir.mkdir(parents=True, exist_ok=True)
    imm_path = out_dir / "imm.ndjson"
    if not imm_path.exists():
        from tma2.eval.predictions import PredictionWriter
        from tma2.references.imm import imm_name

        w = PredictionWriter(imm_path, imm_name(FROZEN_IMM), "per_timestep", truth)
        for _, meta, own, _tgt, obs in iter_pack_raw(truth):
            w.write(imm_predict(bearing_data_from_arrays(meta, own, obs), FROZEN_IMM))
        w.close()
    _, blocks = open_split(truth)
    truths = [Truth.from_block(meta, own, tgt) for _, meta, own, tgt, _ in blocks]
    for variant, speed_prior in (("sp", True), ("nosp", False)):
        pred = out_dir / f"oracle-{variant}.ndjson"
        if not pred.exists():
            predict_split(str(truth), str(pred), speed_prior, False, 40, 8)
        for c in oracle_ratios(truths, str(pred), str(imm_path)):
            key = (variant, c.name)
            exp.metrics[f"oracle-{variant}-{c.name}"] = {
                "ratio": c.interval.ratio,
                "lo": c.interval.lo,
                "hi": c.interval.hi,
                "rows": c.rows,
            }
            if key in NOTE_INTERVALS:
                lo, hi = NOTE_INTERVALS[key]
                inside = lo <= c.interval.ratio <= hi
                exp.checks.append(
                    Check(
                        f"oracle-{variant}-{c.name}",
                        "pass" if inside else "fail",
                        f"median ratio {c.interval.ratio:.3f} "
                        f"[{c.interval.lo:.3f}, {c.interval.hi:.3f}] vs note [{lo}, {hi}]",
                        value=c.interval.ratio,
                        threshold=hi,
                        ci_low=c.interval.lo,
                        ci_high=c.interval.hi,
                        ci_level=0.975,
                    )
                )


def check_export(exp: Experiment) -> None:
    res = ROOT / "conformance" / "onnx" / "results.json"
    if not res.exists():
        exp.checks.append(
            Check(
                "export-conformance",
                "skipped",
                "conformance/onnx/results.json not present (run the harness)",
            )
        )
        return
    r = json.loads(res.read_text())
    for leg in ("python", "wasm"):
        v = r.get(leg)
        if v is None:
            exp.checks.append(Check(f"export-{leg}", "fail", "missing"))
            continue
        worst = max(v["max_rel_diff"].values())
        exp.checks.append(
            Check(
                f"export-{leg}",
                "pass" if worst <= 1e-5 else "fail",
                f"max relative difference {worst:.1e} (double)",
                value=worst,
                threshold=1e-5,
            )
        )
    j = r.get("java")
    if j is None or j.get("deferred"):
        exp.checks.append(
            Check("export-java", "skipped", f"deferred: {j.get('reason') if j else 'not run'}")
        )
    else:
        worst = max(j["max_rel_diff"].values())
        exp.checks.append(
            Check(
                "export-java",
                "pass" if worst <= 1e-5 else "fail",
                f"max relative difference {worst:.1e}",
                value=worst,
                threshold=1e-5,
            )
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-p0")
    ap.add_argument("--experiment", required=True)
    ap.add_argument(
        "--oracle-data", help="directory with validation.f32pack (seed 301, phase-4 ranges)"
    )
    ap.add_argument(
        "--work", help="where oracle/IMM predictions are cached", default="data/p0-work"
    )
    a = ap.parse_args(argv)
    folder = Path(a.experiment)
    exp = Experiment(id=folder.name, folder=folder)
    exp.command_lines.append("tma2-p0 " + " ".join(sys.argv[1:]))
    exp.add_estimator("classical", {"max_iterations": 50, "grid_every": 6})
    exp.add_estimator("imm-cv0.01-ct0.03-w0.01-s0.001-p4-r8", FROZEN_IMM.__dict__)
    exp.add_estimator(
        "oracle-physics", {"iterations": 40, "knots": 8, "tau_ridge_mps": 3.0, "tau_speed_mps": 1.0}
    )
    check_generator(exp)
    check_references(exp)
    check_physics_equals_ls(exp)
    check_noise_free(exp)
    if a.oracle_data:
        check_oracle(exp, Path(a.oracle_data), Path(a.work))
    else:
        exp.checks.append(Check("oracle-ceiling", "skipped", "no --oracle-data"))
    check_export(exp)
    verdict = exp.write("P0")
    for c in exp.checks:
        print(f"{c.result:12s} {c.name:40s} {c.detail}")
    print(json.dumps({"experiment": str(folder), "result": verdict["result"]}))
    return 0 if verdict["result"] == "pass" else 3
