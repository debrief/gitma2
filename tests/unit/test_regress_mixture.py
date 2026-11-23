"""Spec 037 research R3: the fine-tuning mix and starting from a checkpoint."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from tma2.features.batch import generate_indices
from tma2.regress import mixture
from tma2.regress.data import batch_at
from tma2.regress.model import RegressorConfig
from tma2.regress.train import config_digest, train
from tma2.sim import mismatch as mm
from tma2.sim import scenario as sc
from tma2.sim.generate import KernelBuffers, run_kernel
from tma2.sim.ranges import flatten_ranges, rows_for

ROOT = Path(__file__).resolve().parents[2]
RANGES = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())
MIX = mixture.load_mix(ROOT / "configs" / "regress" / "ft-mix.json")


def test_batch_overlay_equals_the_split_generator() -> None:
    conds = json.loads((ROOT / "configs/gateh/conditions.json").read_text())["conditions"]
    cond = mm.flatten_condition(next(c for c in conds if c["id"] == "all-central"))
    idx = np.arange(6, dtype=np.int64)
    M = np.full((6, mm.M_LEN), np.nan)
    M[[0, 2, 5]] = cond.M
    clean = generate_indices(321, idx, RANGES)
    got = generate_indices(321, idx, RANGES, mismatch=M)
    buf = KernelBuffers.for_rows(rows_for(RANGES))
    R = flatten_ranges(RANGES)
    for b in range(6):
        if b in (0, 2, 5):
            run_kernel(np.uint64(321), b, R, buf, cond)
            s = int(buf.TI[sc.TI_SAMPLES])
            assert np.array_equal(got.bearing[b, :s], buf.bearing[:s].astype(np.float32))
            assert not np.array_equal(got.bearing[b], clean.bearing[b])
        else:
            assert np.array_equal(got.bearing[b], clean.bearing[b])
    assert np.array_equal(got.tgt, clean.tgt) and np.array_equal(got.valid, clean.valid)


def test_mix_is_a_pure_function_of_the_index_and_stays_in_range() -> None:
    idx = np.arange(20_000, dtype=np.int64)
    M = mixture.conditions(369, idx, MIX)
    assert np.array_equal(
        M[5000:5010], mixture.conditions(369, idx[5000:5010], MIX), equal_nan=True
    )
    assert not np.array_equal(M, mixture.conditions(370, idx, MIX), equal_nan=True)
    assert np.all(np.isnan(M[:, mm.M_SECOND :]))  # the held-out kinds: never
    clean = np.all(np.isnan(M), axis=1)
    assert abs(clean.mean() - (0.25 + 0.75 / 16)) < 0.015
    for i, c in enumerate(MIX.col):
        v = M[:, c][np.isfinite(M[:, c])]
        assert v.min() >= MIX.lo[i] - 1e-12 and v.max() <= MIX.hi[i] + 1e-12
    # the two fields of a kind go together, as flatten_condition requires
    assert np.array_equal(np.isnan(M[:, mm.M_CORR_TAU]), np.isnan(M[:, mm.M_CORR_SHARE]))
    assert np.array_equal(np.isnan(M[:, mm.M_OUT_RATE]), np.isnan(M[:, mm.M_OUT_SPREAD]))
    assert abs(np.isfinite(M[:, mm.M_BIAS_SD]).mean() - 0.375) < 0.015


def test_a_mix_cannot_name_a_held_out_kind(tmp_path: Path) -> None:
    raw = dict(MIX.raw, white_t_df=[3, 5])
    p = tmp_path / "mix.json"
    p.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        mixture.load_mix(p)


def test_earlier_configurations_keep_their_digests() -> None:
    for run in ("20261111-r-runs/r-a-s1-42990055824", "20261114-tlm-runs"):
        for rec_path in sorted((ROOT / "experiments" / run).rglob("run.json"))[:1]:
            rec = json.loads(rec_path.read_text())
            cfg = RegressorConfig(**rec["config"])
            assert config_digest(cfg) == rec["config_sha256"]
            assert "error_mix" not in cfg.to_json() and "init_sha256" not in cfg.to_json()


def test_stream_with_a_mix_changes_bearings_not_the_truth() -> None:
    cfg = RegressorConfig(batch_scenarios=8, stream_seed=369)
    a = batch_at(cfg, RANGES, 3)
    b = batch_at(cfg, RANGES, 3, mix=MIX)
    # range is untouched; the velocity is the same vector in a frame set by the first bearing
    assert np.array_equal(a.y[..., 0], b.y[..., 0]) and np.array_equal(a.mask, b.mask)
    assert np.allclose(
        np.hypot(a.y[..., 1], a.y[..., 2]), np.hypot(b.y[..., 1], b.y[..., 2]), atol=1e-5
    )
    assert not np.array_equal(a.f, b.f)


def test_fine_tune_starts_from_the_named_checkpoint(tmp_path: Path) -> None:
    toy = json.loads((ROOT / "configs" / "regress" / "toy.json").read_text())
    toy = toy.get("config", toy)
    base = replace(
        RegressorConfig(**toy), total_updates=2, val_every_updates=2, val_count=8, batch_scenarios=4
    )
    train(base, tmp_path / "base")
    ck = tmp_path / "base" / "checkpoint.safetensors"
    sha = hashlib.sha256(ck.read_bytes()).hexdigest()
    ft = replace(
        base, id="ft", init_sha256=sha, error_mix=str(ROOT / "configs/regress/ft-mix.json")
    )
    with pytest.raises(ValueError):
        train(ft, tmp_path / "none")
    with pytest.raises(ValueError):
        train(replace(ft, init_sha256="0" * 64), tmp_path / "bad", init=ck)
    rec = train(ft, tmp_path / "ft", init=ck)
    assert rec["updates"] == 2 and "mis_ln_range_abs_median" in rec["validation"][-1]
    assert rec["config"]["init_sha256"] == sha
