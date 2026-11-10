"""The known-manoeuvres Cramér–Rao bound under a given error covariance (spec 010 research R4).

``references.crb`` assumes independent bearing noise: I = Σ gᵢgᵢᵀ / σ². With covariance Σ on the
bearings used, I = Gᵀ Σ⁻¹ G, G the per-bearing rows gᵢ. The model, its Jacobian and the delta
method are ``references.crb``'s. With a white covariance this is that module's bound.

For the outlier mixture, pass the realised outlier variance on the diagonal (``extra_var``): the
bound of an estimator that knows which bearings were wild, slightly below the bound of one that
does not.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.references.crb import CrbRow, _bound, _model_jacobian, manoeuvre_model

from .cov import ErrorModel, whitener


def crb_rows_cov(
    own: np.ndarray,
    tgt: np.ndarray,
    obs: np.ndarray,
    target_manoeuvres: list[dict[str, Any]],
    rows: list[int],
    model: ErrorModel,
    extra_var: np.ndarray | None = None,
) -> list[CrbRow]:
    """Bounds at ``rows`` from pack arrays own/tgt [S, 5] and obs [S, 3]."""
    t = own[:, 0].astype(np.float64)
    ox, oy = own[:, 1].astype(np.float64), own[:, 2].astype(np.float64)
    tx, ty = tgt[:, 1].astype(np.float64), tgt[:, 2].astype(np.float64)
    course, speed = tgt[:, 3].astype(np.float64), tgt[:, 4].astype(np.float64)
    tvx, tvy = speed * np.sin(course), speed * np.cos(course)
    valid = obs[:, 2] != 0
    theta, mans = manoeuvre_model(
        list(target_manoeuvres), float(tx[0]), float(ty[0]), float(tvx[0]), float(tvy[0])
    )
    last = max(rows) if rows else -1
    jac = _model_jacobian(theta, t[: last + 1], mans)
    dx = tx[: last + 1] - ox[: last + 1]
    dy = ty[: last + 1] - oy[: last + 1]
    rho2 = dx * dx + dy * dy
    g = (dy / rho2)[:, None] * jac[:, 0, :] - (dx / rho2)[:, None] * jac[:, 1, :]  # [N, P]
    out = []
    for k in rows:
        use = valid[: k + 1]
        w = whitener(t[: k + 1], use, model, extra_var[: k + 1] if extra_var is not None else None)
        wg = w @ g[: k + 1]
        out.append(
            _bound(wg.T @ wg, jac[k], float(dx[k]), float(dy[k]), float(tvx[k]), float(tvy[k]))
        )
    return out
