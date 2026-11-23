"""Spec 037 research R7: the hybrid layer (a prior on the state at the reported row)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch

from tma2.features.batch import generate_indices
from tma2.headroom.estimators import estimate
from tma2.headroom.gls import WhitenedLayer
from tma2.physics.segmentation import LayerInputs, trivial_inputs
from tma2.references.classical import BearingData
from tma2.regress import hybrid as hy
from tma2.segment.codeid import code_digest

ROOT = Path(__file__).resolve().parents[2]
RANGES = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())


Item = tuple[BearingData, int, LayerInputs]


def _items() -> list[Item]:
    b = generate_indices(321, np.arange(3, dtype=np.int64), RANGES)
    items: list[Item] = []
    for i in range(3):
        n = int(b.samples[i])
        d = BearingData(
            t=b.t[i, :n].astype(np.float64),
            ox=b.own[i, :n, 0].astype(np.float64),
            oy=b.own[i, :n, 1].astype(np.float64),
            z=b.bearing[i, :n].astype(np.float64),
            valid=b.valid[i, :n].astype(np.uint8),
            zig_index=int(b.zig_index[i]),
            sigma=float(b.sigma[i]),
            index=int(b.index[i]),
        )
        k = min(n - 1, int(b.zig_index[i]) + 180)
        inp = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
        assert inp is not None
        items.append((d, k, inp))
    return items


def _solve(layer: WhitenedLayer, items: list[Item]) -> torch.Tensor:
    r_max = max(d.n for d, _, _ in items)
    out, _ = estimate(layer, items, "nominal", r_max)
    return out.state


def test_no_prior_is_the_parents_solve_and_a_tight_prior_wins() -> None:
    torch.set_default_dtype(torch.float64)
    items = _items()
    base = _solve(WhitenedLayer(knots=12), items)
    layer = hy.HybridLayer(knots=12)
    none = [hy.prior_rows(d, k, None, 1.0) for d, k, _ in items]
    assert not any(u for *_, u in none)
    hy.set_prior(layer, items, none)
    assert torch.allclose(_solve(layer, items), base, rtol=1e-6, atol=1e-3)  # to rounding
    st0 = base.numpy()

    def rows_at(scale: float, sd_r: float, sd_v: float) -> list[dict[str, float]]:
        out = []
        for (d, k, _), s0 in zip(items, st0, strict=True):
            own = np.array([d.ox[k], d.oy[k]])
            rel = (s0[:2] - own) * scale
            out.append(
                {
                    "range_m": float(np.hypot(*rel)),
                    "x_m": float(own[0] + rel[0]),
                    "y_m": float(own[1] + rel[1]),
                    "course_rad": float(math.atan2(s0[2], s0[3]) % (2 * math.pi)),
                    "speed_mps": float(np.hypot(s0[2], s0[3])),
                    "sd_log_range": sd_r,
                    "sd_speed_mps": sd_v,
                }
            )
        return out

    def solve_with(rows: list[dict[str, float]], weight: float) -> np.ndarray:
        pr = [hy.prior_rows(d, k, r, weight) for (d, k, _), r in zip(items, rows, strict=True)]
        assert all(u for *_, u in pr)
        hy.set_prior(layer, items, pr)
        return _solve(layer, items).numpy()

    def ranges(st: np.ndarray) -> np.ndarray:
        return np.array(
            [
                math.hypot(s[0] - d.ox[k], s[1] - d.oy[k])
                for (d, k, _), s in zip(items, st, strict=True)
            ]
        )

    r0 = ranges(st0)
    # a tight prior at the layer's own solution leaves it there
    assert np.allclose(ranges(solve_with(rows_at(1.0, 1e-3, 1e-2), 1.0)), r0, rtol=1e-3)
    # a tight prior 2% out in range pulls the reported range most of the way to it
    pulled = ranges(solve_with(rows_at(1.02, 1e-4, 1.0), 1.0))
    assert np.all((pulled - r0) / (0.02 * r0) > 0.5)
    # the same prior made very loose changes nothing that matters
    assert np.allclose(ranges(solve_with(rows_at(1.02, 1e-4, 1.0), 1e9)), r0, rtol=1e-6)


def test_static_range_prior_and_unusable_rows() -> None:
    d, k, _ = _items()[0]
    a, m, used = hy.prior_rows(d, k, None, 1.0, static=(9.6, 0.5))
    assert used and np.all(a[1:] == 0) and np.all(m[1:] == 0) and np.any(a[0] != 0)
    bad = {
        "range_m": 1e4,
        "x_m": 0.0,
        "y_m": 1e4,
        "course_rad": 0.0,
        "speed_mps": 5.0,
        "sd_log_range": float("nan"),
        "sd_speed_mps": 1.0,
    }
    assert not hy.prior_rows(d, k, bad, 1.0)[2]


def test_c_is_still_the_frozen_code() -> None:
    plan = json.loads((ROOT / "configs" / "gateh" / "gh-a.json").read_text())
    assert code_digest() == plan["c2"]["code_sha256"]
