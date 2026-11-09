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
