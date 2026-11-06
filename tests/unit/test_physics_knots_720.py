"""Spec 005 T006: the physics layer's knot path at 720 rows (G0-MAN2 tested only the trivial path
there). On MAN2 windows with every truth knot, in chord and masked-turn modes, the tensor layer
equals the NumPy reference (cost to 1e-9, determined states to 1e-4, flags exact), and the
gradients are finite."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
import torch

from tma2.data.f32pack import iter_pack_raw
from tma2.physics import reference as ref
from tma2.physics.layer import PhysicsInputs, PhysicsLayer
from tma2.physics.segmentation import LayerInputs, oracle_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays

R_MAX = 720
KNOTS = 16  # MAN2 windows hold up to ~6 changes in 120 min: two knots each
ITER = 40
SCENARIOS = 8


def _pad(a: np.ndarray) -> np.ndarray:
    out = np.zeros(R_MAX)
    out[: a.shape[0]] = a
    return out


def _inputs(items: list[tuple[BearingData, int, LayerInputs]]) -> PhysicsInputs:
    return PhysicsInputs(
        bearing=torch.tensor(np.stack([_pad(d.z) for d, _, _ in items])),
        valid=torch.tensor(np.stack([_pad(d.valid.astype(float)) for d, _, _ in items])),
        own=torch.tensor(np.stack([np.stack([_pad(d.ox), _pad(d.oy)], 1) for d, _, _ in items])),
        t=torch.tensor(np.stack([_pad(d.t) for d, _, _ in items])),
        sigma=torch.tensor([d.sigma for d, _, _ in items]),
        k=torch.tensor([k for _, k, _ in items]),
        changepoint=torch.tensor(np.stack([_pad(i.changepoint) for _, _, i in items])),
        speed_weight=torch.tensor(np.stack([_pad(i.speed_weight) for _, _, i in items])),
        log_weight=torch.tensor(np.stack([_pad(i.log_weight) for _, _, i in items])),
        theta0=torch.tensor(np.stack([i.theta0 for _, _, i in items])),
        speed_skip=torch.tensor(
            np.stack(
                [_pad(i.speed_skip if i.speed_skip is not None else np.zeros(1)) for *_, i in items]
            )
        ),
    )


@pytest.fixture(scope="module")
def items(man2_pack: Path) -> list[tuple[BearingData, int, LayerInputs, int]]:
    """(data, k, inputs, knots) for windows of ≥ 600 rows with at least one completed change;
    k is the last row (≥ 600, past the old 360-row window), chord and masked-turn modes."""
    out = []
    for _, m, own, _tgt, obs in iter_pack_raw(man2_pack):
        d = bearing_data_from_arrays(m, own, obs)
        spans = m.get("manoeuvres") or []
        k = d.n - 1
        if d.n < 600 or not any(int(s["end_index"]) <= k for s in spans):
            continue
        for mask in (False, True):
            inp = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, spans, True, mask)
            if inp is not None:
                out.append((d, k, inp, int((inp.changepoint > 0).sum())))
        if len(out) >= 2 * SCENARIOS:
            break
    assert len(out) >= 2 * SCENARIOS, len(out)
    return out


def test_knot_path_720_matches_reference(
    items: list[tuple[BearingData, int, LayerInputs, int]],
) -> None:
    torch.set_default_dtype(torch.float64)
    layer = PhysicsLayer(iterations=ITER, knots=KNOTS)
    with torch.no_grad():
        out = layer(_inputs([(d, k, i) for d, k, i, _ in items]))
    assert max(n for *_, n in items) >= 4  # several knots in use
    assert max(n for *_, n in items) <= KNOTS
    worst = 0.0
    compared = 0
    for b, (d, k, inp, _n) in enumerate(items):
        res = ref.solve(
            d.t, d.ox, d.oy, d.z, d.valid, d.sigma, k, inp.changepoint, inp.speed_weight,
            inp.log_weight, inp.theta0, ITER, KNOTS, speed_skip=inp.speed_skip,
        )  # fmt: skip
        assert abs(float(out.cost[b]) - res.cost) <= 1e-9 * max(res.cost, 1.0), b
        assert bool(out.plausible[b]) == res.plausible, b
        sd_range = math.sqrt(max(res.cov[0, 0] + res.cov[1, 1], 0.0))
        if res.plausible and sd_range < 0.5 * math.hypot(
            res.state[0] - d.ox[k], res.state[1] - d.oy[k]
        ):
            rel = np.abs(out.state[b].numpy() - res.state) / np.maximum(np.abs(res.state), 1.0)
            worst = max(worst, float(rel.max()))
            compared += 1
    assert compared >= len(items) // 2, (compared, len(items))
    print(f"items {len(items)}, compared {compared}, worst {worst:.2e}")
    assert worst <= 1e-4, worst


def test_knot_path_720_gradients_finite(
    items: list[tuple[BearingData, int, LayerInputs, int]],
) -> None:
    torch.set_default_dtype(torch.float64)
    layer = PhysicsLayer(iterations=ITER, knots=KNOTS, implicit=True)
    x = _inputs([(d, k, i) for d, k, i, _ in items[:8]])
    x.log_weight.requires_grad_(True)
    x.changepoint.requires_grad_(True)
    out = layer(x)
    loss = (out.range / 1e4).sum() + out.speed.sum()
    loss.backward()
    assert x.log_weight.grad is not None and torch.isfinite(x.log_weight.grad).all()
    assert x.changepoint.grad is not None and torch.isfinite(x.changepoint.grad).all()
