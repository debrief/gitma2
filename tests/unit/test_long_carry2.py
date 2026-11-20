"""Spec 027: the runner keeps ``ctl`` and ``ctl-carry`` exactly as spec 026's."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tma2.long import carry, carry2
from tma2.long.sim import generate
from tma2.long.timelate import chain, settings_and_priors

ROOT = Path(__file__).resolve().parents[2]


def test_carry2_equals_carry_and_hands_on() -> None:
    c = json.loads((ROOT / "configs/long/long.json").read_text())
    r = json.loads((ROOT / c["target_ranges"]).read_text())
    e = generate(int(c["seed"]), 1, 6.0, c, r)
    spans = chain(e, 1800.0, 600.0)[:2]
    s, priors, cpar, c2 = settings_and_priors()
    s = dict(s)
    s["steps"] = 2
    old = carry.run_chain(e, spans, 0, len(spans), s, priors, cpar, c2)
    new = carry2.run_chain2(
        e, spans, s, priors, cpar, c2, {"scale": 2.0, "tail_s": 600.0, "alpha": 0.001}
    )
    for w0, w1 in zip(old, new, strict=True):
        for k in ("ctl-d1-q0.01", "ctl-carry", "c2", "history-map"):
            assert np.array_equal(w0["tracks"][k], w1["tracks"][k], equal_nan=True), k
    # the first window has nothing carried: ctl-prior is ctl
    assert np.array_equal(new[0]["tracks"]["ctl-prior"], new[0]["tracks"]["ctl-d1-q0.01"])
    # the second was handed an estimate and ran the guard
    h = new[1]["handed"]
    assert "mean" in h and np.all(np.linalg.eigvalsh(np.array(h["cov"])) > 0)
    assert new[1]["guard"] is not None and np.isfinite(new[1]["guard"]["D"])
    assert np.isfinite(new[1]["tracks"]["ctl-prior"]).all()
