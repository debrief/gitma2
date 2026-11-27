"""Spec 038 (research R2): the bearings C is given by the editing control."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tma2.cli import hpredict
from tma2.headroom.edit import Edit, edited, wild_flags
from tma2.references.classical import BearingData
from tma2.segment import Interval


def _data(n: int = 400, corr: float = 0.0, seed: int = 4) -> BearingData:
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 10.0
    sigma = np.deg2rad(1.0)
    e = rng.normal(0.0, sigma, n)
    if corr > 0.0:  # a first-order correlated part with half the variance, tau = 60 s
        rho, a = np.exp(-10.0 / 60.0), np.zeros(n)
        a[0] = rng.normal(0.0, sigma)
        for i in range(1, n):
            a[i] = rho * a[i - 1] + rng.normal(0.0, sigma * np.sqrt(1 - rho * rho))
        e = np.sqrt(1 - corr) * e + np.sqrt(corr) * a
    z = 0.5 + 0.0004 * t + e
    return BearingData(t, np.zeros(n), t * 3.0, z, np.ones(n, dtype=np.uint8), 100, sigma, 0)


def test_wild_bearings_go_and_the_original_stays() -> None:
    d = _data()
    bad = [50, 51, 180, 333]
    d.z[bad] += np.deg2rad(12.0)
    before = (d.z.copy(), d.valid.copy(), d.sigma)
    e, info = edited(d, [150, 200, 390], Edit(wild=True))
    assert not e.valid[bad].any() and info["edited"] >= 4
    assert int(e.valid.sum()) >= d.n - 6  # few false edits on Gaussian errors
    assert e.sigma == d.sigma and e.valid.dtype == d.valid.dtype
    assert (d.z == before[0]).all() and (d.valid == before[1]).all() and d.sigma == before[2]


def test_flags_are_causal_at_the_scored_rows() -> None:
    d = _data()
    d.z[[148, 149, 199]] += np.deg2rad(12.0)
    rows = [150, 200]
    base = wild_flags(d, rows, d.sigma)
    rng = np.random.default_rng(9)
    for k in rows:
        later = BearingData(d.t, d.ox, d.oy, d.z.copy(), d.valid, d.zig_index, d.sigma, d.index)
        later.z[k + 1 :] += rng.normal(0.0, 0.3, d.n - k - 1)
        assert (wild_flags(later, rows, d.sigma)[: k + 1] == base[: k + 1]).all()
    assert not base[148] and not base[149] and not base[199]  # wild bearings just before a row


def test_effective_sd_only_under_correlated_errors() -> None:
    white, _ = edited(_data(), [300], Edit(effective_sd=True))
    assert white.sigma == pytest.approx(np.deg2rad(1.0))
    corr, info = edited(_data(corr=0.5), [300], Edit(effective_sd=True))
    assert info["share"] >= 0.2 and 1.3 < info["sigma_factor"] < 6.0
    assert corr.sigma == pytest.approx(np.deg2rad(1.0) * info["sigma_factor"])
    assert (corr.valid == 1).all()


def test_edit_settings() -> None:
    with pytest.raises(ValueError):
        Edit()
    with pytest.raises(TypeError):
        Edit(nothing=True)  # type: ignore[call-arg]


def test_segmentation_cache_round_trip(tmp_path: Path) -> None:
    sg = [
        {30: [Interval(0, 0, 30, False)], 60: [Interval(0, 0, 40), Interval(1, 41, 60, True)]},
        {},
    ]
    path = tmp_path / "c" / "k-0-2.json"
    hpredict._save_segs(path, [4, 7], sg)
    assert hpredict._load_segs(path, [4, 7]) == sg
    with pytest.raises(ValueError):
        hpredict._load_segs(path, [4, 8])
