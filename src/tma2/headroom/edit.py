"""Spec 038 (research R2): the bearings C is given, hardened by classical means.

A copy of a scenario's ``BearingData`` for the segmenter only: wild bearings marked invalid
(``timelate.thin.edit_wild``) and the stated sd replaced by an effective sd for correlated errors
(``timelate.corr``). C's code and
parameters are untouched and the final solve reads the original bearings.

Causal at the scored rows: a bearing's wild flag reads the four valid bearings after it, so the
last four valid bearings at or before each scored row take the flag computed from the data cut
at that row, and the effective sd is estimated on the data up to the first scored row and
held. (An sd estimated from second differences was tried and never exceeded the stated one
under the primary condition, so it is not an option.)
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from tma2.references.classical import BearingData
from tma2.timelate.corr import MIN_SHARE, effective_sigma, estimate
from tma2.timelate.thin import WINDOW, edit_wild


@dataclass(frozen=True)
class Edit:
    wild: bool = False
    effective_sd: bool = False

    def __post_init__(self) -> None:
        if not (self.wild or self.effective_sd):
            raise ValueError("an edit that changes nothing")


def wild_flags(d: BearingData, rows: list[int], sigma: float) -> np.ndarray:
    """``valid`` (bool) without the wild bearings, causal at each of ``rows``."""
    t = np.asarray(d.t, dtype=np.float64)
    z = np.asarray(d.z, dtype=np.float64)
    v = np.asarray(d.valid) > 0
    out = edit_wild(t, z, v, sigma)
    half = WINDOW // 2
    for k in sorted(rows):
        cut = edit_wild(t[: k + 1], z[: k + 1], v[: k + 1], sigma)
        last = np.flatnonzero(v[: k + 1])[-half:]
        out[last] = cut[last]
    return out


def edited(d: BearingData, rows: list[int], cfg: Edit) -> tuple[BearingData, dict[str, float]]:
    """(the scenario as the segmenter is to see it, what was done)."""
    v = np.asarray(d.valid) > 0
    sigma = float(d.sigma)
    k0 = min(rows)
    z = np.asarray(d.z, dtype=np.float64)
    info = {"edited": 0.0, "sigma_factor": 1.0, "share": 0.0, "tau_s": 0.0}
    if cfg.wild:
        keep = wild_flags(d, rows, sigma)
        info["edited"] = float(v.sum() - keep.sum())
        v = keep
    if cfg.effective_sd:
        t = np.asarray(d.t, dtype=np.float64)
        pb = (t[: k0 + 1], d.ox[: k0 + 1], d.oy[: k0 + 1], z[: k0 + 1], v[: k0 + 1], sigma)
        share, tau = estimate(pb)
        info["share"], info["tau_s"] = share, tau
        if share >= MIN_SHARE:
            sigma = effective_sigma(sigma, share, tau, float(np.median(np.diff(t))))
    info["sigma_factor"] = sigma / float(d.sigma)
    return replace(d, valid=v.astype(np.asarray(d.valid).dtype), sigma=sigma), info
