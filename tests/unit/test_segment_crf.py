"""Spec 005 T029: L's semi-Markov likelihood (research R6)."""

from __future__ import annotations

import math

import numpy as np
import torch

from tma2.segment import STEADY, TRANSITION, UNKNOWN
from tma2.segment.crf import Lattice, aux_loss
from tma2.segment.search import search

L_MIN, T_MIN, T_MAX, PEN = 4, 2, 4, 3.0


def _toy(seed: int = 0, n: int = 24) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    grid = np.arange(n, dtype=np.int64)
    cost = np.full((n, n), np.inf)
    for i in range(n):
        for j in range(i + 1, n):
            if j - i + 1 >= L_MIN:
                cost[i, j] = (j - i + 1) + rng.uniform(0, 6) * (j - i + 1) / 8
    valid = (rng.uniform(size=n) > 0.1).astype(np.int64)
    return grid, cost, valid


def _paths(lat: Lattice) -> list[tuple[list[tuple[int, int]], bool]]:
    """Every lattice segmentation by brute force."""
    g = lat.g
    legs_ok = {(i, j) for i, j, _ in lat.legs}
    tr_ok = {(p, i) for p, i, _ in lat.trans}
    op_ok = {p for p, _ in lat.open}
    out = []

    def rec(seq: list[tuple[int, int]]) -> None:
        j = seq[-1][1]
        if j == g - 1:
            out.append((list(seq), False))
        if j in op_ok:
            out.append((list(seq), True))
        for i in range(j + 1, g):
            if (j, i) in tr_ok:
                for jj in range(i + 1, g):
                    if (i, jj) in legs_ok:
                        rec([*seq, (i, jj)])

    for j in range(1, g):
        if (0, j) in legs_ok:
            rec([(0, j)])
    return out


def test_log_partition_equals_enumeration() -> None:
    torch.set_default_dtype(torch.float64)
    grid, cost, valid = _toy()
    lat = Lattice(grid, cost, valid, PEN, T_MIN, T_MAX)
    e = torch.tensor(np.random.default_rng(1).normal(size=grid[-1] + 1) * 0.5)
    paths = _paths(lat)
    assert len(paths) > 50
    brute = torch.logsumexp(torch.stack([lat.path_score(lg, o, e) for lg, o in paths]), 0)
    assert abs(float(lat.log_partition(e) - brute)) < 1e-9


def test_best_path_is_the_search() -> None:
    """−2 × the best path's score is the search's minimum cost, with the same evidence."""
    torch.set_default_dtype(torch.float64)
    grid, cost, valid = _toy(2)
    lat = Lattice(grid, cost, valid, PEN, T_MIN, T_MAX)
    ev = np.random.default_rng(3).normal(size=grid[-1] + 1) * 0.3
    e = torch.tensor(ev)
    best = max(float(lat.path_score(lg, o, e)) for lg, o in _paths(lat))
    c, _seg = search(cost, grid, valid, ev, PEN, T_MIN, T_MAX, 1.0)
    assert math.isclose(-2.0 * best, c, rel_tol=1e-12)


def test_truth_path_and_gradient_at_zero() -> None:
    torch.set_default_dtype(torch.float64)
    grid, cost, valid = _toy(4)
    lat = Lattice(grid, cost, valid, PEN, T_MIN, T_MAX)
    n = grid[-1] + 1
    codes = np.full(n, STEADY, dtype=np.int8)
    codes[9:12] = TRANSITION
    codes[:2] = UNKNOWN
    legs, open_end = lat.truth_path(codes)
    assert legs[0][1] == 8 and legs[1][0] == 12 and not open_end
    e = torch.zeros(n, requires_grad=True)
    loss = lat.nll(e, codes)
    (g,) = torch.autograd.grad(loss, e)
    assert torch.isfinite(g).all() and float(g.abs().max()) > 1e-3
    # finite differences
    h = 1e-6
    for r in (3, 10, 20):
        ep = torch.zeros(n)
        ep[r] = h
        em = torch.zeros(n)
        em[r] = -h
        fd = (float(lat.nll(ep, codes)) - float(lat.nll(em, codes))) / (2 * h)
        assert abs(fd - float(g[r])) < 1e-6, (r, fd, float(g[r]))
    # every path's score is finite and the loss is non-negative
    assert float(loss) >= 0.0


def test_aux_loss() -> None:
    codes = np.array([UNKNOWN, STEADY, STEADY, TRANSITION], dtype=np.int8)
    e = torch.tensor([0.0, 5.0, 5.0, -5.0])
    assert float(aux_loss(e, codes, 4)) < 0.01
    assert float(aux_loss(-e, codes, 4)) > 4.0
    assert float(aux_loss(e, np.full(4, UNKNOWN, np.int8), 4)) == 0.0


def test_vectorised_partition_equals_reference() -> None:
    """The vectorised recursion equals the reference one, value and gradient."""
    torch.set_default_dtype(torch.float64)
    for seed in (0, 2, 4):
        grid, cost, valid = _toy(seed)
        lat = Lattice(grid, cost, valid, PEN, T_MIN, T_MAX)
        e1 = torch.tensor(np.random.default_rng(seed).normal(size=grid[-1] + 1), requires_grad=True)
        e2 = e1.detach().clone().requires_grad_(True)
        z1, z2 = lat.log_partition(e1), lat.log_partition_reference(e2)
        assert abs(float(z1 - z2)) < 1e-9
        z1.backward()  # type: ignore[no-untyped-call]
        z2.backward()  # type: ignore[no-untyped-call]
        assert e1.grad is not None and e2.grad is not None
        assert float((e1.grad - e2.grad).abs().max()) < 1e-9
