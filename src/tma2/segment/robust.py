"""Segmenter C-r (spec 011, plan research R1–R3): C's confirmation with a robust test.

C accepts a candidate transition when the drop in the sum of squared residuals exceeds a χ²
point; one wild bearing can buy a transition (diagnosis, ``experiments/20261110-gr-diagnosis``).
C-r changes only the costs the confirmation is given:

* each hypothesis is fitted by iteratively reweighted least squares with Huber weights
  (``huber_k``, ``reweightings`` passes after the plain start);
* its cost is the Huber cost Σ 2ρ(r / s) of that fit (plus the layer's prior terms), divided by
  E[ψ²] / E[ψ′], the factor by which a Huber cost drop exceeds a χ² variable under Gaussian
  errors, and by ``tau_factor``;
* s is the stated σ, or (``scale = "estimated"``) a causal estimate from second differences of
  the bearings up to the prefix row, which reads neither hypothesis (FR-014).

C's generator (``confirm._confirm_one``), nominators, parameters and ``intervals_at`` are used
unchanged, and no file under C's code digest is edited. With ``robust = False`` and
``tau_factor = 1`` the costs are C's own (the equality test); ``robust = False`` with a factor
above 1 is plain C at a higher threshold (the pilot's reference lines).

Causality: the costs of a request on prefix a read bearings at rows ≤ a only, so FR-002 holds
as it does for C.
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from tma2.cli.oracle import inputs_for
from tma2.physics.layer import PhysicsInputs, PhysicsLayer, PhysicsOutputs
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData
from tma2.types.generated.tma import SegmentParameters

from . import Interval
from .confirm import Confirmed, Nomination, Request, _confirm_one
from .inputs import segmentation_inputs
from .segmenter import intervals_at, nominations_for

BATCH = 256
MIN_DIFFS = 20  # second differences needed before the scale estimate replaces the stated σ
SOURCES = ("segment/robust.py",)


@dataclass(frozen=True)
class RobustConfirm:
    robust: bool = True
    huber_k: float = 2.0
    reweightings: int = 2
    scale: str = "stated"  # "stated" | "estimated"
    tau_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.scale not in ("stated", "estimated"):
            raise ValueError(f"scale {self.scale!r}: expected stated or estimated")
        if not (self.huber_k > 0 and self.reweightings >= 1 and self.tau_factor > 0):
            raise ValueError("huber_k, reweightings and tau_factor must be positive")


def robust_code_digest(root: Path | None = None) -> str:
    base = root or Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for rel in SOURCES:
        h.update(f"{rel}:{hashlib.sha256((base / rel).read_bytes()).hexdigest()}\n".encode())
    return h.hexdigest()


def huber_factor(k: float) -> float:
    """E[ψ²] / E[ψ′] for Huber's ψ with constant k under a standard normal."""
    cdf = 0.5 * (1.0 + math.erf(k / math.sqrt(2.0)))
    pdf = math.exp(-0.5 * k * k) / math.sqrt(2.0 * math.pi)
    inner = 2.0 * cdf - 1.0
    return (inner - 2.0 * k * pdf + 2.0 * k * k * (1.0 - cdf)) / inner


def scale_at(d: BearingData, a: int) -> float:
    """1.4826 × the median absolute second difference of the valid bearings at rows ≤ a, ÷ √6
    (white error of sd σ gives σ); the stated σ until ``MIN_DIFFS`` differences exist."""
    v = d.valid[: a + 1] > 0
    z = np.unwrap(d.z[: a + 1])
    ok = v[2:] & v[1:-1] & v[:-2]
    if int(ok.sum()) < MIN_DIFFS:
        return float(d.sigma)
    d2 = (z[2:] - 2.0 * z[1:-1] + z[:-2])[ok]
    s = 1.4826 * float(np.median(np.abs(d2))) / math.sqrt(6.0)
    return s if s > 0 else float(d.sigma)


class RawLayer(PhysicsLayer):
    """``PhysicsLayer`` that keeps the weighted bearing residuals of its last solve."""

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.raw: Tensor | None = None

    def _outputs(self, theta: Tensor, cost: Tensor, x: PhysicsInputs, *args: Any) -> PhysicsOutputs:
        ox, oy, sw, t_knots, c, s, order, ref_order, _knots = args
        r, _ = self._residuals(theta, x.t, ox, oy, x.bearing, sw, t_knots, c, s, order, ref_order)
        self.raw = r[:, : x.bearing.shape[1]]
        return super()._outputs(theta, cost, x, *args)


Item = tuple[BearingData, int, LayerInputs]


def _solve(layer: RawLayer, items: list[Item], r_max: int) -> tuple[np.ndarray, np.ndarray]:
    with torch.no_grad():
        out = layer(inputs_for(items, r_max))
    assert layer.raw is not None
    raw = layer.raw.numpy().copy()
    layer.raw = None
    return out.cost.numpy().copy(), raw


def robust_costs(layer: RawLayer, items: list[Item], cfg: RobustConfirm, r_max: int) -> list[float]:
    """The confirmation cost of each (data, prefix row, inputs) item under ``cfg``."""
    out: list[float] = []
    lam = huber_factor(cfg.huber_k) if cfg.robust else 1.0
    for s0 in range(0, len(items), BATCH):
        part = items[s0 : s0 + BATCH]
        if not cfg.robust:
            cost, _ = _solve(layer, part, r_max)
            out.extend(float(c) / cfg.tau_factor for c in cost)
            continue
        # log-weight offset for the scale: the layer divides by the stated σ
        off = [
            -2.0 * math.log(scale_at(d, k) / d.sigma) if cfg.scale == "estimated" else 0.0
            for d, k, _ in part
        ]
        base = [
            inp.log_weight.astype(np.float64) + o for (_, _, inp), o in zip(part, off, strict=True)
        ]
        w = [np.ones_like(b) for b in base]
        cost = np.zeros(len(part))
        u = [np.zeros_like(b) for b in base]
        for it in range(cfg.reweightings + 1):
            cur = [
                (d, k, dataclasses.replace(inp, log_weight=b + np.log(wi)))
                for (d, k, inp), b, wi in zip(part, base, w, strict=True)
            ]
            cost, raw = _solve(layer, cur, r_max)
            for q, wi in enumerate(w):
                u[q] = raw[q, : wi.shape[0]] / np.sqrt(wi)
                if it < cfg.reweightings:
                    w[q] = np.minimum(1.0, cfg.huber_k / np.maximum(np.abs(u[q]), 1e-300))
        for q, wi in enumerate(w):
            au = np.abs(u[q])
            rho2 = np.where(au <= cfg.huber_k, au * au, 2.0 * cfg.huber_k * au - cfg.huber_k**2)
            prior = float(cost[q]) - float((wi * u[q] * u[q]).sum())
            out.append((prior + float(rho2.sum())) / (lam * cfg.tau_factor))
    return out


def confirm_robust(
    layer: RawLayer,
    data: list[BearingData],
    nominations: list[list[Nomination]],
    p: SegmentParameters,
    r_max: int,
    cfg: RobustConfirm,
    evidence: list[np.ndarray] | None = None,
) -> list[Confirmed]:
    """``confirm.confirm`` with ``robust_costs`` in place of the plain layer costs."""
    gens = [
        _confirm_one(d.n, noms, p, None if evidence is None else evidence[i])
        for i, (d, noms) in enumerate(zip(data, nominations, strict=True))
    ]
    out: list[Confirmed | None] = [None] * len(data)
    pending: dict[int, list[Request]] = {}
    for i, g in enumerate(gens):
        try:
            pending[i] = next(g)
        except StopIteration as stop:
            out[i] = stop.value
    while pending:
        items: list[Item] = []
        owners: list[int] = []
        for i, reqs in pending.items():
            d = data[i]
            for k, trs in reqs:
                inp = segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, trs, "chord", False)
                if inp is None:
                    raise ValueError(f"scenario {d.index}: no valid bearing on [0, {k}]")
                items.append((d, k, inp))
                owners.append(i)
        costs = robust_costs(layer, items, cfg, r_max)
        by: dict[int, list[float]] = {}
        for i, cst in zip(owners, costs, strict=True):
            by.setdefault(i, []).append(cst if math.isfinite(cst) else math.inf)
        nxt: dict[int, list[Request]] = {}
        for i in pending:
            try:
                nxt[i] = gens[i].send(by[i])
            except StopIteration as stop:
                out[i] = stop.value
        pending = nxt
    return [x if x is not None else Confirmed() for x in out]


def robust_segmentations(
    data: list[BearingData],
    rows: list[list[int]],
    p: SegmentParameters,
    cfg: RobustConfirm,
    evidence: list[np.ndarray] | None = None,
) -> tuple[list[dict[int, list[Interval]]], list[Confirmed]]:
    """C-r's segmentation of each scenario at its rows (nominators as C's), and what it
    confirmed. ``evidence``: the zig veto of C″ (``gate2.predict.zig_veto_evidence``)."""
    noms = [nominations_for(d, ks[0], p) for d, ks in zip(data, rows, strict=True)]
    confs = confirm_robust(RawLayer(), data, noms, p, max(d.n for d in data), cfg, evidence)
    segs = [{k: intervals_at(c, k, p) for k in ks} for c, ks in zip(confs, rows, strict=True)]
    return segs, confs
