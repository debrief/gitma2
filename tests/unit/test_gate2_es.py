"""E-s (spec 007 T019): the vectorised relaxed loss is ``tables.relaxed_loss``; untrained E-s is C
(its hard loss is C's error on the decision rows); training lowers the hard loss where the
features say which side of a decision is better; the shuffled labels keep the error pairs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from tma2.gate2.es import (
    ESExample,
    ESSettings,
    evaluate,
    example_of,
    make_net,
    shuffled_labels,
    terms,
    train_es,
)
from tma2.gate2.tables import DecisionRow, ScenarioTable, relaxed_loss
from tma2.segment.confirm import Decision

N, C = 120, 3


def _table(rng: np.random.Generator) -> ScenarioTable:
    ds, rows = [], []
    for q in range(4):
        a = 30 + 20 * q
        start = a - 12
        drop = 13.8 + rng.uniform(-6, 6)
        ds.append(Decision(a, start, 18, "glr", drop, 13.8, drop > 13.8))
        rows.append(DecisionRow(q, a + 5, float(rng.uniform(0, 9)), float(rng.uniform(0, 9))))
    return ScenarioTable(ds, rows, {}, 13.8)


def test_vectorised_matches_reference() -> None:
    torch.set_default_dtype(torch.float64)
    rng = np.random.default_rng(1)
    t = _table(rng)
    x = example_of(0, np.zeros((C, N)), t)
    e = torch.tensor(rng.normal(0, 0.3, N))
    got, _ = terms(e, x, 0.7, None)
    assert float(got.sum()) == pytest.approx(float(relaxed_loss(t, e, 0.7)), rel=1e-12)


def test_untrained_is_c() -> None:
    torch.set_default_dtype(torch.float64)
    rng = np.random.default_rng(2)
    xs = [example_of(i, rng.normal(size=(C, N)), _table(rng)) for i in range(5)]
    net = make_net(ESSettings(width=8, dilations=(1, 2)), C)
    c = np.concatenate([np.where(x.margin > 0, x.e_with, x.e_without) for x in xs])
    assert evaluate(net, xs, 2) == pytest.approx(float(c.mean()), rel=1e-12)


def _learnable(rng: np.random.Generator, i: int) -> ESExample:
    """Every decision is near its threshold; channel 0 is +1 on a candidate's rows when keeping
    the transition is worse (steady evidence should raise the threshold), −1 when it is better."""
    feats = np.zeros((C, N))
    t = _table(rng)
    rows = []
    for q, d in enumerate(t.decisions):
        d.drop, d.accepted = 13.8 + rng.uniform(-1, 1), False
        d.accepted = d.drop > d.threshold
        better = bool(rng.integers(2))
        feats[0, d.start : d.row + 1] = -1.0 if better else 1.0
        rows.append(DecisionRow(q, d.row + 5, 1.0 if better else 9.0, 5.0))
    return example_of(i, feats, ScenarioTable(t.decisions, rows, {}, t.tau))


def test_training_lowers_hard_loss(tmp_path: Path) -> None:
    rng = np.random.default_rng(3)
    train = [_learnable(rng, i) for i in range(48)]
    val = [_learnable(rng, 100 + i) for i in range(16)]
    st = ESSettings(
        width=8,
        kernel=3,
        dilations=(1, 2),
        learning_rate=1e-2,
        batch=8,
        max_epochs=8,
        patience=8,
        temperature=1.0,
    )
    meta = train_es(st, train, val, tmp_path / "ck", {"git_commit": "x"}, log=lambda _s: None)
    assert meta["best_val"] < 0.8 * meta["untrained_val"]
    assert (tmp_path / "ck" / "best.safetensors").exists() and meta["weights_sha256"]
    again = train_es(st, train, val, tmp_path / "ck", {"git_commit": "x"}, log=lambda _s: None)
    assert again["epoch"] == meta["epoch"] and len(again["jobs"]) == 2  # complete: resumes idle


def test_shuffled_labels_keep_pairs() -> None:
    rng = np.random.default_rng(4)
    xs = [example_of(i, np.zeros((C, N)), _table(rng)) for i in range(6)]
    lab = shuffled_labels(xs, 9)
    pairs = sorted(
        zip(
            np.concatenate([x.e_with for x in xs]),
            np.concatenate([x.e_without for x in xs]),
            strict=True,
        )
    )
    got = sorted(
        zip(np.concatenate([w for w, _ in lab]), np.concatenate([o for _, o in lab]), strict=True)
    )
    assert pairs == got and [len(w) for w, _ in lab] == [x.e_with.size for x in xs]
