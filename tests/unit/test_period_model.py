"""Spec 016: the learned whole-period model. The period stream and its mix, the non-causal
model, training, the read-outs and the export check."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.features.batch import generate_indices
from tma2.regress import period_data as pdata
from tma2.regress.model import PERIOD_FIELDS, Regressor, RegressorConfig
from tma2.regress.period_predict import export_check, predict_periods, run_model
from tma2.regress.train import config_digest, period_loss
from tma2.sim import mismatch as mm
from tma2.sim.prng import derive_seed
from tma2.timelate import periods as tlp
from tma2.timelate.learned import (
    arc_readout,
    direct_track,
    spans_from_logit,
    token_times,
)
from tma2.timelate.score import row_errors, truth_rows

ROOT = Path(__file__).resolve().parents[2]
MIX = str(ROOT / "configs/regress/tlm-mix.json")
PERIODS = dict(
    patch_rows=6, max_rows=1440, causal=False, manoeuvre_head=True, n_features=9,
    data="periods", mix=MIX, stream_seed=339, val_seed=339,
)  # fmt: skip
TOY = dict(layers=2, width=32, heads=2, feedforward=64, batch_scenarios=8, precision="float32")


def _cfg(**kw: object) -> RegressorConfig:
    return RegressorConfig(**{**TOY, **PERIODS, **kw})  # type: ignore[arg-type]


def _model(cfg: RegressorConfig, seed: int = 0) -> Regressor:
    """A model with non-zero heads (they start at zero)."""
    torch.manual_seed(seed)
    m = Regressor(cfg).eval()
    torch.nn.init.normal_(m.head.weight, std=0.1)
    torch.nn.init.normal_(m.man_head.weight, std=0.5)
    return m


def _period(index: int, ranges: dict[str, Any], first: int, rows: int) -> tlp.Period:
    """Engagement ``index`` of stream seed 339 as the file path would give it (through
    ``features.batch``, not the stream's own kernel call), as a stored period."""
    b = generate_indices(339, np.array([index], dtype=np.int64), ranges)
    n = int(b.samples[0])
    t = b.t[0, :n].astype(np.float64)
    own = np.column_stack([t, b.own[0, :n].astype(np.float64)])
    tgt = np.column_stack([t, b.tgt[0, :n].astype(np.float64)])
    obs = np.column_stack([t, b.bearing[0, :n], b.valid[0, :n]]).astype(np.float64)
    meta = {
        "parameters": {"noise_sigma_rad": float(b.sigma[0]), "dt_s": 5.0},
        "manoeuvres": [
            {"kind": "course", "start_index": int(s), "end_index": int(e)}
            for _k, s, e in b.spans[0]
            if s >= 0
        ],
    }
    return tlp.Period(index, meta, own, tgt, obs, first, rows, 5.0)


def test_stream_is_a_pure_function_of_config_and_update() -> None:
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    a, b, c = pdata.batch_at(cfg, mix, 3), pdata.batch_at(cfg, mix, 3), pdata.batch_at(cfg, mix, 4)
    for k in pdata.FIELDS:
        assert np.array_equal(getattr(a, k), getattr(b, k), equal_nan=True)
    assert a.index.tolist() == list(range(24, 32)) and c.index[0] == 32
    assert not np.array_equal(a.f, c.f)
    assert a.f.shape == (8, 1440, 9) and a.y.shape == (8, 1440, 3)
    # rows beyond the period carry nothing; the period is at least 20 minutes
    assert not a.f[~a.mask].any() and not a.y[~a.mask].any() and not a.man[~a.mask].any()
    assert (a.rows >= 240).all() and (a.mask.sum(axis=1) == a.rows).all()
    # time from the period's start and its length, ÷ 7,200 s
    assert np.allclose(a.f[0, : a.rows[0], 7], np.arange(a.rows[0]) * 5.0 / 7200.0)
    assert np.allclose(a.f[0, : a.rows[0], 8], a.rows[0] * 5.0 / 7200.0)
    mon = pdata.monitor(_cfg(val_count=4), mix)
    assert mon.index.tolist() == [(1 << 40) + i for i in range(4)]


def test_mix_proportions_and_what_is_never_in_training() -> None:
    """Over 2,000 engagements the families and overlays are within sampling error (4 sd) of
    the declared shares; bias and the sigma factor never appear."""
    mix = pdata.load_mix(MIX)
    n = 2000
    _seeds, u = pdata._draws(np.uint64(339), np.arange(n, dtype=np.int64))
    family, overlay, R, M = pdata.assign(mix, u)

    def close(count: int, p: float, of: int) -> bool:
        return bool(abs(count - p * of) <= 4.0 * np.sqrt(p * (1 - p) * of))

    for i, name in enumerate(pdata.FAMILIES):
        assert close(int((family == i).sum()), mix.raw["families"][name], n), name
    with_overlay = int((overlay > 0).sum())
    assert close(with_overlay, 0.25, n)
    for i in (1, 2, 3):
        assert close(int((overlay == i).sum()), 1 / 3, with_overlay)
    # the overlay is drawn independently of the family
    assert close(int(((overlay > 0) & (family == 0)).sum()), 0.25, int((family == 0).sum()))
    assert np.isnan(M[:, [mm.M_BIAS_SD, mm.M_BIAS_TAU, mm.M_SIGMA_K]]).all()
    corr, out = np.isin(overlay, (1, 3)), np.isin(overlay, (2, 3))
    assert np.isnan(M[~corr][:, [mm.M_CORR_TAU, mm.M_CORR_SHARE]]).all()
    assert np.isnan(M[~out][:, [mm.M_OUT_RATE, mm.M_OUT_SPREAD]]).all()
    for col, lo, hi, on in (
        (mm.M_CORR_TAU, 20.0, 240.0, corr),
        (mm.M_CORR_SHARE, 0.2, 0.7, corr),
        (mm.M_OUT_RATE, 0.0, 0.06, out),
        (mm.M_OUT_SPREAD, 5.0, 15.0, out),
    ):
        assert (M[on, col] >= lo).all() and (M[on, col] <= hi).all()
        assert np.ptp(M[on, col]) > 0.8 * (hi - lo)
    # families read their own ranges: quiet legs never end, randomised ones are their own
    from tma2.sim import ranges as rg

    for i, row in ((0, mix.R_base), (2, mix.R_quiet)):
        own = R[family == i]
        assert np.array_equal(own, np.tile(row, (own.shape[0], 1)), equal_nan=True)
    means = R[family == 1, rg.R_LEG_MEAN]
    assert means.min() >= 600 and means.max() <= 2400 and np.unique(means).size == means.size
    assert np.allclose(R[family == 1, rg.R_LEG_SD], 0.3 * means)
    assert (R[family == 1, rg.R_LEG_MIN] == 300).all()
    k = R[family == 1, rg.R_TM_RATE_MAX] / mix.R_base[rg.R_TM_RATE_MAX]
    assert k.min() >= 0.5 and k.max() <= 1.5
    assert (R[family == 1, rg.R_TM_ANGLE_MAX] <= np.pi).all()


def test_every_family_generates_and_overlays_change_only_bearings() -> None:
    """The kernel accepts every engagement's own ranges (256 engagements, about 50 of them
    randomised); an overlaid engagement differs from the same one without it in its bearings
    only."""
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    idx = np.arange(5000, 5256, dtype=np.int64)
    x = pdata.periods_at(cfg, mix, idx)
    assert np.isfinite(x.f).all() and np.isfinite(x.y).all()
    assert set(x.family.tolist()) == {0, 1, 2} and set(x.overlay.tolist()) == {0, 1, 2, 3}
    # quiet legs last about 10^6 s, so a change falls inside a window in under 1% of them
    busy = x.man.any(axis=1)
    assert busy[x.family == 2].mean() < 0.1 and busy[x.family == 0].mean() > 0.5
    raw = dict(mix.raw, overlay={**mix.raw["overlay"], "fraction": 0.0})
    plain = pdata.periods_at(cfg, pdata.Mix(raw, mix.base, mix.R_base, mix.R_quiet, 1440, 5.0), idx)
    # the truth is the same; only the frame (the first bearing) and the bearings move
    assert np.array_equal(plain.rows, x.rows) and np.array_equal(plain.man, x.man)
    assert np.array_equal(plain.y[..., 0], x.y[..., 0])
    assert np.allclose(np.hypot(*plain.y[..., 1:].T), np.hypot(*x.y[..., 1:].T), atol=1e-6)
    assert np.allclose(np.hypot(*plain.f[..., 2:4].T), np.hypot(*x.f[..., 2:4].T), atol=1e-5)
    same = (plain.f == x.f).all(axis=(1, 2))
    assert same[x.overlay == 0].all() and not same[x.overlay > 0].any()


def test_a_periods_cut_is_gate_ts_cut() -> None:
    """The stream's cut is ``timelate.periods.cut`` (the stream repeats it to keep the scorers
    out of the GPU image), and an Annex B engagement without overlay is, row for row, the
    period the file path gives: features (what ``tma2-tlpredict`` builds), targets, labels."""
    rng = np.random.default_rng(1)
    seeds = rng.integers(0, 2**63, 2000, dtype=np.int64).astype(np.uint64)
    samples = rng.integers(200, 1441, 2000)
    first, rows = pdata._cuts(seeds, samples, 240)
    for s, n, a, r in zip(seeds, samples, first, rows, strict=True):
        assert tlp.cut(s, int(n), 5.0) == (int(a), int(r))
    assert pdata.CUT_STREAM == tlp.CUT_STREAM and pdata.MIN_SECONDS == tlp.MIN_SECONDS

    cfg, mix = _cfg(), pdata.load_mix(MIX)
    x = pdata.batch_at(cfg, mix, 0)
    plain = np.flatnonzero((x.family == 0) & (x.overlay == 0))
    assert plain.size >= 2
    for b in plain[:3]:
        p = _period(int(x.index[b]), mix.base, int(x.first[b]), int(x.rows[b]))
        seed = np.uint64(derive_seed(np.uint64(339), int(x.index[b])))
        assert tlp.cut(seed, p.own.shape[0], 5.0) == (p.first, p.rows)
        f, mask, _th = pdata.inputs_of([p], 1440)
        assert np.array_equal(mask[0], x.mask[b])
        assert np.allclose(f[0], x.f[b], atol=1e-6)
        label = np.zeros(1440, dtype=bool)
        for s in p.spans():
            label[s["start_index"] : s["end_index"] + 1] = True
        assert np.array_equal(label, x.man[b])
        tr = truth_rows(p)
        rng_true = np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])
        assert np.allclose(x.y[b, : p.rows, 0], np.log(rng_true / 1e4), atol=1e-5)
        assert np.allclose(10.0 * np.hypot(*x.y[b, : p.rows, 1:].T), tr[:, 3], atol=1e-4)


def test_token_targets() -> None:
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    x = pdata.batch_at(cfg, mix, 1)
    y, label, exists, last = pdata.token_targets(x, 6)
    assert y.shape == (8, 240, 3) and label.shape == exists.shape == (8, 240)
    for b in range(8):
        t = -(-int(x.rows[b]) // 6)
        assert exists[b].sum() == t and last[b, t - 1] == x.rows[b] - 1
        assert np.array_equal(y[b, :t], x.y[b, last[b, :t]]) and not y[b, t:].any()
        assert np.array_equal(label[b] > 0, x.man[b].reshape(240, 6).any(axis=1))


def test_non_causal_output_does_not_depend_on_padding() -> None:
    """The same period padded to 240 tokens and to its own tokens gives the same output; every
    token reads later rows (non-causal); without the row mask the padding would be read."""
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    prev = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)  # as left by the physics layer's tests and CLIs
    try:
        m = _model(cfg)
    finally:
        torch.set_default_dtype(prev)
    x = pdata.batch_at(cfg, mix, 0)
    b = int(np.argmin(x.rows))
    t = -(-int(x.rows[b]) // 6)
    assert t < 200
    full = run_model(m, x.f[b : b + 1], x.mask[b : b + 1])
    short = run_model(m, x.f[b : b + 1, : 6 * t], x.mask[b : b + 1, : 6 * t])
    batch = run_model(m, x.f, x.mask)
    for a, s, c in zip(full, short, batch, strict=True):
        assert a.dtype == np.float32
        assert np.abs(a[0, :t] - s[0, :t]).max() < 1e-5
        assert np.abs(a[0, :t] - c[b, :t]).max() < 1e-5
    with torch.no_grad():
        unmasked, _ = m(torch.from_numpy(x.f[b : b + 1]))
    assert np.abs(unmasked.numpy()[0, :t] - full[0][0, :t]).max() > 1e-4
    g = x.f[b : b + 1].copy()
    g[:, 6 * (t - 1) : 6 * t] += 1.0  # the last token's rows change the first token's output
    assert np.abs(run_model(m, g, x.mask[b : b + 1])[0][0, 0] - full[0][0, 0]).max() > 1e-6
    # the two-tensor forward of spec 012's callers is unchanged in form
    with torch.no_grad():
        two = m(torch.from_numpy(x.f[b : b + 1]), 0, torch.from_numpy(x.mask[b : b + 1]))
    assert len(two) == 2 and np.allclose(two[0].numpy(), full[0], atol=1e-6)


def test_loss_has_both_terms_over_existing_tokens() -> None:
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    m = _model(cfg)
    x = pdata.batch_at(cfg, mix, 2)
    loss, parts = period_loss(m, x, torch.device("cpu"), False)
    assert torch.isfinite(loss)
    assert torch.allclose(loss, parts["state"] + cfg.manoeuvre_weight * parts["manoeuvre"])
    assert parts["w"].sum().item() == sum(-(-int(r) // 6) for r in x.rows)
    # padding does not enter: the same periods with the features beyond them disturbed
    y = pdata.PeriodTensors(*(getattr(x, k).copy() for k in pdata.FIELDS))
    tokens = -(-y.rows // 6)
    y.f[np.arange(1440)[None, :] >= 6 * tokens[:, None]] = 3.0  # rows of tokens that do not exist
    assert torch.allclose(period_loss(m, y, torch.device("cpu"), False)[0], loss, atol=1e-5)


def _run(cfg: Path, out: Path, *extra: str) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "tma2.cli.rtrain", "--config", str(cfg), "--out", str(out)]
    subprocess.run([*cmd, *extra], check=True, cwd=ROOT, capture_output=True)
    rec: dict[str, Any] = json.loads((out / "run.json").read_text())
    return rec


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_toy_training_learns_is_deterministic_and_resumes(tmp_path: Path) -> None:
    """30 CPU updates lower both monitored loss terms' sum; two fresh interpreters give
    byte-identical checkpoints; a run stopped by its limit resumes on the same stream."""
    cfg = {**TOY, **PERIODS, "id": "t", "total_updates": 30, "warmup_updates": 5,
           "val_count": 16, "val_every_updates": 10, "learning_rate": 1e-3}  # fmt: skip
    p = tmp_path / "plan.json"
    p.write_text(json.dumps({"config": cfg}))  # rtrain reads a plan's config
    full = _run(p, tmp_path / "full")
    v = full["validation"]
    assert full["stopped"] == "complete" and len(v) == 3
    assert v[-1]["loss"] < v[0]["loss"] and v[-1]["state_loss"] < v[0]["state_loss"]
    assert v[-1]["manoeuvre_loss"] < 0.6931 and np.isfinite(v[-1]["ln_range_abs_median"])
    assert full["scenarios_seen"] == 240 and full["config"]["data"] == "periods"
    again = _run(p, tmp_path / "again")
    assert _sha(tmp_path / "full/checkpoint.safetensors") == _sha(
        tmp_path / "again/checkpoint.safetensors"
    )
    assert again["validation"][-1]["loss"] == v[-1]["loss"]
    part = _run(p, tmp_path / "a", "--limit-seconds", "0")
    assert part["stopped"] == "limit" and part["updates"] < 30
    done = _run(p, tmp_path / "b", "--resume", str(tmp_path / "a"))
    assert done["stopped"] == "complete" and done["updates"] == 30 and len(done["segments"]) == 2
    assert _sha(tmp_path / "b/checkpoint.safetensors") == full["checkpoint_sha256"]


def test_spec_012_configurations_keep_their_digests() -> None:
    """New fields at their defaults are absent from a configuration's JSON, so the digests
    bound in spec 012's records do not move (pinned from the code before spec 016)."""
    pinned = {
        "r-a-s1": "f47f5e557b789d0584b160052014f34376476bfa2d80039fcab413a133e8d337",
        "r-a-s2": "2d53e539abf74324fd5d495c92442b2c4f182e0fe838dc31fa7fc0d50a8dfc64",
        "r-a-s3": "a7423b3ab976837e00371dc3f3f4a2c478accabc45e2a810ddf5d1c9ba33ad0d",
        "r-a-tenth": "10e2ae4175e8a9c3ae10239a56140eb760b5dddc71832ee0cef921520a22cf26",
        "toy-plan": "f51cd0a1b1e9dcc025f54d6c3adfe58c78f2e90100dee29eeaa8d4c0aeda041e",
    }
    for name, digest in pinned.items():
        raw = json.loads((ROOT / "configs/regress" / f"{name}.json").read_text())
        cfg = RegressorConfig(**raw["config"])
        assert config_digest(cfg) == digest, name
        assert not set(cfg.to_json()) & set(PERIOD_FIELDS)
    period = _cfg().to_json()
    assert period["data"] == "periods" and period["causal"] is False
    assert "monitor_start" not in period and "manoeuvre_weight" not in period  # at defaults
    assert RegressorConfig(**period) == _cfg()


def test_committed_period_plans() -> None:
    """The pilot fits an hour on a T4 with its allowance; the three registered training plans
    differ in their seed only and each fits nine hours with allowances; every plan reads
    stream seed 339 and no other seed."""
    from tma2.regress.remote import plan_limit_seconds

    plans = {n: json.loads((ROOT / f"configs/regress/tlm-{n}.json").read_text())
             for n in ("toy", "pilot", "s1", "s2", "s3")}  # fmt: skip
    for name, plan in plans.items():
        cfg = RegressorConfig(**plan["config"])
        assert cfg.data == "periods" and not cfg.causal and cfg.manoeuvre_head, name
        assert cfg.stream_seed == cfg.val_seed == 339 and cfg.max_rows // cfg.patch_rows == 240
        assert cfg.monitor_start >= 1 << 40 and cfg.mix == "configs/regress/tlm-mix.json"
    assert plan_limit_seconds(plans["pilot"]) <= 3600 and plans["pilot"]["segments"] == 1
    pilot = RegressorConfig(**plans["pilot"]["config"])
    assert (pilot.layers, pilot.width, pilot.heads, pilot.feedforward) == (8, 256, 8, 1024)
    assert pilot.batch_scenarios == 256 and pilot.precision == "amp"
    for k in (1, 2, 3):
        plan = plans[f"s{k}"]
        cfg = RegressorConfig(**plan["config"])
        assert "draft" not in plan and cfg.total_updates == 49000 and cfg.seed == k
        assert plan["segments"] == 2 and plan_limit_seconds(plan) <= 9 * 3600
        arch = {f: getattr(cfg, f) for f in ("layers", "width", "heads", "feedforward", "mix")}
        assert arch == {f: getattr(pilot, f) for f in arch}
    try:
        RegressorConfig(**{**plans["toy"]["config"], "val_seed": 340})
    except ValueError:
        pass
    else:
        raise AssertionError("a period configuration must not name another seed")


def test_spans_from_logit() -> None:
    tt = token_times(600, 5.0, 6)  # 100 tokens of 30 s
    assert tt.shape == (100, 2) and tt[0].tolist() == [0.0, 25.0] and tt[1].tolist() == [25.0, 55.0]
    assert token_times(601, 5.0, 6)[-1].tolist() == [2995.0, 3000.0]
    p = np.zeros(100)
    assert spans_from_logit(p, tt).shape == (0, 2)
    p[10:13] = 0.9  # one run: tokens 10..12
    assert spans_from_logit(p, tt).tolist() == [[295.0, 385.0]]
    p[14] = 0.8  # 30 s after the run's end: merged within 60 s
    assert spans_from_logit(p, tt).tolist() == [[295.0, 445.0]]
    assert spans_from_logit(p, tt, merge_s=10.0).tolist() == [[295.0, 385.0], [415.0, 445.0]]
    p[40] = 0.51
    p[60:62] = 0.7
    assert spans_from_logit(p, tt).shape == (3, 2)
    # at most two: the weakest run (token 40) goes; order kept
    two = spans_from_logit(p, tt, max_manoeuvres=2)
    assert two.tolist() == [[295.0, 445.0], [1795.0, 1855.0]]
    assert spans_from_logit(p, tt, threshold=0.75).tolist() == [[295.0, 445.0]]
    # a one-row last token is extended back to the arc fit's shortest manoeuvre
    q = np.zeros(101)
    q[100] = 0.9
    assert spans_from_logit(q, token_times(601, 5.0, 6)).tolist() == [[2990.0, 3000.0]]
    s = spans_from_logit(np.ones(100), tt)
    assert s.tolist() == [[0.0, 2995.0]]
    for sp in (two, s):
        assert (sp[:, 1] - sp[:, 0] >= 10.0).all() and (sp[1:, 0] >= sp[:-1, 1]).all()


def test_direct_track_reproduces_the_truth_from_exact_targets() -> None:
    """Fed the exact per-token targets, the direct track is the true track to interpolation
    error: range and velocity whatever the bearings, position where the bearings are clean."""
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    x = pdata.batch_at(cfg, mix, 0)
    y, _label, _exists, _last = pdata.token_targets(x, 6)
    plain = np.flatnonzero((x.family == 0) & (x.overlay == 0) & x.man.any(axis=1))
    for b in plain[:2]:
        p = _period(int(x.index[b]), mix.base, int(x.first[b]), int(x.rows[b]))
        t = -(-p.rows // 6)
        tr = truth_rows(p)
        st = direct_track(y[b, :t], p, 6)
        assert st.shape == (p.rows, 4)
        e = row_errors(st, tr)
        assert e[:, 0].max() < 0.01 and np.median(e[:, 0]) < 1e-4  # relative range
        assert np.median(e[:, 2]) < 0.01 and e[:, 2].max() < 2.0  # speed, kt
        assert np.median(e[:, 1]) < 0.05  # course, degrees (larger inside a turn)
        clean = tlp.Period(p.ordinal, p.meta, p.own, p.tgt, p.obs.copy(), p.first, p.rows, 5.0)
        clean.obs[:, 1] = np.arctan2(p.tgt[:, 1] - p.own[:, 1], p.tgt[:, 2] - p.own[:, 2])
        clean.obs[:, 2] = 1.0
        rng_true = np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])
        pos = row_errors(direct_track(y[b, :t], clean, 6), tr)[:, 3]
        assert (pos / rng_true).max() < 0.01
        # with the measured bearings the position is off by the bearing error across the range
        assert np.median(e[:, 3] / rng_true) < np.radians(1.0)
    dead = tlp.Period(0, p.meta, p.own, p.tgt, p.obs * 0.0, p.first, p.rows, 5.0)
    assert np.isnan(direct_track(y[b, :t], dead, 6)).all()


def test_arc_readout_is_the_refit_control_on_the_models_spans_and_track() -> None:
    """On a held-course period the read-out, started from a track near the truth with no
    spans, returns the arc fit: a straight track that fits the bearings."""
    from tma2.timelate.prior import ManoeuvrePrior

    cfg, mix = _cfg(), pdata.load_mix(MIX)
    x = pdata.periods_at(cfg, mix, np.arange(40, dtype=np.int64))
    b = int(np.flatnonzero((x.family == 2) & (x.overlay == 0))[0])
    quiet = json.loads((ROOT / mix.raw["quiet_ranges"]).read_text())
    p = _period(int(x.index[b]), quiet, int(x.first[b]), int(x.rows[b]))
    y, *_ = pdata.token_targets(x, 6)
    st = direct_track(y[b, : -(-p.rows // 6)], p, 6)
    a, e = p.first, p.first + p.rows
    pb = (
        p.own[a:e, 0] - p.own[a, 0],
        p.own[a:e, 1],
        p.own[a:e, 2],
        p.obs[a:e, 1],
        p.obs[a:e, 2] != 0,
        float(p.meta["parameters"]["noise_sigma_rad"]),
    )
    prior = ManoeuvrePrior.from_ranges(mix.base, 3, "annex-b")
    fit, kinds, ev = arc_readout(pb, st, np.zeros((0, 2)), prior)
    assert fit.spans.shape == (0, 2) and kinds.shape == (0, 2) and np.isfinite(ev["total"])
    assert fit.states.shape == (p.rows, 4) and np.ptp(fit.states[:, 2:], axis=0).max() < 1e-9
    assert fit.cost < 2.0 * int(pb[4].sum())  # χ² near the number of bearings
    try:
        arc_readout(pb, np.full_like(st, np.nan), np.zeros((0, 2)), prior)
    except ValueError:
        pass
    else:
        raise AssertionError("a track with no state and no other start must be refused")


def test_export_agrees_with_the_trained_model(tmp_path: Path) -> None:
    """FR-015: the ONNX export, run by onnxruntime on CPU, agrees with the torch model on the
    tokens that exist, at a batch size other than the one it was traced with."""
    cfg, mix = _cfg(), pdata.load_mix(MIX)
    m = _model(cfg, 3)
    x = pdata.batch_at(cfg, mix, 5)
    prev = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)  # as left by the physics layer's tests and CLIs
    try:
        assert export_check(m, tmp_path / "model.onnx", x.f[:5], x.mask[:5]) < 1e-5
    finally:
        torch.set_default_dtype(prev)
    assert all(p.requires_grad for p in m.parameters())  # the export leaves the model as it was


def test_tlpredict_writes_tracks_without_errors_or_truth(man2_pack: Path, tmp_path: Path) -> None:
    """The shard holds, per period ``tma2-tlsolve`` would cut, the direct track at every row,
    the manoeuvre probabilities and the spans; the header binds weights, config and data."""
    from safetensors.torch import save_file

    from tma2.cli.tlpredict import main

    cfg = _cfg()
    m = _model(cfg, 4)
    w = tmp_path / "checkpoint.safetensors"
    save_file({k: v.contiguous() for k, v in m.state_dict().items()}, str(w))
    c = tmp_path / "plan.json"
    c.write_text(json.dumps({"config": cfg.to_json()}))
    out = tmp_path / "shard"
    args = ["--weights", str(w), "--config", str(c), "--in", str(man2_pack), "--out", str(out)]
    assert main([*args, "--start", "1", "--count", "3", "--split", "annex-b"]) == 0
    z = np.load(f"{out}.npz")
    head = json.loads(Path(f"{out}.json").read_text())["header"]
    periods = list(tlp.iter_periods(str(man2_pack), 1, 3))
    outs = predict_periods(m, periods)
    assert z["ordinal"].tolist() == [1, 2, 3] == [p.ordinal for p in periods]
    assert z["rows"].tolist() == [p.rows for p in periods]
    assert z["first_row"].tolist() == [p.first for p in periods]
    assert z["learned"].shape == (sum(p.rows for p in periods), 4)
    assert np.isfinite(z["learned"]).all() and not any(k.startswith("err") for k in z.files)
    for p, o in zip(periods, outs, strict=True):
        rows = z["row_period"] == p.ordinal
        assert np.array_equal(z["learned"][rows], direct_track(o.mean, p, 6))
        tok = z["token_period"] == p.ordinal
        assert tok.sum() == -(-p.rows // 6) and np.allclose(z["man_prob"][tok], o.prob)
        sp = z["spans"][z["span_period"] == p.ordinal]
        assert np.array_equal(sp, spans_from_logit(o.prob, token_times(p.rows, p.dt, 6)))
    assert head["weights_sha256"] == _sha(w) and head["config_sha256"] == config_digest(cfg)
    assert head["dataset_digest"] == _sha(man2_pack) and head["ordinal_count"] == 3
    assert head["kind"] == "learned-period-tracks" and len(head["git_commit"]) == 40
