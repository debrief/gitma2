"""The usable uncertainty statement (spec 009, research R2–R4).

**Course**: a mixture on the circle centred on E's course,
p · vonMises(0, κ) + (1 − p) · uniform, with κ = 1 / (a · sd)², sd E's stated course sd and a a
scale. The row states an arc half-width X = min(Xmax, 1.96 · a · sd) and its probability
P = p · Pvm(|e| ≤ X) + (1 − p) · X / π, where Pvm uses the normal approximation to the von Mises
(accurate for the small spreads the arc cap allows). Its proper score is the log density of the
mixture at the true (wrapped) course error.

**Range and speed**: 95% half-widths q = c · sd (ln range ratio; speed in m/s), scored by the 95%
central interval score (Gneiting and Raftery), whose minimiser is the 95% quantile of |e| / sd.

**Recalibration**: a monotone isotonic map (pool adjacent violators) from stated P to the observed
hit rate, fitted on tuning rows, applied to P only (the arc is unchanged).

Torch versions (``*_t``) are differentiable for training; NumPy versions are for scoring and files.
"""

from __future__ import annotations

import math

import numpy as np
import torch
from torch import Tensor

Z95 = 1.959963984540054
ALPHA = 0.05
LOG_2PI = math.log(2.0 * math.pi)


def wrap(e: np.ndarray) -> np.ndarray:
    """Angle difference wrapped to (−π, π]."""
    out: np.ndarray = np.arctan2(np.sin(e), np.cos(e))
    return out


def arc(a: np.ndarray, sd: np.ndarray, xmax: float) -> np.ndarray:
    """X = min(Xmax, 1.96 · a · sd)."""
    out: np.ndarray = np.minimum(xmax, Z95 * a * sd)
    return out


def arc_prob(p: np.ndarray, a: np.ndarray, sd: np.ndarray, x: np.ndarray) -> np.ndarray:
    """P(|e| ≤ X) under the mixture (normal approximation for the peaked part)."""
    s = np.maximum(a * sd, 1e-12)
    erf = np.vectorize(math.erf)
    pv = erf(x / (s * math.sqrt(2.0)))
    out: np.ndarray = p * pv + (1.0 - p) * x / math.pi
    return out


def log_i0e(k: Tensor) -> Tensor:
    return torch.log(torch.special.i0e(k))


def course_log_score_t(e: Tensor, a: Tensor, p: Tensor, sd: Tensor) -> Tensor:
    """[N] log density of the mixture at the wrapped course error e (higher is better)."""
    k = torch.clamp(1.0 / (a * sd) ** 2, max=1e8)
    log_vm = k * (torch.cos(e) - 1.0) - log_i0e(k) - LOG_2PI  # log I0(k) = log i0e(k) + k
    log_u = torch.full_like(e, -LOG_2PI)
    p = torch.clamp(p, 1e-6, 1.0 - 1e-6)
    return torch.logsumexp(torch.stack([torch.log(p) + log_vm, torch.log1p(-p) + log_u]), dim=0)


def course_log_score(e: np.ndarray, a: np.ndarray, p: np.ndarray, sd: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        out: np.ndarray = course_log_score_t(
            *(torch.as_tensor(np.asarray(v, dtype=np.float64)) for v in (e, a, p, sd))
        ).numpy()
    return out


def interval_score_t(abs_e: Tensor, q: Tensor) -> Tensor:
    """[N] the 95% central interval score of a symmetric interval ±q around the estimate (lower is
    better): 2q + (2/α)(|e| − q)⁺."""
    return 2.0 * q + (2.0 / ALPHA) * torch.clamp(abs_e - q, min=0.0)


def interval_score(abs_e: np.ndarray, q: np.ndarray) -> np.ndarray:
    out: np.ndarray = 2.0 * q + (2.0 / ALPHA) * np.maximum(abs_e - q, 0.0)
    return out


def isotonic_fit(x: np.ndarray, y: np.ndarray, bins: int) -> tuple[list[float], list[float]]:
    """A monotone non-decreasing map from x to the mean of y: equal-count bins of x, pooled
    adjacent violators on the bin means. Returns knots (bin mean x, fitted y) for interpolation."""
    order = np.argsort(x)
    xs, ys = np.asarray(x, dtype=np.float64)[order], np.asarray(y, dtype=np.float64)[order]
    parts = np.array_split(np.arange(len(xs)), max(1, min(bins, len(xs))))
    bx = [float(xs[i].mean()) for i in parts if len(i)]
    by = [float(ys[i].mean()) for i in parts if len(i)]
    w = [float(len(i)) for i in parts if len(i)]
    # pool adjacent violators
    vals: list[list[float]] = []  # [sum_w_y, sum_w, n_bins]
    for yi, wi in zip(by, w, strict=True):
        vals.append([yi * wi, wi, 1.0])
        while len(vals) > 1 and vals[-2][0] / vals[-2][1] > vals[-1][0] / vals[-1][1]:
            sy, sw, n = vals.pop()
            vals[-1][0] += sy
            vals[-1][1] += sw
            vals[-1][2] += n
    fy: list[float] = []
    for sy, sw, n in vals:
        fy += [sy / sw] * int(n)
    return bx, fy


def isotonic_apply(x: np.ndarray, knots: tuple[list[float], list[float]]) -> np.ndarray:
    """Linear interpolation through the knots, clamped at the ends, then to [0, 1]."""
    bx, fy = knots
    out: np.ndarray = np.clip(np.interp(np.asarray(x, dtype=np.float64), bx, fy), 0.0, 1.0)
    return out


# ---------------------------------------------------------------- spec 010: the truncated form
#
# The row states an arc ±X, the probability P that the course lies within it, and a concentration
# κ for the shape inside (research R2 of spec 010). The density at a wrapped course error e is
#   P · exp(κ (cos e − 1)) / Z(κ, X)        for |e| ≤ X,
#   (1 − P) / (2π − 2X)                      otherwise,
# with Z(κ, X) = ∫_{−X}^{X} exp(κ (cos θ − 1)) dθ. The arc mass is P exactly, for any P, so any
# recalibration of P keeps the statement consistent; the log score is proper.

_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(64)
_REACH = 12.0  # integrate over min(X, 12/√κ): beyond it the integrand is below e^-72


def arc_norm(kappa: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Z(κ, X) by 64-point Gauss–Legendre on [−X′, X′], X′ = min(X, 12/√κ) (the integrand is
    below e^-72 beyond X′, so a narrow peak is still resolved)."""
    k = np.asarray(kappa, dtype=np.float64)[..., None]
    xx = np.minimum(
        np.asarray(x, dtype=np.float64), _REACH / np.sqrt(np.maximum(k[..., 0], 1e-300))
    )
    xx = xx[..., None]
    th = xx * _GL_NODES
    out: np.ndarray = (xx * (_GL_WEIGHTS * np.exp(k * (np.cos(th) - 1.0)))).sum(axis=-1)
    return out


def arc_norm_t(kappa: Tensor, x: Tensor) -> Tensor:
    nodes = torch.as_tensor(_GL_NODES, dtype=kappa.dtype)
    weights = torch.as_tensor(_GL_WEIGHTS, dtype=kappa.dtype)
    xx = torch.minimum(x, _REACH / torch.sqrt(torch.clamp(kappa, min=1e-300)))[..., None]
    th = xx * nodes
    return (xx * weights * torch.exp(kappa[..., None] * (torch.cos(th) - 1.0))).sum(-1)


def vm_arc_mass(kappa: np.ndarray, x: np.ndarray) -> np.ndarray:
    """The exact von Mises (concentration κ, centred) mass on ±X: Z(κ, X) / (2π I0e(κ))."""
    k = np.asarray(kappa, dtype=np.float64)
    out: np.ndarray = arc_norm(k, x) / (2.0 * math.pi * _i0e(k))
    return out


def _i0e(k: np.ndarray) -> np.ndarray:
    """exp(−κ) I0(κ), stable for large κ (torch's special function; NumPy has no i0e)."""
    with torch.no_grad():
        out: np.ndarray = torch.special.i0e(torch.as_tensor(k, dtype=torch.float64)).numpy()
    return out


def truncated_log_score_t(e: Tensor, x: Tensor, prob: Tensor, kappa: Tensor) -> Tensor:
    """[N] log density of the truncated statement at the wrapped course error e."""
    prob = torch.clamp(prob, 1e-9, 1.0 - 1e-9)
    inside = e.abs() <= x
    log_in = torch.log(prob) + kappa * (torch.cos(e) - 1.0) - torch.log(arc_norm_t(kappa, x))
    log_out = torch.log1p(-prob) - torch.log(2.0 * math.pi - 2.0 * x)
    return torch.where(inside, log_in, log_out)


def truncated_log_score(
    e: np.ndarray, x: np.ndarray, prob: np.ndarray, kappa: np.ndarray
) -> np.ndarray:
    with torch.no_grad():
        out: np.ndarray = truncated_log_score_t(
            *(torch.as_tensor(np.asarray(v, dtype=np.float64)) for v in (e, x, prob, kappa))
        ).numpy()
    return out


def platt_fit(prob: np.ndarray, hit: np.ndarray) -> tuple[float, float]:
    """(α, β) minimising the binary log loss of sigmoid(α + β logit P) against the hits."""
    lp = torch.as_tensor(_logit(prob))
    y = torch.as_tensor(np.asarray(hit, dtype=np.float64))
    a = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    b = torch.ones(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([a, b], max_iter=200, line_search_fn="strong_wolfe")

    def closure() -> Tensor:
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(a + b * lp, y)
        loss.backward()  # type: ignore[no-untyped-call]
        return loss

    opt.step(closure)  # type: ignore[no-untyped-call]
    return float(a.detach()), float(b.detach())


def platt_apply(prob: np.ndarray, ab: tuple[float, float]) -> np.ndarray:
    out: np.ndarray = 1.0 / (1.0 + np.exp(-(ab[0] + ab[1] * _logit(prob))))
    return out


def _logit(prob: np.ndarray) -> np.ndarray:
    q = np.clip(np.asarray(prob, dtype=np.float64), 1e-6, 1.0 - 1e-6)
    out: np.ndarray = np.log(q / (1.0 - q))
    return out
