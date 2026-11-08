"""Fitting the usable uncertainty statement (spec 009 T006, T013)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import torch

from tma2.calib.data import CalData
from tma2.calib.statement_fit import (
    StatementHead,
    apply_temperature,
    evaluate,
    fit_global,
    fit_isotonic,
    fit_temperature,
    loss_scale,
    predict_head,
    stated,
    train_statement,
)
from tma2.types.generated.tma import StatementHeadConfig

CFG = {
    "width": 8, "bound": 2.0, "xmax_rad": math.radians(45), "learning_rate": 0.02,
    "batch_rows": 512, "max_epochs": 30, "patience": 5, "min_improvement": 0.001, "seed": 1,
}  # fmt: skip


def _data(n: int, seed: int) -> CalData:
    """Course right (within ~2 sd) with probability 0.9 when x0 > 0 and 0.3 otherwise; range and
    speed errors Gaussian with sd 1.5 × the stated sd."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 5))
    sd = np.column_stack([np.full(n, 0.1), np.full(n, 0.05), np.full(n, 0.5)])
    good = rng.random(n) < np.where(x[:, 0] > 0, 0.9, 0.3)
    course = np.where(good, rng.normal(0, 0.05, n), rng.uniform(-math.pi, math.pi, n))
    err = np.column_stack([rng.normal(0, 0.15, n), course, rng.normal(0, 0.75, n)])
    return CalData(
        ordinal=np.arange(n), k=np.zeros(n, dtype=np.int64), t=np.zeros(n), x=x, q=np.ones(n),
        u=np.zeros((n, 4)), w=np.zeros((n, 4, 4)), own=np.zeros((n, 2)),
        usable=np.ones(n, dtype=bool), scalable=np.ones(n, dtype=bool),
        minute=rng.choice([5, 10], n), open=np.zeros(n, dtype=bool), header={}, sd=sd, err=err,
    )  # fmt: skip


def test_global_and_temperature() -> None:
    d = _data(8000, 1)
    g = fit_global(d)
    assert abs(g["p"] - 0.6) < 0.05  # half the rows at 0.9, half at 0.3
    assert abs(g["c_r"] - 1.5 * 1.96) < 0.15 and abs(g["c_s"] - 1.5 * 1.96) < 0.15
    t = fit_temperature(d, ["minute"])
    s = apply_temperature(t, d, ["minute"])
    out = stated(s, d, CFG["xmax_rad"])
    hit = (np.abs(d.err[:, 1]) <= out["x"]).mean()  # type: ignore[index]
    assert abs(hit - out["p_raw"].mean()) < 0.03  # reliable on average


def test_untrained_head_is_global() -> None:
    torch.set_default_dtype(torch.float64)
    d = _data(500, 2)
    g = fit_global(d)
    h = StatementHead(5, 8, 2.0, g).double()
    s = predict_head(h, d)
    assert np.allclose(s.a, g["a"]) and np.allclose(s.p, g["p"]) and np.allclose(s.c_r, g["c_r"])


def test_head_learns_course_reliability(tmp_path: Path) -> None:
    torch.set_default_dtype(torch.float64)
    tr, va = _data(8000, 3), _data(3000, 4)
    cfg = StatementHeadConfig.model_validate(CFG)
    meta = train_statement(cfg, tr, va, tmp_path / "h", {}, log=lambda _m: None)
    assert meta["best_val"] < meta["untrained_val"] - 0.02
    from safetensors.torch import load_file

    h = StatementHead(5, 8, 2.0, meta["global"]).double()
    h.load_state_dict(load_file(str(tmp_path / "h" / "best.safetensors")))
    s = predict_head(h, va)
    pos = va.x[:, 0] > 0
    assert s.p[pos].mean() > 0.75 and s.p[~pos].mean() < 0.45
    knots = fit_isotonic(s, va, cfg.xmax_rad, 10)
    assert np.all(np.diff(knots[1]) >= -1e-12)
    assert evaluate(h, va, loss_scale(meta["global"], tr)) == meta["best_val"]
