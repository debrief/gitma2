"""``tma2-g0-man2``: the pipeline gate on generator 0.6.0 (spec 006 FR-051, SC-001 to SC-005).

The checks and thresholds were fixed before the first run in
``specs/006-generator-man2/g0-checks.md``; this CLI implements that table and nothing else:

1. ``generator-conformance``: gitma's fixtures regenerate with gitma's digests (P0's check);
2. ``regen-0.5.0``: every scenario of seed 304's validation split regenerates identically;
3. the MAN2 distributions on seed 314's validation split: ``man2-transitions``,
   ``man2-changes``, ``man2-kinds``, ``man2-wander-band``, ``man2-wander-kinds``;
4. ``noise-free-zig-leg``: on seed 316's noise-free validation split, the steady target leg
   containing the zig, fitted alone by batch least squares and by the physics layer;
5. ``physics-equals-ls-720``: P0's layer check on 200 σ = 1° MAN2 scenarios, 720-row windows;
6. ``export-720``: the toy export at 720 rows in Python, browser (WASM) and Java, in double;
7. ``throughput``: at least 10,000 MAN2 scenarios per second from the kernel.

Exit 3 when any gated check fails; ``skipped`` checks are reported but not gated.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import math
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.data.f32pack import (
    _read_header,
    block_to_scenario,
    encode_block,
    iter_pack_raw,
    read_pack_header,
)
from tma2.eval.experiment import Check, Experiment
from tma2.eval.rows import G5_SLICE_SIGMA_RAD, zig_leg
from tma2.physics.layer import PhysicsLayer
from tma2.physics.reference import ITERATIONS, TRIALS
from tma2.physics.segmentation import trivial_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays, classical_predict
from tma2.sim.generate import KernelBuffers, generate_scenario, run_kernel
from tma2.sim.ranges import flatten_ranges, rows_for
from tma2.types import dump_record
from tma2.types.generated.tma import Scenario

from .oracle import run_layer
from .p0 import check_generator, check_physics_equals_ls

ROOT = Path(__file__).resolve().parents[3]
MAN2_RANGES = ROOT / "configs" / "man2-ranges.json"
R_MAN2 = 720  # rows in a 120-minute window at 10 s

TRANSITION_BAND_S = (60.0, 180.0)
TWO_OR_MORE_MIN = 0.60
KIND_SHARES = {"course": 0.8, "speed": 0.1, "both": 0.1}
WANDER_SHARES = {"none": 0.4, "wander": 0.3, "oscillation": 0.3}
SHARE_TOL = 0.02
WANDER_BAND_RAD = math.radians(5.0)
ZIG_LEG_TOL = 1e-3
# Owner amendment, 4 November 2026, after the first result (41.7% skipped against the
# pre-registered ≤ 20%, a property of the leg model): at least 500 of the scenarios fitted.
ZIG_LEG_FITTED_MIN = 500
LAYER_SCENARIOS = 200
LAYER_EVERY = 10
EXPORT_TOL = 1e-5
THROUGHPUT_MIN = 10_000.0


def _kind(x: Any) -> str:
    return str(getattr(x, "value", x))


def check_regen_050(exp: Experiment, split: Path) -> None:
    """Spec 006 SC-001: every scenario of a 0.5.0 split regenerates identically under 0.6.0,
    compared block by block (metadata and arrays as the pack stores them)."""
    hdr, _n, _ = _read_header(str(split))
    ranges = hdr.parameter_ranges.model_dump(mode="json", exclude_none=True)
    seed = int(hdr.dataset_seed)
    n = same = 0
    first_bad: int | None = None
    for _, meta, own, tgt, obs in iter_pack_raw(split):
        mine = encode_block(generate_scenario(seed, int(meta["index"]), ranges).scenario)
        theirs = encode_block(Scenario.model_validate(block_to_scenario(meta, own, tgt, obs)))
        n += 1
        if mine == theirs:
            same += 1
        elif first_bad is None:
            first_bad = int(meta["index"])
    exp.metrics["regen_050"] = {
        "split": str(split),
        "generator_in_file": hdr.generator_version,
        "dataset_seed": seed,
        "scenarios": n,
        "identical": same,
        "first_difference": first_bad,
    }
    exp.checks.append(
        Check(
            "regen-0.5.0",
            "pass" if n > 0 and same == n else "fail",
            f"{same} of {n} scenarios of seed {seed} (generator {hdr.generator_version}) "
            "regenerate identically under 0.6.0"
            + ("" if first_bad is None else f"; first difference at index {first_bad}"),
            value=float(same),
            threshold=float(n),
        )
    )


def _planned_courses(m: dict[str, Any], own_c: np.ndarray) -> list[tuple[int, int, float]]:
    """Straight planned ownship segments as (first, last, course), rows inclusive, excluding each
    planned turn and the row on either side of it. A turn row and the row before a turn carry the
    planned course exactly (``apply_wander``), so each segment's course is read from the row that
    ends the previous turn (the zig rows) or, for the first, the row before the first turn."""
    n = int(m["samples"])
    turns = [(int(m["turn_start_index"]), int(m["zig_index"]))]
    if m.get("turn2_start_index") is not None:
        turns.append((int(m["turn2_start_index"]), int(m["zig2_index"])))
    segs: list[tuple[int, int, float]] = []
    start, course = 0, float(own_c[turns[0][0] - 1])
    for a, b in turns:
        segs.append((start + (1 if start else 0), a - 2, course))
        start, course = b, float(own_c[b])
    segs.append((start + 1, n - 1, course))
    return [s for s in segs if s[1] >= s[0]]


def check_distributions(exp: Experiment, split: Path) -> None:
    """Checks 3a–3e on the MAN2 validation split, plus the reported leg and zig statistics."""
    trans: list[float] = []
    cut = 0
    changes: list[int] = []
    kinds: collections.Counter[str] = collections.Counter()
    wander: collections.Counter[str] = collections.Counter()
    legs_min: list[float] = []
    zom = 0
    worst_band = 0.0
    worst_where: tuple[int, int] | None = None
    band_rows = 0
    course0_mismatch = 0
    n = 0
    for _, m, own, _tgt, _obs in iter_pack_raw(split):
        n += 1
        p = m["parameters"]
        dt = float(p["dt_s"])
        end_s = (int(m["samples"]) - 1) * dt
        spans = m.get("manoeuvres") or []
        changes.append(len(spans))
        for tm in p.get("target_manoeuvres") or []:
            kinds[_kind(tm["kind"])] += 1
            dur = abs(float(tm["change"])) / float(tm["rate"])
            if tm.get("change2") is not None and tm.get("rate2"):
                dur = max(dur, abs(float(tm["change2"])) / float(tm["rate2"]))
            if float(tm["start_time_s"]) + dur > end_s:
                cut += 1  # cut off by the window's end: not seen whole
            else:
                trans.append(dur)
        for a, b in itertools.pairwise(spans):
            legs_min.append((int(b["start_index"]) - 1 - int(a["end_index"])) * dt / 60.0)
        w = m.get("ownship_wander")
        wander[_kind(w["kind"]) if w is not None else "absent"] += 1
        zom += bool(m.get("zig_on_manoeuvre"))
        own_c = own[:, 3].astype(np.float64)
        if (
            abs(float(own_c[int(m["turn_start_index"]) - 1]) - float(p["ownship_course0_rad"]))
            > 1e-6
        ):
            course0_mismatch += 1
        for first, last, course in _planned_courses(m, own_c):
            d = np.abs(np.angle(np.exp(1j * (own_c[first : last + 1] - course))))
            band_rows += int(d.size)
            if d.size and float(d.max()) > worst_band:
                worst_band = float(d.max())
                worst_where = (int(m["index"]), first + int(np.argmax(d)))
    med = float(np.median(trans)) if trans else math.nan
    exp.checks.append(
        Check(
            "man2-transitions",
            "pass" if TRANSITION_BAND_S[0] <= med <= TRANSITION_BAND_S[1] else "fail",
            f"median planned duration {med:.0f} s over {len(trans)} changes seen whole "
            f"({cut} cut off by the window's end, left out); band {TRANSITION_BAND_S}",
            value=med,
        )
    )
    two = float(np.mean(np.asarray(changes) >= 2)) if changes else math.nan
    exp.checks.append(
        Check(
            "man2-changes",
            "pass" if two >= TWO_OR_MORE_MIN else "fail",
            f"{two:.3f} of {n} engagements have two or more target changes in the window",
            value=two,
            threshold=TWO_OR_MORE_MIN,
        )
    )
    total = sum(kinds.values())
    shares = {k: kinds[k] / total for k in KIND_SHARES} if total else {}
    dev = max((abs(shares[k] - v) for k, v in KIND_SHARES.items()), default=math.inf)
    exp.checks.append(
        Check(
            "man2-kinds",
            "pass" if dev <= SHARE_TOL and set(kinds) <= set(KIND_SHARES) else "fail",
            "planned change kinds "
            + ", ".join(f"{k} {shares.get(k, 0):.3f}" for k in KIND_SHARES)
            + f" over {total}; largest deviation {dev:.3f}",
            value=dev,
            threshold=SHARE_TOL,
        )
    )
    exp.checks.append(
        Check(
            "man2-wander-band",
            "pass" if worst_band <= WANDER_BAND_RAD and course0_mismatch == 0 else "fail",
            f"worst recorded course off the planned leg course {math.degrees(worst_band):.2f}° "
            f"over {band_rows} straight rows (at index, row {worst_where}); "
            f"{course0_mismatch} scenarios whose row before the turn is not the planned course0",
            value=math.degrees(worst_band),
            threshold=5.0,
        )
    )
    wshares = {k: wander[k] / n for k in WANDER_SHARES} if n else {}
    wdev = max((abs(wshares[k] - v) for k, v in WANDER_SHARES.items()), default=math.inf)
    exp.checks.append(
        Check(
            "man2-wander-kinds",
            "pass" if wdev <= SHARE_TOL and set(wander) <= set(WANDER_SHARES) else "fail",
            "ownship wander "
            + ", ".join(f"{k} {wshares.get(k, 0):.3f}" for k in WANDER_SHARES)
            + f" over {n}; largest deviation {wdev:.3f}"
            + ("" if set(wander) <= set(WANDER_SHARES) else f"; unexpected {dict(wander)}"),
            value=wdev,
            threshold=SHARE_TOL,
        )
    )
    q = np.quantile(legs_min, [0.05, 0.5, 0.95]) if legs_min else [math.nan] * 3
    counts = np.bincount(np.asarray(changes, dtype=np.int64))
    exp.metrics["man2_distributions"] = {
        "split": str(split),
        "scenarios": n,
        "transition_s_p10_p50_p90": [float(x) for x in np.quantile(trans, [0.1, 0.5, 0.9])],
        "transitions_cut_off": cut,
        "changes_per_engagement": {str(k): int(c) for k, c in enumerate(counts)},
        "two_or_more": two,
        "kind_counts": dict(kinds),
        "wander_counts": dict(wander),
        "wander_worst_deg": math.degrees(worst_band),
        "complete_legs": len(legs_min),
        "complete_leg_min_p5_p50_p95": [float(x) for x in q],
        "complete_leg_share_le_10_min": float(np.mean(np.asarray(legs_min) <= 10.0)),
        "zig_on_manoeuvre": zom,
    }


def _leg_data(
    meta: dict[str, Any], own: np.ndarray, obs: np.ndarray, first: int, last: int
) -> BearingData:
    """The leg's rows alone, with time re-based to its first row."""
    full = bearing_data_from_arrays(meta, own, obs)
    s = slice(first, last + 1)
    return BearingData(
        t=full.t[s] - full.t[first],
        ox=full.ox[s],
        oy=full.oy[s],
        z=full.z[s],
        valid=full.valid[s],
        zig_index=full.zig_index - first,
        sigma=full.sigma,
        index=full.index,
    )


def check_noise_free_zig_leg(exp: Experiment, split: Path) -> None:
    """Check 4 (research R3): the steady target leg containing the zig, fitted alone, recovers
    noise-free truth at its last row by batch least squares (final mode) and by the physics
    layer with trivial inputs."""
    n = 0
    skipped = 0
    worst_ls = 0.0
    worst_ls_at = -1
    items: list[tuple[BearingData, int, Any]] = []
    truths: list[float] = []
    no_start = 0
    for _, meta, own, tgt, obs in iter_pack_raw(split):
        n += 1
        if float(meta["parameters"]["noise_sigma_rad"]) != 0.0:
            raise SystemExit(f"{split}: scenario {meta['index']} is not noise-free")
        leg = zig_leg(meta)
        if leg is None:
            skipped += 1
            continue
        first, last = leg
        bd = _leg_data(meta, own, obs, first, last)
        tr = math.hypot(float(tgt[last, 1] - own[last, 1]), float(tgt[last, 2] - own[last, 2]))
        row = classical_predict(bd, "final")["rows"][-1]
        e = abs(row["range_m"] - tr) / tr if row["converged"] else math.inf
        if e > worst_ls:
            worst_ls, worst_ls_at = e, int(meta["index"])
        k = bd.n - 1
        inp = trivial_inputs(bd.t, bd.ox, bd.oy, bd.z, bd.valid, k)
        if inp is None:
            no_start += 1
            continue
        items.append((bd, k, inp))
        truths.append(tr)
    layer = PhysicsLayer()
    worst_layer = math.inf if no_start else 0.0
    worst_layer_at = -1
    for c in range(0, len(items), 100):
        chunk = items[c : c + 100]
        out = run_layer(layer, chunk, R_MAN2)
        for b, (bd, _k, _inp) in enumerate(chunk):
            tr = truths[c + b]
            e = abs(float(out.range[b]) - tr) / tr if bool(out.plausible[b]) else math.inf
            if e > worst_layer:
                worst_layer, worst_layer_at = e, bd.index
    share = skipped / n if n else math.inf
    fitted = n - skipped
    ok = worst_ls < ZIG_LEG_TOL and worst_layer < ZIG_LEG_TOL and fitted >= ZIG_LEG_FITTED_MIN
    exp.metrics["noise_free_zig_leg"] = {
        "split": str(split),
        "scenarios": n,
        "fitted": fitted,
        "zig_leg_skipped": skipped,
        "skipped_share": share,
        "worst_least_squares": worst_ls,
        "worst_least_squares_index": worst_ls_at,
        "worst_physics_layer": worst_layer,
        "worst_physics_layer_index": worst_layer_at,
        "layer_without_grid_start": no_start,
    }
    exp.checks.append(
        Check(
            "noise-free-zig-leg",
            "pass" if ok else "fail",
            f"zig leg alone, {fitted} of {n} scenarios ({skipped} skipped, {share:.1%}): worst "
            f"relative range error at the leg's last row: least squares {worst_ls:.2e}, physics "
            f"layer {worst_layer:.2e}; needs ≥ {ZIG_LEG_FITTED_MIN} fitted (owner amendment)",
            value=max(worst_ls, worst_layer),
            threshold=ZIG_LEG_TOL,
        )
    )


def check_layer_720(exp: Experiment, split: Path) -> None:
    """Check 5: P0's physics-equals-least-squares on 720-row MAN2 windows."""
    blocks: list[tuple[dict[str, Any], np.ndarray, np.ndarray]] = []
    for _, meta, own, _tgt, obs in iter_pack_raw(split):
        if abs(float(meta["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) > 1e-6:
            continue
        blocks.append((meta, own, obs))
        if len(blocks) == LAYER_SCENARIOS:
            break

    def rows_of(meta: dict[str, Any], bd: BearingData) -> range:
        zig = int(meta["zig_index"])
        last = bd.n - 1
        for sp in meta.get("manoeuvres") or []:
            a = int(sp["start_index"])
            if a - 1 > zig:
                last = min(last, a - 2)
        return range(zig + 1, last + 1, LAYER_EVERY)

    check_physics_equals_ls(
        exp, blocks=blocks, rows_of=rows_of, r_max=R_MAN2, name="physics-equals-ls-720"
    )


def check_export_720(exp: Experiment, results: Path | None) -> None:
    """Check 6: a fresh 720-row export (golden batch from seed 316), its Python leg here, the
    browser and Java legs read from ``results`` only when they name this export's SHA-256."""
    from tma2.export.onnx_export import export, man2_fixture

    with tempfile.TemporaryDirectory() as tmp:
        pack, rows = man2_fixture(Path(tmp))
        d64 = export(Path(tmp) / "f64", pack, dtype="float64", rows=rows, zig_leg_rows=True)
        sha = hashlib.sha256((Path(tmp) / "f64" / "toy.onnx").read_bytes()).hexdigest()
        man = json.loads((Path(tmp) / "f64" / "manifest.json").read_text())
        h = hashlib.sha256()
        for f in sorted(q.name for q in (Path(tmp) / "f64").glob("in_*.bin")):
            h.update((Path(tmp) / "f64" / f).read_bytes())
        inputs_sha = h.hexdigest()
    worst = max(d64.values())
    exp.metrics["export_720"] = {
        "onnx_sha256": sha,
        "inputs_sha256": inputs_sha,
        "rows": rows,
        "batch": len(man["golden_k"]),
        "golden_k": man["golden_k"],
        "golden_valid_rows": man["golden_valid_rows"],
        "python_f64_max_rel_diff": d64,
    }
    exp.checks.append(
        Check(
            "export-720-python",
            "pass" if worst <= EXPORT_TOL else "fail",
            f"max relative difference {worst:.1e} (double, {rows} rows; batch of "
            f"{len(man['golden_k'])}, k {min(man['golden_k'])}–{max(man['golden_k'])})",
            value=worst,
            threshold=EXPORT_TOL,
        )
    )
    r: dict[str, Any] = {}
    if results is not None and results.exists():
        r = json.loads(results.read_text())
        exp.folder.mkdir(parents=True, exist_ok=True)
        kept = exp.folder / "conformance-720-results.json"
        kept.write_bytes(results.read_bytes())
        exp.add_artefact(kept, "720-row export conformance results (browser and Java legs)")
    for leg in ("wasm", "java"):
        v = r.get(leg)
        if leg == "java" and (v is None or v.get("deferred")):
            reason = v.get("reason") if v else "not run"
            exp.checks.append(Check("export-720-java", "skipped", f"deferred: {reason}"))
            continue
        if v is None:
            exp.checks.append(Check(f"export-720-{leg}", "fail", "leg missing from the results"))
            continue
        if v.get("onnx_sha256") != sha or v.get("inputs_sha256") != inputs_sha:
            exp.checks.append(
                Check(
                    f"export-720-{leg}",
                    "fail",
                    f"leg ran on model {v.get('onnx_sha256')} with inputs "
                    f"{v.get('inputs_sha256')}, not this export ({sha}, {inputs_sha})",
                )
            )
            continue
        w = max(v["max_rel_diff"].values())
        exp.checks.append(
            Check(
                f"export-720-{leg}",
                "pass" if w <= EXPORT_TOL else "fail",
                f"max relative difference {w:.1e} (double, {v.get('runtime')})",
                value=w,
                threshold=EXPORT_TOL,
            )
        )


def check_throughput(exp: Experiment, count: int = 10_000) -> None:
    """Check 7 (SC-004): the kernel on MAN2 ranges through ``generate_indices``, the path that
    generates training data on the fly (the scenario kernel in a numba ``prange`` over four
    threads, labels and padding included), best of two passes over ``count`` scenarios after a
    compiling call; this is how the pre-registered 30,000/s was measured. 0.5.0 phase-4 ranges,
    and a one-thread Python loop over ``run_kernel`` (dominated by call overhead), are reported."""
    from tma2.features.batch import generate_indices

    ranges = json.loads(MAN2_RANGES.read_text())
    p4 = json.loads(
        (ROOT / "tests" / "fixtures" / "gitma" / "phase4-seed777" / "ranges.json").read_text()
    )
    idx = np.arange(count, dtype=np.int64)

    def batched(r: dict[str, Any]) -> float:
        generate_indices(np.uint64(314), idx[:64], r, workers=4)
        best = math.inf
        for _ in range(2):
            t0 = time.perf_counter()
            generate_indices(np.uint64(314), idx, r, workers=4)
            best = min(best, time.perf_counter() - t0)
        return count / best

    def looped(r: dict[str, Any]) -> float:
        R = flatten_ranges(r)
        buf = KernelBuffers.for_rows(rows_for(r))
        run_kernel(np.uint64(314), 0, R, buf)
        t0 = time.perf_counter()
        for i in range(count):
            run_kernel(np.uint64(314), i, R, buf)
        return count / (time.perf_counter() - t0)

    man2 = batched(ranges)
    v050 = batched(p4)
    exp.metrics["throughput"] = {
        "method": "features.batch.generate_indices, 4 threads, best of two",
        "kernel_scenarios_per_s_man2": man2,
        "kernel_scenarios_per_s_050_phase4": v050,
        "python_loop_one_thread_man2": looped(ranges),
        "python_loop_one_thread_050_phase4": looped(p4),
        "scenarios": count,
        "threads": 4,
    }
    exp.checks.append(
        Check(
            "throughput",
            "pass" if man2 >= THROUGHPUT_MIN else "fail",
            f"kernel {man2:,.0f} MAN2 scenarios/s (0.5.0 phase-4 ranges {v050:,.0f}/s), "
            "generate_indices on four threads",
            value=man2,
            threshold=THROUGHPUT_MIN,
        )
    )


def layer_cost(exp: Experiment, split: Path) -> None:
    """Reported: the physics layer's forward cost per solve at 360 and 720 rows, batch 64: the
    first 64 scenarios of at least 600 rows, all their rows padded to 720, and their first 360."""
    blocks = []
    for _, meta, own, _tgt, obs in iter_pack_raw(split):
        if int(meta["samples"]) >= 600:
            blocks.append((meta, own, obs))
        if len(blocks) == 64:
            break
    threads = torch.get_num_threads()
    torch.set_num_threads(4)
    try:
        layer = PhysicsLayer()
        out: dict[str, float] = {}
        for r in (360, 720):
            sub = []
            for meta, own, obs in blocks:
                bd = _leg_data(meta, own, obs, 0, min(r, int(meta["samples"])) - 1)
                inp = trivial_inputs(bd.t, bd.ox, bd.oy, bd.z, bd.valid, bd.n - 1)
                if inp is not None:
                    sub.append((bd, bd.n - 1, inp))
            best = math.inf
            for _ in range(2):
                t0 = time.perf_counter()
                run_layer(layer, sub, r)
                best = min(best, time.perf_counter() - t0)
            out[f"ms_per_solve_{r}"] = 1000 * best / len(sub)
    finally:
        torch.set_num_threads(threads)
    exp.metrics["physics_layer_cost"] = {
        **out,
        "batch": len(blocks),
        "threads": 4,
        "iterations": ITERATIONS,
        "trials": TRIALS,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g0-man2", description=__doc__.split("\n")[0])
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--man2", required=True, help="seed 314 MAN2 dataset (validation.f32pack)")
    ap.add_argument("--noise-free", required=True, help="seed 316 noise-free MAN2 dataset")
    ap.add_argument("--regen", required=True, help="seed 304 dataset (generator 0.5.0)")
    ap.add_argument(
        "--conformance-results",
        help="results.json of the browser and Java legs run on the 720-row export",
    )
    a = ap.parse_args(argv)
    torch.set_default_dtype(torch.float64)
    folder = Path(a.experiment)
    exp = Experiment(id=folder.name, folder=folder)
    exp.command_lines.append("tma2-g0-man2 " + " ".join(sys.argv[1:] if argv is None else argv))
    man2 = Path(a.man2) / "validation.f32pack"
    nf = Path(a.noise_free) / "validation.f32pack"
    regen = Path(a.regen) / "validation.f32pack"
    for p in (man2, nf, regen):
        h = read_pack_header(p)
        if p != regen and h.generator_version != "0.6.0":
            raise SystemExit(f"{p}: generator {h.generator_version}, expected 0.6.0")
        exp.command_lines.append(f"dataset: {h.created_by} (commit {h.generator_git_commit})")
        exp.add_dataset(str(p), dump_record(h))  # binds the file's digest and header
    exp.command_lines.append(
        "conformance: python -m tma2.export.onnx_export --out <dir> --man2; "
        "(cd conformance/onnx && node wasm_leg.mjs --dir <dir>/f64 --out <results>); "
        "python conformance/onnx/java_leg.py <dir>/f64"
    )
    exp.add_estimator("classical", {"max_iterations": 50, "grid_every": 6})
    exp.add_estimator("physics", {"iterations": ITERATIONS, "trials": TRIALS, "knots": 0})
    check_throughput(exp)
    layer_cost(exp, man2)
    check_generator(exp)
    check_regen_050(exp, regen)
    check_distributions(exp, man2)
    check_noise_free_zig_leg(exp, nf)
    check_layer_720(exp, man2)
    check_export_720(exp, Path(a.conformance_results) if a.conformance_results else None)
    verdict = exp.write("G0")  # the pipeline gate; this experiment is its MAN2 run
    for c in exp.checks:
        print(f"{c.result:12s} {c.name:40s} {c.detail}")
    print(json.dumps({"experiment": str(folder), "result": verdict["result"]}))
    return 0 if verdict["result"] == "pass" else 3


if __name__ == "__main__":
    raise SystemExit(main())
