"""Spec 010 (US2, US3): covariance and whitening, the whitened solve, ceilings, robust control."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from tma2.cli import hpredict
from tma2.cli.generate import load_condition
from tma2.cli.oracle import run_layer
from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.headroom.cov import ErrorModel, covariance, whitener
from tma2.headroom.estimators import (
    RobustSettings,
    Truth,
    estimate,
    mixture_inflation,
    robust_model,
    settings_from,
    used,
)
from tma2.headroom.gls import WhitenedLayer, solve
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment.score import g5_rows, iter_selected
from tma2.segment.score import oracle as oracle_inputs
from tma2.sim import mismatch as mm

ROOT = Path(__file__).resolve().parents[2]
RANGES = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())
HELDOUT = json.loads((ROOT / "configs" / "man2-heldout.json").read_text())
CONDITIONS = str(ROOT / "configs" / "gateh" / "conditions.json")
PLAN = str(ROOT / "configs" / "gateh" / "gh-draft.json")


@pytest.fixture(scope="module")
def splits(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    out = {}
    for cid in ("off", "all-central"):
        d = tmp_path_factory.mktemp(cid)
        generate_dataset(
            GenerateOptions(
                seed=np.uint64(320),
                count=30,
                out_dir=d,
                ranges=RANGES,
                heldout_ranges=HELDOUT,
                format="f32pack",
                created_by="test",
                generator_git_commit="0" * 40,
                generator_git_dirty=False,
                mismatch=load_condition(f"{CONDITIONS}#{cid}"),
            )
        )
        out[cid] = d
    return out


def _items(pack: Path, n: int) -> tuple[list[Any], list[dict[str, Any]]]:
    torch.set_default_dtype(torch.float64)
    items, metas = [], []
    for j, m, own, _tgt, obs in iter_selected(pack, 0, n):
        d = bearing_data_from_arrays(m, own, obs)
        for k in g5_rows(m, d.n)[:2]:
            inp = oracle_inputs(j, m, d, k)
            if inp is not None:
                items.append((d, k, inp))
                metas.append(m)
    return items, metas


def test_covariance_and_whitener() -> None:
    t = np.array([0.0, 10.0, 20.0, 40.0, 50.0, 60.0])
    model = ErrorModel(0.01, 0.012, 60.0, 0.005, 1800.0)
    extra = np.array([0.0, 0.0, 0.03**2, 0.0, 0.0, 0.0])
    cov = covariance(t, model, extra)
    assert cov[0, 0] == pytest.approx(model.marginal_var)
    assert cov[2, 2] == pytest.approx(model.marginal_var + 0.03**2)
    want = 0.012**2 * math.exp(-40 / 60) + 0.005**2 * math.exp(-40 / 1800)
    assert cov[0, 3] == pytest.approx(want)
    use = np.array([True, True, False, True, True, True, False])
    tt = np.append(t, 70.0)
    w = whitener(tt, use, model, np.append(extra, 0.0))
    idx = np.flatnonzero(use)
    sub = w[np.ix_(idx, idx)]
    assert np.allclose(
        sub @ covariance(tt[idx], model, np.append(extra, 0.0)[idx]) @ sub.T, np.eye(5)
    )
    assert not w[2].any() and not w[:, 2].any() and not w[6].any()
    white = whitener(tt, use, ErrorModel(0.02))
    assert np.allclose(np.diag(white), use / 0.02) and np.count_nonzero(white) == 5


def test_whitened_solve_is_the_layer_when_white(splits: dict[str, Path]) -> None:
    items, _ = _items(splits["off"] / "train.f32pack", 4)
    r_max = max(d.n for d, _, _ in items)
    base = run_layer(PhysicsLayer(knots=12), items, r_max)
    ws = [whitener(d.t, used(d, k, i), ErrorModel(d.sigma)) for d, k, i in items]
    got, raw = solve(WhitenedLayer(knots=12), items, ws, r_max)
    assert np.allclose(got.state.numpy(), base.state.numpy(), rtol=1e-6, atol=1e-2)
    assert np.allclose(got.cov.numpy(), base.cov.numpy(), rtol=1e-5, atol=1e-6)
    assert (got.plausible == base.plausible).all()
    d, k, _ = items[0]
    assert raw[0, k + 1 : d.n].max(initial=0.0) == 0.0  # nothing after the row
    assert 0.2 * d.sigma < raw[0, : k + 1][d.valid[: k + 1] > 0].std() < 3 * d.sigma


def test_estimators_refuse_the_wrong_inputs(splits: dict[str, Path]) -> None:
    items, _ = _items(splits["off"] / "train.f32pack", 1)
    layer = WhitenedLayer(knots=12)
    tr = [Truth(np.zeros(mm.E_LEN), np.zeros(items[0][0].n, dtype=bool))] * len(items)
    with pytest.raises(ValueError):
        estimate(layer, items, "attainable", 720)
    with pytest.raises(ValueError):
        estimate(layer, items, "robust", 720, tr)
    with pytest.raises(ValueError):
        estimate(layer, items, "nominal", 720, tr)
    with pytest.raises(ValueError):
        estimate(layer, items, "nope", 720)
    with pytest.raises(ValueError):
        settings_from({}, "nope")
    assert settings_from({"huber_k": 2.0}, "sigma") == RobustSettings(
        huber=False, sigma=True, whiten=False, huber_k=2.0
    )


def test_robust_with_nothing_estimated_is_the_nominal_solve(splits: dict[str, Path]) -> None:
    items, _ = _items(splits["all-central"] / "train.f32pack", 2)
    r_max = max(d.n for d, _, _ in items)
    layer = WhitenedLayer(knots=12)
    nominal, _ = estimate(layer, items, "nominal", r_max)
    never = RobustSettings(min_bearings=10_000)
    got, _ = estimate(layer, items, "robust", r_max, None, never)
    assert np.array_equal(got.state.numpy(), nominal.state.numpy())
    moved, info = estimate(layer, items, "robust", r_max, None, RobustSettings())
    assert not np.array_equal(moved.state.numpy(), nominal.state.numpy())
    assert all(i["sigma_hat_rad"] > 0 for i in info)


def test_robust_model_recovers_a_known_process() -> None:
    rng = np.random.default_rng(7)
    n, dt, sd, share, tau = 600, 10.0, 0.02, 0.5, 60.0
    phi = math.exp(-dt / tau)
    z = np.zeros(n)
    z[0] = rng.standard_normal()
    for i in range(1, n):
        z[i] = phi * z[i - 1] + math.sqrt(1 - phi * phi) * rng.standard_normal()
    raw = sd * (math.sqrt(1 - share) * rng.standard_normal(n) + math.sqrt(share) * z)
    raw[::40] += 0.3
    ok = np.ones(n, dtype=bool)
    model, extra = robust_model(raw, ok, dt, 0.0175, RobustSettings())
    assert math.sqrt(model.marginal_var) == pytest.approx(sd, rel=0.25)
    assert model.sigma_c > 0 and 10.0 < model.tau_c < 600.0  # moments of two lags: crude
    assert (extra[::40] > 5 * model.marginal_var).all() and np.median(extra) == 0.0
    short, e2 = robust_model(raw[:30], ok[:30], dt, 0.0175, RobustSettings())
    assert short == ErrorModel(0.0175) and not e2.any()
    white = sd * rng.standard_normal(n)
    m3, _ = robust_model(white, ok, dt, 0.0175, RobustSettings(huber=False))
    assert m3.sigma_c == 0.0 or m3.sigma_c**2 / m3.marginal_var < 0.3


def test_mixture_inflation() -> None:
    s2, out = 0.02**2, 0.2**2
    v = mixture_inflation(np.array([0.0, 0.02, 0.2, 0.5]), s2, 0.02, out)
    assert v[0] < 0.05 * s2 and v[1] < 0.2 * s2
    assert v[2] > 0.9 * out and v[3] == pytest.approx(out, rel=1e-3)
    assert not mixture_inflation(np.array([0.5]), s2, 0.0, out).any()


def _run(args: list[str]) -> int:
    return hpredict.main([*args, "--workers", "1"])


def _rows(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text().splitlines()
    return [json.loads(x) for x in lines[1:]]


def test_cli_ceilings_and_refusals(splits: dict[str, Path], tmp_path: Path) -> None:
    off = str(splits["off"] / "train.f32pack")
    on = str(splits["all-central"] / "train.f32pack")
    truth = str(splits["all-central"] / "train.mismatch.npz")
    base = ["--start", "0", "--count", "3", "--out"]
    # FR-013: with no mismatch both ceilings are the plain oracle solve.
    assert _run(["--in", off, "--kind", "attainable", *base, str(tmp_path / "a.ndjson")]) == 0
    assert _run(["--in", off, "--kind", "realisation", *base, str(tmp_path / "r.ndjson")]) == 0
    assert _run(["--in", off, "--kind", "nominal", *base, str(tmp_path / "n.ndjson")]) == 0
    a, r, n = (_rows(tmp_path / f"{x}.ndjson") for x in "arn")
    assert a == [{**x, "estimator": "attainable@truth"} for x in r]
    items, _ = _items(splits["off"] / "train.f32pack", 3)
    assert len(a) == 3 and a[0]["rows"][0]["converged"]
    for x, y in zip(a, n, strict=True):  # the whitened path agrees with the plain one
        for p, q in zip(x["rows"], y["rows"], strict=True):
            assert p["range_m"] == pytest.approx(q["range_m"], rel=1e-6)
    # Refusals (FR-005, contracts/cli.md).
    out = str(tmp_path / "x.ndjson")
    assert _run(["--in", on, "--kind", "attainable", *base, out]) == 2
    assert (
        _run(
            ["--in", on, "--kind", "robust", "--plan", PLAN, "--mismatch-truth", truth, *base, out]
        )
        == 2
    )
    assert _run(["--in", on, "--kind", "nominal", "--mismatch-truth", truth, *base, out]) == 2
    assert _run(["--in", off, "--kind", "attainable", "--mismatch-truth", truth, *base, out]) == 2
    assert _run(["--in", on, "--kind", "robust", *base, out]) == 2
    other = str(splits["all-central"] / "validation.mismatch.npz")
    assert _run(["--in", on, "--kind", "attainable", "--mismatch-truth", other, *base, out]) == 2
    assert not Path(out).exists()
    # With the truth, the two ceilings run and differ (the flags are worth something).
    assert _run(["--in", on, "--kind", "realisation", "--mismatch-truth", truth, *base, out]) == 0
    hdr = json.loads(Path(out).read_text().splitlines()[0])
    assert hdr["condition"] == "all-central" and len(hdr["truth_sha256"]) == 64
    rob = str(tmp_path / "rob.ndjson")
    assert (
        _run(["--in", on, "--kind", "robust", "--plan", PLAN, "--only", "huber", *base, rob]) == 0
    )
    h2 = json.loads(Path(rob).read_text().splitlines()[0])
    assert h2["estimator"] == "robust-huber@truth" and "truth_sha256" not in h2
    assert json.loads(h2["settings"])["whiten"] is False


def test_bound_under_a_white_covariance_is_the_reference_bound(splits: dict[str, Path]) -> None:
    from tma2.headroom.crb import crb_rows_cov
    from tma2.references.crb import crb_rows

    for _j, m, own, tgt, obs in iter_selected(splits["off"] / "train.f32pack", 0, 2):
        rows = g5_rows(m, own.shape[0])
        plan = m["parameters"].get("target_manoeuvres") or []
        sigma = float(m["parameters"]["noise_sigma_rad"])
        ref = crb_rows(
            own,
            tgt,
            obs,
            sigma,
            int(m["zig_index"]),
            m.get("manoeuvres") or [],
            rows,
            model="known_manoeuvres",
            target_manoeuvres=plan,
        )
        got = crb_rows_cov(own, tgt, obs, plan, rows, ErrorModel(sigma))
        wider = crb_rows_cov(own, tgt, obs, plan, rows, ErrorModel(sigma * 0.7, sigma * 0.7, 60.0))
        for a, b, c in zip(ref, got, wider, strict=True):
            assert a.singular == b.singular
            if not a.singular:
                assert b.sd_range_rel == pytest.approx(a.sd_range_rel, rel=1e-6)
                assert b.sd_speed_kt == pytest.approx(a.sd_speed_kt, rel=1e-6)
                # same marginal sd, half of it correlated: less information
                assert c.sd_range_rel > 0.9 * a.sd_range_rel


def test_headroom_statistics() -> None:
    from tma2.headroom import gate

    rng = np.random.default_rng(3)
    n = 400
    cluster = np.repeat(np.arange(n // 4), 4)
    minute = np.tile(np.array([5, 10, 15, 20]), n // 4)
    base = np.abs(rng.standard_normal((n, 3))) * 0.05
    errs = {
        "attainable@truth": base,
        "realisation@truth": base * 0.95,
        "robust@truth": base * 1.25,
        "nominal@truth": base * 1.5,
    }
    errs["nominal@truth"][:8] = np.inf
    true_range = np.full(n, 10_000.0)
    settled = np.ones(n, dtype=bool)
    res = gate.headroom(errs, cluster, settled, true_range, minute, base / 0.6745, 200)
    r = res["R"]["range"]
    assert r["value"] == pytest.approx(0.25) and r["lo"] <= 0.25 <= r["hi"]
    assert res["R_nominal"]["range"]["value"] > 0.4
    assert res["closed_by_robust"]["range"]["value"] == pytest.approx(0.5, abs=0.05)
    assert res["rows_all_answer"] == n - 8 and res["R_all_answer"]["rows"] == n - 8
    assert res["estimators"]["attainable@truth"]["efficiency_settled_range"] == pytest.approx(
        1.0, abs=1e-3
    )
    op = res["operational"]["attainable@truth"]
    assert op["median_range_m"] == pytest.approx(10_000.0 * np.median(base[:, 0]), rel=0.02)
    assert 0.0 <= op["settled_by_5min"] <= op["settled_by_20min"] <= 1.0
    assert gate.verdict(res, 0.10)["H-c"]["verdict"] == "material"
    assert gate.verdict(res, 0.50)["H-c"]["verdict"] == "not_material"
    assert gate.verdict(res, 0.25)["H-c"]["verdict"] == "inconclusive"
    off = {"robust_over_nominal": {"range": {"value": 0.005, "lo": -0.01, "hi": 0.015}}}
    snd = gate.soundness(res, off, (0.8, 1.3), 1.02)
    assert snd["H-a"]["pass"] and snd["H-b"]["pass"]
    off["robust_over_nominal"]["range"]["hi"] = 0.03
    assert not gate.soundness(res, off, (0.8, 1.3), 1.02)["H-b"]["pass"]


def test_scorer_cli(splits: dict[str, Path], tmp_path: Path) -> None:
    from tma2.cli import gh

    on = str(splits["all-central"] / "train.f32pack")
    truth = str(splits["all-central"] / "train.mismatch.npz")
    base = ["--start", "0", "--count", "3", "--out"]
    files = []
    for kind in ("nominal", "attainable"):
        f = str(tmp_path / f"{kind}.ndjson")
        extra = ["--mismatch-truth", truth] if kind == "attainable" else []
        assert _run(["--in", on, "--kind", kind, *extra, *base, f]) == 0
        files.append(f)
    out = tmp_path / "score"
    args = ["--truth", on, "--start", "0", "--count", "3", "--resamples", "50"]
    assert (
        gh.main([*args, "--predictions", *files, "--mismatch-truth", truth, "--out", str(out)]) == 0
    )
    res = json.loads((out / "headroom.json").read_text())
    assert res["condition"] == "all-central" and res["bound"] == "true_covariance"
    assert set(res["estimators"]) == {"one_leg", "oracle", "nominal@truth", "attainable@truth"}
    # the plain oracle solved in the scoring run is the nominal estimator's file
    a = res["estimators"]["oracle"]["median_range"]
    assert res["estimators"]["nominal@truth"]["median_range"] == pytest.approx(a, rel=1e-6)
    assert "R_nominal" in res and "R" not in res
    z = np.load(out / "errors.npz")
    assert z["err_oracle"].shape == (res["rows"], 3) and z["bound"].shape == (res["rows"], 3)
    # refusals: a gate split needs the decision record; another split's predictions are refused
    assert (
        gh.main([*args, "--split", "validation", "--predictions", *files, "--out", str(out)]) == 2
    )
    off = str(splits["off"] / "train.f32pack")
    assert gh.main(["--truth", off, *args[2:], "--predictions", *files, "--out", str(out)]) == 2
