"""The Cramér–Rao bound for the state at every row of a period, given all the period's
bearings and the manoeuvre times (spec 013 research R5).

The known-manoeuvres model is parameterised from the engagement's start (``references/crb.py``).
Information is additive over bearings, so the period's information is the information
accumulated to its last row minus that accumulated before its first; the state map at each row
comes from the same pass. Combinations of parameters the period's bearings do not see are
allowed only if the state at the row does not move along them (``crb._bound``), which is what
makes a period with no ownship manoeuvre come out undetermined.
"""

from __future__ import annotations

import numpy as np

from tma2.kinds import manoeuvre_table
from tma2.references.crb import _bound, known_manoeuvre_information

from .periods import Period


def period_bound(p: Period) -> np.ndarray:
    """[rows, 3] standard deviations (relative range, course °, speed kt) at each row of the
    period; NaN where the state is not determined."""
    own, tgt, obs = p.own, p.tgt, p.obs
    t = own[:, 0].astype(np.float64)
    ox, oy = own[:, 1].astype(np.float64), own[:, 2].astype(np.float64)
    tx, ty = tgt[:, 1].astype(np.float64), tgt[:, 2].astype(np.float64)
    course, speed = tgt[:, 3].astype(np.float64), tgt[:, 4].astype(np.float64)
    tvx, tvy = speed * np.sin(course), speed * np.cos(course)
    valid = (obs[:, 2] != 0).astype(np.float64)
    tm = manoeuvre_table(list(p.meta["parameters"].get("target_manoeuvres") or []))
    order = np.argsort(tm[:, 1], kind="stable") if tm.shape[0] else np.zeros(0, dtype=np.int64)
    tms = tm[order]
    both = tms[:, 0] == 2.0
    dur2 = np.zeros(tms.shape[0])
    if both.any():
        dur2[both] = np.abs(tms[both, 4]) / tms[both, 5]
    mans = np.stack([tms[:, 0], tms[:, 1], np.abs(tms[:, 2]) / tms[:, 3], tms[:, 2], dur2], axis=1)
    changes: list[float] = []
    for r in range(tms.shape[0]):
        changes.append(float(tms[r, 2]))
        if both[r]:
            changes.append(float(tms[r, 4]))
    theta = np.concatenate([[tx[0], ty[0], tvx[0], tvy[0]], changes]).astype(np.float64)
    rows = np.arange(max(p.first - 1, 0), p.last + 1, dtype=np.int64)
    sigma = float(p.meta["parameters"]["noise_sigma_rad"])
    info, g = known_manoeuvre_information(
        theta, np.ascontiguousarray(mans.reshape(-1, 5)), t, ox, oy, tx, ty, valid, rows, sigma
    )
    off = 1 if p.first > 0 else 0
    total = info[-1] - (info[0] if p.first > 0 else 0.0)
    out = np.full((p.rows, 3), np.nan)
    for q in range(p.rows):
        i = p.first + q
        b = _bound(total, g[off + q], tx[i] - ox[i], ty[i] - oy[i], float(tvx[i]), float(tvy[i]))
        if not b.singular:
            out[q] = (b.sd_range_rel, b.sd_course_deg, b.sd_speed_kt)
    return out
