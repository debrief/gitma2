"""Bearing errors that are not independent or not Gaussian, handled before the search
(spec 016, research R3 and R4). Each function returns a ``Problem`` the fits accept unchanged.

* ``edited``: wild bearings are not used (``thin.edit_wild``).
* ``estimate``: the share of the error variance that is correlated in time and its
  correlation time, from the variance of the bearings' second differences at lags of 5 to
  60 s. A second difference removes the smooth geometry; for white error its variance is
  6σ², and for a first-order Gauss–Markov error of correlation ρ per lag it is
  (6 − 8ρ + 2ρ²)σ². The variances are robust (median absolute deviation), so wild bearings
  and a few manoeuvres do not move them. The total sd is the stated one.
* ``effective``: the problem with one larger sd for every bearing, chosen so that
  independent errors of that sd carry the same information about anything slow as the
  estimated correlated errors do (the same spectral density at zero frequency):
  σ_eff² = σ²·[(1 − share) + share·(1 + ρ) / (1 − ρ)], ρ = exp(−Δt / τ).

A whitened (generalised least squares) fit would also use the errors' short-time structure;
this form uses none of it, which is cautious about when a manoeuvre happened and right about
range, course and speed.
"""

from __future__ import annotations

import numpy as np

from .retest import Problem
from .thin import edit_wild

LAGS = tuple(range(1, 13))  # rows: 5 to 60 s at 5-second bearings
TAUS = np.geomspace(10.0, 600.0, 40)
SHARES = np.linspace(0.0, 0.9, 46)
MIN_SHARE = 0.2  # below this the errors are treated as independent


def edited(pb: Problem) -> tuple[Problem, int]:
    """(the problem without its wild bearings, how many were edited out)."""
    t, ox, oy, z, v, sigma = pb
    keep = edit_wild(t, z, v.astype(bool), float(sigma))
    return (t, ox, oy, z, keep, sigma), int(v.astype(bool).sum() - keep.sum())


def second_difference_variances(pb: Problem) -> np.ndarray:
    """[len(LAGS)] robust variance of z[i − h] − 2 z[i] + z[i + h] over valid triples (NaN
    where there are fewer than 30)."""
    _t, _ox, _oy, z, v, _sigma = pb
    ok = v.astype(bool)
    zz = np.where(ok, z, 0.0)
    k = np.flatnonzero(ok)
    if k.size:
        zz[k] = np.unwrap(z[k])
    out = np.full(len(LAGS), np.nan)
    for j, h in enumerate(LAGS):
        if zz.size <= 2 * h:
            continue
        d = zz[: -2 * h] - 2.0 * zz[h:-h] + zz[2 * h :]
        m = ok[: -2 * h] & ok[h:-h] & ok[2 * h :]
        if int(m.sum()) < 30:
            continue
        dd = d[m]
        out[j] = (1.4826 * float(np.median(np.abs(dd - np.median(dd))))) ** 2
    return out


def estimate(pb: Problem) -> tuple[float, float]:
    """(share, τ in s) of the correlated part; (0, 0) when it cannot be estimated."""
    t, *_rest, sigma = pb
    var = second_difference_variances(pb) / float(sigma) ** 2
    ok = np.isfinite(var)
    if int(ok.sum()) < 6:
        return 0.0, 0.0
    dt = float(np.median(np.diff(t)))
    h = np.array(LAGS, dtype=np.float64)[ok]
    best = (np.inf, 0.0, 0.0)
    for tau in TAUS:
        rho = np.exp(-h * dt / tau)
        corr = 6.0 - 8.0 * rho + 2.0 * rho * rho
        for s in SHARES:
            e = float(np.sum((var[ok] - (6.0 * (1.0 - s) + s * corr)) ** 2))
            if e < best[0]:
                best = (e, float(s), float(tau))
    return best[1], (best[2] if best[1] > 0.0 else 0.0)


def effective_sigma(sigma: float, share: float, tau: float, dt: float) -> float:
    if share <= 0.0 or tau <= 0.0:
        return sigma
    rho = float(np.exp(-dt / tau))
    return sigma * float(np.sqrt((1.0 - share) + share * (1.0 + rho) / (1.0 - rho)))


def effective(pb: Problem, share: float, tau: float) -> Problem:
    """``pb`` with the effective sd for errors of that correlated share and time."""
    t, ox, oy, z, v, sigma = pb
    dt = float(np.median(np.diff(t)))
    return (t, ox, oy, z, v, effective_sigma(float(sigma), share, tau, dt))
