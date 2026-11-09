"""Gate 5's criteria (spec 010 T006): verdict logic on synthetic statements (a fast version of
``scripts/research/g5_synthetic.py``, SC-003)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

from tma2.calib.gate5 import FAIL, PASS, criteria, not_outside

_spec = importlib.util.spec_from_file_location(
    "g5_synthetic", Path(__file__).parents[2] / "scripts/research/g5_synthetic.py"
)
assert _spec and _spec.loader
syn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(syn)


def test_not_outside() -> None:
    assert not_outside({"value": 0.07, "lo": 0.02, "hi": 0.12}, -0.05, 0.05) == PASS
    assert not_outside({"value": 0.2, "lo": 0.06, "hi": 0.3}, -0.05, 0.05) == FAIL


def test_calibrated_passes_and_offset_slice_fails() -> None:
    rng = np.random.default_rng(11)
    c, cl, sl = syn.dataset(rng, 0.0)
    err = np.zeros((c.shape[0], 3))
    r = criteria(c, {"t": c}, err, err, cl, sl, syn.BANDS, PASS, 0.975, 200)
    assert r["g5a"] == PASS and r["g5b"] != FAIL and r["g5e"] == PASS
    c2, cl2, sl2 = syn.dataset(rng, 0.15)
    err2 = np.zeros((c2.shape[0], 3))
    r2 = criteria(c2, {"t": c2}, err2, err2, cl2, sl2, syn.BANDS, PASS, 0.975, 200)
    assert r2["g5b"] == FAIL
    flagged = [x for x in r2["slices"] if x["slice"] == "proxy" and x["label"] == "flagged"]
    assert flagged and flagged[0]["verdict_reliability"] == FAIL


def test_points_changed_or_mass_error_fail_g5e() -> None:
    rng = np.random.default_rng(12)
    c, cl, sl = syn.dataset(rng, 0.0)
    err = np.zeros((c.shape[0], 3))
    assert criteria(c, {"t": c}, err, err + 1e-9, cl, sl, syn.BANDS, PASS, 0.975, 50)["g5e"] == FAIL
    assert (
        criteria(c, {"t": c}, err, err, cl, sl, syn.BANDS, PASS, 0.975, 50, max_mass_error=1e-3)[
            "g5e"
        ]
        == FAIL
    )
