"""Detector losses (spec 004 FR-016–FR-018; research R5).

Classification (every term a binary cross-entropy on logits, so its gradient is p − y and never
saturates):

* ``now``: per row of the window, held-leg rows weighted ``held_leg_weight`` (Annex A §A.4's
  held-leg weighting, declared before training), the others 1; a weighted mean;
* ``boundary``: ``w_change[k, j]`` against the triangular targets at every pair j ≤ k (j > 0,
  inside the window) of the scored rows k; a mean over pairs;
* ``kind``: ``p_kind[k, j]`` against the nearest past boundary's kind, weighted by the boundary
  target (rows near a boundary count, others not); a weighted mean, 0 when no boundary is near.

Downstream (the primary objective): the physics layer fed by the soft segmentation at the scored
rows (``detector_inputs.physics_inputs``), its error in log range, vx and vy at the row divided by
the known-manoeuvres Cramér–Rao standard deviations, squared, summed and capped per row
(``LOSS_CAP``, as Gate 1); rows whose solution is implausible, whose covariance is unusable or
whose bound is singular are excluded (the layer's "undetermined" rows). The gradient reaches the
detector through the implicit Newton step (spec 003 R1). The classification-only control has
``loss_downstream_weight`` 0, and then the layer is not run at all.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional as F  # noqa: N812

from tma2.physics.layer import PhysicsOutputs
from tma2.types.generated.tma import DetectorConfig

from .detector import DetectorOutput
from .loss import _bound_sd, _components

LOSS_CAP = 100.0


@dataclass
class DetectorTargets:
    """Tensors from ``detector_labels`` (float64)."""

    now: Tensor  # [B, R]
    held: Tensor  # [B, R] bool
    valid_row: Tensor  # [B, R] bool
    w_target: Tensor  # [B, N, R]
    kind: Tensor  # [B, N, R]
    kind_weight: Tensor  # [B, N, R]
    query: Tensor  # [B, N] int64 (−1: none)


@dataclass
class DetectorLossParts:
    total: Tensor
    now: Tensor
    boundary: Tensor
    kind: Tensor
    downstream: Tensor
    downstream_rows: int


def _allowed(query: Tensor, valid_row: Tensor) -> Tensor:
    r = valid_row.shape[1]
    idx = torch.arange(r, device=query.device).view(1, 1, -1)
    return (idx <= query.unsqueeze(2)) & (idx > 0) & valid_row.unsqueeze(1)


def classification_losses(
    out: DetectorOutput, y: DetectorTargets, cfg: DetectorConfig
) -> tuple[Tensor, Tensor, Tensor]:
    dt = out.now_logit.dtype
    w_now = y.valid_row.to(dt) * torch.where(
        y.held, torch.full_like(y.now, cfg.held_leg_weight), torch.ones_like(y.now)
    )
    bce_now = F.binary_cross_entropy_with_logits(out.now_logit, y.now, reduction="none")
    now = (bce_now * w_now).sum() / w_now.sum().clamp_min(1.0)
    allowed = _allowed(y.query, y.valid_row).to(dt)
    bce_w = F.binary_cross_entropy_with_logits(out.w_logit, y.w_target, reduction="none")
    boundary = (bce_w * allowed).sum() / allowed.sum().clamp_min(1.0)
    wk = y.kind_weight * allowed
    bce_k = F.binary_cross_entropy_with_logits(out.kind_logit, y.kind, reduction="none")
    kind = (bce_k * wk).sum() / wk.sum().clamp_min(1e-12) if bool(wk.sum() > 0) else bce_k.sum() * 0
    return now, boundary, kind


def downstream_loss(
    res: PhysicsOutputs, truth: Tensor, bound_cov: Tensor, okx: Tensor, oky: Tensor
) -> tuple[Tensor, int]:
    """Mean capped CRB-normalised squared error over usable rows; truth [N, 4] (x, y, vx, vy),
    bound_cov [N, 4, 4] (NaN where singular), ownship at the row (okx, oky) [N]."""
    keep = (
        res.plausible
        & res.cov_ok
        & torch.isfinite(res.state).all(dim=1)
        & torch.isfinite(bound_cov).all(dim=2).all(dim=1)
    )
    n = int(keep.sum())
    if n == 0:
        return res.state.sum() * 0.0, 0
    st, tr, bc = res.state[keep], truth[keep], bound_cov[keep]
    x, y = okx[keep], oky[keep]
    sd = _bound_sd(bc, tr, x, y)
    est, tru = _components(st, tr, x, y)
    e = (est - tru) / sd
    return torch.clamp((e * e).sum(dim=1), max=LOSS_CAP).mean(), n


def detector_loss(
    out: DetectorOutput,
    y: DetectorTargets,
    cfg: DetectorConfig,
    downstream: tuple[Tensor, int] | None,
) -> DetectorLossParts:
    now, boundary, kind = classification_losses(out, y, cfg)
    total = cfg.loss_now_weight * now + cfg.loss_boundary_weight * boundary
    total = total + cfg.loss_kind_weight * kind
    if downstream is not None and cfg.loss_downstream_weight > 0:
        ds, n = downstream
        total = total + cfg.loss_downstream_weight * ds
    else:
        ds, n = now.detach() * 0.0, 0
    return DetectorLossParts(total, now.detach(), boundary.detach(), kind.detach(), ds.detach(), n)


def run_downstream(
    layer: torch.nn.Module,
    out: DetectorOutput,
    bearing: Tensor,
    valid: Tensor,
    own_xy: Tensor,
    t: Tensor,
    sigma: Tensor,
    query: Tensor,
    k_state: Tensor | None = None,
    theta0: Tensor | None = None,
) -> tuple[PhysicsOutputs, Tensor, Tensor]:
    """The physics layer at every present query (scenario b, slot q): returns its outputs and the
    (b, q) of each solved row. ``k_state`` [B, N] reports the state at another row than the
    question's (the time-late variant); ``theta0`` [B, N, 4] is the grid start per question."""
    from .detector_inputs import physics_inputs

    bi, qi = torch.nonzero(query >= 0, as_tuple=True)
    k = query[bi, qi]
    x = physics_inputs(
        out.w_change[bi, qi],
        out.p_kind[bi, qi],
        bearing[bi],
        valid[bi],
        own_xy[bi],
        t[bi],
        sigma[bi],
        k,
        k_state[bi, qi] if k_state is not None else None,
        theta0[bi, qi] if theta0 is not None else None,
    )
    res: PhysicsOutputs = layer(x)
    return res, bi, qi
