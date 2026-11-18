"""Spec 027: the carried prior (``tma2.long.carried``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.long.carried import (
    CarriedPrior,
    elimination_path_c,
    evidence_search_c,
    guard,
    hand_on,
    joint_fit_c,
    log_evidence_c,
    widen,
)
from tma2.long.sim import generate
from tma2.long.timelate import period_of

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def setup() -> dict[str, Any]:
    from tma2.timelate.prior import ManoeuvrePrior

    c = json.loads((ROOT / "configs/long/long.json").read_text())
    r = json.loads((ROOT / c["target_ranges"]).read_text())
    e = generate(int(c["seed"]), 1, 6.0, c, r)
    p = period_of(e, 600, 240, 0)  # 20 minutes, no target manoeuvre
    assert not p.meta["manoeuvres"]
    t = p.own[:, 0].astype(np.float64) - float(p.own[0, 0])
    pb = (
        t,
        p.own[:, 1].astype(np.float64),
        p.own[:, 2].astype(np.float64),
        p.obs[:, 1].astype(np.float64),
        p.obs[:, 2] != 0,
        float(p.meta["parameters"]["noise_sigma_rad"]),
    )
    prior = ManoeuvrePrior.from_ranges(json.loads((ROOT / c["target_ranges"]).read_text()), 3)
    truth = p.tgt.astype(np.float64)
    th0 = np.array([truth[0, 1] + 800.0, truth[0, 2] - 500.0, truth[0, 3] + 0.2, truth[0, 4]])
    return {"pb": pb, "prior": prior, "truth": truth, "th0": th0}


def test_no_carried_prior_equals_the_original(setup) -> None:  # type: ignore[no-untyped-def]
    from tma2.timelate.hedge import elimination_path
    from tma2.timelate.retest import joint_fit, log_evidence
    from tma2.timelate.search import evidence_search

    pb, prior, th0 = setup["pb"], setup["prior"], setup["th0"]
    none = np.zeros((0, 2))
    kinds = np.zeros((0, 2), dtype=bool)
    a = joint_fit(pb, th0, none, free_changes=kinds, prior=prior)
    b = joint_fit_c(pb, th0, none, free_changes=kinds, prior=prior, cp=None)
    assert np.array_equal(a.theta, b.theta) and a.cost == b.cost
    assert log_evidence(pb, a, kinds, prior) == log_evidence_c(pb, b, kinds, prior, None)
    h1, s1 = evidence_search(pb, th0, none, prior, 3, 2)
    h2, s2 = evidence_search_c(pb, th0, none, prior, None, 3, 2)
    assert len(s1) == len(s2)
    assert all(x.evidence == y.evidence for x, y in zip(s1, s2, strict=True))
    assert np.array_equal(h1.fit.states, h2.fit.states)
    p1 = elimination_path(pb, h1, prior)
    p2 = elimination_path_c(pb, h2, prior, None)
    assert [x.evidence for x in p1] == [x.evidence for x in p2]


def test_carried_prior_pulls_and_guard_reads_it(setup) -> None:  # type: ignore[no-untyped-def]
    pb, prior, th0, truth = setup["pb"], setup["prior"], setup["th0"], setup["truth"]
    none = np.zeros((0, 2))
    kinds = np.zeros((0, 2), dtype=bool)
    good = CarriedPrior(
        np.array([truth[0, 1], truth[0, 2], truth[0, 3], truth[0, 4]]),
        np.diag([200.0**2, 200.0**2, 0.05**2, 0.3**2]),
    )
    bad = CarriedPrior(good.mean + np.array([3000.0, -3000.0, 0.8, 2.0]), good.cov)
    f0 = joint_fit_c(pb, th0, none, free_changes=kinds, prior=prior)
    fg = joint_fit_c(pb, th0, none, free_changes=kinds, prior=prior, cp=good)
    e0 = np.hypot(f0.theta[0] - truth[0, 1], f0.theta[1] - truth[0, 2])
    eg = np.hypot(fg.theta[0] - truth[0, 1], fg.theta[1] - truth[0, 2])
    assert eg <= e0 + 1.0
    ev = log_evidence_c(pb, fg, kinds, prior, good)
    assert "carried" in ev and np.isfinite(ev["total"])
    hg, _ = evidence_search_c(pb, th0, none, prior, good, 2, 1)
    hb, _ = evidence_search_c(pb, th0, none, prior, bad, 2, 1)
    assert guard(pb, hg, prior, good) < guard(pb, hb, prior, bad)
    assert guard(pb, hb, prior, bad) > 18.47  # rejected at 0.001


def test_hand_on_recovers_the_state(setup) -> None:  # type: ignore[no-untyped-def]
    pb, prior, th0 = setup["pb"], setup["prior"], setup["th0"]
    none = np.zeros((0, 2))
    h, _ = evidence_search_c(pb, th0, none, prior, None, 3, 2)
    t_o = float(pb[0][200])
    ho = hand_on(pb, h, prior, None, t_o)
    assert ho is not None
    assert ho.t_o == t_o and ho.t_last < t_o
    assert np.all(np.linalg.eigvalsh(ho.cov) > 0)
    # the carried state agrees with the full window's track at t_o within a few sds
    st = h.fit.states[200]
    d = np.array([ho.mean[0] - st[0], ho.mean[1] - st[1]])
    sd = np.sqrt(np.diag(ho.cov)[:2])
    assert np.all(np.abs(d) < 6 * sd + 50.0)
    cov, info = widen(ho, prior, 2.0, 600.0)
    assert np.all(np.diag(cov) >= 2.0 * np.diag(ho.cov))
    assert info["tau_s"] >= 600.0
