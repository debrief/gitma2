"""The calibration head, its loss, the temperature control and calibrated files (spec 008 T025)."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.calib.data import CalData
from tma2.calib.head import CalHead
from tma2.calib.loss import beta_nll
from tma2.calib.predict import calibrate_row, write_calibrated
from tma2.calib.temperature import apply, fit
from tma2.calib.train import evaluate, predict_s, train_head
from tma2.types.generated.tma import CalibrationHeadConfig, TemperatureConfig

CFG = {
    "width": 8,
    "bound": 2.0,
    "beta": 0.5,
    "cap": 100.0,
    "learning_rate": 0.01,
    "batch_rows": 256,
    "max_epochs": 30,
    "patience": 5,
    "min_improvement": 0.001,
    "seed": 1,
}


def _synthetic(n: int, seed: int) -> CalData:
    """Rows whose true variance is the raw one scaled by e^(2·s_true), s_true = 0.7 · x0: the
    NEES under the raw covariance is e^(2 s_true) · χ²₄."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 5))
    s_true = 0.7 * x[:, 0]
    q = np.exp(2 * s_true) * rng.chisquare(4, n)
    return _data(x, q, rng)


def _data(x: np.ndarray, q: np.ndarray, rng: np.random.Generator) -> CalData:
    """Rows whose raw NEES is q: identity information, the error spread over the four local
    coordinates."""
    n = len(q)
    return CalData(
        ordinal=np.arange(n),
        k=np.zeros(n, dtype=np.int64),
        t=np.zeros(n),
        x=x,
        q=q,
        u=np.sqrt(q / 4)[:, None] * np.ones((n, 4)),
        w=np.broadcast_to(np.eye(4), (n, 4, 4)).copy(),
        own=np.zeros((n, 2)),
        usable=np.ones(n, dtype=bool),
        scalable=np.ones(n, dtype=bool),
        minute=rng.choice([5, 10, 15, 20], n),
        open=rng.random(n) < 0.1,
        header={"weights_sha256": "w"},
    )


def test_untrained_head_is_the_identity() -> None:
    torch.set_default_dtype(torch.float64)
    head = CalHead(CalibrationHeadConfig.model_validate(CFG), 5).double()
    assert np.all(predict_s(head, np.random.default_rng(0).normal(size=(50, 5))) == 0.0)


def test_loss_minimum_and_temperature() -> None:
    """A single scale: β-NLL's minimum is s = ½ log(E q / 4); the temperature finds it."""
    torch.set_default_dtype(torch.float64)
    u = torch.full((1000, 4), 2.0)  # NEES 16, 4× the χ²₄ mean: s = ½ log 4
    w = torch.eye(4, dtype=torch.float64).expand(1000, 4, 4)
    s = torch.zeros(1, requires_grad=True)
    opt = torch.optim.Adam([s], lr=0.05)
    for _ in range(800):
        loss = beta_nll(s.expand(1000), u, w, 0.5, 100.0)
        opt.zero_grad()
        loss.backward()  # type: ignore[no-untyped-call]
        opt.step()
    assert abs(float(s.detach()) - 0.5 * math.log(4)) < 1e-3
    d = _synthetic(4000, 2)
    q = np.full(len(d), 16.0) * np.where(d.minute == 5, 4.0, 1.0)
    d.q, d.u = q, np.sqrt(q / 4)[:, None] * np.ones((len(q), 4))
    temps = fit(TemperatureConfig(slices=["minute"], beta=0.5, cap=100.0), d)
    assert abs(temps["minute=5"][0] - 0.5 * math.log(16)) < 0.01
    assert abs(temps["minute=10"][0] - 0.5 * math.log(4)) < 0.01
    assert np.allclose(apply(temps, d, ["minute"])[d.minute == 10], temps["minute=10"])


def test_head_learns_a_feature_dependent_scale(tmp_path: Path) -> None:
    torch.set_default_dtype(torch.float64)
    tr, va = _synthetic(6000, 3), _synthetic(2000, 4)
    cfg = CalibrationHeadConfig.model_validate(CFG)
    meta = train_head(cfg, tr, va, tmp_path / "ck", {"test": True}, log=lambda _m: None)
    assert meta["best_val"] < meta["untrained_val"] - 0.2
    assert (tmp_path / "ck" / "last.safetensors").exists()
    head = CalHead(cfg, 5).double()
    from safetensors.torch import load_file

    head.load_state_dict(load_file(str(tmp_path / "ck" / "best.safetensors")))
    s = predict_s(head, va.x)[:, 0]
    assert np.corrcoef(s, va.x[:, 0])[0, 1] > 0.9
    assert evaluate(head, va, cfg.cap) == meta["best_val"]


def test_shuffled_control_keeps_its_last_epoch(tmp_path: Path) -> None:
    torch.set_default_dtype(torch.float64)
    cfg = CalibrationHeadConfig.model_validate({**CFG, "shuffled": True, "max_epochs": 3})
    meta = train_head(
        cfg, _synthetic(2000, 5), _synthetic(500, 6), tmp_path / "s", {}, log=lambda _m: None
    )
    assert meta["epoch"] == 3 and "last_weights_sha256" in meta and "last_val" in meta


def test_calibrated_file_keeps_points(tmp_path: Path) -> None:
    row = {
        "timestamp_s": 600.0,
        "range_m": 9000.0,
        "course_rad": 1.0,
        "speed_mps": 4.0,
        "x_m": 1.0,
        "y_m": 2.0,
        "converged": True,
        "iterations": 0,
        "cov_ok": True,
        "cov_xyvv": [4.0] + [0.0] * 3 + [4.0] + [0.0] * 2 + [1.0, 0.0, 1.0],
        "log_range_sd": 0.1,
        "course_sd_rad": 0.05,
        "speed_sd_mps": 0.3,
    }
    out = calibrate_row(row, [math.log(2.0)])
    assert out["cov_xyvv"][0] == 16.0 and abs(out["log_range_sd"] - 0.2) < 1e-15
    assert all(out[k] == row[k] for k in ("range_m", "course_rad", "speed_mps", "x_m", "y_m"))
    src, dst = tmp_path / "e.ndjson", tmp_path / "c.ndjson"
    src.write_text(
        json.dumps({"record": "header", "weights_sha256": "w"})
        + "\n"
        + json.dumps({"record": "prediction", "ordinal": 7, "rows": [row]})
        + "\n"
    )
    n = write_calibrated(src, dst, {(7, 600.0): ([0.0], (0.0, 0.0))}, {"kind": "head"})
    assert n == 1
    lines = dst.read_text().splitlines()
    assert json.loads(lines[0])["calibration"] == {"kind": "head"}
    r = json.loads(lines[1])["rows"][0]
    assert r["cov_scale_log"] == [0] and r["range_m"] == row["range_m"]


def test_resume_is_deterministic(tmp_path: Path) -> None:
    """Two epochs in one job equal one epoch then a resumed one (fresh interpreters)."""
    code = f"""
import sys, numpy as np, torch
sys.path.insert(0, {str(Path(__file__).parent)!r})
from test_calib import _synthetic, CFG
from tma2.calib.train import train_head
from tma2.types.generated.tma import CalibrationHeadConfig
cfg = CalibrationHeadConfig.model_validate({{**CFG, "max_epochs": 4, "patience": 10}})
from pathlib import Path
tr, va = _synthetic(1500, 7), _synthetic(400, 8)
train_head(cfg, tr, va, Path(sys.argv[1]), {{}}, epochs=int(sys.argv[2]), log=lambda m: None)
"""
    run = [sys.executable, "-c", code]
    subprocess.run([*run, str(tmp_path / "a"), "2"], check=True)
    subprocess.run([*run, str(tmp_path / "b"), "1"], check=True)
    subprocess.run([*run, str(tmp_path / "b"), "1"], check=True)
    a = (tmp_path / "a" / "last.safetensors").read_bytes()
    b = (tmp_path / "b" / "last.safetensors").read_bytes()
    assert a == b


def test_export_features_match_the_cache() -> None:
    """The exported graph's head features (``gate2.export.log_sds``) are the cache's log sds
    (``physics.uncertainty.derived_sds``), so the exported head sees what it was trained on."""
    from tma2.gate2.export import log_sds
    from tma2.physics.uncertainty import derived_sds

    rng = np.random.default_rng(3)
    st = rng.normal(0, [5000, 5000, 4, 4], size=(20, 4))
    a = rng.normal(size=(20, 4, 4))
    cov = a @ a.transpose(0, 2, 1) + 0.1 * np.eye(4)
    own = rng.normal(0, 1000, size=(20, 2))
    lsd, ok = log_sds(torch.tensor(st), torch.tensor(cov), torch.tensor(own))
    got = lsd.numpy()
    assert bool(ok.all())
    want = np.log([derived_sds(st[i], cov[i], (own[i, 0], own[i, 1])) for i in range(20)])
    np.testing.assert_allclose(got, want, rtol=1e-12, atol=1e-14)


def test_local_rescale() -> None:
    """Equal scales give e^(2s) P; each local standard deviation moves by its own e^(s_i)."""
    from tma2.physics.uncertainty import derived_sds, local_rescale

    rng = np.random.default_rng(4)
    a = rng.normal(size=(4, 4))
    p = a @ a.T + np.diag([1e4, 1e4, 0.1, 0.1])
    st, own = np.array([8000.0, 3000.0, 3.0, -2.0]), (500.0, -200.0)
    np.testing.assert_allclose(local_rescale(st, p, own, np.full(4, 0.3)), np.exp(0.6) * p)
    s = np.array([0.2, -0.1, 0.5, 1.5])  # log range, bearing, speed, course
    lr, cr, sp = derived_sds(st, p, own)
    lr2, cr2, sp2 = derived_sds(st, local_rescale(st, p, own, s), own)
    np.testing.assert_allclose([lr2 / lr, sp2 / sp, cr2 / cr], np.exp(s[[0, 2, 3]]), rtol=1e-10)


def test_local_head_learns_per_coordinate_scales(tmp_path: Path) -> None:
    """Only the course coordinate's error is inflated (by e^1.5): the local head raises s_course
    alone."""
    torch.set_default_dtype(torch.float64)
    rng = np.random.default_rng(9)
    n = 6000
    d = _data(rng.normal(size=(n, 5)), np.ones(n), rng)
    d.u = rng.normal(size=(n, 4)) * np.array([1.0, 1.0, 1.0, math.exp(1.5)])
    d.q = (d.u**2).sum(axis=1)
    cfg = CalibrationHeadConfig.model_validate({**CFG, "form": "local", "bound": 3.0})
    va = d.select(np.arange(n) >= 5000)
    meta = train_head(
        cfg, d.select(np.arange(n) < 5000), va, tmp_path / "l", {}, log=lambda _m: None
    )
    head = CalHead(cfg, 5).double()
    from safetensors.torch import load_file

    head.load_state_dict(load_file(str(tmp_path / "l" / "best.safetensors")))
    s = predict_s(head, va.x).mean(axis=0)
    assert meta["best_val"] < meta["untrained_val"]
    assert abs(s[3] - 1.5) < 0.15 and np.all(np.abs(s[:3]) < 0.15), s
    temps = fit(
        TemperatureConfig.model_validate(
            {"slices": ["minute"], "beta": 0.5, "cap": 100.0, "form": "local"}
        ),
        d,
    )
    assert all(abs(v[3] - 1.5) < 0.15 for v in temps.values())


def test_export_local_rescale_matches_numpy() -> None:
    from tma2.gate2.export import local_rescale_t
    from tma2.physics.uncertainty import local_rescale

    rng = np.random.default_rng(5)
    st = rng.normal(0, [5000, 5000, 4, 4], size=(10, 4))
    a = rng.normal(size=(10, 4, 4))
    cov = a @ a.transpose(0, 2, 1) + np.diag([1e3, 1e3, 0.1, 0.1])
    own = rng.normal(0, 1000, size=(10, 2))
    s = rng.normal(0, 1, size=(10, 4))
    got = local_rescale_t(*(torch.tensor(v) for v in (st, cov, own, s))).numpy()
    for i in range(10):
        want = local_rescale(st[i], cov[i], (own[i, 0], own[i, 1]), s[i])
        np.testing.assert_allclose(got[i], want, rtol=1e-9, atol=1e-9 * np.abs(want).max())


def _g3_inputs(tmp_path: Path, cache_ords: list[int], file_ords: list[int]) -> list[str]:
    """A feature cache over ``cache_ords`` and an E prediction file over ``file_ords`` (one row
    each, the same state), a plan and a temperature; returns tma2-g3predict's common args."""
    from tma2.cli.g2predict import write_features
    from tma2.physics.uncertainty import pack_cov, row_fields

    st = np.array([8000.0, 3000.0, 3.0, -2.0])
    cov = np.diag([1e4, 2e4, 0.1, 0.2])
    own = (0.0, 0.0)
    fr = [
        {
            "ordinal": j, "k": 60, "t": 600.0, "h": np.zeros(3), "cov": cov, "state": st,
            "truth": st + 1, "own": own, "code_k": 0.0, "plausible": True, "cov_ok": True,
            "minute": 5, "open": False,
        }
        for j in cache_ords
    ]  # fmt: skip
    write_features(tmp_path / "c.npz", fr, {"weights_sha256": "w"})
    sp, cr = float(np.hypot(st[2], st[3])), float(np.arctan2(st[2], st[3]))
    row = {"timestamp_s": 600.0, "x_m": st[0], "y_m": st[1], "speed_mps": sp, "course_rad": cr}
    row |= {"range_m": 8544.0, **row_fields(st, cov, own)}
    assert row["cov_xyvv"] == pack_cov(cov)
    lines = [json.dumps({"record": "header", "weights_sha256": "w"})]
    lines += [json.dumps({"record": "prediction", "ordinal": j, "rows": [row]}) for j in file_ords]
    (tmp_path / "e.ndjson").write_text("\n".join(lines) + "\n")
    (tmp_path / "plan.json").write_text(json.dumps({"head": CFG, "models": {}}))
    temps = {"slices": ["minute"], "temperatures": {"minute=5": [0.5, 0.0, 0.2, 1.0]}}
    (tmp_path / "t.json").write_text(json.dumps(temps))
    args = ["--in", str(tmp_path / "e.ndjson"), "--features", str(tmp_path / "c.npz")]
    return [*args, "--plan", str(tmp_path / "plan.json"), "--temperature", str(tmp_path / "t.json")]


def test_g3predict_scenario_coverage(tmp_path: Path, capsys: Any) -> None:
    """A cache wider than the file is narrowed (counted); a file scenario without cache rows is
    refused, so no row passes through raw under a calibrated header."""
    from tma2.cli.g3predict import main

    args = _g3_inputs(tmp_path, [1, 2, 3], [2, 3])
    assert main([*args, "--out", str(tmp_path / "o.ndjson")]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["rows_scaled"] == 2 and out["cache_rows_outside_file"] == 1
    r = json.loads((tmp_path / "o.ndjson").read_text().splitlines()[1])["rows"][0]
    assert r["cov_scale_log"] == [0.5, 0.0, 0.2, 1.0]
    assert (
        abs(
            r["course_sd_rad"]
            / json.loads((tmp_path / "e.ndjson").read_text().splitlines()[1])["rows"][0][
                "course_sd_rad"
            ]
            - math.exp(1.0)
        )
        < 1e-9
    )
    args = _g3_inputs(tmp_path, [1, 2], [2, 3])
    assert main([*args, "--out", str(tmp_path / "o2.ndjson")]) == 2
    assert not (tmp_path / "o2.ndjson").exists()
