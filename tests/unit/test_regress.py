"""Spec 012: the regressor control. Causality, frame invariance, the stream, resume."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

from tma2.regress.data import batch_at, load_ranges, stream_indices, supervised
from tma2.regress.frame import features, targets, to_state
from tma2.regress.model import Regressor, RegressorConfig

ROOT = Path(__file__).resolve().parents[2]
TOY = dict(layers=2, width=32, heads=2, feedforward=64, batch_scenarios=8, precision="float32")


def _cfg(**kw: object) -> RegressorConfig:
    return RegressorConfig(**{**TOY, "ranges": str(ROOT / "configs/man2-ranges.json"), **kw})  # type: ignore[arg-type]


def test_stream_is_a_function_of_the_config() -> None:
    cfg = _cfg()
    rg = load_ranges(cfg.ranges)
    a, b = batch_at(cfg, rg, 3), batch_at(cfg, rg, 3)
    assert np.array_equal(a.f, b.f) and np.array_equal(a.y, b.y)
    assert stream_indices(cfg, 3)[0] == 24
    rep = _cfg(stream_repeat=16)
    assert stream_indices(rep, 2).tolist() == list(range(8))  # 16..23 wraps to 0..7


def test_held_course_share_of_the_stream() -> None:
    """A quarter of each batch from the held-course ranges: those targets do not change."""
    cfg = _cfg(
        held_fraction=0.25, held_ranges=str(ROOT / "configs/regress/held-course-ranges.json")
    )
    held = load_ranges(cfg.held_ranges)
    x = batch_at(cfg, load_ranges(cfg.ranges), 0, held)
    assert x.f.shape[0] == 8
    v = x.y[:2, :, 1:]  # the first two scenarios: velocity targets constant over existing rows
    for i in range(2):
        rows = x.mask[i]
        assert np.ptp(v[i][rows], axis=0).max() < 1e-4
    assert any(np.ptp(x.y[i, x.mask[i], 1:], axis=0).max() > 1e-3 for i in range(2, 8))


def test_causal() -> None:
    """A token's output does not change when later rows change."""
    cfg = _cfg()
    torch.manual_seed(0)
    prev = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)  # as left by the physics layer's tests and CLIs
    try:
        m = Regressor(cfg).eval()
    finally:
        torch.set_default_dtype(prev)
    torch.nn.init.normal_(m.head.weight, std=0.1)
    x = batch_at(cfg, load_ranges(cfg.ranges), 0)
    f = torch.from_numpy(x.f)
    g = f.clone()
    g[:, 300:] += 1.0
    for off in (0, 1, 2):
        with torch.no_grad():
            a, _ = m(f, off)
            b, _ = m(g, off)
        last = off + (np.arange(a.shape[1]) + 1) * 3 - 1
        before = torch.from_numpy(last < 300)
        assert torch.allclose(a[:, before], b[:, before], atol=1e-5)
        assert not torch.allclose(a[:, ~before], b[:, ~before], atol=1e-5)


def test_frame_is_rotation_and_translation_invariant() -> None:
    rng = np.random.default_rng(2)
    b, r = 3, 50
    t = np.tile(10.0 * np.arange(r, dtype=np.float32), (b, 1))
    own = np.cumsum(rng.normal(0, 50, (b, r, 2)), axis=1)
    tgt = np.zeros((b, r, 4))
    tgt[..., :2] = own + rng.normal(0, 8000, (b, 1, 2))
    tgt[..., 2] = rng.uniform(0, 6.28, (b, 1))
    tgt[..., 3] = 6.0
    d = tgt[..., :2] - own
    bearing = np.arctan2(d[..., 0], d[..., 1])
    valid = np.ones((b, r), dtype=bool)
    valid[:, 0] = False
    sigma = np.full(b, np.pi / 180, dtype=np.float32)
    f0, th0 = features(t, own, bearing, valid, valid | True, sigma)
    y0 = targets(own, tgt, th0)
    a = 0.7  # rotate everything clockwise by a (compass angles increase by a), then shift
    c, s = np.cos(a), np.sin(a)

    def rot(p: np.ndarray) -> np.ndarray:
        return np.stack([p[..., 0] * c + p[..., 1] * s, p[..., 1] * c - p[..., 0] * s], -1)

    own2 = rot(own) + np.array([1234.0, -987.0])
    tgt2 = tgt.copy()
    tgt2[..., :2] = rot(tgt[..., :2]) + np.array([1234.0, -987.0])
    tgt2[..., 2] = tgt[..., 2] + a
    f1, th1 = features(t, own2, bearing + a, valid, valid | True, sigma)
    y1 = targets(own2, tgt2, th1)
    assert np.allclose(f0, f1, atol=1e-4) and np.allclose(y0, y1, atol=1e-5)
    k = 30
    st, (rng_m, course, speed) = to_state(y0[0, k], th0[0], bearing[0, k], tuple(own[0, k]))
    assert np.allclose(st[:2], tgt[0, k, :2], atol=1.0)
    assert abs(speed - 6.0) < 1e-4
    assert abs(((course - tgt[0, k, 2]) + np.pi) % (2 * np.pi) - np.pi) < 1e-5
    assert abs(rng_m - np.hypot(*d[0, k])) < 1.0


def test_supervised_tokens() -> None:
    mask = np.zeros((1, 12), dtype=bool)
    mask[0, :8] = True
    assert supervised(mask, 3, 0).tolist() == [[1, 1, 0, 0]]  # tokens end at rows 2, 5, 8, 11
    assert supervised(mask, 3, 2).tolist() == [[1, 1, 0, 0]]  # rows 4, 7, 10, 13 (beyond: 0)


def _run(cfg: Path, out: Path, *extra: str) -> dict:  # type: ignore[type-arg]
    cmd = [sys.executable, "-m", "tma2.cli.rtrain", "--config", str(cfg), "--out", str(out)]
    subprocess.run([*cmd, *extra], check=True, cwd=ROOT, capture_output=True)
    return json.loads((out / "run.json").read_text())  # type: ignore[no-any-return]


def test_toy_training_learns_and_resumes(tmp_path: Path) -> None:
    """A CPU toy run lowers its validation loss; a run stopped by its limit resumes on the same
    stream and finishes with the same number of updates and scenarios."""
    cfg = {**TOY, "id": "t", "total_updates": 60, "warmup_updates": 5, "val_count": 32,
           "val_every_updates": 20, "learning_rate": 1e-3,
           "ranges": str(ROOT / "configs/man2-ranges.json")}  # fmt: skip
    p = tmp_path / "c.json"
    p.write_text(json.dumps(cfg))
    full = _run(p, tmp_path / "full")
    v = full["validation"]
    assert full["stopped"] == "complete" and v[-1]["loss"] < v[0]["loss"]
    part = _run(p, tmp_path / "a", "--limit-seconds", "0")
    assert part["stopped"] == "limit" and part["updates"] < 60
    done = _run(p, tmp_path / "b", "--resume", str(tmp_path / "a"))
    assert done["stopped"] == "complete" and done["updates"] == 60
    assert done["scenarios_seen"] == full["scenarios_seen"] and len(done["segments"]) == 2


def test_segments_resume_and_ledger(tmp_path: Path) -> None:
    """The provider-free segment runner (what the GPU function calls): two segments of a plan
    continue one run and accumulate their time; the ledger refuses a plan past the cap."""
    from tma2.regress.ledger import check
    from tma2.regress.remote import plan_limit_seconds, run_segment

    cfg = {**TOY, "id": "t", "total_updates": 30, "warmup_updates": 3, "val_count": 16,
           "val_every_updates": 15, "ranges": str(ROOT / "configs/man2-ranges.json")}  # fmt: skip
    plan = {"config": cfg, "segments": 2, "segment_limit_seconds": 0}
    work = tmp_path / "run"
    a = run_segment(plan, work, "cpu", "abc")
    assert a["stopped"] == "limit" and a["gpu_seconds"] > 0
    b = run_segment({**plan, "segment_limit_seconds": 600}, work, "cpu", "abc")
    assert b["stopped"] == "complete" and b["updates"] == 30 and len(b["segments"]) == 2
    assert b["gpu_seconds"] > a["gpu_seconds"] and b["segments"][0]["git_commit"] == "abc"
    assert not (tmp_path / "run.prev").exists()
    assert plan_limit_seconds({"segments": 2, "segment_limit_seconds": 18000}) == 2 * 18600
    assert check(10 * 3600, 5 * 3600, 50 * 3600) and not check(46 * 3600, 5 * 3600, 50 * 3600)


def test_config_matches_its_schema_type() -> None:
    """Types once: the dataclass the code uses has exactly the schema type's fields, and every
    committed plan's config validates against it."""
    import dataclasses
    import json

    from tma2.types.generated.tma import RegressorConfig as Schema

    assert {f.name for f in dataclasses.fields(RegressorConfig)} == set(Schema.model_fields)
    for plan in sorted((ROOT / "configs" / "regress").glob("*.json")):
        raw = json.loads(plan.read_text())
        if "config" not in raw:
            continue
        cfg = RegressorConfig(**raw["config"])
        Schema.model_validate(cfg.to_json())
