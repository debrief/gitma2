"""ONNX export of the toy model and the golden-batch conformance check (constitution VI).

``python -m tma2.export.onnx_export --out <dir>`` writes, under ``f64/`` and ``f32/``,
``toy.onnx``, raw golden inputs and outputs (``in_*.bin``, ``out_*.bin``, ``ort_*.bin``,
``manifest.json``) and ``ops.txt``, and checks onnxruntime (Python) against torch to 1e-5 in
double. The browser and Java legs read the same files (``conformance/onnx/``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

from tma2.data.f32pack import iter_pack_raw
from tma2.physics.segmentation import trivial_inputs
from tma2.references.classical import bearing_data_from_arrays

from .toy_model import ToyModel

R_MAX = 360
OPSET = 17
TOL = 1e-5


def golden_batch(
    fixture_pack: Path, n: int = 8, rows: int = R_MAX, zig_leg_rows: bool = False
) -> dict[str, np.ndarray]:
    """Eight rows for the conformance batch: ``zig + 30`` (the 0.5.0 fixtures), or, with
    ``zig_leg_rows`` (MAN2), the last row of the steady target leg containing the zig, in
    scenarios where that leg starts at row 0, so the toy model's single constant-velocity leg over
    the prefix is the truth and the solve is well-posed. On
    MAN2 data ``zig + 30`` can fall after a target turn, where the one-leg fit runs away along a
    flat valley (range 1e11 m, covariance condition 1e19) and no two runtimes need agree."""
    from tma2.eval.rows import zig_leg

    bearing, valid, own, t, sigma, k, theta0 = [], [], [], [], [], [], []
    for _, meta, own_a, _tgt, obs in iter_pack_raw(fixture_pack):
        d = bearing_data_from_arrays(meta, own_a, obs)
        if zig_leg_rows:
            # the toy model fits one leg over the whole prefix [0, k]: the target must hold its
            # course from row 0 to k, i.e. the zig leg must start at row 0
            leg = zig_leg(meta)
            if leg is None or leg[0] != 0:
                continue
            kk = leg[1]
        else:
            kk = min(d.zig_index + 30, d.n - 1)
        inp = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, kk)
        if inp is None:
            continue

        def pad(a: np.ndarray) -> np.ndarray:
            out = np.zeros(rows)
            out[: a.shape[0]] = a
            return out

        bearing.append(pad(d.z))
        valid.append(pad(d.valid.astype(float)))
        own.append(np.stack([pad(d.ox), pad(d.oy)], 1))
        t.append(pad(d.t))
        sigma.append(d.sigma)
        k.append(kk)
        theta0.append(inp.theta0)
        if len(k) == n:
            break
    f = np.float32
    return {
        "bearing": np.stack(bearing).astype(f),
        "valid": np.stack(valid).astype(f),
        "own": np.stack(own).astype(f),
        "t": np.stack(t).astype(f),
        "sigma": np.array(sigma, dtype=f),
        "k": np.array(k, dtype=np.int64),
        "theta0": np.stack(theta0).astype(f),
    }


def man2_fixture(tmp: Path) -> tuple[Path, int]:
    """A small MAN2 pack (generator 0.6.0, seed 316, 80 scenarios) and its window rows (720),
    generated deterministically so no binary fixture is committed."""
    from tma2.data.dataset import GenerateOptions, generate_dataset
    from tma2.sim.ranges import rows_for

    root = Path(__file__).resolve().parents[3] / "configs"
    ranges = json.loads((root / "man2-ranges.json").read_text())
    heldout = json.loads((root / "man2-heldout.json").read_text())
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(316),
            count=80,
            out_dir=tmp,
            ranges=ranges,
            heldout_ranges=heldout,
            format="f32pack",
            created_by="onnx_export --man2",
            generator_git_commit="export",
            generator_git_dirty=False,
        )
    )
    return tmp / "train.f32pack", rows_for(ranges)


def export(
    out_dir: Path,
    fixture_pack: Path,
    seed: int = 1,
    dtype: str = "float64",
    rows: int = R_MAX,
    zig_leg_rows: bool = False,
) -> dict[str, float]:
    """Export in ``dtype`` (float64 by default: the iterative solve amplifies float32 kernel
    differences between runtimes to ~1e-4, so the conformance proof is made in double).

    The model is built under float32 and converted, with the default dtype pinned for the whole
    export, so the graph does not depend on what the caller set (P0 round 2: tma2-p0's physics
    checks had set double)."""
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float32)
    try:
        return _export(out_dir, fixture_pack, seed, dtype, rows, zig_leg_rows)
    finally:
        torch.set_default_dtype(default)


def _export(
    out_dir: Path, fixture_pack: Path, seed: int, dtype: str, rows: int, zig_leg_rows: bool
) -> dict[str, float]:
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    model = ToyModel().eval()
    batch = golden_batch(fixture_pack, rows=rows, zig_leg_rows=zig_leg_rows)
    np_dtype = np.float64 if dtype == "float64" else np.float32
    batch = {n: (a.astype(np_dtype) if a.dtype != np.int64 else a) for n, a in batch.items()}
    if dtype == "float64":
        model = model.double()
    tensors = {kk: torch.tensor(v) for kk, v in batch.items()}
    with torch.no_grad():
        ref = model(*[tensors[n] for n in ("bearing", "valid", "own", "t", "sigma", "k", "theta0")])
    onnx_path = out_dir / "toy.onnx"
    # Scalar constants inside the scripted physics Loop take the default dtype at export: it
    # must match the model's, or onnxruntime rejects mixed float/double products (spec 003).
    torch.set_default_dtype(torch.float64 if dtype == "float64" else torch.float32)
    torch.onnx.export(
        model,
        tuple(tensors[n] for n in ("bearing", "valid", "own", "t", "sigma", "k", "theta0")),
        str(onnx_path),
        input_names=["bearing", "valid", "own", "t", "sigma", "k", "theta0"],
        output_names=["state", "cov", "cost", "plausible"],
        dynamic_axes={
            n: {0: "batch"}
            for n in (
                "bearing",
                "valid",
                "own",
                "t",
                "sigma",
                "k",
                "theta0",
                "state",
                "cov",
                "cost",
                "plausible",
            )
        },
        opset_version=OPSET,
        dynamo=False,
    )
    # Raw little-endian copies for the browser and Java legs (no npz reader there).
    for name, arr in batch.items():
        (out_dir / f"in_{name}.bin").write_bytes(np.ascontiguousarray(arr).tobytes())
    outs = {n: o.numpy() for n, o in zip(("state", "cov", "cost", "plausible"), ref, strict=True)}
    for name, arr in outs.items():
        (out_dir / f"out_{name}.bin").write_bytes(np.ascontiguousarray(arr).tobytes())
    (out_dir / "shapes.json").write_text(json.dumps({n: list(a.shape) for n, a in batch.items()}))
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    n: {"shape": list(a.shape), "dtype": str(a.dtype)} for n, a in batch.items()
                },
                "outputs": {
                    n: {"shape": list(a.shape), "dtype": str(a.dtype)} for n, a in outs.items()
                },
            },
            indent=2,
        )
    )
    import onnx

    m = onnx.load(str(onnx_path))
    ops = sorted({node.op_type for node in m.graph.node})
    (out_dir / "ops.txt").write_text("\n".join(ops) + "\n")
    # Python runtime leg.
    import onnxruntime as ort  # type: ignore[import-untyped]

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    got = sess.run(None, {n: batch[n] for n in batch})
    for name, a in zip(("state", "cov", "cost", "plausible"), got, strict=True):
        (out_dir / f"ort_{name}.bin").write_bytes(np.ascontiguousarray(a).tobytes())
    diffs = {}
    for name, a, b in zip(("state", "cov", "cost", "plausible"), got, ref, strict=True):
        b_np = b.numpy()
        scale = np.maximum(np.abs(b_np), 1.0)
        diffs[name] = float(np.max(np.abs(a - b_np) / scale))
    (out_dir / "python_leg.json").write_text(
        json.dumps(
            {
                "max_rel_diff": diffs,
                "tol": TOL,
                "dtype": dtype,
                "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
                "runtime": f"onnxruntime {ort.__version__} (Python)",
            },
            indent=2,
        )
    )
    return diffs


def main(argv: list[str] | None = None) -> int:
    """Export ``<out>/f64`` (the conformance artefact: Python, browser and Java legs against torch
    to 1e-5) and ``<out>/f32`` (reported only: in float32 the damped solve's accept/reject
    decisions can flip between runtimes, so float32 agreement is ~1e-3, not 1e-5)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--fixture", default="tests/fixtures/gitma/phase4-seed777/test.f32pack")
    ap.add_argument(
        "--man2",
        action="store_true",
        help="720-row windows: the golden batch is generated from configs/man2-ranges.json, "
        "seed 316 (generator 0.6.0, spec 006), instead of read from --fixture",
    )
    a = ap.parse_args(argv)
    rows = R_MAX
    fixture = Path(a.fixture)
    tmp = None
    if a.man2:
        tmp = tempfile.TemporaryDirectory()
        fixture, rows = man2_fixture(Path(tmp.name))
    try:
        d64 = export(Path(a.out) / "f64", fixture, dtype="float64", rows=rows, zig_leg_rows=a.man2)
        d32 = export(Path(a.out) / "f32", fixture, dtype="float32", rows=rows, zig_leg_rows=a.man2)
    finally:
        if tmp is not None:
            tmp.cleanup()
    print(json.dumps({"f64_vs_torch": d64, "f32_vs_torch": d32}))
    bad = {k: v for k, v in d64.items() if v > TOL}
    if bad:
        print(f"python runtime leg (double) exceeds {TOL}: {bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
