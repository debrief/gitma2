"""E-s's decision tables (spec 007 research R2; task T017).

C is run once per scenario with its confirmation recording every decision (``Decision``: the
row a it was tested on, the best candidate's start and length, its source, the cost drop and the
χ² threshold without evidence, and whether C accepted it). For each decision and each scored row
k ≥ a, the table holds the bound-normalised error of the physics layer's estimate at k with the
transition and without it, holding C's other decisions as C made them:

* an accepted decision: "with" is C's own segmentation at k; "without" drops that transition;
* a rejected decision: "without" is C's own segmentation; "with" adds the candidate, closed at
  its length if that end is ≤ k, open at k otherwise.

E-s's loss over one table is Σ_decisions Σ_k p·e_with + (1 − p)·e_without with
p = σ((drop − threshold − shift)/T) and shift = clamp(2 Σ e over the candidate's rows up to a,
± τ/2), the evidence's threshold shift as in spec 005. At e = 0 and T → 0 the decisions are C's,
so the loss is C's own error (FR-022). One decision at a time: a decision's effect on later
decisions is ignored (exact for isolated changes; research R2).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.cli.oracle import inputs_for
from tma2.models.loss import _bound_sd, _components
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData
from tma2.segment.confirm import Confirmed, Decision, Transition, confirm
from tma2.segment.segmenter import intervals_at, nominations_for
from tma2.types.generated.tma import SegmentParameters

from .inputs import prefix_inputs


@dataclass
class DecisionRow:
    decision: int  # index into the scenario's decisions
    k: int
    e_with: float
    e_without: float


@dataclass
class ScenarioTable:
    decisions: list[Decision]
    rows: list[DecisionRow]
    c_error: dict[int, float]  # C's own error at each scored row
    tau: float


def _without(conf: Confirmed, x: Transition) -> Confirmed:
    return Confirmed(
        transitions=[t for t in conf.transitions if t is not x],
        near_misses=conf.near_misses,
        solves=conf.solves,
        decisions=conf.decisions,
    )


def _with(conf: Confirmed, dd: Decision, margin: float) -> Confirmed:
    """C's decisions plus the rejected candidate, open until its full length (then closed)."""
    end = dd.start + dd.length - 1
    x = Transition(dd.start, end, dd.row, max(dd.row, end), dd.drop, margin, dd.source)
    return Confirmed(
        transitions=[*conf.transitions, x],
        near_misses=conf.near_misses,
        solves=conf.solves,
        decisions=conf.decisions,
    )


def _accepted_transition(conf: Confirmed, dd: Decision) -> Transition | None:
    for x in conf.transitions:
        if (
            x.accepted_at == dd.row
            and x.source == dd.source
            and abs(x.start_at(dd.row) - dd.start) <= 3
        ):
            return x
    return None


def normalised_errors(
    out: Any,
    truth: torch.Tensor,  # [N, 4]
    bound_cov: torch.Tensor,  # [N, 4, 4]
    okx: torch.Tensor,
    oky: torch.Tensor,
    n_valid: torch.Tensor,
    cap: float,
    fail_per_bearing: float = 20.0,
) -> torch.Tensor:
    """[N] capped normalised squared errors as ``gate2.loss.e_loss``; a prefix e_loss would
    exclude (failed fit, implausible, non-finite) scores ``cap``: a decision that breaks the fit
    is charged for it."""
    sd = _bound_sd(bound_cov, truth, okx, oky)
    est, tru = _components(out.state, truth, okx, oky)
    e = (est - tru) / sd
    sq = torch.clamp((e * e).sum(dim=1), max=cap)
    ok = (
        out.cov_ok
        & out.plausible
        & torch.isfinite(out.state).all(dim=1)
        & (out.cost <= fail_per_bearing * n_valid.to(out.cost.dtype))
        & torch.isfinite(sq)
    )
    return torch.where(ok, sq, torch.full_like(sq, cap))


def c_confirmations(
    layer: PhysicsLayer, data: list[BearingData], anchors: list[int], p: SegmentParameters
) -> list[Confirmed]:
    """C's confirmations with their decisions, scenarios batched and padded to the longest as
    ``segmenter.segment`` (so a chunk equal to a segmentation run's chunk reproduces it).
    ``anchors``: each scenario's first scored row, the search grid's anchor."""
    noms = [nominations_for(d, a, p) for d, a in zip(data, anchors, strict=True)]
    return confirm(layer, data, noms, p, max(d.n for d in data))


def c_confirmation(
    layer: PhysicsLayer, d: BearingData, anchor: int, p: SegmentParameters
) -> Confirmed:
    """``c_confirmations`` of one scenario."""
    return c_confirmations(layer, [d], [anchor], p)[0]


def in_band(dd: Decision, tau: float) -> bool:
    """Whether evidence can flip the decision: the shift is capped at ± τ/2, so a decision whose
    score is further than that from zero is C's whatever the evidence."""
    return abs(dd.drop - dd.threshold) < tau / 2.0


def scenario_table(
    layer: PhysicsLayer,
    d: BearingData,
    conf: Confirmed,
    ks: list[int],
    truth: dict[int, np.ndarray],
    bound: dict[int, np.ndarray],
    p: SegmentParameters,
    mode: str,
    open_handover: str | None,
    cap: float = 100.0,
    r_max: int | None = None,
    batch: int = 64,
) -> ScenarioTable:
    """C's decisions on one scenario (``c_confirmation``) with the errors with and without each
    in-band decision, at rows ``ks``. Out-of-band decisions get no rows: they are C's under any
    evidence, so their rows are constants of the loss."""
    jobs: list[tuple[int, list[Any]]] = []  # (k, intervals)
    for k in ks:
        jobs.append((k, intervals_at(conf, k, p)))
    keys: list[tuple[int, int, str]] = []  # (decision, k, "with" | "without") for the extra solves
    for q, dd in enumerate(conf.decisions):
        for k in ks:
            if k < dd.row or not in_band(dd, p.tau):
                continue
            if dd.accepted:
                x = _accepted_transition(conf, dd)
                if x is None:
                    continue
                jobs.append((k, intervals_at(_without(conf, x), k, p)))
                keys.append((q, k, "without"))
            else:
                jobs.append((k, intervals_at(_with(conf, dd, p.margin), k, p)))
                keys.append((q, k, "with"))
    items: list[tuple[int, tuple[BearingData, int, LayerInputs]]] = []
    for i, (k, ivs) in enumerate(jobs):
        inp = prefix_inputs(d, k, ivs, mode, open_handover)
        if inp is not None:
            items.append((i, (d, k, inp)))
    errs = [cap] * len(jobs)
    f64 = torch.float64
    for b0 in range(0, len(items), batch):
        part = items[b0 : b0 + batch]
        ks_ = [k for _, (_, k, _) in part]
        with torch.no_grad():
            out = layer(inputs_for([it for _, it in part], r_max or d.n))
            sq = normalised_errors(
                out,
                torch.tensor(np.stack([truth[k] for k in ks_]), dtype=f64),
                torch.tensor(np.stack([bound[k] for k in ks_]), dtype=f64),
                torch.tensor([float(d.ox[k]) for k in ks_], dtype=f64),
                torch.tensor([float(d.oy[k]) for k in ks_], dtype=f64),
                torch.tensor([int(d.valid[: k + 1].sum()) for k in ks_]),
                cap,
            )
        for n, (i, _) in enumerate(part):
            errs[i] = float(sq[n])
    c_error = {k: errs[i] for i, k in enumerate(ks)}
    rows: list[DecisionRow] = []
    for n, (q, k, kind) in enumerate(keys):
        extra = errs[len(ks) + n]
        if kind == "without":
            rows.append(DecisionRow(q, k, c_error[k], extra))
        else:
            rows.append(DecisionRow(q, k, extra, c_error[k]))
    return ScenarioTable(conf.decisions, rows, c_error, p.tau)


CAP = 100.0  # the per-row error cap (research R4), as gate2.loss's default


def c_block_sha256(plan: dict[str, Any]) -> str:
    """Digest of a Gate 2 plan's ``c`` block (C's digests, mode and hand-over): what decision
    tables depend on. Tables bind it rather than the whole plan, which names the tables' own
    results branch."""
    return hashlib.sha256(json.dumps(plan["c"], sort_keys=True).encode()).hexdigest()


def save_tables(path: str | Path, tables: dict[int, ScenarioTable], header: dict[str, Any]) -> None:
    """One npz: per ordinal, the decisions ([D, 6]: row, start, length, drop, threshold,
    accepted), their sources, the decision rows ([R, 4]: decision, k, e_with, e_without) and C's
    errors ([K, 2]: k, error)."""
    arrays: dict[str, Any] = {"header": np.array(json.dumps(header, sort_keys=True))}
    for j, t in sorted(tables.items()):
        arrays[f"{j}/decisions"] = np.array(
            [
                [x.row, x.start, x.length, x.drop, x.threshold, float(x.accepted)]
                for x in t.decisions
            ],
            dtype=np.float64,
        ).reshape(-1, 6)
        arrays[f"{j}/sources"] = np.array([x.source for x in t.decisions], dtype="U16")
        arrays[f"{j}/rows"] = np.array(
            [[r.decision, r.k, r.e_with, r.e_without] for r in t.rows], dtype=np.float64
        ).reshape(-1, 4)
        arrays[f"{j}/c_error"] = np.array(sorted(t.c_error.items()), dtype=np.float64).reshape(
            -1, 2
        )
        arrays[f"{j}/tau"] = np.array(t.tau)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def load_tables(path: str | Path) -> tuple[dict[str, Any], dict[int, ScenarioTable]]:
    z = np.load(path)
    header = json.loads(str(z["header"]))
    ords = sorted({int(k.split("/")[0]) for k in z.files if "/" in k})
    out: dict[int, ScenarioTable] = {}
    for j in ords:
        dec = z[f"{j}/decisions"]
        src = z[f"{j}/sources"]
        decisions = [
            Decision(int(r[0]), int(r[1]), int(r[2]), str(s_), float(r[3]), float(r[4]), bool(r[5]))
            for r, s_ in zip(dec, src, strict=True)
        ]
        rows = [DecisionRow(int(r[0]), int(r[1]), float(r[2]), float(r[3])) for r in z[f"{j}/rows"]]
        c_error = {int(r[0]): float(r[1]) for r in z[f"{j}/c_error"]}
        out[j] = ScenarioTable(decisions, rows, c_error, float(z[f"{j}/tau"]))
    return header, out


def relaxed_loss(
    table: ScenarioTable,
    evidence: torch.Tensor,  # [n] per-row evidence (positive = steady)
    temperature: float,
) -> torch.Tensor:
    """Σ over decision rows of p·e_with + (1 − p)·e_without (module docstring)."""
    ce = torch.cat([evidence.new_zeros(1), torch.cumsum(evidence, 0)])
    total = evidence.sum() * 0.0
    for r in table.rows:
        dd = table.decisions[r.decision]
        e_end = min(dd.start + dd.length - 1, dd.row)
        shift = torch.clamp(2.0 * (ce[e_end + 1] - ce[dd.start]), -table.tau / 2.0, table.tau / 2.0)
        p = torch.sigmoid((dd.drop - dd.threshold - shift) / temperature)
        total = total + p * r.e_with + (1.0 - p) * r.e_without
    return total


def truth_and_bounds(
    m: dict[str, Any], own: np.ndarray, tgt: np.ndarray, obs: np.ndarray, ks: list[int]
) -> tuple[list[int], dict[int, np.ndarray], dict[int, np.ndarray]]:
    """The rows of ``ks`` with a known-manoeuvres bound, their truth (x, y, vx, vy) and bound
    covariance, as ``train.build_prefixes``."""
    from tma2.references.crb import crb_rows

    crb = crb_rows(
        own,
        tgt,
        obs,
        float(m["parameters"]["noise_sigma_rad"]),
        int(m["zig_index"]),
        m.get("manoeuvres") or [],
        ks,
        model="known_manoeuvres",
        target_manoeuvres=m["parameters"].get("target_manoeuvres") or [],
        fast=True,
    )
    tg = tgt.astype(np.float64)
    kept: list[int] = []
    truth: dict[int, np.ndarray] = {}
    bound: dict[int, np.ndarray] = {}
    for k, c in zip(ks, crb, strict=True):
        if c.state_cov is None or c.singular:
            continue
        course, speed = tg[k, 3], tg[k, 4]
        kept.append(k)
        truth[k] = np.array([tg[k, 1], tg[k, 2], speed * np.sin(course), speed * np.cos(course)])
        bound[k] = np.asarray(c.state_cov, dtype=np.float64)
    return kept, truth, bound
