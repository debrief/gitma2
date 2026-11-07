"""Gate 2's training loss (spec 007 research R4; task T014).

Per scored prefix, the errors of (log range, vx, vy) are divided by the known-manoeuvres
Cramér–Rao standard deviations from the truth (``references.crb``, ``state_cov``) and squared,
summed and capped (``cap``): spec 003's normalised squared error, made robust because Gate S's L
was decided by one failed fit (a 96,000-nat prefix):

* **excluded**: prefixes whose covariance flag or plausibility is false, whose state is not
  finite, or whose solve cost exceeds ``fail_per_bearing`` × their valid bearings (a failed fit);
* **capped**: each kept prefix's term at ``cap``;
* **auxiliary**: the same term for the corrected start's state at the row, weighted
  ``init_weight`` (implicit differentiation leaves the start without a gradient);
* **validation**: the trimmed mean (``trim`` in each tail) of the per-prefix terms, for early
  stopping.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from tma2.models.loss import _bound_sd, _components

from .model import EOutput


@dataclass
class ELoss:
    total: Tensor  # the training objective (mean over kept prefixes)
    per_prefix: Tensor  # [n] capped normalised squared errors of the kept prefixes (detached)
    kept: Tensor  # [N] bool
    excluded_failed_fits: int


def e_loss(
    out: EOutput,
    truth: Tensor,  # [N, 4] (x, y, vx, vy) at the row
    bound_cov: Tensor,  # [N, 4, 4]
    okx: Tensor,
    oky: Tensor,
    n_valid: Tensor,  # [N] valid bearings up to the row
    cap: float = 100.0,
    init_weight: float = 0.1,
    fail_per_bearing: float = 20.0,
) -> ELoss:
    fit_ok = out.cost <= fail_per_bearing * n_valid.to(out.cost.dtype)
    sane = out.cov_ok & out.plausible & torch.isfinite(out.state).all(dim=1)
    bound_ok = torch.isfinite(bound_cov).all(dim=(1, 2))
    kept = sane & fit_ok & bound_ok
    failed = int((sane & bound_ok & ~fit_ok).sum())
    if not bool(kept.any()):
        z = out.state.sum() * 0.0
        return ELoss(z, z.detach().reshape(0), kept, failed)
    tr, x, y = truth[kept], okx[kept], oky[kept]
    sd = _bound_sd(bound_cov[kept], tr, x, y)
    est, tru = _components(out.state[kept], tr, x, y)
    e = (est - tru) / sd
    sq = torch.clamp((e * e).sum(dim=1), max=cap)
    ie, _ = _components(out.init_state[kept], tr, x, y)
    ei = (ie - tru) / sd
    init = torch.clamp((ei * ei).sum(dim=1), max=cap)
    total = sq.mean() + init_weight * init.mean()
    return ELoss(total, sq.detach(), kept, failed)


def trimmed_mean(values: Tensor, trim: float = 0.1) -> float:
    """Mean of the values between the ``trim`` and 1 − ``trim`` quantiles (validation)."""
    v = torch.sort(values.reshape(-1)).values
    n = v.numel()
    if n == 0:
        return float("nan")
    lo = int(n * trim)
    hi = n - lo
    return float(v[lo:hi].mean()) if hi > lo else float(v.mean())
