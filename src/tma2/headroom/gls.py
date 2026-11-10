"""The physics layer's solve with a whitened bearing block (spec 010 research R3).

``WhitenedLayer`` is ``PhysicsLayer`` with one change: the bearing residuals and their Jacobian
rows are multiplied by a per-item operator W [B, R, R] before the normal equations, so the solve
is generalised least squares under the covariance (WᵀW)⁻¹. Knots, the ridge and speed-continuity
priors, the damping ladder, the acceptance rule and the outputs are the parent's. Inputs must
carry σ = 1 (W holds the scale). With W = diag(valid · mask / σ) the two layers solve the same
problem; the ceilings take the parent's path outright when there is no mismatch, so that case is
the existing oracle row for row (FR-013).

Not exported: this is a reference estimator (an oracle and a classical control), never a carried
model, so it uses a plain Python iteration.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from torch import Tensor

from tma2.physics.layer import (
    PhysicsInputs,
    PhysicsLayer,
    PhysicsOutputs,
    _diag,
    _diagonal,
    _finite,
    residuals,
    spd_solve,
)
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData


class WhitenedLayer(PhysicsLayer):
    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.w: Tensor | None = None  # [B, R, R], set by ``solve``
        self.raw: Tensor | None = None  # [B, R] unweighted bearing residuals at the solution

    def _raw(self, theta: Tensor, *args: Tensor) -> tuple[Tensor, Tensor]:
        t, ox, oy, z, sw, t_knots, c, s, order, ref_order = args
        return residuals(
            theta,
            t,
            ox,
            oy,
            z,
            sw,
            t_knots,
            c,
            s,
            order,
            ref_order,
            self.tau_r,
            self.tau_s,
            self.knots == 0,
        )

    def _whiten(self, r: Tensor, jac: Tensor | None) -> tuple[Tensor, Tensor | None]:
        """Apply W to the first R entries of r [N, R + …] (and rows of jac), N = B · n."""
        assert self.w is not None
        w = self.w
        b_, r_ = w.shape[0], w.shape[1]
        n = r.shape[0] // b_
        rb = torch.einsum("bij,bnj->bni", w, r[:, :r_].reshape(b_, n, r_)).reshape(b_ * n, r_)
        r2 = torch.cat([rb, r[:, r_:]], dim=1)
        if jac is None:
            return r2, None
        jb = torch.einsum(
            "bij,bnjp->bnip", w, jac[:, :r_].reshape(b_, n, r_, jac.shape[2])
        ).reshape(b_ * n, r_, jac.shape[2])
        return r2, torch.cat([jb, jac[:, r_:]], dim=1)

    def _residuals(self, theta: Tensor, *args: Tensor) -> tuple[Tensor, Tensor]:
        r, jac = self._raw(theta, *args)
        r2, j2 = self._whiten(r, jac)
        assert j2 is not None
        return r2, j2

    def _iterate(
        self,
        theta: Tensor,
        cost: Tensor,
        lam: Tensor,
        ladder: Tensor,
        x: PhysicsInputs,
        ox: Tensor,
        oy: Tensor,
        sw: Tensor,
        t_knots: Tensor,
        c: Tensor,
        s: Tensor,
        order: Tensor,
        ref_order: Tensor,
        reps: tuple[Tensor, ...],
    ) -> tuple[Tensor, Tensor]:
        """``physics.layer.iterate`` with the whitened residuals (same ladder and acceptance)."""
        b_, n_p = theta.shape
        dt = theta.dtype
        nt = self.trials
        for _ in range(self.iterations):
            r, jac = self._residuals(
                theta, x.t, ox, oy, x.bearing, sw, t_knots, c, s, order, ref_order
            )
            jt = jac.transpose(1, 2)
            jtj = jt @ jac
            jtr = -(jt @ r.unsqueeze(2))[..., 0]
            diag = _diagonal(jtj)
            inert = (diag == 0).to(dt)
            lam_t = (lam.unsqueeze(1) * ladder.unsqueeze(0)).clamp_max(1e12)
            dvec = (diag.unsqueeze(1) * lam_t.unsqueeze(2) + inert.unsqueeze(1)).reshape(
                b_ * nt, n_p
            )
            damped = jtj.repeat_interleave(nt, dim=0) + _diag(dvec)
            steps = spd_solve(damped, jtr.repeat_interleave(nt, dim=0)).reshape(b_, nt, n_p)
            cand_theta = theta.unsqueeze(1) + steps
            rc_raw, _ = self._raw(cand_theta.reshape(b_ * nt, n_p), *reps)
            rc, _ = self._whiten(rc_raw, None)
            cand_cost = (rc * rc).sum(dim=1).reshape(b_, nt)
            ok = (cand_cost <= cost.unsqueeze(1)) & _finite(cand_cost)
            accept = ok.any(dim=1)
            first = torch.argmax(ok.to(dt), dim=1, keepdim=True)
            pick = torch.gather(cand_theta, 1, first.unsqueeze(2).expand(b_, 1, n_p))[:, 0]
            theta = torch.where(accept.unsqueeze(1), pick, theta)
            cost = torch.where(accept, torch.gather(cand_cost, 1, first)[:, 0], cost)
            lam_used = torch.gather(lam_t, 1, first)[:, 0]
            lam = torch.where(
                accept, (lam_used / 10.0).clamp_min(1e-12), (lam * 10.0**nt).clamp_max(1e12)
            )
        return theta, cost

    def _outputs(self, theta: Tensor, cost: Tensor, x: PhysicsInputs, *args: Any) -> PhysicsOutputs:
        ox, oy, sw, t_knots, c, s, order, ref_order, _knots = args
        r, _ = self._raw(theta, x.t, ox, oy, x.bearing, sw, t_knots, c, s, order, ref_order)
        self.raw = r[:, : x.bearing.shape[1]]
        return super()._outputs(theta, cost, x, *args)


def solve(
    layer: WhitenedLayer,
    items: list[tuple[BearingData, int, LayerInputs]],
    w: list[np.ndarray],
    r_max: int,
) -> tuple[PhysicsOutputs, np.ndarray]:
    """One whitened solve for (data, row, inputs) items with operators ``w`` (each [n, n] on the
    item's own rows, padded here). Returns the outputs and the unweighted bearing residuals
    [B, r_max] in radians at the solution (zero on rows the solve does not use)."""
    from tma2.cli.oracle import inputs_for

    x = inputs_for(items, r_max)
    x.sigma = torch.ones_like(x.sigma)
    wp = np.zeros((len(items), r_max, r_max))
    for b, m in enumerate(w):
        wp[b, : m.shape[0], : m.shape[1]] = m
    layer.w = torch.tensor(wp, dtype=torch.float64)
    with torch.no_grad():
        out: PhysicsOutputs = layer(x)
    assert layer.raw is not None
    raw = layer.raw.numpy().copy()
    layer.w = None
    layer.raw = None
    return out, raw
