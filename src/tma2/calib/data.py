"""The calibration head's feature cache (spec 008 data-model, research R7).

``tma2-g2predict --features`` writes one ``.npz`` per shard: for every scored row, E-w's encoder
state at the row (``h``), the solve's raw covariance (packed), the estimate, the truth, ownship
at the row, C's code there, the plausible and ``cov_ok`` flags, and the slice keys (G5 minute,
open-at-k). This module loads shards into one ``CalData`` and derives what the head and the loss
need: the input features and the NEES under the raw covariance (``q``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tma2.physics.uncertainty import derived_sds, unpack_cov


@dataclass
class CalData:
    ordinal: np.ndarray  # [N]
    k: np.ndarray  # [N]
    t: np.ndarray  # [N] the row's float32 timestamp, as prediction rows carry it
    x: np.ndarray  # [N, F] head inputs: h, log raw sds (3), code_k
    q: np.ndarray  # [N] NEES of the estimate under the raw covariance
    usable: np.ndarray  # [N] bool: plausible, cov_ok and q finite (training and fitting)
    scalable: np.ndarray  # [N] bool: plausible, cov_ok, sds finite (no truth: what gets scaled)
    minute: np.ndarray  # [N]
    open: np.ndarray  # [N] bool
    header: dict[str, Any]

    def select(self, mask: np.ndarray) -> CalData:
        return CalData(
            self.ordinal[mask],
            self.k[mask],
            self.t[mask],
            self.x[mask],
            self.q[mask],
            self.usable[mask],
            self.scalable[mask],
            self.minute[mask],
            self.open[mask],
            self.header,
        )

    def __len__(self) -> int:
        return int(self.ordinal.shape[0])


def load(paths: list[str | Path]) -> CalData:
    """Concatenate cache shards, in ordinal order. Every shard's header must name the same
    model, weights and plan (refused otherwise)."""
    parts: list[dict[str, np.ndarray]] = []
    head: dict[str, Any] | None = None
    for p in paths:
        z = np.load(p)
        h = json.loads(str(z["header"]))
        key = {k: h.get(k) for k in ("model", "weights_sha256", "plan_sha256")}
        if head is None:
            head = h
        elif key != {k: head.get(k) for k in key}:
            raise ValueError(f"{p}: made by another model, weights or plan")
        parts.append({k: z[k] for k in z.files if k != "header"})
    if head is None:
        raise ValueError("no feature cache given")
    cat = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    order = np.lexsort((cat["k"], cat["ordinal"]))
    cat = {k: v[order] for k, v in cat.items()}
    n = cat["ordinal"].shape[0]
    log_sd = np.full((n, 3), np.nan)
    q = np.full(n, np.inf)
    for i in range(n):
        if not (cat["plausible"][i] and cat["cov_ok"][i]):
            continue
        p_ = unpack_cov(cat["cov"][i])
        st = cat["state"][i]
        own = (float(cat["own"][i, 0]), float(cat["own"][i, 1]))
        log_sd[i] = np.log(derived_sds(st, p_, own))
        e = st - cat["truth"][i]
        try:
            q[i] = float(e @ np.linalg.solve(p_, e))
        except np.linalg.LinAlgError:
            q[i] = np.inf
    scalable = cat["plausible"] & cat["cov_ok"] & np.isfinite(log_sd).all(axis=1)
    usable = scalable & np.isfinite(q)
    x = np.concatenate([cat["h"], np.nan_to_num(log_sd), cat["code_k"][:, None]], axis=1)
    return CalData(
        ordinal=cat["ordinal"],
        k=cat["k"],
        t=cat["t"],
        x=x,
        q=q,
        usable=usable,
        scalable=scalable,
        minute=cat["minute"],
        open=cat["open"].astype(bool),
        header=head,
    )
