"""The steady-leg detector (spec 004 FR-012–FR-015; research R2).

Inputs: 13 channels per row, with fixed scales only (no statistics from data, constitution IV):
gitma's raw channels (bearing sin and cos, ownship position, course sin and cos and speed, time,
valid, window mask) and its derived channels (trailing least-squares bearing rate, its validity
flag, bearing-line intercept), defined as gitma's ``packages/features/src/derived.ts`` with fixed
scales in place of gitma's train-split quantile.

Encoder: spec 003's transformer (``gate1.Block``), causal unless the variant is time-late. Heads,
on its output h (one vector per row):

* ``p_change[k] = σ(MLP(h_k))``: a manoeuvre is in progress at k or began within 60 s;
* ``w_change[k, j] = σ(b + (Q h_k)·(K h_j)/√d)`` for j ≤ k (0 elsewhere): soft changepoint
  weights over earlier rows, revised by the asking row k as it sees more bearings after j;
* ``p_kind[k, j] = σ(b' + (Q' h_k)·(K' h_j)/√d)``: a changepoint at j is a course change (1) or a
  speed change (0).

Every MLP is Linear → tanh → zero-initialised Linear, so the untrained p_change is 0.5. In each
pairwise head the key projection K starts at zero and the query projection Q is random (one side
zero, so the score is exactly 0 and both sides still receive gradient once K moves); with
b = ``W_BIAS0`` the untrained w_change is σ(−10) ≈ 4.5e-5 everywhere, so no knot is exported and
the physics layer's increments are pinned (prior sd √c·τ_r ≈ 0.02 m/s): the untrained detector
gives batch least squares to within that. b' = 0, so the untrained p_kind is 0.5.

The time-late variant drops the causal mask (padded keys stay masked) and is asked its question
at the window's last row; the pairwise mask j ≤ k applies to both.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor, nn

from tma2.physics.layer import cos_export
from tma2.types.generated.tma import DetectorConfig, DetectorVariant, HeadLiveness

from .gate1 import POS_SCALE_M, TIME_SCALE_S, Block
from .heads import head, liveness, zero_linear

FEATURES = 13
SPEED_SCALE_MPS = 10.0
RATE_SCALE_RAD_S = 1e-3  # a 5 m/s crossing target at 5 km: 1e-3 rad/s
RATE_WINDOW_ROWS = 18  # gitma derived.ts: 3 min at 10 s
MIN_RATE_SAMPLES = 3
W_BIAS0 = -10.0
TWO_PI = 2.0 * math.pi
CHANNELS = (
    "bearing_sin",
    "bearing_cos",
    "own_x_scaled",
    "own_y_scaled",
    "own_course_sin",
    "own_course_cos",
    "own_speed_scaled",
    "time_scaled",
    "valid",
    "window_mask",
    "bearing_rate_scaled",
    "rate_valid",
    "intercept_scaled",
)


def _shift(x: Tensor, s: int) -> Tensor:
    """x[:, i − s] with zeros for i < s (static shapes; standard operators)."""
    if s == 0:
        return x
    return torch.cat([torch.zeros_like(x[:, :s]), x[:, :-s]], dim=1)


def bearing_rate(t: Tensor, bearing: Tensor, valid: Tensor) -> tuple[Tensor, Tensor]:
    """gitma ``trailingBearingRate``: the least-squares slope of the bearing (unwrapped relative
    to row i) against time over the valid rows max(0, i − 17) … i; (rate, rate_valid), both 0 on
    rows without a bearing or with fewer than 3 valid rows in the window. [B, R] → [B, R]."""
    m = torch.zeros_like(t)
    st = torch.zeros_like(t)
    su = torch.zeros_like(t)
    stt = torch.zeros_like(t)
    stu = torch.zeros_like(t)
    for s in range(RATE_WINDOW_ROWS):
        v = _shift(valid, s) * valid
        tau = (_shift(t, s) - t) * v
        d = _shift(bearing, s) - bearing
        u = (d - TWO_PI * torch.floor(d / TWO_PI + 0.5)) * v  # Math.round is half-up
        m = m + v
        st = st + tau
        su = su + u
        stt = stt + tau * tau
        stu = stu + tau * u
    den = m * stt - st * st
    ok = (valid > 0) & (m >= MIN_RATE_SAMPLES) & (den > 0)
    rate = torch.where(ok, (m * stu - st * su) / torch.where(ok, den, torch.ones_like(den)), m * 0)
    return rate, ok.to(t.dtype)


def features(
    bearing: Tensor,
    valid: Tensor,
    own: Tensor,
    t: Tensor,
    window: Tensor,
) -> Tensor:
    """[B, R, 13]: bearing [B, R], valid [B, R] (0/1), own [B, R, 4] (x, y, course, speed),
    t [B, R] (s), window [B, R] (1 inside the scenario's window, 0 on padding)."""
    v = valid * window
    ox = (own[..., 0] - own[:, :1, 0]) * window
    oy = (own[..., 1] - own[:, :1, 1]) * window
    sb = torch.sin(bearing) * v
    cb = cos_export(bearing) * v
    rate, rate_ok = bearing_rate(t, bearing, v)
    return torch.stack(
        [
            sb,
            cb,
            ox / POS_SCALE_M,
            oy / POS_SCALE_M,
            torch.sin(own[..., 2]) * window,
            cos_export(own[..., 2]) * window,
            own[..., 3] / SPEED_SCALE_MPS * window,
            t / TIME_SCALE_S * window,
            v,
            window,
            rate / RATE_SCALE_RAD_S,
            rate_ok,
            (ox * cb - oy * sb) / POS_SCALE_M,
        ],
        dim=2,
    )


@dataclass
class DetectorOutput:
    p_change: Tensor  # [B, R]
    w_change: Tensor  # [B, N, R]: rows j of the question asked at query row q
    p_kind: Tensor  # [B, N, R]
    w_logit: Tensor  # [B, N, R] (for the losses; −∞-free)
    kind_logit: Tensor  # [B, N, R]
    now_logit: Tensor  # [B, R]


class Pairwise(nn.Module):
    """σ(b + (Q h_k)·(K h_j)/√d) for query rows k and every row j."""

    def __init__(self, width: int, bias0: float) -> None:
        super().__init__()
        self.q = nn.Linear(width, width)
        self.k = zero_linear(width, width)
        self.bias = nn.Parameter(torch.full((1,), bias0))
        self.scale = 1.0 / math.sqrt(width)

    def forward(self, hq: Tensor, h: Tensor) -> Tensor:
        """hq [B, N, W], h [B, R, W] → logits [B, N, R]."""
        out: Tensor = (self.q(hq) @ self.k(h).transpose(1, 2)) * self.scale + self.bias
        return out


class Detector(nn.Module):
    def __init__(self, cfg: DetectorConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.causal = cfg.variant == DetectorVariant.causal
        self.embed = nn.Linear(FEATURES, cfg.width)
        self.layers = nn.ModuleList(
            Block(cfg.width, cfg.heads, cfg.feedforward) for _ in range(cfg.layers)
        )
        self.norm = nn.LayerNorm(cfg.width)
        self.now_head = head(cfg.width, 1, cfg.head_activation)
        self.w_head = Pairwise(cfg.width, W_BIAS0)
        self.kind_head = Pairwise(cfg.width, 0.0)
        self.weights_digest: str | None = None

    def encode(self, x: Tensor, window: Tensor) -> Tensor:
        r = x.shape[1]
        idx = torch.arange(r, device=x.device)
        pad = window <= 0
        if self.causal:
            masked = (idx.unsqueeze(0) > idx.unsqueeze(1)).unsqueeze(0)  # key j > query i
        else:
            masked = pad.unsqueeze(1).expand(-1, r, -1)
        h = self.embed(x)
        for layer in self.layers:
            h = layer(h, masked)
        out: Tensor = self.norm(h)
        return out

    def forward(self, x: Tensor, window: Tensor, query: Tensor) -> DetectorOutput:
        """x [B, R, 13], window [B, R], query [B, N] int64 rows (−1: none) → outputs.

        ``w_change`` is 0 and ``p_kind`` 0.5 on pairs with j > k, at j = 0 (the layer never puts
        a knot at row 0), at padded j and for absent queries; the logits are returned unmasked
        and the losses mask them."""
        h = self.encode(x, window)
        now_logit = self.now_head(h)[..., 0]
        q = query.clamp_min(0)
        hq = torch.gather(h, 1, q.unsqueeze(2).expand(-1, -1, h.shape[2]))
        idx = torch.arange(x.shape[1], device=x.device).view(1, 1, -1)
        allowed = (idx <= query.unsqueeze(2)) & (idx > 0) & (window.unsqueeze(1) > 0)
        w_logit = self.w_head(hq, h)
        kind_logit = self.kind_head(hq, h)
        w = torch.where(allowed, torch.sigmoid(w_logit), torch.zeros_like(w_logit))
        return DetectorOutput(
            p_change=torch.sigmoid(now_logit),
            w_change=w,
            p_kind=torch.where(
                allowed, torch.sigmoid(kind_logit), torch.full_like(kind_logit, 0.5)
            ),
            w_logit=w_logit,
            kind_logit=kind_logit,
            now_logit=now_logit,
        )

    @torch.no_grad()
    def head_liveness(self, x: Tensor, window: Tensor, query: Tensor) -> list[HeadLiveness]:
        """Liveness of the now head, and the spread of the pairwise logits across rows."""
        h = self.encode(x, window)
        keep = window > 0
        recs = [liveness("now", self.now_head, h[keep])]
        out = self.forward(x, window, query)
        for name, logit in (("w_change", out.w_logit), ("p_kind", out.kind_logit)):
            sel = logit[(query >= 0).unsqueeze(2).expand_as(logit) & keep.unsqueeze(1)]
            sd = float(sel.std()) if sel.numel() > 1 else 0.0
            recs.append(
                HeadLiveness(head=name, alive_share=1.0 if sd > 1e-3 else 0.0, output_sd=sd)
            )
        return recs
