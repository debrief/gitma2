"""``tma2-p0``: run every pipeline-gate check and write the experiment record (spec 002 FR-016).

Checks (SRD §5, P0):
1. generator conformance: the spec-001 fixtures regenerate with gitma's digests;
2. reference reproduction: classical, EKF and IMM rows match gitma's prediction fixtures;
3. physics layer with trivial inputs equals batch least squares (converged, determined rows);
4. noise-free recovery: final-mode least squares within 0.1% range on 200 noise-free scenarios;
4a. efficiency: batch least squares' speed efficiency on held-course σ = 1° rows in [0.8, 1.3];
5. oracle ceiling (needs ``--oracle-data``): median range ratios to the frozen IMM on the G5 rows
   inside the research note's intervals, with and without the speed prior;
6. export conformance: a fresh export, its Python leg run here, and the browser and Java legs read
   from ``conformance/onnx/results.json`` only when they name this export's SHA-256; all within
   1e-5 in double (float32 reported); the Java leg may be deferred.
Exit 3 when any gated check fails; ``skipped`` checks are reported but not gated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.data.f32pack import iter_pack_raw, read_pack_header
from tma2.data.io import file_digest
from tma2.eval.errors import Truth
from tma2.eval.experiment import Check, Experiment
from tma2.eval.oracle_check import load_rows, oracle_ratios
from tma2.eval.predictions import check_bound
from tma2.physics.layer import PhysicsLayer
from tma2.physics.reference import ITERATIONS
from tma2.physics.segmentation import trivial_inputs
from tma2.references.classical import bearing_data_from_arrays, classical_predict
from tma2.references.ekf import ekf_predict
from tma2.references.imm import ImmParams, imm_predict
from tma2.sim.ranges import noise_free
from tma2.types import dump_record

from .estimators import open_split
from .oracle import predict_split, run_layer

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "fixtures" / "gitma"
R_MAX = 360  # rows in the longest window (60 min at 10 s)
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


COST_TOL = 1e-9  # relative: equal cost means the same minimum
STATE_TOL = 1e-4  # relative range and speed, on determined rows at the same minimum
SD_TOL = 1e-2  # in the row's own standard deviations, on every row at the same minimum


def check_physics_equals_ls(exp: Experiment) -> None:
    """FR-007 / SC-002 on every scored row of every split of both fixtures: the physics layer
    with trivial inputs against the ported batch least squares from the same grid start at that
    row (``solve_batch``; the per-timestep rows are warm-started, so they can sit in another
    minimum). Where the solver converged, the layer's cost must not exceed the solver's by more
    than 1e-9 relative (it did not stop short), and where the costs agree the states must agree
    to 1e-4; rows where the layer reaches a lower cost than the solver are counted and reported.
    """
    from tma2.references.classical import plausible, solve_batch

    torch.set_default_dtype(torch.float64)
    items = []
    refs = []
    for name in ("phase4-seed777", "iter4-seed777"):
        for split in ("train", "validation", "test", "heldout"):
            for _, meta, own, _tgt, obs in iter_pack_raw(FIXTURES / name / f"{split}.f32pack"):
                bd = bearing_data_from_arrays(meta, own, obs)
                for k in range(bd.zig_index + 1, bd.n):
                    inp = trivial_inputs(bd.t, bd.ox, bd.oy, bd.z, bd.valid, k)
                    sol = solve_batch(bd, k + 1)
                    if inp is None or sol is None:
                        continue
                    th = sol.theta
                    tk = float(bd.t[k])
                    rng = math.hypot(th[0] + th[2] * tk - bd.ox[k], th[1] + th[3] * tk - bd.oy[k])
                    refs.append(
                        (
                            rng,
                            math.hypot(th[2], th[3]),
                            sol.cost,
                            sol.converged,
                            bd.sigma,
                            plausible(bd, sol, k),
                        )
                    )
                    items.append((bd, k, inp))
    layer = PhysicsLayer()
    short = 0  # layer cost above the solver's: it stopped short
    lower = 0  # layer cost below the solver's: the solver stopped short or another minimum
    same = 0
    worst = 0.0
    worst_sd = 0.0
    determined = 0
    unconverged = 0
    flag_mismatch = 0
    cov_bad = 0
    nonfinite_sd = 0
    unconv_plausible = 0
    unconv_lower = 0
    implausible = 0  # both flag the solution implausible (gitma scores it as not converged)
    for a in range(0, len(items), 500):
        out = run_layer(layer, items[a : a + 500], R_MAX)
        for j, (rng, spd, cost, conv, sigma, ok_ls) in enumerate(refs[a : a + 500]):
            if not conv:
                # Reported: the layer's flag and whether it reached a lower cost than the
                # solver's stopping point.
                unconverged += 1
                unconv_plausible += bool(out.plausible[j])
                unconv_lower += float(out.cost[j]) * sigma * sigma < cost * (1 - COST_TOL)
                continue
            if bool(out.plausible[j]) != ok_ls:
                flag_mismatch += 1
            elif not ok_ls:
                implausible += 1
            dc = (float(out.cost[j]) * sigma * sigma - cost) / max(cost, 1e-300)
            if dc > COST_TOL:
                short += 1
            elif dc < -COST_TOL:
                lower += 1
            elif ok_ls and bool(out.plausible[j]):
                same += 1
                rel = max(
                    abs(float(out.range[j]) - rng) / rng,
                    abs(float(out.speed[j]) - spd) / max(spd, 1.0),
                )
                # In units of the row's own standard deviations (layer covariance): at equal
                # cost an undetermined row may move along its flat direction, never across it.
                if not bool(out.cov_ok[j]):
                    cov_bad += 1  # degenerate (on ownship): counted, the sd test cannot apply
                    continue
                cov = out.cov[j].numpy()
                st = out.state[j].numpy()
                bd, k, _ = items[a + j]
                dx, dy = st[0] - bd.ox[k], st[1] - bd.oy[k]
                rr = math.hypot(dx, dy)
                gr = np.array([dx, dy]) / rr
                sd_r = math.sqrt(max(float(gr @ cov[:2, :2] @ gr), 1e-300))
                u = st[2:]
                gs = u / max(float(np.linalg.norm(u)), 1e-12)
                sd_s = math.sqrt(max(float(gs @ cov[2:, 2:] @ gs), 1e-300))
                in_sd = max(
                    abs(float(out.range[j]) - rng) / sd_r, abs(float(out.speed[j]) - spd) / sd_s
                )
                if not math.isfinite(in_sd):
                    nonfinite_sd += 1
                    continue
                worst_sd = max(worst_sd, in_sd)
                if sd_r < 0.5 * rr:
                    determined += 1
                    worst = max(worst, rel)
    exp.metrics["physics-equals-least-squares"] = {
        "rows": len(items),
        "solver_converged_rows": len(items) - unconverged,
        "plausibility_flag_mismatches": flag_mismatch,
        "both_implausible_rows": implausible,
        "same_minimum_plausible_rows": same,
        "layer_cost_higher_rows": short,
        "layer_cost_lower_rows": lower,
        "determined_rows": determined,
        "covariance_degenerate_rows": cov_bad,
        "nonfinite_sd_rows": nonfinite_sd,
        "solver_unconverged_layer_plausible": unconv_plausible,
        "solver_unconverged_layer_cost_lower": unconv_lower,
        "worst_relative_difference_determined": worst,
        "worst_difference_in_sd_same_minimum": worst_sd,
        "iterations": layer.iterations,
        "trials": layer.trials,
    }
    ok = (
        short == 0
        and flag_mismatch == 0
        and nonfinite_sd == 0
        and worst <= STATE_TOL
        and worst_sd <= SD_TOL
        and determined > 0
    )
    exp.checks.append(
        Check(
            "physics-equals-least-squares",
            "pass" if ok else "fail",
            f"{len(items)} rows ({len(items) - unconverged} with the solver converged; "
            f"plausibility flags differ on {flag_mismatch}, both implausible on {implausible}): "
            f"{same} plausible at the same minimum: worst {worst:.1e} relative on the {determined} "
            f"determined rows, {worst_sd:.1e} standard deviations on all ({cov_bad} degenerate "
            f"covariances, {nonfinite_sd} non-finite); layer cost higher on {short}, lower on "
            f"{lower}; on the {unconverged} unconverged solver rows the layer is lower on "
            f"{unconv_lower}",
            value=worst,
            threshold=STATE_TOL,
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
        scenarios = 0
        items = []
        truths = []
        for _, meta, own, tgt, obs in iter_pack_raw(Path(tmp) / "train.f32pack"):
            scenarios += 1
            bd = bearing_data_from_arrays(meta, own, obs)
            row = classical_predict(bd, "final")["rows"][-1]
            i = int(meta["samples"]) - 1
            true_range = math.hypot(tgt[i, 1] - own[i, 1], tgt[i, 2] - own[i, 2])
            worst = max(
                worst,
                abs(row["range_m"] - true_range) / true_range if row["converged"] else math.inf,
            )
            inp = trivial_inputs(bd.t, bd.ox, bd.oy, bd.z, bd.valid, i)
            if inp is None:
                continue
            items.append((bd, i, inp))
            truths.append(true_range)
    out = run_layer(PhysicsLayer(), items, R_MAX)
    worst_layer = max(
        (
            abs(float(out.range[b]) - tr) / tr if bool(out.plausible[b]) else math.inf
            for b, tr in enumerate(truths)
        ),
        default=math.inf,
    )
    if len(items) < scenarios:
        worst_layer = math.inf
    # SRD §5: the physics layer recovers noise-free truth; least squares is reported beside it.
    exp.checks.append(
        Check(
            "noise-free-recovery",
            "pass" if worst_layer < 1e-3 and worst < 1e-3 else "fail",
            f"physics layer (trivial inputs): worst relative range error {worst_layer:.2e} over "
            f"{len(items)} of {scenarios} scenarios; least squares {worst:.2e}",
            value=worst_layer,
            threshold=1e-3,
        )
    )


EFFICIENCY_BAND = (0.8, 1.3)


def check_efficiency(exp: Experiment) -> None:
    """Spec 002 SC-005: batch least squares is at the bound on held-course rows.

    2,000 constant-velocity scenarios (gitma iteration-4 ranges, seed 43; no target manoeuvre,
    so every row is on a held leg), the 1,600-scenario train split, σ = 1° only, rows at
    zig + 300 s and zig + 600 s pooled, full-window bound at truth. Gated on speed (the spec's
    criterion); range and course are reported in the metrics.
    """
    from tma2.eval.errors import row_error
    from tma2.eval.metrics import efficiency
    from tma2.references.crb import crb_rows

    d = FIXTURES / "iter4-seed777"
    ranges = json.loads((d / "ranges.json").read_text())
    heldout = json.loads((d / "heldout-ranges.json").read_text())
    pairs: dict[str, list[tuple[float, float]]] = {"range": [], "course": [], "speed": []}
    scenarios = 0
    with tempfile.TemporaryDirectory() as tmp:
        generate_dataset(
            GenerateOptions(
                seed=np.uint64(43),
                count=2000,
                out_dir=Path(tmp),
                ranges=ranges,
                heldout_ranges=heldout,
                format="f32pack",
                created_by="p0",
                generator_git_commit="p0",
                generator_git_dirty=True,
            )
        )
        for _, meta, own, tgt, obs in iter_pack_raw(Path(tmp) / "train.f32pack"):
            sigma = float(meta["parameters"]["noise_sigma_rad"])
            if abs(sigma - math.radians(1.0)) > 1e-6:
                continue
            scenarios += 1
            bd = bearing_data_from_arrays(meta, own, obs)
            rows = classical_predict(bd, "per_timestep")["rows"]
            truth = Truth.from_block(meta, own, tgt)
            zig = int(meta["zig_index"])
            for sec in (300, 600):
                k = zig + sec // int(meta["parameters"]["dt_s"])
                if k >= int(meta["samples"]):
                    continue
                row = next((r for r in rows if abs(r["timestamp_s"] - own[k, 0]) < 1e-6), None)
                if row is None:
                    continue
                bound = crb_rows(own, tgt, obs, sigma, zig, None, [k], False)[0]
                if bound.singular:
                    continue
                e = row_error(truth, row)
                pairs["range"].append((e.range_rel, bound.sd_range_rel))
                pairs["course"].append((e.course_deg, bound.sd_course_deg))
                pairs["speed"].append((e.speed_kt, bound.sd_speed_kt))
    eff = {k: efficiency(v) for k, v in pairs.items()}
    exp.metrics["least-squares-efficiency"] = {
        **{f"efficiency_{k}": v for k, v in eff.items()},
        "rows": len(pairs["speed"]),
        "scenarios": scenarios,
    }
    lo, hi = EFFICIENCY_BAND
    exp.checks.append(
        Check(
            "least-squares-efficiency-speed",
            "pass" if lo <= eff["speed"] <= hi else "fail",
            f"speed efficiency {eff['speed']:.3f} over {len(pairs['speed'])} held-course rows "
            f"(range {eff['range']:.3f}, course {eff['course']:.3f}); band [{lo}, {hi}]",
            value=eff["speed"],
            threshold=hi,
            threshold_low=lo,
        )
    )


def check_oracle(exp: Experiment, data_dir: Path, out_dir: Path) -> Path:
    truth = data_dir / "validation.f32pack"
    header = read_pack_header(truth)
    exp.add_dataset(truth, dump_record(header))
    from tma2.cli.oracle import ORACLE
    from tma2.eval.predictions import PredictionWriter
    from tma2.references.imm import imm_name

    # Prediction caches live under the code commit and are reused only from a clean tree, after
    # checking that their header names this truth file and the expected estimator; every file
    # used is recorded in the manifest with its digest.
    commit, dirty = exp.git()
    cache = out_dir / commit[:12]
    cache.mkdir(parents=True, exist_ok=True)

    def usable(path: Path, estimator: str) -> bool:
        if dirty or not path.exists():
            return False
        header = check_bound(path, truth)
        if header.estimator != estimator:
            raise ValueError(f"{path}: estimator {header.estimator}, expected {estimator}")
        return True

    imm_path = cache / "imm.ndjson"
    if not usable(imm_path, imm_name(FROZEN_IMM)):
        w = PredictionWriter(imm_path, imm_name(FROZEN_IMM), "per_timestep", truth)
        for _, meta, own, _tgt, obs in iter_pack_raw(truth):
            w.write(imm_predict(bearing_data_from_arrays(meta, own, obs), FROZEN_IMM))
        w.close()
    exp.add_artefact(imm_path, "IMM predictions (oracle denominator)")
    _, blocks = open_split(truth)
    truths = [Truth.from_block(meta, own, tgt) for _, meta, own, tgt, _ in blocks]
    # masked-sp is a diagnostic (panel round 1): bearings inside each manoeuvre are given zero
    # weight, measuring how much of the oracle's error is the chord approximation. Reported only.
    for variant, speed_prior, masked in (
        ("sp", True, False),
        ("nosp", False, False),
        ("masked-sp", True, True),
    ):
        pred = cache / f"oracle-{variant}.ndjson"
        name = ORACLE + ("-sp" if speed_prior else "") + ("-masked" if masked else "")
        if not usable(pred, name):
            predict_split(
                str(truth), str(pred), speed_prior, False, ITERATIONS, 8, mask_turns=masked
            )
        exp.add_artefact(pred, f"oracle predictions ({variant})")
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
                        threshold_low=lo,
                        ci_low=c.interval.lo,
                        ci_high=c.interval.hi,
                        ci_level=0.975,
                    )
                )
    return imm_path


AT_SCALE_ROW_LIMIT = 1e-3  # fraction of converged rows allowed beyond 1e-4 relative


def check_imm_at_scale(exp: Experiment, data_dir: Path, gitma_imm: Path, ours: Path) -> None:
    """Our IMM against gitma's own ``tma-track`` output on the 10,000-scenario split.

    The 20-scenario fixtures cannot show rare knife-edge rows; here flags must be identical, at
    most 0.1% of converged rows may differ by more than 1e-4 relative, and the G5 median range
    error ratio must be 1 to 1e-4 (the gates compare medians). Panel round 1 traced the residual
    rows to scenarios where a 1e-15–1e-12 bearing jitter moves our own IMM as far.
    """
    truth = data_dir / "validation.f32pack"
    exp.add_artefact(gitma_imm, "gitma tma-track IMM predictions (seed 301 validation)")
    theirs = load_rows(str(gitma_imm))
    mine = load_rows(str(ours))
    flags = 0
    rows = 0
    beyond = 0
    worst = 0.0
    for idx, by_t in theirs.items():
        m = mine.get(idx, {})
        for ts, r in by_t.items():
            q = m.get(float(ts))
            if q is None or q["converged"] != r["converged"]:
                flags += 1
                continue
            if not r["converged"]:
                continue
            rows += 1
            e = max(
                abs(q[k] - r[k]) / max(abs(r[k]), 1.0)
                for k in ("range_m", "speed_mps", "x_m", "y_m")
            )
            worst = max(worst, e)
            beyond += e > 1e-4
    _, blocks = open_split(truth)
    truths = [Truth.from_block(meta, own, tgt) for _, meta, own, tgt, _ in blocks]
    ratio = next(
        c for c in oracle_ratios(truths, str(gitma_imm), str(ours)) if c.name == "all-range"
    )
    frac = beyond / max(rows, 1)
    ok = flags == 0 and frac <= AT_SCALE_ROW_LIMIT and abs(ratio.interval.ratio - 1) <= 1e-4
    exp.metrics["reference-imm-at-scale"] = {
        "rows": rows,
        "flag_mismatches": flags,
        "rows_beyond_1e-4": beyond,
        "worst_relative_difference": worst,
        "g5_median_range_ratio_gitma_over_ours": ratio.interval.ratio,
    }
    exp.checks.append(
        Check(
            "reference-imm-at-scale",
            "pass" if ok else "fail",
            f"{rows} rows, {flags} flag mismatches, {beyond} rows beyond 1e-4 "
            f"({frac:.2e}; worst {worst:.1e}); G5 median range ratio {ratio.interval.ratio:.6f}",
            value=frac,
            threshold=AT_SCALE_ROW_LIMIT,
        )
    )


def check_export(exp: Experiment) -> None:
    """Export the toy model afresh (byte-deterministic), run the Python leg here, and accept the
    browser and Java legs from ``conformance/onnx/results.json`` only if they name this export's
    SHA-256. A missing results file or browser leg fails the gate; the Java leg may be deferred
    (spec 002) and is then skipped, never passed."""
    from tma2.export.onnx_export import export

    fixture = FIXTURES / "phase4-seed777" / "test.f32pack"
    with tempfile.TemporaryDirectory() as tmp:
        d64 = export(Path(tmp) / "f64", fixture, dtype="float64")
        d32 = export(Path(tmp) / "f32", fixture, dtype="float32")
        sha = hashlib.sha256((Path(tmp) / "f64" / "toy.onnx").read_bytes()).hexdigest()
        ops = (Path(tmp) / "f64" / "ops.txt").read_text().split()
    exp.metrics["export"] = {
        "onnx_sha256": sha,
        "ops": ops,
        "python_f64_max_rel_diff": d64,
        "python_f32_max_rel_diff_reported_only": d32,
    }
    worst = max(d64.values())
    exp.checks.append(
        Check(
            "export-python",
            "pass" if worst <= 1e-5 else "fail",
            f"max relative difference {worst:.1e} (double; float32 reported: "
            f"{max(d32.values()):.1e})",
            value=worst,
            threshold=1e-5,
        )
    )
    res = ROOT / "conformance" / "onnx" / "results.json"
    if not res.exists():
        exp.checks.append(
            Check("export-wasm", "fail", "conformance/onnx/results.json missing (run the legs)")
        )
        return
    exp.add_artefact(res, "export conformance results (browser and Java legs)")
    r = json.loads(res.read_text())
    for leg in ("wasm", "java"):
        v = r.get(leg)
        if leg == "java" and (v is None or v.get("deferred")):
            reason = v.get("reason") if v else "not run"
            exp.checks.append(Check("export-java", "skipped", f"deferred: {reason}"))
            continue
        if v is None:
            exp.checks.append(Check(f"export-{leg}", "fail", "leg missing from results.json"))
            continue
        if v.get("onnx_sha256") != sha:
            exp.checks.append(
                Check(
                    f"export-{leg}",
                    "fail",
                    f"leg ran on {v.get('onnx_sha256')}, not this export ({sha})",
                )
            )
            continue
        worst = max(v["max_rel_diff"].values())
        exp.metrics["export"][f"{leg}_runtime"] = v.get("runtime")
        exp.checks.append(
            Check(
                f"export-{leg}",
                "pass" if worst <= 1e-5 else "fail",
                f"max relative difference {worst:.1e} (double, {v.get('runtime')})",
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
    ap.add_argument(
        "--gitma-imm",
        help="gitma tma-track IMM predictions on the same validation split (at-scale check)",
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
    check_efficiency(exp)
    if a.oracle_data:
        imm_path = check_oracle(exp, Path(a.oracle_data), Path(a.work))
        if a.gitma_imm:
            check_imm_at_scale(exp, Path(a.oracle_data), Path(a.gitma_imm), imm_path)
    else:
        exp.checks.append(Check("oracle-ceiling", "skipped", "no --oracle-data"))
    check_export(exp)
    verdict = exp.write("P0")
    for c in exp.checks:
        print(f"{c.result:12s} {c.name:40s} {c.detail}")
    print(json.dumps({"experiment": str(folder), "result": verdict["result"]}))
    return 0 if verdict["result"] == "pass" else 3
