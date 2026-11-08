"""β-NLL of the 4-state Gaussian with a rescaled covariance (spec 008 research R5, R6 as amended).

The covariance is rescaled in local coordinates (log range, bearing, speed, course): their
standard deviations by e^(s_i), correlations kept. With a row's local error u and raw local
information W (``calib.data``), the NEES is q(s) = Σ_ij u_i u_j W_ij e^(−s_i − s_j) and the
negative log-likelihood (constants dropped) is ½ q(s) + Σ_i s_i. A scalar s (the same in all
four) gives ½ e^(−2s) q + 4s, minimised at s = ½ log(q / 4).

β-NLL (Seitzer et al. 2022) weights each row by the stop-gradient of its variance scale to the
power β, here e^(2β·mean(s)), so rows stated as very uncertain do not dominate.

``cap`` bounds each row's raw NEES: a row whose q(0) exceeds it has its error shrunk to it
(q multiplied by cap / q(0)). A gross row can then pull its own scale up but cannot, alone, set
the scale for every other row, and it keeps a gradient (a capped *term* would pass none, and the
head could never learn to widen the rows that need it most).
"""

from __future__ import annotations

import torch
from torch import Tensor


def _four(s: Tensor) -> Tensor:
    """[N] or [N, 1] or [N, 4] → [N, 4]."""
    if s.dim() == 1:
        s = s.unsqueeze(1)
    return s.expand(-1, 4)


def nees(s: Tensor, u: Tensor, w: Tensor) -> Tensor:
    """[N] q(s) for local errors u [N, 4] and information w [N, 4, 4]."""
    v = u * torch.exp(-_four(s))
    return torch.einsum("ni,nij,nj->n", v, w, v)


def nll(s: Tensor, u: Tensor, w: Tensor, cap: float) -> Tensor:
    """[N] per-row Gaussian negative log-likelihood (constants dropped), raw NEES capped."""
    q0 = torch.einsum("ni,nij,nj->n", u, w, u)
    f = torch.clamp(cap / q0, max=1.0).detach()
    return 0.5 * f * nees(s, u, w) + _four(s).sum(dim=1)


def beta_nll(s: Tensor, u: Tensor, w: Tensor, beta: float, cap: float) -> Tensor:
    """Mean over rows of the β-weighted NLL. Rows must be usable (finite raw NEES)."""
    term = nll(s, u, w, cap)
    wt = torch.exp(2.0 * beta * _four(s).mean(dim=1)).detach()
    return (wt * term).sum() / wt.sum()


def score(s: Tensor, u: Tensor, w: Tensor, cap: float) -> float:
    """The validation score: mean NLL, no β weighting (lower is better)."""
    return float(nll(s, u, w, cap).mean())
