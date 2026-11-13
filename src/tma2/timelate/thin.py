"""Thinning the bearings a whole-period fit sees (spec 014 FR-011, research R6; the owner's
idea of 2026-11-11: where the bearing rate is steady, fewer observations may do).

Three forms, each returning a ``Problem`` the arc fits accept unchanged:

* ``drop:N``: every N-th valid bearing, as it is.
* ``fixed:N``: one normal point per N rows: the value at the bin's mean time of a
  least-squares line through its bearings, with sd σ / √k for k bearings.
* ``adaptive:TOL``: bins that grow, two rows at a time up to ``MAX_ROWS``, while the bearing's
  departure from a straight line across the bin (the quadratic term at the bin's ends) stays
  under TOL · σ / √k: long bins where the bearing rate is steady, short ones where it bends.
  ``adaptive:TOL:robust`` (and ``fixed:N:robust``) first edits wild bearings out: one more
  than ``WILD`` sd from the running median of its ``WINDOW`` neighbours is not used, so it
  neither moves a point nor breaks a bin; each bin's line then takes Huber weights.

A normal point's ownship position is the ownship's at the point's time (interpolated), and
its sd is per point: the fits divide by it row by row.
"""

from __future__ import annotations

import numpy as np

from .retest import Problem

MAX_ROWS = 24  # 2 minutes at 5 seconds
MIN_ROWS = 2
HUBER = 2.0
WILD = 4.0
WINDOW = 9


def _line(t: np.ndarray, z: np.ndarray, sigma: float, robust: bool) -> tuple[float, float, float]:
    """(value at the weighted mean time, that time, its sd) of a line through (t, z)."""
    w = np.ones(t.size)
    tm, zm = float(t.mean()), float(z.mean())
    for _ in range(5 if robust and t.size >= 4 else 1):
        tm = float((w * t).sum() / w.sum())
        zm = float((w * z).sum() / w.sum())
        den = float((w * (t - tm) ** 2).sum())
        slope = float((w * (t - tm) * (z - zm)).sum() / den) if den > 0 else 0.0
        if not robust:
            break
        r = np.abs(z - zm - slope * (t - tm)) / sigma
        w = np.where(r <= HUBER, 1.0, HUBER / np.maximum(r, 1e-12))
    return zm, tm, sigma / float(np.sqrt(w.sum()))


def _bend(t: np.ndarray, z: np.ndarray) -> float:
    """The quadratic term of the bearings across a bin, as a bearing at the bin's ends."""
    if t.size < 4:
        return 0.0
    u = t - t.mean()
    half = float(np.abs(u).max())
    c = np.polyfit(u / max(half, 1e-9), z, 2)
    return float(abs(c[0]))


def _point(
    pb: Problem, rows: np.ndarray, robust: bool
) -> tuple[float, float, float, float, float] | None:
    t, ox, oy, z, v, sigma = pb
    k = rows[v[rows]]
    if k.size == 0:
        return None
    zz = np.unwrap(z[k])
    val, tm, sd = _line(t[k], zz, float(sigma), robust)
    return tm, float(np.interp(tm, t, ox)), float(np.interp(tm, t, oy)), val, sd


def edit_wild(t: np.ndarray, z: np.ndarray, v: np.ndarray, sigma: float) -> np.ndarray:
    """``v`` without the bearings more than ``WILD`` sd from the median of the ``WINDOW``
    valid bearings around them."""
    k = np.flatnonzero(v)
    if k.size < WINDOW:
        return v
    zz = np.unwrap(z[k])
    half = WINDOW // 2
    pad = np.concatenate([np.full(half, zz[0]), zz, np.full(half, zz[-1])])
    med = np.median(np.lib.stride_tricks.sliding_window_view(pad, WINDOW), axis=1)
    out = v.copy()
    out[k[np.abs(zz - med) > WILD * sigma]] = False
    return out


def thin(pb: Problem, form: str) -> Problem:
    """``pb`` thinned by ``form`` ("none", "drop:N", "fixed:N", "adaptive:TOL[:robust]")."""
    t, ox, oy, z, v, sigma = pb
    v = v.astype(bool)
    if np.ndim(sigma) != 0:
        raise ValueError("thin() takes a problem with one sd for every bearing")
    if form in ("", "none"):
        return pb
    kind, _, arg = form.partition(":")
    if kind == "drop":
        n = int(arg)
        keep = np.zeros(t.size, dtype=bool)
        keep[np.flatnonzero(v)[::n]] = True
        return (t, ox, oy, z, keep, sigma)
    bins: list[np.ndarray] = []
    robust = False
    if kind == "fixed":
        n_s, _, flag = arg.partition(":")
        n, robust = int(n_s), flag == "robust"
        v = edit_wild(t, z, v, float(sigma)) if robust else v
        bins = [np.arange(a, min(a + n, t.size)) for a in range(0, t.size, n)]
    elif kind == "adaptive":
        tol_s, _, flag = arg.partition(":")
        tol, robust = float(tol_s), flag == "robust"
        v = edit_wild(t, z, v, float(sigma)) if robust else v
        a = 0
        while a < t.size:
            b = min(a + MIN_ROWS, t.size)
            while b < t.size and b - a < MAX_ROWS:
                rows = np.arange(a, min(b + 2, t.size))
                k = rows[v[rows]]
                if k.size >= 4 and _bend(t[k], np.unwrap(z[k])) > tol * sigma / np.sqrt(k.size):
                    break
                b = min(b + 2, t.size)
            bins.append(np.arange(a, b))
            a = b
    else:
        raise ValueError(f"unknown thinning {form!r}")
    pts = [p for p in (_point((t, ox, oy, z, v, sigma), rows, robust) for rows in bins) if p]
    if len(pts) < 8:
        raise ValueError("thinning left fewer than eight points")
    arr = np.array(pts)
    sd: np.ndarray = arr[:, 4]
    return (
        arr[:, 0],
        arr[:, 1],
        arr[:, 2],
        (arr[:, 3] + np.pi) % (2 * np.pi) - np.pi,
        np.ones(arr.shape[0], dtype=bool),
        sd,  # type: ignore[return-value]
    )
