"""β-NLL of the 4-state Gaussian with a scaled covariance (spec 008 research R6).

With the calibrated covariance e^(2s) · P and the raw NEES q = eᵀP⁻¹e, the negative
log-likelihood (dropping constants) is ½ e^(−2s) q + 4s, minimised at s = ½ log(q / 4). β-NLL
(Seitzer et al. 2022) weights each row by the stop-gradient of its variance to the power β,
here e^(2sβ), so rows stated as very uncertain do not dominate. Each row's term is capped
(``cap``) so that a gross row, whose q is enormous, cannot set the scale for every other row; a
capped term passes no gradient.
"""

from __future__ import annotations

import torch
from torch import Tensor


def nll(s: Tensor, q: Tensor) -> Tensor:
    """[N] per-row Gaussian negative log-likelihood (constants dropped)."""
    return 0.5 * torch.exp(-2.0 * s) * q + 4.0 * s


def beta_nll(s: Tensor, q: Tensor, beta: float, cap: float) -> Tensor:
    """Mean over rows of the capped, β-weighted NLL. Rows must be usable (finite q)."""
    term = torch.clamp(nll(s, q), max=cap)
    w = torch.exp(2.0 * beta * s).detach()
    return (w * term).sum() / w.sum()


def score(s: Tensor, q: Tensor, cap: float) -> float:
    """The validation score: mean capped NLL, no β weighting (lower is better)."""
    return float(torch.clamp(nll(s, q), max=cap).mean())
