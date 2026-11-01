"""Gate 1 training (spec 003 FR-011–FR-016; research R4, R5, R7).

Epoch e trains on fresh on-the-fly scenarios [e·N, (e+1)·N) of the plan's training seed stream,
in batches of ``batch_scenarios``; every random choice (noise draws, scored rows, shuffled labels)
derives from (model seed, epoch, batch), and the model has no dropout, so a run resumed at an
epoch boundary equals an uninterrupted one. After each epoch the validation loss (the mean
normalised squared error on fixed validation rows, solved to convergence) is recorded and a
checkpoint written: weights, best weights, optimiser state and :class:`CheckpointMeta`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors.torch import load_file, save_file

from tma2.data.f32pack import iter_pack_raw
from tma2.data.io import AtomicFile, file_digest
from tma2.eval.experiment import ROOT, run_environment
from tma2.features.batch import Batch, generate_batch
from tma2.types import dump_record, parse_record
from tma2.types.generated.tma import (
    CheckpointMeta,
    JobRecord,
    PhysicsModelConfig,
    TrainingPlan,
)

from .batching import ModelInputs, model_inputs, run
from .gate1 import Gate1Model
from .loss import gate1_loss
from .rows import row_batch, scenario_tensors

GRAD_CLIP = 1.0
VALIDATION_ROW_SEED = 0


def load_plan(path: str | Path) -> tuple[TrainingPlan, str]:
    raw = Path(path).read_bytes()
    plan = parse_record(TrainingPlan, json.loads(raw), str(path), 1)
    return plan, hashlib.sha256(raw).hexdigest()


def model_from_plan(plan: TrainingPlan, model_id: str) -> PhysicsModelConfig:
    for m in plan.models:
        if m.id == model_id:
            return m
    raise ValueError(f"plan {plan.id} has no model {model_id}")


def batch_from_pack(path: Path, limit: int) -> Batch:
    """The first ``limit`` scenarios of a split file as a :class:`Batch` (validation, scoring)."""
    blocks = []
    for n, (_, meta, own, tgt, obs) in enumerate(iter_pack_raw(path)):
        if n >= limit:
            break
        blocks.append((meta, own, tgt, obs))
    rmax = max(int(m["samples"]) for m, *_ in blocks)
    s = len(blocks)
    b = Batch(
        index=np.array([int(m["index"]) for m, *_ in blocks], dtype=np.int64),
        samples=np.array([int(m["samples"]) for m, *_ in blocks], dtype=np.int32),
        zig_index=np.array([int(m["zig_index"]) for m, *_ in blocks], dtype=np.int32),
        sigma=np.array([m["parameters"]["noise_sigma_rad"] for m, *_ in blocks], dtype=np.float32),
        dropout=np.array(
            [m["parameters"]["dropout_fraction"] for m, *_ in blocks], dtype=np.float32
        ),
        redraws=np.zeros(s, dtype=np.int32),
        t=np.zeros((s, rmax), dtype=np.float32),
        mask=np.zeros((s, rmax), dtype=np.bool_),
        own=np.zeros((s, rmax, 4), dtype=np.float32),
        tgt=np.zeros((s, rmax, 4), dtype=np.float32),
        bearing=np.zeros((s, rmax), dtype=np.float32),
        valid=np.zeros((s, rmax), dtype=np.bool_),
        manoeuvring=np.zeros((s, rmax), dtype=np.bool_),
        last_kind=np.full((s, rmax), -1, dtype=np.int8),
        since_zig_s=np.zeros((s, rmax), dtype=np.float32),
        since_manoeuvre_end_s=np.full((s, rmax), -1.0, dtype=np.float32),
        spans=np.full((s, 4, 3), -1, dtype=np.int32),
    )
    for i, (meta, own, tgt, obs) in enumerate(blocks):
        n = int(meta["samples"])
        b.t[i, :n] = own[:n, 0]
        b.mask[i, :n] = True
        b.own[i, :n] = own[:n, 1:5]
        b.tgt[i, :n] = tgt[:n, 1:5]
        b.bearing[i, :n] = obs[:n, 1]
        b.valid[i, :n] = obs[:n, 2] != 0
        zt = float(own[int(meta["zig_index"]), 0])
        b.since_zig_s[i, :n] = own[:n, 0] - zt
    return b


def _inputs(
    batch: Batch, seed: int, draws: int, rng: np.random.Generator, per: int, all_rows: bool
) -> ModelInputs:
    tens = scenario_tensors(batch, seed, draws)
    rows = row_batch(batch, tens, rng, per_scenario=per, all_rows=all_rows)
    return model_inputs(tens, rows, np.tile(batch.samples, draws))


VALIDATION_GROUP = 64


def validation_inputs(
    plan: TrainingPlan, cfg: PhysicsModelConfig, data_dir: Path
) -> list[ModelInputs]:
    """Fixed validation rows, in groups of scenarios so each group's encoder runs once."""
    path = data_dir / Path(plan.validation.path).name
    digest = file_digest(path)
    if plan.validation.digest and digest != plan.validation.digest:
        raise ValueError(f"{path}: digest {digest} is not the plan's {plan.validation.digest}")
    batch = batch_from_pack(path, plan.validation_scenarios)
    rng = np.random.default_rng(VALIDATION_ROW_SEED)
    groups = []
    for a in range(0, len(batch), VALIDATION_GROUP):
        sub = slice_batch(batch, a, min(a + VALIDATION_GROUP, len(batch)))
        groups.append(_inputs(sub, 0, 1, rng, cfg.rows_per_scenario, False))
    return groups


def slice_batch(b: Batch, a: int, z: int) -> Batch:
    from dataclasses import fields, replace

    return replace(b, **{f.name: getattr(b, f.name)[a:z] for f in fields(b)})


def validation_loss(model: Gate1Model, groups: list[ModelInputs], cfg: PhysicsModelConfig) -> float:
    model.set_implicit(False)
    total = 0.0
    rows = 0
    with torch.no_grad():
        for x in groups:
            out = run(model, x)
            lp = gate1_loss(out, x.truth, x.bound_cov, x.okx(), x.oky(), cfg)
            total += float(lp.squared) * lp.rows
            rows += lp.rows
    return total / max(rows, 1)


def _select_rows(x: ModelInputs, sel: torch.Tensor) -> ModelInputs:
    return ModelInputs(
        bearing=x.bearing,
        valid=x.valid,
        ox=x.ox,
        oy=x.oy,
        t=x.t,
        sigma=x.sigma,
        n_rows=x.n_rows,
        source=x.source[sel],
        k=x.k[sel],
        theta_grid=x.theta_grid[sel],
        truth=x.truth[sel],
        bound_cov=x.bound_cov[sel],
    )


@dataclass
class Checkpoint:
    folder: Path

    @property
    def meta_path(self) -> Path:
        return self.folder / "meta.json"

    def exists(self) -> bool:
        return self.meta_path.exists()

    def load_meta(self) -> CheckpointMeta:
        return parse_record(
            CheckpointMeta, json.loads(self.meta_path.read_text()), str(self.meta_path), 1
        )

    def save(
        self,
        model: Gate1Model,
        best: dict[str, torch.Tensor] | None,
        opt: torch.optim.Optimizer,
        meta: CheckpointMeta,
    ) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        save_file(
            {k: v.contiguous() for k, v in model.state_dict().items()},
            str(self.folder / "weights.safetensors.tmp"),
        )
        os.replace(self.folder / "weights.safetensors.tmp", self.folder / "weights.safetensors")
        if best is not None:
            save_file(best, str(self.folder / "best.safetensors.tmp"))
            os.replace(self.folder / "best.safetensors.tmp", self.folder / "best.safetensors")
        torch.save(opt.state_dict(), self.folder / "optim.pt.tmp")
        os.replace(self.folder / "optim.pt.tmp", self.folder / "optim.pt")
        f = AtomicFile(self.meta_path)
        f.write((json.dumps(dump_record(meta), indent=2, sort_keys=True) + "\n").encode())
        f.commit()


def _git_commit() -> str:
    import subprocess

    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def train(
    plan_path: str | Path,
    model_id: str,
    checkpoint: str | Path,
    data_dir: str | Path,
    max_wall_s: float = 1e12,
    epochs: int | None = None,
    scenarios: int | None = None,
    log: Any = print,
) -> CheckpointMeta:
    """Train or resume one model; returns the checkpoint metadata after the last epoch run."""
    t_start = time.time()
    started = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    plan, plan_digest = load_plan(plan_path)
    cfg = model_from_plan(plan, model_id)
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(cfg.threads)
    torch.use_deterministic_algorithms(True)
    n_epoch = scenarios or plan.scenarios_per_epoch
    max_epochs = epochs or cfg.epochs
    ck = Checkpoint(Path(checkpoint))
    torch.manual_seed(cfg.seed)
    model = Gate1Model(cfg)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    best: dict[str, torch.Tensor] | None = None
    if ck.exists():
        meta = ck.load_meta()
        if meta.plan_id != plan.id or meta.model_id != model_id or meta.plan_digest != plan_digest:
            raise ValueError(f"{checkpoint}: checkpoint is for {meta.plan_id}/{meta.model_id}")
        model.load_state_dict(load_file(str(ck.folder / "weights.safetensors")))
        opt.load_state_dict(torch.load(ck.folder / "optim.pt", weights_only=True))
        if (ck.folder / "best.safetensors").exists():
            best = load_file(str(ck.folder / "best.safetensors"))
    else:
        meta = CheckpointMeta(
            model_id=model_id,
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
    val = validation_inputs(plan, cfg, Path(data_dir))
    ranges = plan.ranges.model_dump(mode="json", exclude_none=True)
    while not meta.complete and meta.epoch < max_epochs:
        e = meta.epoch + 1
        last = (meta.epoch_seconds or [0.0])[-1]
        if time.time() - t_start + last > max_wall_s:
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
            x = _inputs(
                batch, cfg.seed * 1_000_003 + e, cfg.noise_draws, rng, cfg.rows_per_scenario, False
            )
            if cfg.shuffle_labels:
                perm = torch.from_numpy(rng.permutation(x.truth.shape[0]))
                x.truth, x.bound_cov = x.truth[perm], x.bound_cov[perm]
            model.set_implicit(True)
            out = run(model, x)
            lp = gate1_loss(out, x.truth, x.bound_cov, x.okx(), x.oky(), cfg)
            opt.zero_grad()
            if lp.rows:
                lp.total.backward()  # type: ignore[no-untyped-call]
                torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
                opt.step()
            losses.append(float(lp.squared))
        v = validation_loss(model, val, cfg)
        secs = time.time() - t0
        meta.epoch = e
        meta.train_losses = [*(meta.train_losses or []), float(np.mean(losses))]
        meta.val_losses = [*(meta.val_losses or []), v]
        meta.epoch_seconds = [*(meta.epoch_seconds or []), secs]
        if v < meta.best_val_loss:
            meta.best_val_loss, meta.best_epoch = v, e
            best = {k: t.detach().clone().contiguous() for k, t in model.state_dict().items()}
        if e - meta.best_epoch >= cfg.patience or e >= cfg.epochs:
            meta.complete = True
        ck.save(model, best, opt, meta)
        log(
            json.dumps(
                {
                    "model": model_id,
                    "epoch": e,
                    "train": meta.train_losses[-1],
                    "val": v,
                    "seconds": round(secs, 1),
                }
            )
        )
    env = run_environment()
    job = JobRecord(
        started=started,
        finished=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        seconds=time.time() - t_start,
        first_epoch=first_epoch,
        last_epoch=meta.epoch,
        cpu_model=str(env.get("cpu_model", "unknown")),
        threads=cfg.threads,
        git_commit=_git_commit(),
    )
    meta.jobs = [*(meta.jobs or []), job]
    ck.save(model, best, opt, meta)
    return meta
