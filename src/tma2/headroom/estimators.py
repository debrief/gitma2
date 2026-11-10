"""The oracle ceilings and the classical robust control (spec 010 research R3 and R5).

Every estimator here is the declared piecewise-constant-velocity solve (``gls.WhitenedLayer``)
on given layer inputs (the true segmentation, or C″'s hand-over); they differ only in the
covariance the bearing residuals are whitened by:

- ``nominal``: white, the stated σ. The plain physics layer (the oracle, or C″'s own solve).
- ``realisation``: the true error model, with the outlier variance at the flagged bearings.
- ``attainable``: the true error model without the flags. Outliers are handled by iterated
  reweighting from the two-component mixture at each bearing's residual: responsibility γ, and a
  diagonal inflation v with 1/(s² + v) = (1 − γ)/s² + γ/(s² + s_o²), s² the marginal variance.
  Exact for white errors (it is EM for the mixture); an approximation with correlation.
- ``robust``: nothing is told. From the residuals of a nominal solve it estimates σ̂ (median
  absolute residual), a correlation model (moments of the lag-one and lag-two autocorrelations:
  white plus first-order, or first-order alone) and Huber weights, and re-solves; iterated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from tma2.physics.layer import PhysicsOutputs
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData
from tma2.sim import mismatch as mm

from .cov import ErrorModel, whitener
from .gls import WhitenedLayer, solve

Item = tuple[BearingData, int, LayerInputs]
KINDS = ("nominal", "realisation", "attainable", "robust")
MAD_TO_SD = 1.4826


@dataclass(frozen=True)
class RobustSettings:
    """The classical robust control's settings (chosen on the tuning seed; research R5)."""

    huber: bool = True
    huber_k: float = 1.345
    sigma: bool = True
    whiten: bool = True
    min_bearings: int = 60
    rho_shrink: float = 0.0
    outer: int = 3
    sigma_clamp: float = 4.0
    """σ̂ is kept within [nominal / clamp, nominal · clamp]."""


@dataclass(frozen=True)
class Truth:
    """One engagement's mismatch truth, as the side file holds it."""

    eng: np.ndarray  # [E_LEN]
    outlier: np.ndarray  # [samples] bool


def used(d: BearingData, k: int, inp: LayerInputs) -> np.ndarray:
    """Rows the solve reads: valid, up to k, and not masked by the inputs' log-weight."""
    idx = np.arange(d.n)
    return (d.valid > 0) & (idx <= k) & (inp.log_weight[: d.n] > -30.0)


def true_model(eng: np.ndarray) -> ErrorModel:
    return ErrorModel(
        sigma_w=float(eng[mm.E_SIGMA_W]),
        sigma_c=float(eng[mm.E_SIGMA_C]),
        tau_c=float(eng[mm.E_TAU_C]),
        sigma_b=float(eng[mm.E_SIGMA_B]),
        tau_b=float(eng[mm.E_TAU_B]),
    )


def mixture_inflation(raw: np.ndarray, s2: float, rate: float, out_var: float) -> np.ndarray:
    """Diagonal variance inflation from the outlier mixture at residuals ``raw`` (see module)."""
    if rate <= 0.0 or out_var <= 0.0:
        return np.zeros_like(raw)
    wide = s2 + out_var
    log_in = math.log1p(-rate) - 0.5 * math.log(s2) - 0.5 * raw * raw / s2
    log_out = math.log(rate) - 0.5 * math.log(wide) - 0.5 * raw * raw / wide
    gamma = 1.0 / (1.0 + np.exp(np.clip(log_in - log_out, -700.0, 700.0)))
    precision = (1.0 - gamma) / s2 + gamma / wide
    out: np.ndarray = 1.0 / precision - s2
    return out


def _autocorr(r: np.ndarray, ok: np.ndarray, lag: int) -> float:
    """Autocorrelation of ``r`` at ``lag`` samples over pairs whose both ends are used."""
    pair = ok[lag:] & ok[:-lag]
    if int(pair.sum()) < 8:
        return 0.0
    den = float(np.sum(r[ok] ** 2)) / int(ok.sum())
    if den <= 0.0:
        return 0.0
    return float(np.mean(r[lag:][pair] * r[:-lag][pair])) / den


def robust_model(
    raw: np.ndarray, ok: np.ndarray, dt: float, nominal: float, s: RobustSettings
) -> tuple[ErrorModel, np.ndarray]:
    """(error model, diagonal inflation [n]) from the residuals of the previous solve.

    Below ``min_bearings`` used rows nothing is estimated: the nominal white model, no weights.
    """
    n_used = int(ok.sum())
    zero = np.zeros_like(raw)
    if n_used < s.min_bearings:
        return ErrorModel(nominal), zero
    sd = nominal
    if s.sigma:
        sd = MAD_TO_SD * float(np.median(np.abs(raw[ok])))
        sd = min(max(sd, nominal / s.sigma_clamp), nominal * s.sigma_clamp)
    model = ErrorModel(sd)
    if s.whiten:
        clipped = np.clip(raw, -2.5 * sd, 2.5 * sd)
        r1 = _autocorr(clipped, ok, 1) * (1.0 - s.rho_shrink)
        r2 = _autocorr(clipped, ok, 2) * (1.0 - s.rho_shrink)
        if r1 > 0.05:
            phi, share = (r2 / r1, r1 * r1 / r2) if r2 > 0.0 else (0.0, 2.0)
            if 0.05 < phi < 0.995 and 0.0 < share < 0.98:
                # white plus first-order: ρ₁ = share · φ, ρ₂ = share · φ²
                model = ErrorModel(
                    sigma_w=sd * math.sqrt(1.0 - share),
                    sigma_c=sd * math.sqrt(share),
                    tau_c=-dt / math.log(phi),
                )
            else:
                rho = min(r1, 0.9)  # first-order alone, a little white for conditioning
                model = ErrorModel(
                    sigma_w=sd * 0.1, sigma_c=sd * math.sqrt(0.99), tau_c=-dt / math.log(rho)
                )
    extra = zero
    if s.huber:
        u = np.abs(raw) / sd
        w = np.where(u > s.huber_k, s.huber_k / np.maximum(u, 1e-300), 1.0)
        extra = model.marginal_var * (1.0 / w - 1.0)
    return model, extra


def _whiteners(
    items: list[Item], models: list[ErrorModel], extras: list[np.ndarray | None]
) -> list[np.ndarray]:
    return [
        whitener(d.t, used(d, k, inp), m, e)
        for (d, k, inp), m, e in zip(items, models, extras, strict=True)
    ]


def _unweight(items: list[Item], raw: np.ndarray) -> list[np.ndarray]:
    """The layer's residuals carry exp(log_weight / 2) (a fade); take it off to get radians."""
    return [
        raw[b, : d.n] * np.exp(-0.5 * inp.log_weight[: d.n]) for b, (d, _, inp) in enumerate(items)
    ]


def estimate(
    layer: WhitenedLayer,
    items: list[Item],
    kind: str,
    r_max: int,
    truths: list[Truth] | None = None,
    settings: RobustSettings | None = None,
) -> tuple[PhysicsOutputs, list[dict[str, Any]]]:
    """Solve a batch of items as ``kind``; returns the outputs and per-item diagnostics."""
    if kind not in KINDS:
        raise ValueError(f"unknown estimator kind {kind}")
    if kind in ("realisation", "attainable") and truths is None:
        raise ValueError(f"{kind} needs the mismatch truth")
    if kind in ("nominal", "robust") and truths is not None:
        raise ValueError(f"{kind} must not be given the mismatch truth")
    info: list[dict[str, Any]] = [{} for _ in items]
    n_items = len(items)
    none: list[np.ndarray | None] = [None] * n_items
    if kind == "nominal":
        models = [ErrorModel(d.sigma) for d, _, _ in items]
        out, _ = solve(layer, items, _whiteners(items, models, none), r_max)
        return out, info
    if kind == "realisation":
        assert truths is not None
        models = [true_model(t.eng) for t in truths]
        extras: list[np.ndarray | None] = [
            t.outlier[: d.n] * float(t.eng[mm.E_OUT_SD]) ** 2
            for (d, _, _), t in zip(items, truths, strict=True)
        ]
        out, _ = solve(layer, items, _whiteners(items, models, extras), r_max)
        return out, info
    if kind == "attainable":
        assert truths is not None
        models = [true_model(t.eng) for t in truths]
        out, raw = solve(layer, items, _whiteners(items, models, none), r_max)
        if all(float(t.eng[mm.E_OUT_RATE]) <= 0.0 for t in truths):
            return out, info
        for _ in range(3):
            extras = [
                mixture_inflation(
                    r,
                    m.marginal_var,
                    float(t.eng[mm.E_OUT_RATE]),
                    float(t.eng[mm.E_OUT_SD]) ** 2,
                )
                for r, m, t in zip(_unweight(items, raw), models, truths, strict=True)
            ]
            out, raw = solve(layer, items, _whiteners(items, models, extras), r_max)
        return out, info
    s = settings or RobustSettings()
    models = [ErrorModel(d.sigma) for d, _, _ in items]
    out, raw = solve(layer, items, _whiteners(items, models, none), r_max)
    for _ in range(s.outer):
        fitted = [
            robust_model(r, used(d, k, inp), float(d.t[1] - d.t[0]), d.sigma, s)
            for r, (d, k, inp) in zip(_unweight(items, raw), items, strict=True)
        ]
        models = [m for m, _ in fitted]
        extras = [e for _, e in fitted]
        out, raw = solve(layer, items, _whiteners(items, models, extras), r_max)
    for b, m in enumerate(models):
        info[b] = {
            "sigma_hat_rad": math.sqrt(m.marginal_var),
            "share_hat": m.sigma_c**2 / m.marginal_var,
            "tau_hat_s": m.tau_c,
        }
    return out, info


def settings_from(d: dict[str, Any], only: str | None = None) -> RobustSettings:
    """Settings from a plan's ``robust`` block; ``only`` keeps one of the three fixes."""
    s = RobustSettings(**d)
    if only is None:
        return s
    if only not in ("huber", "sigma", "whiten"):
        raise ValueError(f"--only {only}: expected huber, sigma or whiten")
    return replace(s, huber=only == "huber", sigma=only == "sigma", whiten=only == "whiten")
