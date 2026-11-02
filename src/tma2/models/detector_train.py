"""Detector training (spec 004 FR-019–FR-021; research R5).

As spec 003's ``train``: epoch e trains on fresh on-the-fly scenarios [e·N, (e+1)·N) of the
plan's training stream (seed 311), in batches of ``batch_scenarios``, with the generator's own
bearings (``noise_draws`` 1: every epoch's scenarios are new, so a re-draw adds nothing); every
random choice derives from (detector seed, epoch, batch) and the model has no dropout, so a run
resumed at an epoch boundary equals an uninterrupted one.

Per scenario: the classification losses at every row (``now``) and at the scored rows (pairs);
the downstream loss at ``downstream_rows`` scored rows: one G5 row (zig + 5/10/15/20 min, where
the window reaches it) and random post-zig rows, the physics layer run with ``train_iterations``
iterations and ``knots`` knots, gradients by the implicit Newton step. The causal variant asks
each question at its scored row; the time-late variant asks it at the window's last row and
reports the state at the scored row (``k_state``).

After each epoch: the validation loss (the configured weighted total on fixed validation rows,
the layer solved with ``iterations``), head liveness, and a checkpoint (weights, best weights and
their digest, optimiser state, ``CheckpointMeta``).
"""

from __future__ import annotations

import datetime as dt
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from numba import njit, prange
from safetensors.torch import load_file

from tma2.data.io import file_digest
from tma2.eval.experiment import run_environment
from tma2.eval.rows import G5_GATE_MIN
from tma2.features.batch import Batch, generate_batch
from tma2.physics.layer import PhysicsLayer
from tma2.references import lsq
from tma2.references.crb import crb_known_manoeuvres_fast
from tma2.types.generated.tma import (
    CheckpointMeta,
    DetectorConfig,
    DetectorVariant,
    JobRecord,
    TrainingPlan,
)

from .detector import Detector, DetectorOutput, features
from .detector_labels import pair_labels, row_labels
from .detector_loss import (
    DetectorLossParts,
    DetectorTargets,
    detector_loss,
    downstream_loss,
    run_downstream,
)
from .train import (
    GRAD_CLIP,
    VALIDATION_GROUP,
    VALIDATION_ROW_SEED,
    Checkpoint,
    batch_from_pack,
    git_state,
    improved,
    load_plan,
    slice_batch,
)


def detector_from_plan(plan: TrainingPlan, detector_id: str) -> DetectorConfig:
    for d in plan.detectors or []:
        if d.id == detector_id:
            return d
    raise ValueError(f"plan {plan.id} has no detector {detector_id}")


def _dt(batch: Batch) -> np.ndarray:
    return np.where(batch.samples > 1, batch.t[:, 1] - batch.t[:, 0], 10.0).astype(np.float64)


def scored_rows(batch: Batch, rng: np.random.Generator, per_scenario: int) -> np.ndarray:
    """[B, per_scenario] rows (−1: none): one G5 row where the window reaches one, then random
    post-zig rows, all distinct and sorted per scenario."""
    out = np.full((len(batch), per_scenario), -1, dtype=np.int64)
    dts = _dt(batch)
    for s in range(len(batch)):
        n = int(batch.samples[s])
        zig = int(batch.zig_index[s])
        post = list(range(zig + 1, n))
        if not post:
            continue
        g5 = [zig + int(round(m * 60 / dts[s])) for m in G5_GATE_MIN]
        g5 = [k for k in g5 if k < n]
        chosen = [int(rng.choice(g5))] if g5 else []
        rest = [k for k in post if k not in chosen]
        extra = min(per_scenario - len(chosen), len(rest))
        if extra > 0:
            chosen += [int(v) for v in rng.choice(rest, size=extra, replace=False)]
        chosen.sort()
        out[s, : len(chosen)] = chosen
    return out


@njit(parallel=True, cache=True)
def grid_starts(
    t: np.ndarray, ox: np.ndarray, oy: np.ndarray, z: np.ndarray, valid: np.ndarray, ks: np.ndarray
) -> np.ndarray:
    """gitma's grid start (``lsq.grid_start`` on rows [0, k]) for every question k ≥ 0 of
    ks [B, N] (zeros where k < 0 or no bearing): [B, N, 4], scenarios in parallel."""
    b_, n_ = ks.shape
    out = np.zeros((b_, n_, 4))
    for s in prange(b_):
        for q in range(n_):
            k = ks[s, q]
            if k >= 0:
                found, th = lsq.grid_start(t[s], ox[s], oy[s], z[s], valid[s], k + 1)
                if found:
                    for c in range(4):
                        out[s, q, c] = th[c]
    return out


@dataclass
class DetectorBatch:
    x: torch.Tensor  # [B, R, 13]
    window: torch.Tensor  # [B, R]
    bearing: torch.Tensor
    valid: torch.Tensor
    own_xy: torch.Tensor  # [B, R, 2]
    t: torch.Tensor
    sigma: torch.Tensor  # [B]
    y: DetectorTargets  # pairs at the question rows
    scored: torch.Tensor  # [B, N] the rows whose state is scored
    truth: torch.Tensor  # [B, N, 4] (x, y, vx, vy) at the scored rows (NaN: none)
    bound_cov: torch.Tensor  # [B, N, 4, 4] known-manoeuvres bound (NaN: singular or none)
    own_at: torch.Tensor  # [B, N, 2] ownship at the scored rows
    theta0: torch.Tensor  # [B, N, 4] grid start at each question's row (numba)


def detector_batch(batch: Batch, cfg: DetectorConfig, rng: np.random.Generator) -> DetectorBatch:
    def d(a: np.ndarray) -> torch.Tensor:
        return torch.from_numpy(np.ascontiguousarray(a, dtype=np.float64))

    r = batch.t.shape[1]
    dts = _dt(batch)
    window = d(batch.mask)
    bearing = d(batch.bearing)
    valid = d(batch.valid) * window
    own = d(batch.own)
    t = d(batch.t)
    scored = scored_rows(batch, rng, cfg.downstream_rows)
    if cfg.variant == DetectorVariant.time_late:
        last = (batch.samples.astype(np.int64) - 1)[:, None]
        query = np.where(scored >= 0, np.broadcast_to(last, scored.shape), -1)
    else:
        query = scored
    rl = row_labels(batch.spans, batch.samples, dts, r, cfg.now_window_s, cfg.tolerance_s)
    pl = pair_labels(batch.spans, dts, query, r, cfg.tolerance_s)
    y = DetectorTargets(
        now=d(rl.now),
        held=torch.from_numpy(rl.held),
        valid_row=torch.from_numpy(rl.valid_row),
        w_target=d(pl.w_target),
        kind=d(pl.kind),
        kind_weight=d(pl.kind_weight),
        query=torch.from_numpy(query),
    )
    b_, n_ = scored.shape
    theta0 = grid_starts(
        batch.t.astype(np.float64),
        batch.own[..., 0].astype(np.float64),
        batch.own[..., 1].astype(np.float64),
        batch.bearing.astype(np.float64),
        batch.valid.astype(np.uint8),
        np.ascontiguousarray(query, dtype=np.int64),
    )
    truth = np.full((b_, n_, 4), np.nan)
    bound = np.full((b_, n_, 4, 4), np.nan)
    own_at = np.zeros((b_, n_, 2))
    if cfg.loss_downstream_weight > 0:
        for s in range(b_):
            ks = [int(k) for k in scored[s] if k >= 0]
            if not ks:
                continue
            n = int(batch.samples[s])
            c = batch.tgt[s, :n, 2].astype(np.float64)
            v = batch.tgt[s, :n, 3].astype(np.float64)
            tvx, tvy = v * np.sin(c), v * np.cos(c)
            rows = crb_known_manoeuvres_fast(
                batch.t[s, :n],
                batch.own[s, :n, 0],
                batch.own[s, :n, 1],
                batch.tgt[s, :n, 0],
                batch.tgt[s, :n, 1],
                tvx,
                tvy,
                batch.valid[s, :n],
                batch.tm[s, : max(int(batch.n_tm[s]), 0)],
                ks,
                float(batch.sigma[s]),
            )
            for q, (k, cr) in enumerate(zip(ks, rows, strict=True)):
                truth[s, q] = (batch.tgt[s, k, 0], batch.tgt[s, k, 1], tvx[k], tvy[k])
                if cr.state_cov is not None and not cr.singular:
                    bound[s, q] = cr.state_cov
                own_at[s, q] = batch.own[s, k, :2]
    return DetectorBatch(
        x=features(bearing, valid, own, t, window),
        window=window,
        bearing=bearing,
        valid=valid,
        own_xy=own[..., :2].contiguous(),
        t=t,
        sigma=d(batch.sigma),
        y=y,
        scored=torch.from_numpy(scored),
        truth=d(truth),
        bound_cov=d(bound),
        own_at=d(own_at),
        theta0=d(theta0),
    )


def step_loss(
    model: Detector, layer: PhysicsLayer, xb: DetectorBatch, cfg: DetectorConfig
) -> tuple[DetectorLossParts, DetectorOutput]:
    out = model(xb.x, xb.window, xb.y.query)
    ds = None
    if cfg.loss_downstream_weight > 0:
        k_state = xb.scored if cfg.variant == DetectorVariant.time_late else None
        res, bi, qi = run_downstream(
            layer,
            out,
            xb.bearing,
            xb.valid,
            xb.own_xy,
            xb.t,
            xb.sigma,
            xb.y.query,
            k_state,
            xb.theta0,
        )
        own = xb.own_at[bi, qi]
        ds = downstream_loss(res, xb.truth[bi, qi], xb.bound_cov[bi, qi], own[:, 0], own[:, 1])
    return detector_loss(out, xb.y, cfg, ds), out


def validation_batches(
    plan: TrainingPlan, cfg: DetectorConfig, data_dir: Path
) -> list[DetectorBatch]:
    path = data_dir / Path(plan.validation.path).name
    digest = file_digest(path)
    if plan.validation.digest and digest != plan.validation.digest:
        raise ValueError(f"{path}: digest {digest} is not the plan's {plan.validation.digest}")
    batch = batch_from_pack(path, plan.validation_scenarios)
    rng = np.random.default_rng(VALIDATION_ROW_SEED)
    return [
        detector_batch(slice_batch(batch, a, min(a + VALIDATION_GROUP, len(batch))), cfg, rng)
        for a in range(0, len(batch), VALIDATION_GROUP)
    ]


def validation_loss(
    model: Detector, layer: PhysicsLayer, groups: list[DetectorBatch], cfg: DetectorConfig
) -> float:
    """The configured weighted total, averaged over groups by scenario count."""
    layer.implicit = False
    total = 0.0
    n = 0
    with torch.no_grad():
        for xb in groups:
            lp, _ = step_loss(model, layer, xb, cfg)
            total += float(lp.total) * xb.x.shape[0]
            n += xb.x.shape[0]
    return total / max(n, 1)


def train_detector(
    plan_path: str | Path,
    detector_id: str,
    checkpoint: str | Path,
    data_dir: str | Path,
    max_wall_s: float = 1e12,
    epochs: int | None = None,
    scenarios: int | None = None,
    log: Any = print,
) -> CheckpointMeta:
    """Train or resume one detector; returns the checkpoint metadata after the last epoch run."""
    t_start = time.time()
    started = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    plan, plan_digest = load_plan(plan_path)
    cfg = detector_from_plan(plan, detector_id)
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(cfg.threads)
    torch.use_deterministic_algorithms(True)
    n_epoch = scenarios or plan.scenarios_per_epoch
    max_epochs = epochs or cfg.epochs
    ck = Checkpoint(Path(checkpoint))
    torch.manual_seed(cfg.seed)
    model = Detector(cfg)
    layer = PhysicsLayer(iterations=cfg.iterations, knots=cfg.knots)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    best: dict[str, torch.Tensor] | None = None
    if ck.exists():
        meta = ck.load_meta()
        if (
            meta.plan_id != plan.id
            or meta.model_id != detector_id
            or meta.plan_digest != plan_digest
        ):
            raise ValueError(f"{checkpoint}: checkpoint is for {meta.plan_id}/{meta.model_id}")
        model.load_state_dict(load_file(str(ck.folder / "weights.safetensors")))
        opt.load_state_dict(torch.load(ck.folder / "optim.pt", weights_only=True))
        if (ck.folder / "best.safetensors").exists():
            best = load_file(str(ck.folder / "best.safetensors"))
    else:
        meta = CheckpointMeta(
            model_id=detector_id,
            plan_id=plan.id,
            plan_digest=plan_digest,
            epoch=0,
            best_epoch=0,
            best_val_loss=float("inf"),
            val_losses=[],
            train_losses=[],
            epoch_seconds=[],
            complete=False,
            jobs=[],
        )
    first_epoch = meta.epoch + 1
    val = validation_batches(plan, cfg, Path(data_dir))
    ranges = plan.ranges.model_dump(mode="json", exclude_none=True)
    while not meta.complete and meta.epoch < max_epochs:
        e = meta.epoch + 1
        last = (meta.epoch_seconds or [0.0])[-1]
        if e > first_epoch and time.time() - t_start + last > max_wall_s:
            log(f"wall-clock cap: stopping before epoch {e}")
            break
        t0 = time.time()
        model.train()
        losses = []
        for b in range(int(np.ceil(n_epoch / cfg.batch_scenarios))):
            batch = generate_batch(
                plan.train_seed,
                b,
                cfg.batch_scenarios,
                ranges,
                start=(e - 1) * n_epoch,
                end=e * n_epoch,
            )
            rng = np.random.default_rng([cfg.seed, e, b])
            xb = detector_batch(batch, cfg, rng)
            layer.implicit = True
            layer.iterations = cfg.train_iterations
            lp, _ = step_loss(model, layer, xb, cfg)
            layer.iterations = cfg.iterations
            opt.zero_grad()
            lp.total.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            opt.step()
            losses.append(float(lp.total.detach()))
        train_s = time.time() - t0
        model.eval()
        v = validation_loss(model, layer, val, cfg)
        secs = time.time() - t0
        meta.epoch = e
        meta.train_losses = [*(meta.train_losses or []), float(np.mean(losses))]
        meta.val_losses = [*(meta.val_losses or []), v]
        meta.epoch_seconds = [*(meta.epoch_seconds or []), secs]
        g0 = val[0]
        meta.liveness = model.head_liveness(g0.x, g0.window, g0.y.query)
        if improved(v, meta.best_val_loss, cfg.min_improvement):
            meta.best_val_loss, meta.best_epoch = v, e
            best = {k: t.detach().clone().contiguous() for k, t in model.state_dict().items()}
        if e - meta.best_epoch >= cfg.patience or e >= cfg.epochs:
            meta.complete = True
        ck.save(model, best, opt, meta)
        log(
            json.dumps(
                {
                    "detector": detector_id,
                    "epoch": e,
                    "train": meta.train_losses[-1],
                    "val": v,
                    "seconds": round(secs, 1),
                    "train_seconds": round(train_s, 1),
                    "scenarios": n_epoch,
                }
            )
        )
    env = run_environment()
    commit, dirty = git_state()
    job = JobRecord(
        started=started,
        finished=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        seconds=time.time() - t_start,
        first_epoch=first_epoch,
        last_epoch=meta.epoch,
        cpu_model=str(env.get("cpu_model", "unknown")),
        threads=cfg.threads,
        git_commit=commit,
        git_dirty=dirty,
    )
    meta.jobs = [*(meta.jobs or []), job]
    ck.save(model, best, opt, meta)
    return meta
