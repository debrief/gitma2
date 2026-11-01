"""Gate 1 loss (spec 003 FR-011; research R3).

For each scored row, the errors of log range, vx and vy are divided by the row's Cramér–Rao
standard deviations (full window, from the truth), so every row counts by how far it is from the
information limit:

* squared normalised errors, summed over the three, capped per row (gross errors must not
  dominate the gradient);
* β-NLL: stop-grad(v^β) · (½ log v + e²/2v) per component, v the calibrated variance divided by the
  bound's variance, capped like the squared term;
* an auxiliary squared normalised error of the initial state (the solve's start), which the
  implicit backward pass leaves without a gradient.

Rows whose covariance flag is false are excluded.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from tma2.types.generated.tma import PhysicsModelConfig

from .gate1 import ModelOutput


@dataclass
class LossParts:
    total: Tensor
    squared: Tensor  # mean normalised squared error (the validation metric)
    nll: Tensor
    init: Tensor
    rows: int


def _components(state: Tensor, truth: Tensor, okx: Tensor, oky: Tensor) -> tuple[Tensor, Tensor]:
    """(log range, vx, vy) of a state and of the truth: [N, 3] each."""
    r_hat = torch.hypot(state[:, 0] - okx, state[:, 1] - oky).clamp_min(1.0)
    r = torch.hypot(truth[:, 0] - okx, truth[:, 1] - oky).clamp_min(1.0)
    est = torch.stack([torch.log(r_hat), state[:, 2], state[:, 3]], dim=1)
    tru = torch.stack([torch.log(r), truth[:, 2], truth[:, 3]], dim=1)
    return est, tru


def _bound_sd(bound_cov: Tensor, truth: Tensor, okx: Tensor, oky: Tensor) -> Tensor:
    """Cramér–Rao standard deviations of (log range, vx, vy): [N, 3]."""
    dx, dy = truth[:, 0] - okx, truth[:, 1] - oky
    r2 = (dx * dx + dy * dy).clamp_min(1.0)
    g = torch.stack([dx, dy], dim=1) / r2.unsqueeze(1)  # ∂ log r / ∂(x, y)
    var_lr = torch.einsum("ni,nij,nj->n", g, bound_cov[:, :2, :2], g)
    return torch.sqrt(
        torch.stack([var_lr, bound_cov[:, 2, 2], bound_cov[:, 3, 3]], dim=1).clamp_min(1e-30)
    )


def _model_var(out: ModelOutput, okx: Tensor, oky: Tensor) -> Tensor:
    """Calibrated variances of (log range, vx, vy) from the model's covariance: [N, 3]."""
    st, cov = out.state, out.cov
    dx, dy = st[:, 0] - okx, st[:, 1] - oky
    r2 = (dx * dx + dy * dy).clamp_min(1.0)
    g = torch.stack([dx, dy], dim=1) / r2.unsqueeze(1)
    var_lr = torch.einsum("ni,nij,nj->n", g, cov[:, :2, :2], g)
    return torch.stack([var_lr, cov[:, 2, 2], cov[:, 3, 3]], dim=1).clamp_min(1e-30)


def gate1_loss(
    out: ModelOutput,
    truth: Tensor,
    bound_cov: Tensor,
    okx: Tensor,
    oky: Tensor,
    cfg: PhysicsModelConfig,
) -> LossParts:
    keep = out.cov_ok & out.plausible & torch.isfinite(out.state).all(dim=1)
    n = int(keep.sum())
    if n == 0:
        z = out.state.sum() * 0.0
        return LossParts(z, z.detach(), z.detach(), z.detach(), 0)
    st, tr, bc = out.state[keep], truth[keep], bound_cov[keep]
    x, y = okx[keep], oky[keep]
    sd = _bound_sd(bc, tr, x, y)
    est, tru = _components(st, tr, x, y)
    e = (est - tru) / sd  # [n, 3]
    squared = torch.clamp((e * e).sum(dim=1), max=cfg.loss_cap)
    if out.log_var_rel is not None:
        v = torch.exp(out.log_var_rel[keep])
    else:
        sub = ModelOutput(st, out.cov[keep], st, keep[keep], keep[keep])
        v = _model_var(sub, x, y) / (sd * sd)
    nll = (v.detach() ** cfg.nll_beta) * (0.5 * torch.log(v) + 0.5 * e * e / v)
    nll = torch.clamp(nll.sum(dim=1), max=cfg.loss_cap)
    init_est, _ = _components(out.init_state[keep], tr, x, y)
    ei = (init_est - tru) / sd
    init = torch.clamp((ei * ei).sum(dim=1), max=cfg.loss_cap)
    total = squared.mean() + cfg.loss_nll_weight * nll.mean() + cfg.loss_init_weight * init.mean()
    return LossParts(total, squared.mean().detach(), nll.mean().detach(), init.mean().detach(), n)
