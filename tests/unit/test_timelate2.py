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
