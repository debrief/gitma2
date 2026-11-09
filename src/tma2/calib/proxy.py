"""The causal unsettled proxy (spec 010 research R1).

Per scored row (ordinal, k), from information available at k only:

* ``bias{W}`` (W = 6, 12, 30 rows): |mean| · √n of the normalised bearing residuals over the
  last W valid bearings, against E's state at k propagated back at constant velocity. A fresh
  target manoeuvre leaves a run of same-signed residuals at the end of the window.
* ``chi60``: the mean squared normalised residual over the last 60 rows.
* C's open flag at k is taken from the feature cache (``open``, E's own re-run of C); time since C's
  last transition was dropped (tuning AUC 0.50, research R1).

The proxy score is a logistic function of these, E's three log sds and the minute, fitted on
tuning rows for the truth "not settled" (``fit_proxy``); the flag is the score above a threshold
matched to the tuning base rate. Both are bound by the Gate 5 decision record.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

WINDOWS = (6, 12, 30)
CHI_WINDOW = 60
FEATURES = ("bias6", "bias12", "bias30", "chi60")


def residual_features(
    state: np.ndarray, k: int, own: np.ndarray, obs: np.ndarray, sigma: float
) -> dict[str, float]:
    """Residual statistics at row k. ``own`` [S, ≥3] (t, x, y), ``obs`` [S, 3] (t, bearing,
    valid); ``state`` (x, y, vx, vy) of the target at row k. Uses rows ≤ k only."""
    x, y, vx, vy = (float(v) for v in state)
    tk = float(own[k, 0])
    out: dict[str, float] = {}
    for w in (*WINDOWS, CHI_WINDOW):
        j = np.arange(max(0, k - w + 1), k + 1)
        j = j[obs[j, 2] != 0]
        if len(j) < 3:
            r = np.zeros(0)
        else:
            dt = tk - own[j, 0]
            px, py = x - dt * vx, y - dt * vy
            pred = np.arctan2(px - own[j, 1], py - own[j, 2])
            d = obs[j, 1] - pred
            r = np.arctan2(np.sin(d), np.cos(d)) / sigma
        if w in WINDOWS:
            out[f"bias{w}"] = float(abs(r.mean()) * math.sqrt(len(r))) if len(r) else math.nan
        if w == CHI_WINDOW:
            out["chi60"] = float(np.mean(r**2)) if len(r) else math.nan
    return out


def design(
    feats: dict[str, np.ndarray], c_open: np.ndarray, log_sd: np.ndarray, minute: np.ndarray
) -> np.ndarray:
    """[N, F] proxy inputs: log1p of the residual biases, log χ², C's open flag, the three log
    sds and the minute."""
    cols = [
        np.log1p(feats["bias6"]),
        np.log1p(feats["bias12"]),
        np.log1p(feats["bias30"]),
        np.log(np.maximum(feats["chi60"], 1e-6)),
        c_open.astype(np.float64),
        log_sd[:, 0],
        log_sd[:, 1],
        log_sd[:, 2],
        minute.astype(np.float64),
    ]
    return np.stack(cols, axis=1)


DESIGN_NAMES = (
    "log1p_bias6",
    "log1p_bias12",
    "log1p_bias30",
    "log_chi60",
    "c_open",
    "log_sd_range",
    "log_sd_course",
    "log_sd_speed",
    "minute",
)


def fit_proxy(x: np.ndarray, y: np.ndarray, l2: float = 1e-3) -> dict[str, Any]:
    """Logistic regression of y (not settled) on the standardised design; returns a
    ProxyDefinition-shaped dict without the threshold."""
    import torch

    ok = np.isfinite(x).all(axis=1)
    mu, sd = x[ok].mean(axis=0), x[ok].std(axis=0) + 1e-12
    xs = torch.as_tensor((x[ok] - mu) / sd)
    yt = torch.as_tensor(y[ok].astype(np.float64))
    w = torch.zeros(x.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b], max_iter=500, line_search_fn="strong_wolfe")

    def closure() -> torch.Tensor:
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(xs @ w + b, yt)
        loss = loss + l2 * (w**2).sum()
        loss.backward()  # type: ignore[no-untyped-call]
        return loss

    opt.step(closure)  # type: ignore[no-untyped-call]
    return {
        "features": list(DESIGN_NAMES),
        "mean": [float(v) for v in mu],
        "scale": [float(v) for v in sd],
        "coef": [float(v) for v in w.detach().numpy()],
        "intercept": float(b.detach()),
    }


def score(defn: dict[str, Any], x: np.ndarray) -> np.ndarray:
    """The proxy's logistic score (logit); NaN where an input is not finite."""
    z = (x - np.asarray(defn["mean"])) / np.asarray(defn["scale"])
    out: np.ndarray = z @ np.asarray(defn["coef"]) + float(defn["intercept"])
    return out


def load_aligned(
    paths: list[str | Path], ordinal: np.ndarray, k: np.ndarray
) -> dict[str, np.ndarray]:
    """Proxy features for the rows (ordinal, k), in that order; refuses a row the cache lacks."""
    parts: dict[str, list[np.ndarray]] = {}
    for p in paths:
        z = np.load(p)
        for key in ("ordinal", "k", *FEATURES):
            parts.setdefault(key, []).append(z[key])
    cat = {key: np.concatenate(v) for key, v in parts.items()}
    pos = {
        (int(o), int(kk)): i for i, (o, kk) in enumerate(zip(cat["ordinal"], cat["k"], strict=True))
    }
    try:
        idx = np.array(
            [pos[(int(o), int(kk))] for o, kk in zip(ordinal, k, strict=True)], dtype=np.int64
        )
    except KeyError as exc:
        raise ValueError(f"proxy cache has no row {exc}") from exc
    return {key: cat[key][idx] for key in FEATURES}


def header_of(path: str | Path) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(str(np.load(path)["header"]))
    return out
