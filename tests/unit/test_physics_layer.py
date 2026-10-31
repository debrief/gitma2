"""The physics layer (spec 002 FR-006..011): reference ≡ tensor layer, trivial inputs ≡ batch
least squares, gradients, masking, and the oracle's effect after a manoeuvre."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
import torch

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.physics import reference as ref
from tma2.physics.layer import PhysicsInputs, PhysicsLayer
from tma2.physics.reference import ITERATIONS
from tma2.physics.segmentation import LayerInputs, oracle_inputs, trivial_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays, classical_predict

R_MAX = 360
torch.set_default_dtype(torch.float64)


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
                [
                    _pad(i.speed_skip if i.speed_skip is not None else np.zeros(1))
                    for _, _, i in items
                ]
            )
        ),
    )


@pytest.fixture(scope="module")
def phase4_items() -> list[
    tuple[BearingData, int, LayerInputs, dict[str, Any], bool, dict[str, Any]]
]:
    """(data, row, inputs, classical row, oracle?, meta) for a spread of fixture rows."""
    items = []
    for n, (_, meta, own, _tgt, obs) in enumerate(
        iter_pack_raw(fixture_dir("phase4-seed777") / "test.f32pack")
    ):
        if n >= 6:
            break
        d = bearing_data_from_arrays(meta, own, obs)
        pred = classical_predict(d, "per_timestep")
        for row in pred["rows"][10::40]:
            k = int(round(row["timestamp_s"] / 10))
            for oracle in (False, True):
                inp = (
                    oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, meta.get("manoeuvres"), True)
                    if oracle
                    else trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
                )
                if inp is not None:
                    items.append((d, k, inp, row, oracle, meta))
    return items


def test_layer_matches_reference_and_least_squares(phase4_items: Any) -> None:
    layer = PhysicsLayer(iterations=40, knots=8)
    with torch.no_grad():
        out = layer(_inputs([(d, k, i) for d, k, i, _, _, _ in phase4_items]))
    worst_ref = 0.0
    worst_ls = 0.0
    for b, (d, k, inp, row, oracle, _) in enumerate(phase4_items):
        res = ref.solve(
            d.t,
            d.ox,
            d.oy,
            d.z,
            d.valid,
            d.sigma,
            k,
            inp.changepoint,
            inp.speed_weight,
            inp.log_weight,
            inp.theta0,
            40,
            8,
            speed_skip=inp.speed_skip,
        )
        assert abs(float(out.cost[b]) - res.cost) <= 1e-9 * max(res.cost, 1.0)
        # States are compared where the problem determines them (relative range sd from the
        # covariance below 1); in flat directions two solvers stop at points of equal cost.
        sd_range = math.sqrt(max(res.cov[0, 0] + res.cov[1, 1], 0.0))
        if res.plausible and sd_range < 0.5 * math.hypot(
            res.state[0] - d.ox[k], res.state[1] - d.oy[k]
        ):
            rel = np.abs(out.state[b].numpy() - res.state) / np.maximum(np.abs(res.state), 1.0)
            worst_ref = max(worst_ref, float(rel.max()))
        if not oracle and row["converged"]:
            dr = abs(float(out.range[b]) - row["range_m"]) / row["range_m"]
            ds = abs(float(out.speed[b]) - row["speed_mps"]) / max(row["speed_mps"], 1.0)
            worst_ls = max(worst_ls, dr, ds)
    assert worst_ref <= 1e-4, worst_ref
    assert worst_ls <= 1e-4, worst_ls


def test_masking_is_exact(phase4_items: Any) -> None:
    layer = PhysicsLayer(iterations=20, knots=8)
    items = [(d, k, i) for d, k, i, _, _, _ in phase4_items[:5]]
    with torch.no_grad():
        batch = layer(_inputs(items))
        singles = [layer(_inputs([it])) for it in items]
    # Padded rows contribute exact zeros; BLAS reduction order differs with the batch shape, and a
    # last-bit difference can flip one damping decision, so agreement is to ~1e-7, not bitwise.
    for b, single in enumerate(singles):
        assert torch.allclose(batch.state[b], single.state[0], rtol=1e-6, atol=1e-4)
        assert torch.allclose(batch.cost[b], single.cost[0], rtol=1e-6)


def test_gradients_on_selected_knots(phase4_items: Any) -> None:
    """Autograd equals central finite differences for the selected knots' changepoint and speed
    weights, bearing log-weights and the initial state. (TopK selects the knots; a weight that is
    not selected has zero gradient by construction, as in any sparse selection.)"""
    d, k, inp, _, _, _ = next(
        it for it in phase4_items if not it[4] and it[1] > it[0].zig_index + 40
    )
    base = _inputs([(d, k, inp)])
    r1, r2 = k - 30, k - 10
    layer = PhysicsLayer(iterations=6, knots=4)
    cp0 = base.changepoint.clone()
    cp0[0, r1] = 0.6
    cp0[0, r2] = 0.3
    sw0 = torch.full((1, R_MAX), 0.4)
    lw0 = torch.zeros(1, R_MAX)

    def loss(
        cp: torch.Tensor, sw: torch.Tensor, lw: torch.Tensor, th0: torch.Tensor
    ) -> torch.Tensor:
        x = PhysicsInputs(
            base.bearing, base.valid, base.own, base.t, base.sigma, base.k, cp, sw, lw, th0
        )
        st = layer(x).state
        out: torch.Tensor = st[0, 0] + st[0, 1] + 100.0 * (st[0, 2] + st[0, 3])
        return out

    cp, sw, lw, th0 = (v.clone().requires_grad_(True) for v in (cp0, sw0, lw0, base.theta0))
    loss(cp, sw, lw, th0).backward()  # type: ignore[no-untyped-call]
    # Every entry, including invalid rows, rows beyond k and unselected candidates, is finite
    # (P0 panel: a sqrt of a masked zero once gave NaN on those rows and poisoned the model).
    for leaf in (cp, sw, lw, th0):
        assert leaf.grad is not None and bool(torch.isfinite(leaf.grad).all())
    assert lw.grad is not None and float(lw.grad[0, k + 1 :].abs().max()) == 0.0
    probes = [
        ("cp", cp, cp0, (0, r1)),
        ("cp", cp, cp0, (0, r2)),
        ("sw", sw, sw0, (0, r1)),
        ("sw", sw, sw0, (0, r2)),
        ("lw", lw, lw0, (0, k - 5)),
        ("lw", lw, lw0, (0, k // 2)),
    ]
    probes += [("th0", th0, base.theta0, (0, i)) for i in range(4)]
    for name, leaf, value, pos in probes:
        eps = 1e-5 if name != "th0" else 1e-3
        plus = value.clone()
        minus = value.clone()
        plus[pos] += eps
        minus[pos] -= eps
        args = {"cp": cp0, "sw": sw0, "lw": lw0, "th0": base.theta0}
        with torch.no_grad():
            fd = (loss(**{**args, name: plus}) - loss(**{**args, name: minus})) / (2 * eps)
        assert leaf.grad is not None
        an = leaf.grad[pos]
        assert abs(float(an - fd)) <= 1e-4 * max(1.0, abs(float(fd))), (
            name,
            pos,
            float(an),
            float(fd),
        )


def test_oracle_segmentation_helps_after_manoeuvres(phase4_items: Any) -> None:
    """With truth knots the physics layer should not be worse than the trivial fit on rows after
    a manoeuvre, in the median (the ceiling of docs/research/05)."""
    rows: dict[tuple[int, int], dict[bool, float]] = {}
    layer = PhysicsLayer(iterations=40, knots=8)
    with torch.no_grad():
        out = layer(_inputs([(d, k, i) for d, k, i, _, _, _ in phase4_items]))
    for b, (d, k, _inp, _row, oracle, meta) in enumerate(phase4_items):
        spans = meta.get("manoeuvres") or []
        if not any(s["end_index"] <= k for s in spans):
            continue
        rng_true = None
        for _, m2, own, tgt, _o in iter_pack_raw(fixture_dir("phase4-seed777") / "test.f32pack"):
            if m2["index"] == d.index:
                rng_true = math.hypot(tgt[k, 1] - own[k, 1], tgt[k, 2] - own[k, 2])
                break
        assert rng_true is not None
        rows.setdefault((d.index, k), {})[oracle] = abs(float(out.range[b]) - rng_true) / rng_true
    pairs = [(v[False], v[True]) for v in rows.values() if False in v and True in v]
    assert pairs, "no post-manoeuvre rows in the sample"
    assert float(np.median([o for _, o in pairs])) <= float(np.median([t for t, _ in pairs])) + 1e-9


@pytest.mark.parametrize(("iterations", "knots"), [(8, 4), (ITERATIONS, 8)])
def test_model_gradients_are_finite(iterations: int, knots: int) -> None:
    """A full backward pass through encoder and physics layer (export toy model, padded golden
    batch with invalid and beyond-k rows) leaves every parameter gradient finite and non-zero."""
    from tma2.export.onnx_export import golden_batch
    from tma2.export.toy_model import ToyModel

    torch.manual_seed(0)
    g = golden_batch(fixture_dir("phase4-seed777") / "test.f32pack", n=4)
    x = {
        k: torch.from_numpy(v).to(torch.float64) if v.dtype != np.int64 else torch.from_numpy(v)
        for k, v in g.items()
    }
    model = ToyModel(iterations=iterations, knots=knots).to(torch.float64)
    state, _cov, _cost, _ = model(
        x["bearing"], x["valid"], x["own"], x["t"], x["sigma"], x["k"], x["theta0"]
    )
    (state[:, :2].abs().sum() / 1e4 + state[:, 2:].abs().sum()).backward()
    grads = [p.grad for p in model.parameters()]
    assert all(gr is not None and bool(torch.isfinite(gr).all()) for gr in grads)
    assert any(gr is not None and float(gr.abs().max()) > 0 for gr in grads)


def test_covariance_equals_sigma2_inverse_information(phase4_items: Any) -> None:
    """FR-007: with trivial inputs the layer's covariance equals σ²(JᵀJ)⁻¹ mapped to the state at
    row k, computed here independently from the constant-velocity bearing Jacobian at the
    layer's own solution."""
    items = [(d, k, i) for d, k, i, _, oracle, _ in phase4_items if not oracle]
    with torch.no_grad():
        out = PhysicsLayer()(_inputs(items))
    checked = 0
    for b, (d, k, _) in enumerate(items):
        x0, y0, vx, vy = (float(v) for v in out.theta[b, :4])
        jtj = np.zeros((4, 4))
        for i in range(k + 1):
            if not d.valid[i]:
                continue
            dx = x0 + vx * d.t[i] - d.ox[i]
            dy = y0 + vy * d.t[i] - d.oy[i]
            r2 = dx * dx + dy * dy
            g = np.array([dy / r2, -dx / r2, d.t[i] * dy / r2, -d.t[i] * dx / r2])
            jtj += np.outer(g, g)
        tk = d.t[k]
        gmap = np.array([[1, 0, tk, 0], [0, 1, 0, tk], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
        expected = d.sigma**2 * gmap @ np.linalg.inv(jtj) @ gmap.T
        got = out.cov[b].numpy()
        rng = math.hypot(x0 + vx * tk - d.ox[k], y0 + vy * tk - d.oy[k])
        if not bool(out.plausible[b]) or math.sqrt(expected[0, 0] + expected[1, 1]) > 0.5 * rng:
            continue
        checked += 1
        scale = np.sqrt(np.outer(np.diag(expected), np.diag(expected)))
        assert np.abs(got - expected).max() <= 1e-6 * scale.max(), (b, got, expected)
    assert checked >= 5
