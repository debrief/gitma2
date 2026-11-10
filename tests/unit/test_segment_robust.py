"""Spec 011: C-r (``segment/robust.py``). C stays frozen; C-r with plain costs is C; a robust
test survives a wild bearing; prefixes do not depend on later bearings."""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path

import numpy as np

from tma2.cli.segment import params_digest
from tma2.data.f32pack import iter_pack_raw
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment.codeid import code_digest
from tma2.segment.inputs import segmentation_inputs
from tma2.segment.robust import (
    RawLayer,
    RobustConfirm,
    huber_factor,
    robust_costs,
    robust_segmentations,
    scale_at,
)
from tma2.segment.score import g5_rows
from tma2.segment.segmenter import segment
from tma2.types.generated.tma import SegmentParameters

ROOT = Path(__file__).resolve().parents[2]
C_CODE = "4d2c084f288fa12034413a6a71ef741ca0b468eece24ea349d82d8494f55db27"
C_PARAMS = "60e6ee635d9390e2c959b408997e39e8c30859febcb2d86f199142ea66aa425f"


def _params() -> SegmentParameters:
    plan = ROOT / "configs" / "segment" / "gs-plan.json"
    return SegmentParameters(**json.loads(plan.read_text())["segmenter"]["parameters"])


def _scenario(pack: Path) -> tuple[dict, BearingData]:  # type: ignore[type-arg]
    _, m, own, _tgt, obs = next(
        x for x in iter_pack_raw(pack) if int(x[1]["samples"]) <= 420 and x[1]["manoeuvres"]
    )
    return m, bearing_data_from_arrays(m, own, obs)


def test_c_is_frozen() -> None:
    assert code_digest() == C_CODE
    assert params_digest(_params()) == C_PARAMS


def test_huber_factor() -> None:
    assert math.isclose(huber_factor(2.0), 0.96442, abs_tol=1e-4)
    assert math.isclose(huber_factor(50.0), 1.0, abs_tol=1e-12)


def test_scale_on_white_noise() -> None:
    rng = np.random.default_rng(5)
    n = 600
    sigma = math.radians(1.0)
    z = 0.3 + 1e-4 * np.arange(n) + sigma * rng.standard_normal(n)
    d = BearingData(
        t=10.0 * np.arange(n),
        ox=np.zeros(n),
        oy=np.zeros(n),
        z=z,
        valid=np.ones(n, dtype=np.uint8),
        zig_index=300,
        sigma=2.0 * sigma,
        index=0,
    )
    assert abs(scale_at(d, n - 1) / sigma - 1.0) < 0.1
    assert scale_at(d, 10) == d.sigma  # too few differences: the stated σ


def test_plain_costs_are_c(man2_pack: Path) -> None:
    """``robust = False``, factor 1: the segmentation is C's, interval for interval."""
    p = _params()
    m, d = _scenario(man2_pack)
    ks = g5_rows(m, d.n)[:2]
    want = segment(PhysicsLayer(), [d], [m], [ks], p)[0]
    got, _ = robust_segmentations([d], [ks], p, RobustConfirm(robust=False))
    assert [got[0][s.k] for s in want] == [s.intervals for s in want]


def test_wild_bearing_cost_is_bounded(man2_pack: Path) -> None:
    """A 30 σ bearing adds about 900 to the plain cost and at most 2k·30 − k² to the Huber
    cost; the costs are finite and the robust fit is not dragged."""
    m, d = _scenario(man2_pack)
    k = g5_rows(m, d.n)[0]
    z = d.z.copy()
    z[k - 40] += 30.0 * d.sigma
    bad = dataclasses.replace(d, z=z)
    cfg = RobustConfirm()
    plain = RobustConfirm(robust=False)

    def cost(dd: BearingData, c: RobustConfirm) -> float:
        inp = segmentation_inputs(dd.t, dd.ox, dd.oy, dd.z, dd.valid, k, [], "chord", False)
        assert inp is not None
        return robust_costs(RawLayer(), [(dd, k, inp)], c, dd.n)[0]

    add_plain = cost(bad, plain) - cost(d, plain)
    add_robust = cost(bad, cfg) - cost(d, cfg)
    assert math.isfinite(add_robust)
    assert add_plain > 500.0
    assert add_robust < (2 * 2.0 * 31.0) / huber_factor(2.0)


def test_prefix_does_not_read_later_bearings(man2_pack: Path) -> None:
    p = _params()
    m, d = _scenario(man2_pack)
    k = g5_rows(m, d.n)[0]
    z = d.z.copy()
    z[k + 1 :] += 0.2
    other = dataclasses.replace(d, z=z)
    cfg = RobustConfirm(scale="estimated")
    a, _ = robust_segmentations([d], [[k]], p, cfg)
    b, _ = robust_segmentations([other], [[k]], p, cfg)
    assert a[0][k] == b[0][k]
