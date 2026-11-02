"""Detector losses: finite gradients through the physics layer (spec 004 FR-016–FR-018)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from tests.conftest import fixture_dir
from tests.unit.test_detector import config
from tma2.models.detector import Detector, features
from tma2.models.detector_labels import pair_labels, row_labels
from tma2.models.detector_loss import (
    DetectorTargets,
    detector_loss,
    downstream_loss,
    run_downstream,
)
from tma2.models.train import batch_from_pack
from tma2.physics.layer import PhysicsLayer
from tma2.references.crb import crb_known_manoeuvres_fast


def d(a: object) -> torch.Tensor:
    return torch.tensor(np.asarray(a, dtype=np.float64))


def _setup(n: int = 6) -> tuple[Any, np.ndarray, DetectorTargets, tuple[torch.Tensor, ...]]:
    b = batch_from_pack(Path(fixture_dir("phase4-seed777") / "validation.f32pack"), n)
    r = b.t.shape[1]
    dt = np.full(n, 10.0)
    ks = np.stack([b.samples - 1, np.minimum(b.zig_index + 30, b.samples - 1)], axis=1)
    rl = row_labels(b.spans, b.samples, dt, r)
    pl = pair_labels(b.spans, dt, ks, r)
    y = DetectorTargets(
        now=d(rl.now),
        held=torch.tensor(rl.held),
        valid_row=torch.tensor(rl.valid_row),
        w_target=d(pl.w_target),
        kind=d(pl.kind),
        kind_weight=d(pl.kind_weight),
        query=torch.tensor(ks, dtype=torch.int64),
    )
    window = d(b.mask)
    inputs = (d(b.bearing), d(b.valid) * window, d(b.own), d(b.t), window)
    return b, ks, y, inputs


def test_gradients_finite_through_the_layer() -> None:
    torch.manual_seed(3)
    b, ks, y, (bearing, valid, own, t, window) = _setup()
    det = Detector(config()).double()
    with torch.no_grad():
        det.w_head.bias.fill_(0.0)  # knots with weight 0.5: the layer's increments are live
    out = det(features(bearing, valid, own, t, window), window, y.query)
    layer = PhysicsLayer(iterations=5, knots=8, implicit=True)
    res, bi, qi = run_downstream(
        layer,
        out,
        bearing,
        valid,
        own[..., :2],
        t,
        torch.tensor(b.sigma, dtype=torch.float64),
        y.query,
    )
    truth, cov, okx, oky = [], [], [], []
    for s, q in zip(bi.tolist(), qi.tolist(), strict=True):
        k = int(ks[s, q])
        n = int(b.samples[s])
        c, v = b.tgt[s, :n, 2].astype(float), b.tgt[s, :n, 3].astype(float)
        tvx, tvy = v * np.sin(c), v * np.cos(c)
        bound = crb_known_manoeuvres_fast(
            b.t[s, :n],
            b.own[s, :n, 0],
            b.own[s, :n, 1],
            b.tgt[s, :n, 0],
            b.tgt[s, :n, 1],
            tvx,
            tvy,
            b.valid[s, :n],
            b.tm[s, : max(int(b.n_tm[s]), 0)],
            [k],
            float(b.sigma[s]),
        )[0]
        truth.append([b.tgt[s, k, 0], b.tgt[s, k, 1], tvx[k], tvy[k]])
        cov.append(bound.state_cov if bound.state_cov is not None else np.full((4, 4), np.nan))
        okx.append(b.own[s, k, 0])
        oky.append(b.own[s, k, 1])
    ds = downstream_loss(
        res,
        torch.tensor(np.array(truth), dtype=torch.float64),
        torch.tensor(np.array(cov), dtype=torch.float64),
        torch.tensor(okx, dtype=torch.float64),
        torch.tensor(oky, dtype=torch.float64),
    )
    assert ds[1] > 0
    parts = detector_loss(out, y, config(), ds)
    assert torch.isfinite(parts.total)
    parts.total.backward()  # type: ignore[no-untyped-call]
    for name, p in det.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all(), name
    gk = det.w_head.k.weight.grad
    last = det.now_head[2]
    assert isinstance(last, torch.nn.Linear) and last.weight.grad is not None
    assert gk is not None and gk.abs().sum() > 0
    assert last.weight.grad.abs().sum() > 0


def test_classification_only_skips_the_layer() -> None:
    _b, _ks, y, (bearing, valid, own, t, window) = _setup(3)
    cfg = config().model_copy(update={"loss_downstream_weight": 0.0})
    det = Detector(cfg).double()
    out = det(features(bearing, valid, own, t, window), window, y.query)
    parts = detector_loss(out, y, cfg, None)
    assert parts.downstream_rows == 0 and torch.isfinite(parts.total)
    # untrained: now = boundary-free BCE of p = 0.5 on the now targets
    assert abs(float(parts.now) - float(np.log(2.0))) < 1e-12
