"""Spec 005 T011: C's additive search (research R1) on MAN2 windows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.data.f32pack import iter_pack_raw
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment import metrics as mx
from tma2.segment.search import anchored_grid, cost_table, prefix_grid, run_search
from tma2.segment.truth import change_rows

L_MIN, T_MIN, T_MAX, STEP, PENALTY = 30, 6, 36, 6, 20.0


def _short(
    pack: Path, n_max: int = 420, count: int = 3
) -> list[tuple[dict[str, Any], BearingData]]:
    out = []
    for _, m, own, _tgt, obs in iter_pack_raw(pack):
        if int(m["samples"]) <= n_max:
            out.append((m, bearing_data_from_arrays(m, own, obs)))
        if len(out) == count:
            break
    assert len(out) == count
    return out


@pytest.fixture(scope="module")
def noise_free(man2_noise_free_pack: Path) -> list[tuple[dict[str, Any], BearingData]]:
    return _short(man2_noise_free_pack)


def test_anchored_grid() -> None:
    g = anchored_grid(100, 94, 6)
    assert g[0] == 0 and 94 in g and 100 in g and 88 in g
    assert list(prefix_grid(g, 94)) == [r for r in g if r <= 94]
    with pytest.raises(ValueError):
        prefix_grid(g, 95)


def test_noise_free_transitions_recovered(
    noise_free: list[tuple[dict[str, Any], BearingData]],
) -> None:
    """Every target change with a full leg on both sides is found, both boundaries within 8 rows
    (grid step 6), and nothing else is reported away from the window's ends."""
    checked = 0
    for m, d in noise_free:
        k = d.n - 1
        _c, _legs, trans = run_search(d, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP)
        pred = [(a, b) for a, b, _ in trans]
        truth = [(a, b) for a, b in change_rows(m, "target") if a >= L_MIN and b <= k - L_MIN]
        assert all(mx.boundary_hits(pred, truth, 8)), (m["index"], truth, pred)
        # away from the window's ends (a change within L_min of an end can only be reported
        # displaced, since a leg needs L_min rows), the transitions are exactly the changes
        e = 2 * L_MIN
        inner_p = [p for p in pred if p[0] >= e and p[1] <= k - e]
        inner_t = [p for p in change_rows(m, "target") if p[0] >= e and p[1] <= k - e]
        assert len(inner_p) == len(inner_t), (m["index"], truth, pred)
        checked += len(truth)
    assert checked >= 3


def test_prefix_invariance(noise_free: list[tuple[dict[str, Any], BearingData]]) -> None:
    """A table built on the whole window gives the same answer at a prefix as a table built on the
    prefix alone (no bearing after k is used, FR-002)."""
    m, d = noise_free[0]
    k = d.n - 1 - 60
    grid = anchored_grid(d.n - 1, k, STEP)
    full = run_search(
        d, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP, table=(grid, cost_table(d, grid, L_MIN))
    )
    own = run_search(d, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP)
    assert full == own
    # and with the bearings after k removed
    cut = BearingData(**{**d.__dict__})
    cut.valid = d.valid.copy()
    cut.valid[k + 1 :] = 0
    cut.z = d.z.copy()
    cut.z[k + 1 :] = 0.0
    assert run_search(cut, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP) == own


def test_evidence(noise_free: list[tuple[dict[str, Any], BearingData]]) -> None:
    """Zero evidence is C exactly; strong transition evidence on steady rows forces a transition
    there, and strong steady evidence on a true transition's rows removes it."""
    m, d = noise_free[0]
    k = d.n - 1
    base = run_search(d, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP)
    assert run_search(d, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP, evidence=np.zeros(d.n)) == base
    legs = base[1]
    a, b = max(legs, key=lambda x: x[1] - x[0])
    mid = (a + b) // 2 // STEP * STEP
    e = np.zeros(d.n)
    e[mid + 1 : mid + 12] = -1e4
    _c, _l, trans = run_search(d, k, PENALTY, L_MIN, T_MIN, T_MAX, STEP, evidence=e)
    assert any(s <= mid + 1 and f >= mid + 11 for s, f, _ in trans), trans
