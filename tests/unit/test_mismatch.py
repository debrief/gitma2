"""Spec 010 (US1): the bearing-error mismatch overlay."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.cli.generate import load_condition
from tma2.cli.generate import run as generate_run
from tma2.data.dataset import GenerateOptions, generate_dataset, mismatch_truth_digest
from tma2.data.f32pack import read_pack_header, read_pack_raw
from tma2.sim import mismatch as mm
from tma2.sim import scenario as sc
from tma2.sim.generate import KernelBuffers, run_kernel
from tma2.sim.ranges import flatten_ranges, rows_for

ROOT = Path(__file__).resolve().parents[2]
RANGES = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())
HELDOUT = json.loads((ROOT / "configs" / "man2-heldout.json").read_text())
CONDITIONS = str(ROOT / "configs" / "gateh" / "conditions.json")
DEG = math.pi / 180.0


def _opts(
    out: Path, mismatch: dict[str, Any] | None, seed: int = 320, count: int = 20
) -> GenerateOptions:
    return GenerateOptions(
        seed=np.uint64(seed),
        count=count,
        out_dir=out,
        ranges=RANGES,
        heldout_ranges=HELDOUT,
        format="f32pack",
        created_by="test",
        generator_git_commit="0" * 40,
        generator_git_dirty=False,
        mismatch=mismatch,
    )


def _kernel(cond: mm.Condition | None, n: int, seed: int = 320) -> list[dict[str, np.ndarray]]:
    R = flatten_ranges(RANGES)
    buf = KernelBuffers.for_rows(rows_for(RANGES))
    out = []
    for i in range(n):
        run_kernel(np.uint64(seed), i, R, buf, cond)
        s = int(buf.TI[sc.TI_SAMPLES])
        out.append(
            {
                "bearing": buf.bearing[:s].copy(),
                "valid": buf.valid[:s].copy(),
                "own": buf.own[:s].copy(),
                "tgt": buf.tgt[:s].copy(),
                "P": buf.P.copy(),
                "tm": buf.tm.copy(),
                "clean": buf.clean[:s].copy(),
                "eng": buf.eng.copy(),
                "comp": buf.comp[:s].copy(),
                "outlier": buf.outlier[:s].copy(),
            }
        )
    return out


@pytest.mark.parametrize("seed", [320, 321, 322])
def test_off_is_generator_060_byte_for_byte(tmp_path: Path, seed: int) -> None:
    """FR-002, SC-001: no condition, and the ``off`` condition, give the same files."""
    generate_dataset(_opts(tmp_path / "a", None, seed))
    generate_dataset(_opts(tmp_path / "b", load_condition(CONDITIONS + "#off"), seed))
    for split in ("train", "validation", "test", "heldout"):
        a = (tmp_path / "a" / f"{split}.f32pack").read_bytes()
        b = (tmp_path / "b" / f"{split}.f32pack").read_bytes()
        assert a == b
        assert not (tmp_path / "b" / f"{split}.mismatch.npz").exists()
    assert read_pack_header(tmp_path / "b" / "train.f32pack").generator_version == "0.6.0"


def test_condition_changes_only_the_bearings() -> None:
    """FR-003: tracks, manoeuvres, dropouts and parameters are those of the off split."""
    base = _kernel(None, 12)
    cond = mm.flatten_condition(load_condition(CONDITIONS + "#all-central"))
    got = _kernel(cond, 12)
    for a, b in zip(base, got, strict=True):
        for key in ("valid", "own", "tgt", "tm", "clean"):
            assert np.array_equal(a[key], b[key]), key
        assert np.array_equal(a["P"], b["P"], equal_nan=True)
        assert not np.array_equal(a["bearing"], b["bearing"])
        assert np.array_equal(a["bearing"][~a["valid"]], b["bearing"][~b["valid"]])


def test_deterministic_and_components_sum_to_the_bearing() -> None:
    cond = mm.flatten_condition(load_condition(CONDITIONS + "#all-central"))
    a = _kernel(cond, 6)
    b = _kernel(cond, 6)
    for x, y in zip(a, b, strict=True):
        assert np.array_equal(x["bearing"], y["bearing"])
        assert np.array_equal(x["comp"], y["comp"])
        v = x["valid"]
        want = np.mod(x["clean"] + x["comp"].sum(axis=1), 2 * math.pi)
        d = np.angle(np.exp(1j * (x["bearing"] - want)))
        assert np.abs(d[v]).max() < 1e-6  # float32 rounding of the stored bearing


def test_single_kinds_are_components_of_the_combined_condition() -> None:
    """One fixed draw order: the correlated part of ``corr-central`` is that of ``all-central``
    up to the sigma factor."""
    one = _kernel(mm.flatten_condition(load_condition(CONDITIONS + "#corr-central")), 3)
    both = _kernel(mm.flatten_condition(load_condition(CONDITIONS + "#all-central")), 3)
    for a, b in zip(one, both, strict=True):
        f = b["eng"][mm.E_SIGMA_TRUE] / a["eng"][mm.E_SIGMA_TRUE]
        assert np.allclose(a["comp"][:, 1] * f, b["comp"][:, 1], rtol=1e-12, atol=0)
        assert not a["outlier"].any() and np.all(a["comp"][:, 2] == 0)


def test_statistics_match_the_declared_process() -> None:
    """SC-002 on 200 engagements of the primary condition."""
    c = load_condition(CONDITIONS + "#all-central")
    rows = _kernel(mm.flatten_condition(c), 200)
    dt = float(rows[0]["P"][sc.P_DT])
    # Correlated component: lag-one autocorrelation exp(-dt / tau), unit-variance scaled.
    z = [r["comp"][:, 1] / r["eng"][mm.E_SIGMA_C] for r in rows]
    num = sum(float(np.sum(x[1:] * x[:-1])) for x in z)
    den = sum(float(np.sum(x[:-1] ** 2)) for x in z)
    assert num / den == pytest.approx(math.exp(-dt / c["corr_tau_s"]), abs=0.01)
    assert np.concatenate(z).std() == pytest.approx(1.0, abs=0.02)
    # Share: correlated and white variances equal at share 0.5.
    for r in rows[:5]:
        assert r["eng"][mm.E_SIGMA_C] == pytest.approx(r["eng"][mm.E_SIGMA_W])
        total = math.hypot(r["eng"][mm.E_SIGMA_C], r["eng"][mm.E_SIGMA_W])
        assert total == pytest.approx(r["eng"][mm.E_SIGMA_TRUE])
    # Bias: stationary sd, and lag-one autocorrelation exp(-dt / tau_b).
    b = [r["comp"][:, 2] for r in rows]
    first = np.array([x[0] for x in b])
    assert first.std() == pytest.approx(c["bias_sd_rad"], rel=0.15)
    num = sum(float(np.sum(x[1:] * x[:-1])) for x in b)
    den = sum(float(np.sum(x[:-1] ** 2)) for x in b)
    assert num / den == pytest.approx(math.exp(-dt / c["bias_tau_s"]), abs=0.003)
    # Sigma factor within [1/k, k], spread over it.
    k = c["sigma_factor_max"]
    f = np.array([r["eng"][mm.E_SIGMA_TRUE] / r["P"][sc.P_SIGMA] for r in rows])
    assert f.min() >= 1 / k - 1e-9 and f.max() <= k + 1e-9
    assert np.log(f).std() == pytest.approx(math.log(k) / math.sqrt(3), rel=0.15)
    # Outliers: rate, and spread in units of the true sd.
    flags = np.concatenate([r["outlier"] for r in rows])
    assert flags.mean() == pytest.approx(c["outlier_rate"], abs=0.002)
    o = np.concatenate([r["comp"][r["outlier"], 3] / r["eng"][mm.E_SIGMA_TRUE] for r in rows])
    assert o.std() == pytest.approx(c["outlier_spread"], rel=0.05)
    white = np.concatenate([r["comp"][:, 0] / r["eng"][mm.E_SIGMA_W] for r in rows])
    assert white.std() == pytest.approx(1.0, abs=0.02)


def test_side_file_and_header(tmp_path: Path) -> None:
    """FR-004, FR-005: the truth is in the side file; the pack states the nominal sigma only."""
    cond = load_condition(CONDITIONS + "#all-central")
    generate_dataset(_opts(tmp_path, cond))
    hdr = read_pack_header(tmp_path / "validation.f32pack")
    assert hdr.generator_version == "0.7.0"
    assert hdr.mismatch is not None and hdr.mismatch.id == "all-central"
    side = np.load(tmp_path / "validation.mismatch.npz")
    meta = json.loads(str(side["meta"]))
    assert meta["condition"]["id"] == "all-central" and meta["split"] == "validation"
    assert meta["scenario_count"] == hdr.scenario_count == side["eng"].shape[0]
    assert meta["truth_sha256"] == mismatch_truth_digest(side["eng"], side["comp"], side["outlier"])
    _, blocks = read_pack_raw(tmp_path / "validation.f32pack")
    sigmas = set(RANGES["noise_sigma_rad_values"])
    for j, (_, metadata, _own, _tgt, _obs) in enumerate(blocks):
        nominal = float(metadata["parameters"]["noise_sigma_rad"])
        assert any(abs(nominal - s) < 1e-7 for s in sigmas)
        assert side["eng"][j, mm.E_SIGMA_TRUE] != pytest.approx(nominal, rel=1e-6)
        assert "mismatch" not in json.dumps(metadata)


def test_condition_validation_and_cli(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        mm.flatten_condition({"id": "x", "corr_tau_s": 60.0})
    with pytest.raises(ValueError):
        mm.flatten_condition({"id": "x", "sigma_factor_max": 0.5})
    with pytest.raises(KeyError):
        load_condition(CONDITIONS + "#nope")
    doc = json.loads(Path(CONDITIONS).read_text())
    assert len(doc["conditions"]) == 16 and doc["primary"] == "all-central"
    for raw in doc["conditions"]:
        assert mm.flatten_condition(raw).off == (raw["id"] == "off")
    args = ["--seed", "320", "--count", "10", "--out", str(tmp_path), "--allow-dirty"]
    args += ["--ranges", str(ROOT / "configs" / "man2-ranges.json")]
    args += ["--heldout-ranges", str(ROOT / "configs" / "man2-heldout.json")]
    assert generate_run([*args, "--mismatch", CONDITIONS + "#nope"]) == 2
    assert generate_run([*args, "--mismatch", CONDITIONS + "#all-mild", "--noise-free"]) == 2
    assert generate_run([*args, "--format", "f32pack", "--mismatch", CONDITIONS + "#all-mild"]) == 0
    assert (tmp_path / "test.mismatch.npz").exists()
    assert "#all-mild" in read_pack_header(tmp_path / "test.f32pack").created_by
