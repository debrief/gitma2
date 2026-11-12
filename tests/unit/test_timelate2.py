"""Spec 014: Gate T's search stays as registered; the corrected and flat priors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.timelate.prior import (
    ManoeuvrePrior,
    _leg_pdf,
    log_prior,
    prior_precision,
    prior_residuals,
)

from .test_timelate import _arc_case

RANGES = json.loads(Path("configs/timelate/tl-ranges.json").read_text())


def _problem(seed: int) -> tuple[Any, np.ndarray, np.ndarray]:
    t, ox, oy, z, spans, theta, _st = _arc_case()
    sigma = 0.0175
    rng = np.random.default_rng(seed)
    pb = (t, ox, oy, z + sigma * rng.standard_normal(t.size), np.ones(t.size, dtype=bool), sigma)
    return pb, spans, theta


def test_gate_t_search_is_unchanged() -> None:
    from tma2.timelate.search import candidate_set, evidence_search

    want = json.loads(Path("tests/fixtures/timelate/gt-fixture.json").read_text())["candidates"]
    pb, _spans, theta = _problem(7)
    prior = ManoeuvrePrior.from_ranges(RANGES)
    assert prior.version == 1 and prior.kind == "annex-b"
    _best, seen = evidence_search(pb, theta[:4], np.zeros((0, 2)), prior, steps=4)
    got = candidate_set(seen)
    assert len(got) == len(want)
    for (h, p), w in zip(got, want, strict=True):
        assert h.evidence == pytest.approx(w["evidence"], abs=1e-9)
        assert p == pytest.approx(w["p"], abs=1e-9)
        assert np.allclose(h.fit.spans, np.array(w["spans"]).reshape(-1, 2), atol=1e-9)
        assert h.kinds.tolist() == w["kinds"]


def test_corrected_leg_density_integrates_to_one_and_forbids_short_legs() -> None:
    p2 = ManoeuvrePrior.from_ranges(RANGES, version=2)
    g = np.linspace(-300.0, 8000.0, 83001)
    d = np.exp([_leg_pdf(p2, float(x)) for x in g])
    assert abs(float(np.sum(d) * (g[1] - g[0])) - 1.0) < 1e-4
    p1 = ManoeuvrePrior.from_ranges(RANGES)
    short = p2.leg_min / 2
    assert _leg_pdf(p2, short) < _leg_pdf(p1, short) - 5.0
    assert _leg_pdf(p2, p2.leg_mean) > _leg_pdf(p1, p1.leg_mean)


def test_corrected_precision_gives_a_uniform_direction_its_width() -> None:
    p2 = ManoeuvrePrior.from_ranges(RANGES, version=2)
    d = prior_precision(p2, 2, 8000.0)
    w = p2.speed[1] - p2.speed[0]
    assert np.sqrt(2 * np.pi / d[3]) == pytest.approx(w)
    assert np.sqrt(2 * np.pi / d[4]) == pytest.approx(2 * (p2.angle[1] - p2.angle[0]))
    assert d[8] > 0.0 and d[9] == 0.0  # only the first start keeps a stand-in
    d1 = prior_precision(ManoeuvrePrior.from_ranges(RANGES), 2, 8000.0)
    assert d1[9] == d1[8] > 0.0


def test_corrected_residual_is_continuous_at_the_minimum_leg() -> None:
    p2 = ManoeuvrePrior.from_ranges(RANGES, version=2)
    kinds = np.array([[True, False], [True, False]])
    theta = np.array([0.0, 8000.0, 1.0, 5.0, 0.8, 0.0, 0.8, 0.0])

    def last(gap: float) -> float:
        spans = np.array([[600.0, 660.0], [660.0 + gap, 720.0 + gap]])
        return float(prior_residuals(p2, theta, spans, kinds)[-1])

    assert last(p2.leg_min + 1e-6) == pytest.approx(last(p2.leg_min - 1e-6), abs=1e-3)
    assert abs(last(p2.leg_min / 2)) > abs(last(p2.leg_min))


def test_flat_prior_is_constant_inside_the_box() -> None:
    flat = ManoeuvrePrior.from_ranges(RANGES, version=2, kind="flat")
    kinds = np.array([[True, False], [False, True]])
    a = np.array([0.0, 8000.0, 1.0, 5.0, 0.3, 0.0, 0.0, 1.0])
    b = np.array([0.0, 8000.0, 1.0, 5.0, 2.0, 0.0, 0.0, -1.5])
    sa = np.array([[300.0, 340.0], [900.0, 1500.0]])
    sb = np.array([[1200.0, 1260.0], [1300.0, 1330.0]])
    la, lb = (
        log_prior(flat, a, sa, kinds, 3600.0, 8000.0),
        log_prior(flat, b, sb, kinds, 3600.0, 8000.0),
    )
    assert la["legs"] == pytest.approx(lb["legs"])
    assert la["changes"] == pytest.approx(lb["changes"])
    r = prior_residuals(flat, a, sa, kinds)
    assert np.count_nonzero(r) == 0  # speeds inside their range: nothing else is penalised
    informed = ManoeuvrePrior.from_ranges(RANGES, version=2)
    assert prior_residuals(informed, a, sa, kinds).size == r.size
    with pytest.raises(ValueError):
        ManoeuvrePrior.from_ranges(RANGES, version=3)


def test_counts_match_nearest_and_ignore_edge_manoeuvres() -> None:
    from tma2.timelate.counts import match, pooled

    true = [[100.0, 200.0], [1000.0, 1100.0], [3500.0, 3600.0]]
    found = [[1080.0, 1140.0], [2000.0, 2050.0]]
    c = match(true, found, 120.0)
    assert (c["matched"], c["missed"], c["false"]) == (1, 2, 1)
    assert c["timing"] == [60.0]
    assert match(true, found, 30.0)["matched"] == 0
    c = match(true, found + [[3540.0, 3590.0]], 120.0, edge=[False, False, True])
    assert (c["true"], c["matched"], c["missed"], c["false"]) == (2, 1, 1, 1)
    recs = [{"true": true, "true_edge": None, "histories": {"s": {"spans": found}}}]
    p = pooled(recs, "s")
    assert p["120"]["missed_share"] == pytest.approx(2 / 3)
    assert p["60"]["matched"] == 0 and p["240"]["matched"] == 1


def test_paired_ratio_and_gain_share() -> None:
    from tma2.timelate.study import gain_share, paired, verdict, wilson

    rng = np.random.default_rng(1)
    base = np.exp(rng.normal(-2.0, 0.3, 200))
    whole = base / 2.0
    part = base / np.sqrt(2.0)
    p = paired(base, whole)
    assert p["geometric_mean"] == pytest.approx(2.0)
    assert p["a_better"] == 0.0 and p["lo"] <= 2.0 <= p["hi"]
    assert verdict(p, 1.10) == "material"
    assert verdict({"lo": 0.9, "hi": 1.3}, 1.10) == "inconclusive"
    assert verdict({"lo": 0.9, "hi": 1.05}, 1.10) == "not material"
    g = gain_share(base, part, whole)
    assert g["share"] == pytest.approx(0.5)
    same = paired(base, base)  # a composite equal to the search on every period
    assert same["geometric_mean"] == 1.0 and same["lo"] == 1.0
    w = wilson(200, 400)
    assert w["hi"] - w["lo"] < 0.10


def test_classes_follow_the_evidence_difference() -> None:
    from tma2.timelate.study import classify

    def rec(true_ev: float, cand: list[list[float]]) -> dict[str, Any]:
        return {
            "true": [[900.0, 1000.0]],
            "true_evidence": true_ev,
            "candidates": [{"spans": cand, "evidence": -100.0}],
        }

    assert classify(rec(-90.0, [[910.0, 990.0]]), 3.0, 120.0) == "right"
    assert classify(rec(-99.0, []), 3.0, 120.0) == "ambiguous"
    assert classify(rec(-101.5, []), 3.0, 120.0) == "ambiguous"
    assert classify(rec(-90.0, []), 3.0, 120.0) == "search_failure"
    assert classify(rec(-110.0, []), 3.0, 120.0) == "evidence_failure"
    assert classify(rec(-99.0, []), 0.5, 120.0) == "search_failure"
    assert classify({"true": [], "candidates": []}, 3.0, 120.0) is None


def test_c2_refit_keeps_the_given_manoeuvres_and_never_searches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import tma2.timelate.search as search
    from tma2.timelate.arc import arc_states
    from tma2.timelate.controls import c2_refit
    from tma2.timelate.run import nominal_starts

    def boom(*_a: Any, **_k: Any) -> None:
        raise AssertionError("the refit control must not search over histories")

    monkeypatch.setattr(search, "evidence_search", boom)
    pb, spans, theta = _problem(3)
    prior = ManoeuvrePrior.from_ranges(RANGES, version=2)
    late = spans + 60.0  # a causal segmenter's times: late
    track = arc_states(theta, pb[0], spans)
    g, kinds, ev = c2_refit(pb, late, track, prior, nominal_starts(pb))
    assert g.spans.shape == spans.shape and kinds.shape == (2, 2)
    assert np.isfinite(ev["total"])
    assert float(np.abs(g.spans.mean(axis=1) - spans.mean(axis=1)).max()) < 120.0


def test_thinning_forms() -> None:
    from tma2.timelate.arc import fit_arc
    from tma2.timelate.thin import thin

    pb, spans, theta = _problem(11)
    t, ox, oy, z, v, sigma = pb
    assert thin(pb, "none") is pb
    one = thin(pb, "fixed:1")
    wrapped = (one[3] - z + np.pi) % (2 * np.pi) - np.pi
    assert np.allclose(one[0], t) and np.allclose(wrapped, 0.0, atol=1e-12)
    assert np.allclose(one[5], sigma)
    d = thin(pb, "drop:4")
    assert int(d[4].sum()) == (int(v.sum()) + 3) // 4 and d[0] is t
    f = thin(pb, "fixed:6")
    assert f[0].size == -(-t.size // 6)
    assert np.allclose(np.asarray(f[5])[:-1], sigma / np.sqrt(6.0))
    a = thin(pb, "adaptive:3.0")
    assert t.size // 2 >= a[0].size >= t.size // 24
    full = fit_arc(t, ox, oy, z, v, sigma, spans, theta)
    thinned = fit_arc(f[0], f[1], f[2], f[3], f[4], f[5], spans, theta)
    assert np.allclose(thinned.theta[:2], full.theta[:2], atol=150.0)
    wild = z.copy()
    wild[100] += 0.3  # 17 sd
    plain = thin((t, ox, oy, wild, v, sigma), "adaptive:3.0")
    robust = thin((t, ox, oy, wild, v, sigma), "adaptive:3.0:robust")
    clean = thin(pb, "adaptive:3.0:robust")

    def worst(p: Any) -> float:
        k = int(np.argmin(np.abs(p[0] - t[100])))
        j = int(np.argmin(np.abs(clean[0] - p[0][k])))
        return float(abs(p[3][k] - clean[3][j]))

    assert worst(robust) < worst(plain)
    with pytest.raises(ValueError):
        thin(pb, "wavelet:3")


def test_smoother_equals_the_filter_at_the_end_and_does_not_hurt_on_a_held_course() -> None:
    from tma2.references.classical import BearingData
    from tma2.timelate.smooth import ekf_rts, rows_from_points

    n = 360
    t = np.arange(n) * 10.0
    ox = np.where(t < 900, 4.0 * t, 3600.0)
    oy = np.where(t < 900, 0.0, 4.0 * (t - 900.0))
    tx, ty = 2000.0 + 3.0 * t, 9000.0 - 2.0 * t
    rng = np.random.default_rng(4)
    sigma = 0.0175
    z = np.arctan2(tx - ox, ty - oy) + sigma * rng.standard_normal(n)
    d = BearingData(t, ox, oy, z, np.ones(n, dtype=np.uint8), 95, sigma, 0)
    sm, fl = ekf_rts(d, 0.00003, 4.0, 0.5)
    assert np.isfinite(fl[-1]).all() and np.allclose(sm[-1], fl[-1])
    assert np.isfinite(sm).all() and not np.isfinite(fl[:90]).any()
    k = np.isfinite(fl[:, 0])
    truth = np.stack([tx, ty], axis=1)
    e_s = np.hypot(*(sm[k, :2] - truth[k]).T)
    e_f = np.hypot(*(fl[k, :2] - truth[k]).T)
    assert float(np.median(e_s)) <= float(np.median(e_f))
    assert rows_from_points(sm, 2, 2 * n).shape == (2 * n, 4)
