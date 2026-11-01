"""The physics layer in PyTorch: batched, masked, fixed-iteration, export-friendly.

Same equations as ``reference.py`` (the documentation of record). Everything is a tensor
operation with static shapes and standard operators: knot selection is TopK, acceptance is
``where``, matrices are assembled by concatenation (no in-place slice writes), and the linear
solve is an unrolled Gaussian elimination on the SPD normal matrix (ONNX has no ``Solve``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor

from .reference import (
    ITERATIONS,
    LAMBDA0,
    LAMBDA_MAX,
    LAMBDA_MIN,
    MAX_RANGE_M,
    MAX_SPEED_MPS,
    MIN_SIGMA_RAD,
    TAU_RIDGE_MPS,
    TAU_SPEED_MPS,
    TRIALS,
)

TWO_PI = 2.0 * math.pi


@dataclass
class PhysicsInputs:
    bearing: Tensor  # [B, R]
    valid: Tensor  # [B, R] float 0/1
    own: Tensor  # [B, R, 2]
    t: Tensor  # [B, R]
    sigma: Tensor  # [B]
    k: Tensor  # [B] int64
    changepoint: Tensor  # [B, R]
    speed_weight: Tensor  # [B, R]
    log_weight: Tensor  # [B, R]
    theta0: Tensor  # [B, 4]
    speed_skip: Tensor | None = None  # [B, R] in [0, 1]: reference velocity skips the previous knot


@dataclass
class PhysicsOutputs:
    state: Tensor  # [B, 4]
    cov: Tensor  # [B, 4, 4]
    range: Tensor  # [B]
    course: Tensor  # [B]
    speed: Tensor  # [B]
    cost: Tensor  # [B]
    plausible: Tensor  # [B] bool
    theta: Tensor  # [B, P]
    knots: Tensor  # [B, M] int64
    knot_weights: Tensor  # [B, M]


def cos_export(a: Tensor) -> Tensor:
    """cos(a) as sin(a + π/2): the browser runtime (onnxruntime-web WASM) has a float64 ``Sin``
    kernel but no float64 ``Cos``. The shift adds at most one ulp of |a| + π/2 of absolute error."""
    return torch.sin(a + math.pi / 2)


def atan_export(x: Tensor) -> Tensor:
    """atan in the tensor's precision from a float32 seed refined by two Newton steps on
    sin a − x cos a = 0 (ONNX Runtime has no float64 ``Atan`` kernel; Sin/Cos it has)."""
    a = torch.atan(x.to(torch.float32)).to(x.dtype)
    for _ in range(2):
        sa = torch.sin(a)
        ca = cos_export(a)
        a = a - (sa - x * ca) / (ca + x * sa)
    return a


def atan2_export(y: Tensor, x: Tensor) -> Tensor:
    """atan2 built from ``atan_export`` with quadrant corrections (same values as torch.atan2
    to ~1e-16, and exportable in double)."""
    pi = math.pi
    safe_x = torch.where(x == 0, torch.ones_like(x), x)
    base = atan_export(y / safe_x)
    quad = torch.where(x < 0, torch.where(y >= 0, base + pi, base - pi), base)
    on_axis = torch.where(y >= 0, torch.full_like(y, pi / 2), torch.full_like(y, -pi / 2))
    return torch.where(x == 0, on_axis, quad)


def wrap_pi(a: Tensor) -> Tensor:
    return atan2_export(torch.sin(a), cos_export(a))


def wrap_2pi(a: Tensor) -> Tensor:
    w = a - torch.floor(a / TWO_PI) * TWO_PI
    return torch.where(w >= TWO_PI, torch.zeros_like(w), w)


def _hypot(x: Tensor, y: Tensor) -> Tensor:
    return torch.sqrt(x * x + y * y)


def _finite(x: Tensor) -> Tensor:
    return (x == x) & (x.abs() < float("inf"))


def _diagonal(m: Tensor) -> Tensor:
    """Main diagonal of batched square matrices as a masked sum (``torch.diagonal`` exports an
    ``If`` for the empty case)."""
    eye = torch.eye(m.shape[-1], dtype=m.dtype, device=m.device).unsqueeze(0)
    return (m * eye).sum(dim=2)


def _diag(v: Tensor) -> Tensor:
    """diag_embed by broadcasting against an identity (exportable)."""
    eye = torch.eye(v.shape[-1], dtype=v.dtype, device=v.device)
    return eye.unsqueeze(0) * v.unsqueeze(2)


def safe_sqrt(x: Tensor) -> Tensor:
    """√x for x ≥ 0 with gradient 0, not NaN, where x = 0 (the unselected branch sees a positive
    argument, so its backward is finite)."""
    pos = x > 0
    return torch.where(
        pos, torch.sqrt(torch.where(pos, x, torch.ones_like(x))), torch.zeros_like(x)
    )


def spd_solve(a: Tensor, b: Tensor) -> Tensor:
    """Solve A x = b for batched SPD A [B,P,P], b [B,P]: Jacobi scaling (columns of very different
    units: metres, metres per second) then Gauss–Jordan elimination without pivoting, written as
    one whole-matrix update per pivot (a static loop over P pivots; the graph holds only
    Gather/Mul/Sub/Div/Where/Sqrt). Every element sees the same operations as the row-by-row form
    in ``reference.spd_solve`` (f_i = a_ij / a_jj, then a_i − f_i a_j), so the two agree to
    rounding (≈1e-17 on well-scaled systems). P0 panel round 1 replaced the row-by-row graph
    (≈3,000 nodes per solve, which onnxruntime loaded very slowly) with this one."""
    p = a.shape[-1]
    eye = torch.eye(p, dtype=a.dtype, device=a.device).unsqueeze(0)
    dinv = 1.0 / torch.sqrt((a * eye).sum(dim=2).clamp_min(1e-300))  # [B,P]
    a = a * dinv.unsqueeze(2) * dinv.unsqueeze(1)
    b = b * dinv
    idx = torch.arange(p, device=a.device)
    for j in range(p):
        row_j = a[:, j, :]  # [B,P]
        f = a[:, :, j] / row_j[:, j : j + 1]  # [B,P]: f_i for every row i
        keep = (idx == j).unsqueeze(0)  # the pivot row itself is not updated
        a = torch.where(keep.unsqueeze(2), a, a - f.unsqueeze(2) * row_j.unsqueeze(1))
        b = torch.where(keep, b, b - f * b[:, j : j + 1])
    y = b / (a * eye).sum(dim=2)
    return y * dinv


class PhysicsLayer(torch.nn.Module):
    def __init__(
        self,
        iterations: int = ITERATIONS,
        knots: int = 8,
        tau_ridge_mps: float = TAU_RIDGE_MPS,
        tau_speed_mps: float = TAU_SPEED_MPS,
        lambda0: float = LAMBDA0,
        trials: int = TRIALS,
    ) -> None:
        super().__init__()
        self.iterations = iterations
        self.knots = knots
        self.tau_r = tau_ridge_mps
        self.tau_s = tau_speed_mps
        self.lambda0 = lambda0
        self.trials = trials

    def _residuals(
        self,
        theta: Tensor,
        t: Tensor,
        ox: Tensor,
        oy: Tensor,
        z: Tensor,
        sw: Tensor,
        t_knots: Tensor,
        c: Tensor,
        s: Tensor,
        order: Tensor,
        ref_order: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Residual vector [B, R+3M] and Jacobian [B, R+3M, P]."""
        b_ = t.shape[0]
        m = t_knots.shape[1]
        dt = theta.dtype
        p0 = theta[:, 0:2]
        u0 = theta[:, 2:4]
        d = theta[:, 4:].reshape(b_, m, 2)
        a = c.unsqueeze(1) * torch.relu(t.unsqueeze(2) - t_knots.unsqueeze(1))  # [B,R,M]
        pos = p0.unsqueeze(1) + u0.unsqueeze(1) * t.unsqueeze(2) + a @ d  # [B,R,2]
        dx = pos[..., 0] - ox
        dy = pos[..., 1] - oy
        rho2 = dx * dx + dy * dy
        rho2 = torch.where(rho2 > 0, rho2, torch.ones_like(rho2))
        r_b = sw * wrap_pi(z - atan2_export(dx, dy))
        gx = -sw * dy / rho2
        gy = sw * dx / rho2
        # columns for (p0x, p0y, u0x, u0y, d1x, d1y, ...): [B,R,4+2M]
        j_d = torch.stack([gx.unsqueeze(2) * a, gy.unsqueeze(2) * a], dim=3).reshape(b_, -1, 2 * m)
        j_b = torch.cat([torch.stack([gx, gy, gx * t, gy * t], dim=2), j_d], dim=2)
        # ridge on increments: rows 2M, columns on d only
        wr = safe_sqrt(c) / self.tau_r  # [B,M]
        r_ridge = -(wr.unsqueeze(2) * d).reshape(b_, 2 * m)
        eye2m = torch.eye(2 * m, dtype=dt, device=theta.device).unsqueeze(0)
        j_ridge = torch.cat(
            [
                torch.zeros(b_, 2 * m, 4, dtype=dt, device=theta.device),
                -wr.repeat_interleave(2, dim=1).unsqueeze(2) * eye2m,
            ],
            dim=2,
        )
        # speed continuity across each knot
        cd = c.unsqueeze(2) * d  # [B,M,2]
        u_before = u0.unsqueeze(1) + order @ cd  # velocity just before knot m
        u_ref = (
            u0.unsqueeze(1) + ref_order @ cd
        )  # reference velocity (skips the previous knot by speed_skip)
        u_after = u_before + cd
        # sqrt(max(x, 1e-24)) = max(sqrt(x), 1e-12), with a finite gradient at a zero velocity
        nr = torch.sqrt((u_ref * u_ref).sum(dim=2).clamp_min(1e-24))
        na = torch.sqrt((u_after * u_after).sum(dim=2).clamp_min(1e-24))
        ws = safe_sqrt(c * s) / self.tau_s  # [B,M]
        r_speed = -(ws * (na - nr))
        gr = u_ref / nr.unsqueeze(2)
        ga = u_after / na.unsqueeze(2)
        # ∂r/∂u0 = ws (ga − gr);
        # ∂r/∂d_j = ws (order_mj c_j ga − ref_order_mj c_j gr) + [j = m] ws c_m ga
        d_u0 = (ga - gr) * ws.unsqueeze(2)  # [B,M,2]
        contrib = (
            (order.unsqueeze(3) * ga.unsqueeze(2) - ref_order.unsqueeze(3) * gr.unsqueeze(2))
            * c.unsqueeze(1).unsqueeze(3)
            * ws.unsqueeze(2).unsqueeze(3)
        )  # [B,M,M,2]
        eye_m = torch.eye(m, dtype=dt, device=theta.device).unsqueeze(0).unsqueeze(3)
        own_term = eye_m * (c * ws).unsqueeze(1).unsqueeze(3) * ga.unsqueeze(2)
        j_speed = torch.cat(
            [
                torch.zeros(b_, m, 2, dtype=dt, device=theta.device),
                -d_u0,
                -(contrib + own_term).reshape(b_, m, 2 * m),
            ],
            dim=2,
        )
        r = torch.cat([r_b, r_ridge, r_speed], dim=1)
        jac = torch.cat([j_b, j_ridge, j_speed], dim=1)
        return r, jac

    def forward(self, x: PhysicsInputs) -> PhysicsOutputs:
        b_, r_ = x.bearing.shape
        dt = x.bearing.dtype
        dev = x.bearing.device
        m = self.knots
        idx = torch.arange(r_, device=dev).unsqueeze(0)
        kk = x.k.unsqueeze(1)
        mask = (idx <= kk).to(dt)
        sigma = x.sigma.clamp_min(MIN_SIGMA_RAD)
        # √w = √(valid·mask) · exp(ℓ/2): no sqrt of a zero that carries a gradient, so masked
        # and invalid rows get an exact zero gradient instead of 0 · ∞ = NaN.
        sw = safe_sqrt(x.valid * mask) * torch.exp(0.5 * x.log_weight) / sigma.unsqueeze(1)
        cand = torch.where(
            (mask > 0) & (idx > 0), x.changepoint, torch.full_like(x.changepoint, -1.0)
        )
        vals, knots = torch.topk(cand, m, dim=1)
        c = vals.clamp(0.0, 1.0)
        s = torch.gather(x.speed_weight, 1, knots).clamp(0.0, 1.0)
        t_knots = torch.gather(x.t, 1, knots)
        tm = t_knots.unsqueeze(2)
        tj = t_knots.unsqueeze(1)
        jm = torch.arange(m, device=dev)
        earlier_idx = (jm.unsqueeze(0) < jm.unsqueeze(1)).unsqueeze(0)
        order = ((tj < tm) | ((tj == tm) & earlier_idx)).to(dt)  # [B,M,M]
        # The previous knot of m: the latest knot strictly before m in the ordering; the reference
        # velocity for the speed prior skips its increment by speed_skip[m].
        skip = (
            torch.gather(x.speed_skip, 1, knots).clamp(0.0, 1.0)
            if x.speed_skip is not None
            else torch.zeros_like(c)
        )
        # Predecessors are counted among active knots only (weight > 0): an inert candidate sitting
        # between a manoeuvre's start and end knots must not become the end knot's predecessor.
        active = (c > 0).to(dt)  # [B,M]
        order_active = order * active.unsqueeze(1)
        rank = order_active.sum(dim=2)  # number of active knots before m [B,M]
        is_prev = (rank.unsqueeze(2) - 1 == rank.unsqueeze(1)).to(
            dt
        ) * order_active  # j is m's active predecessor
        ref_order = order - skip.unsqueeze(2) * is_prev
        ox = x.own[..., 0]
        oy = x.own[..., 1]
        theta = torch.cat([x.theta0.to(dt), torch.zeros(b_, 2 * m, dtype=dt, device=dev)], dim=1)
        lam = torch.full((b_,), self.lambda0, dtype=dt, device=dev)
        r, _ = self._residuals(theta, x.t, ox, oy, x.bearing, sw, t_knots, c, s, order, ref_order)
        cost = (r * r).sum(dim=1)
        nt = self.trials
        n_p = theta.shape[1]
        ladder = torch.tensor([10.0**j for j in range(nt)], dtype=dt, device=dev)

        def rep(v: Tensor) -> Tensor:
            return v.repeat_interleave(nt, dim=0)

        # Inputs repeated once for the B·T trial evaluations.
        t_r, ox_r, oy_r, z_r, sw_r = rep(x.t), rep(ox), rep(oy), rep(x.bearing), rep(sw)
        tk_r, c_r, s_r, order_r, ref_order_r = (
            rep(t_knots),
            rep(c),
            rep(s),
            rep(order),
            rep(ref_order),
        )

        for _ in range(self.iterations):
            r, jac = self._residuals(
                theta, x.t, ox, oy, x.bearing, sw, t_knots, c, s, order, ref_order
            )
            jt = jac.transpose(1, 2)
            jtj = jt @ jac
            jtr = -(jt @ r.unsqueeze(2))[..., 0]
            diag = _diagonal(jtj)
            inert = (diag == 0).to(dt)
            # gitma's inner retry, side by side: T damping values λ·10^j, j = 0 … T−1, solved
            # as one batch of B·T systems; the first trial that does not increase the cost wins.
            lam_t = (lam.unsqueeze(1) * ladder.unsqueeze(0)).clamp_max(LAMBDA_MAX)  # [B,T]
            dvec = (diag.unsqueeze(1) * lam_t.unsqueeze(2) + inert.unsqueeze(1)).reshape(
                b_ * nt, n_p
            )
            damped = jtj.repeat_interleave(nt, dim=0) + _diag(dvec)  # [B·T,P,P]
            steps = spd_solve(damped, jtr.repeat_interleave(nt, dim=0)).reshape(b_, nt, n_p)
            cand_theta = theta.unsqueeze(1) + steps  # [B,T,P]
            rc, _ = self._residuals(
                cand_theta.reshape(b_ * nt, n_p),
                t_r,
                ox_r,
                oy_r,
                z_r,
                sw_r,
                tk_r,
                c_r,
                s_r,
                order_r,
                ref_order_r,
            )
            cand_cost = (rc * rc).sum(dim=1).reshape(b_, nt)
            ok = (cand_cost <= cost.unsqueeze(1)) & _finite(cand_cost)  # [B,T]
            accept = ok.any(dim=1)
            first = torch.argmax(ok.to(dt), dim=1, keepdim=True)  # first True (ONNX: first max)
            pick = torch.gather(cand_theta, 1, first.unsqueeze(2).expand(b_, 1, n_p))[:, 0]
            theta = torch.where(accept.unsqueeze(1), pick, theta)
            cost = torch.where(accept, torch.gather(cand_cost, 1, first)[:, 0], cost)
            lam_used = torch.gather(lam_t, 1, first)[:, 0]
            lam = torch.where(
                accept,
                (lam_used / 10.0).clamp_min(LAMBDA_MIN),
                (lam * 10.0**nt).clamp_max(LAMBDA_MAX),
            )
        tk = torch.gather(x.t, 1, kk)  # [B,1]
        p0 = theta[:, 0:2]
        u0 = theta[:, 2:4]
        d = theta[:, 4:].reshape(b_, m, 2)
        dtm = c * torch.relu(tk - t_knots)  # [B,M]
        act = c * (t_knots <= tk).to(dt)
        pk = p0 + u0 * tk + (dtm.unsqueeze(2) * d).sum(dim=1)
        uk = u0 + (act.unsqueeze(2) * d).sum(dim=1)
        state = torch.cat([pk, uk], dim=1)
        # G = ∂state/∂θ, rows for (x, y, vx, vy)
        zero = torch.zeros(b_, dtype=dt, device=dev)
        one = torch.ones(b_, dtype=dt, device=dev)
        tk1 = tk[:, 0]
        dpair = torch.stack([dtm, torch.zeros_like(dtm)], dim=2).reshape(
            b_, 2 * m
        )  # x-row: dtm on x comps
        dpair_y = torch.stack([torch.zeros_like(dtm), dtm], dim=2).reshape(b_, 2 * m)
        apair = torch.stack([act, torch.zeros_like(act)], dim=2).reshape(b_, 2 * m)
        apair_y = torch.stack([torch.zeros_like(act), act], dim=2).reshape(b_, 2 * m)
        g = torch.stack(
            [
                torch.cat([torch.stack([one, zero, tk1, zero], 1), dpair], dim=1),
                torch.cat([torch.stack([zero, one, zero, tk1], 1), dpair_y], dim=1),
                torch.cat([torch.stack([zero, zero, one, zero], 1), apair], dim=1),
                torch.cat([torch.stack([zero, zero, zero, one], 1), apair_y], dim=1),
            ],
            dim=1,
        )  # [B,4,P]
        _, jac = self._residuals(theta, x.t, ox, oy, x.bearing, sw, t_knots, c, s, order, ref_order)
        jtj = jac.transpose(1, 2) @ jac
        inert = (_diagonal(jtj) == 0).to(dt)
        jtj = jtj + _diag(inert)
        cov_cols = [spd_solve(jtj, g[:, i, :]) for i in range(4)]
        cov = torch.stack([(g @ col.unsqueeze(2))[..., 0] for col in cov_cols], dim=2)
        okx = torch.gather(ox, 1, kk)[:, 0]
        oky = torch.gather(oy, 1, kk)[:, 0]
        rng = _hypot(state[:, 0] - okx, state[:, 1] - oky)
        speed = _hypot(state[:, 2], state[:, 3])
        course = wrap_2pi(atan2_export(state[:, 2], state[:, 3]))
        plausible = _finite(state).all(dim=1) & (speed <= MAX_SPEED_MPS) & (rng <= MAX_RANGE_M)
        return PhysicsOutputs(state, cov, rng, course, speed, cost, plausible, theta, knots, c)
