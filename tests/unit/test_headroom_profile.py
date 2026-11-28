"""Spec 039: the read-out told the generator's priors (headroom/profile.py)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from tma2.headroom.cov import ErrorModel
from tma2.headroom.profile import Prior, ProfileSettings, inflation, weighted_median

ROOT = Path(__file__).resolve().parents[2]


def test_weighted_median_of_a_symmetric_density_is_its_mode() -> None:
    x = np.linspace(-3.0, 3.0, 61) + 9.0
    lw = -0.5 * ((x - 9.0) / 0.4) ** 2
    med, i, f = weighted_median(x, lw)
    assert med == pytest.approx(9.0, abs=1e-6)
    assert x[i] <= med <= x[i + 1] and 0.0 <= f <= 1.0


def test_weighted_median_on_an_uneven_grid_and_a_skewed_density() -> None:
    rng = np.random.default_rng(0)
    x = np.sort(rng.uniform(0.0, 6.0, 400))
    lw = np.log(np.maximum(np.exp(-x), 1e-300))  # exponential: median ln 2 (truncated at 6)
    med, _, _ = weighted_median(x, lw)
    want = -math.log(1.0 - 0.5 * (1.0 - math.exp(-6.0)))
    assert med == pytest.approx(want, abs=0.02)


def test_weighted_median_degenerate() -> None:
    x = np.array([1.0, 2.0, 3.0])
    med, i, f = weighted_median(x, np.array([-np.inf, 0.0, -np.inf]))
    assert 1.0 < med < 3.0 and i in (0, 1) and 0.0 <= f <= 1.0


def test_prior_table() -> None:
    p = Prior.load(ROOT / "configs/pic/prior-man2.json")
    edges, dens = p.edges, p.density
    assert np.sum(dens * np.diff(edges)) == pytest.approx(1.0, abs=1e-4)
    mid = 0.5 * (edges[:-1] + edges[1:])
    assert np.allclose(p.log_range(mid), np.log(np.maximum(dens, 1e-4 * dens.max())))
    far = p.log_range(np.array([edges[-1] + 2.0, edges[0] - 2.0]))
    assert np.allclose(far, math.log(1e-4 * dens.max()))
    lo, hi = p.speed
    s = np.array([lo, 0.5 * (lo + hi), hi, 1.5 * hi, 0.5 * lo])
    ls = p.log_speed(s, 0.1)
    assert ls[:3].tolist() == [0.0, 0.0, 0.0] and ls[3] < -10 and ls[4] < -10
    meta = json.loads((ROOT / "configs/pic/prior-man2.json").read_text())
    assert meta["seed"] == 321  # a spent seed, never a test seed


def test_inflation() -> None:
    assert inflation(ErrorModel(0.02), 10.0) == 1.0
    m = ErrorModel(sigma_w=0.02 * math.sqrt(0.5), sigma_c=0.02 * math.sqrt(0.5), tau_c=60.0)
    rho = math.exp(-10.0 / 60.0)
    assert inflation(m, 10.0) == pytest.approx(0.5 + 0.5 * (1 + rho) / (1 - rho))


def test_settings() -> None:
    with pytest.raises(ValueError):
        ProfileSettings(prior="x", temper="warm")
    with pytest.raises(ValueError):
        ProfileSettings(prior="x", grid=3)


def test_read_out_follows_the_prior_where_the_bearings_do_not_decide(man2_pack: Path) -> None:
    """One scenario on its true segmentation: a prior concentrated far from the mode moves the
    read-out towards it, and with a flat prior the read-out stays within the likelihood's
    profile about the mode."""
    import torch

    from tma2.headroom.estimators import RobustSettings
    from tma2.headroom.profile import profile_estimate
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.regress.hybrid import HybridLayer
    from tma2.segment.score import g5_rows, iter_selected
    from tma2.segment.score import oracle as oracle_inputs

    torch.set_default_dtype(torch.float64)
    try:
        for j, m, own, _tgt, obs in iter_selected(man2_pack, 0, 4):
            d = bearing_data_from_arrays(m, own, obs)
            ks = g5_rows(m, d.n)
            if ks:
                inp = oracle_inputs(j, m, d, ks[0])
                if inp is not None:
                    break
        assert inp is not None
        items = [(d, ks[0], inp)]
        layer = HybridLayer(knots=12)
        base = Prior.load(ROOT / "configs/pic/prior-man2.json")
        cfg = ProfileSettings(prior="unused", grid=12)
        out, flat = profile_estimate(
            layer,
            items,
            d.n,
            RobustSettings(),
            ProfileSettings(prior="unused", grid=12, flat=True),
            base,
        )
        mode = float(out.range[0])
        assert flat[0] is not None and math.isfinite(flat[0]["range_m"])
        sd = max(flat[0]["profile_sd_log_range"], 0.01)
        assert abs(math.log(flat[0]["range_m"] / mode)) < 3.0 * sd + 0.05
        # a prior about a refinement point of the grid, 1.5 sds of the mode's own covariance out
        # (a window between grid points would be read as flat: the table must be smoother than
        # the grid, as the generator's is)
        target = math.log(mode) + 1.5 * sd
        edges = np.array([target - 0.75 * sd, target + 0.75 * sd])
        tight = Prior(edges, np.array([1.0 / (1.5 * sd)]), (0.01, 1000.0))
        _, moved = profile_estimate(layer, items, d.n, RobustSettings(), cfg, tight)
        assert moved[0] is not None
        assert math.log(moved[0]["range_m"] / mode) > 0.5 * sd
        assert layer.prior is None  # the layer is left as it was found
    finally:
        torch.set_default_dtype(torch.float32)
