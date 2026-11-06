"""Gate 2's robust loss (spec 007 T014)."""

from __future__ import annotations

import torch

from tma2.gate2.loss import e_loss, trimmed_mean
from tma2.gate2.model import EOutput


def _out(n: int, cost: list[float], state_off: float = 0.0) -> tuple[EOutput, torch.Tensor]:
    truth = torch.tensor([[5000.0, 5000.0, 3.0, -2.0]] * n)
    st = truth.clone()
    st[:, 0] += state_off
    ok = torch.ones(n, dtype=torch.bool)
    z = torch.zeros(n)
    out = EOutput(
        st,
        torch.eye(4).repeat(n, 1, 1),
        ok,
        ok,
        torch.tensor(cost),
        st.clone(),
        torch.zeros(n, 3),
        z,
        z,
        z,
    )
    return out, truth


def test_failed_fits_are_excluded_and_terms_capped() -> None:
    torch.set_default_dtype(torch.float64)
    out, truth = _out(3, [10.0, 10.0, 1e6], state_off=4000.0)
    bc = torch.diag(torch.tensor([100.0, 100.0, 0.01, 0.01])).repeat(3, 1, 1)
    z = torch.zeros(3)
    loss = e_loss(out, truth, bc, z, z, torch.full((3,), 100), cap=50.0)
    assert loss.kept.tolist() == [True, True, False] and loss.excluded_failed_fits == 1
    assert torch.all(loss.per_prefix <= 50.0) and float(loss.per_prefix.max()) == 50.0


def test_zero_error_gives_zero_loss() -> None:
    torch.set_default_dtype(torch.float64)
    out, truth = _out(2, [1.0, 1.0])
    bc = torch.diag(torch.tensor([100.0, 100.0, 0.01, 0.01])).repeat(2, 1, 1)
    z = torch.zeros(2)
    assert float(e_loss(out, truth, bc, z, z, torch.full((2,), 50)).total) == 0.0


def test_trimmed_mean_ignores_one_outlier() -> None:
    v = torch.tensor([1.0] * 19 + [96000.0])
    assert trimmed_mean(v, 0.1) == 1.0
