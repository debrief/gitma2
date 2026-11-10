"""Bearing-error covariance and whitening (spec 010 research R3).

The Gaussian part of the mismatch error has covariance

    Σ_ij = σ_w² δ_ij + σ_c² exp(−|t_i − t_j| / τ_c) + σ_b² exp(−|t_i − t_j| / τ_b) + v_i δ_ij

on the samples used (valid, up to the row), built from their times so that dropouts need no
special case. ``v`` is an extra per-sample variance: the outlier variance at flagged samples
(realisation ceiling), a mixture-responsibility inflation (attainable ceiling) or a Huber
inflation (robust control). The whitening operator is W = L⁻¹ with Σ = L Lᵀ, embedded in the
window's rows; a whitened residual W r has identity covariance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ErrorModel:
    """Parameters of the Gaussian part (radians, seconds). A zero sd switches a term off."""

    sigma_w: float
    sigma_c: float = 0.0
    tau_c: float = 0.0
    sigma_b: float = 0.0
    tau_b: float = 0.0

    @property
    def marginal_var(self) -> float:
        return self.sigma_w**2 + self.sigma_c**2 + self.sigma_b**2


def covariance(t: np.ndarray, model: ErrorModel, extra_var: np.ndarray | None = None) -> np.ndarray:
    """Σ on sample times ``t`` [n]."""
    n = t.shape[0]
    cov = np.zeros((n, n))
    lag = np.abs(t[:, None] - t[None, :])
    if model.sigma_c > 0.0:
        cov += model.sigma_c**2 * np.exp(-lag / model.tau_c)
    if model.sigma_b > 0.0:
        cov += model.sigma_b**2 * np.exp(-lag / model.tau_b)
    d = np.full(n, model.sigma_w**2)
    if extra_var is not None:
        d = d + extra_var
    cov[np.diag_indices(n)] += d
    return cov


def whitener(
    t: np.ndarray,
    use: np.ndarray,
    model: ErrorModel,
    extra_var: np.ndarray | None = None,
) -> np.ndarray:
    """W [R, R]: L⁻¹ of the covariance on the rows where ``use`` is true, zero elsewhere.

    ``extra_var`` [R] is read on the used rows. With a white model and no extra variance this is
    diag(use / σ_w), the physics layer's own weighting."""
    r = t.shape[0]
    idx = np.flatnonzero(use)
    w = np.zeros((r, r))
    if idx.size == 0:
        return w
    ev = extra_var[idx] if extra_var is not None else None
    if model.sigma_c <= 0.0 and model.sigma_b <= 0.0:
        var = np.full(idx.size, model.sigma_w**2)
        if ev is not None:
            var = var + ev
        w[idx, idx] = 1.0 / np.sqrt(var)
        return w
    chol = np.linalg.cholesky(covariance(t[idx], model, ev))
    linv = np.linalg.solve(chol, np.eye(idx.size))
    w[np.ix_(idx, idx)] = linv
    return w
