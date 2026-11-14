"""Training loop for the regressor (spec 012 research R3): on-the-fly data, a time limit,
checkpoints and resume. One process trains one segment; ``run.json`` accumulates segments.

With ``data: "periods"`` (spec 016 research R7, R9) the stream is ``period_data``'s, the loss is
the state's β-NLL plus ``manoeuvre_weight`` × the manoeuvre logit's cross-entropy over tokens
that exist, and the monitor is a slice of the same stream seed far from the training indices."""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.data.provenance import read_git_provenance

from . import period_data as pdata
from .data import Tensors, batch_at, load_ranges, supervised, validation
from .model import Regressor, RegressorConfig, beta_nll, manoeuvre_bce


def config_digest(cfg: RegressorConfig) -> str:
    return hashlib.sha256(json.dumps(cfg.to_json(), sort_keys=True).encode()).hexdigest()


def lr_at(cfg: RegressorConfig, update: int) -> float:
    if update < cfg.warmup_updates:
        return cfg.learning_rate * (update + 1) / cfg.warmup_updates
    p = (update - cfg.warmup_updates) / max(1, cfg.total_updates - cfg.warmup_updates)
    return cfg.learning_rate * 0.5 * (1.0 + math.cos(math.pi * min(1.0, p)))


def _loss(
    model: Regressor, x: Tensors, offset: int, device: torch.device, amp: bool
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    patch = model.patch
    f = torch.from_numpy(x.f).to(device)
    last = offset + (np.arange(x.f.shape[1] // patch) + 1) * patch - 1
    keep = np.minimum(last, x.f.shape[1] - 1)
    y = torch.from_numpy(x.y[:, keep]).to(device)
    w = torch.from_numpy(supervised(x.mask, patch, offset)).to(device)
    with torch.autocast(device.type, enabled=amp):
        mean, logvar = model(f, offset)
    mean, logvar = mean.float(), logvar.float()
    return beta_nll(mean, logvar, y, w, model.cfg.beta), mean, y, w


def evaluate(model: Regressor, val: Tensors, device: torch.device, amp: bool) -> dict[str, float]:
    """Loss, and the median absolute error of ln range and of velocity (m/s) on supervised
    tokens at least 10 min after the ownship zig."""
    model.eval()
    losses, e_r, e_v = [], [], []
    patch = model.patch
    with torch.no_grad():
        for s in range(0, val.f.shape[0], 128):
            part = Tensors(*(a[s : s + 128] for a in (val.f, val.y, val.mask, val.zig, val.index)))
            loss, mean, y, w = _loss(model, part, 0, device, amp)
            losses.append(float(loss) * part.f.shape[0])
            last = (np.arange(part.f.shape[1] // patch) + 1) * patch - 1
            late = torch.from_numpy((last[None, :] >= part.zig[:, None] + 60).astype(np.float32))
            sel = (w.cpu() * late) > 0
            d = (mean - y).cpu()
            e_r.append(d[..., 0][sel].abs())
            e_v.append((d[..., 1:][sel].pow(2).sum(-1).sqrt()) * 10.0)
    model.train()
    return {
        "loss": sum(losses) / val.f.shape[0],
        "ln_range_abs_median": float(torch.cat(e_r).median()) if e_r else math.nan,
        "velocity_mps_median": float(torch.cat(e_v).median()) if e_v else math.nan,
    }


def period_loss(
    model: Regressor, x: pdata.PeriodTensors, device: torch.device, amp: bool
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    """(loss, parts) on a batch of periods. Tokens start at the period's first row (no folding
    offset: the model reads the whole period); parts: the two loss terms, the predicted mean,
    the target and the tokens that exist."""
    cfg = model.cfg
    y_np, label_np, w_np, _last = pdata.token_targets(x, model.patch)
    f = torch.from_numpy(x.f).to(device)
    mask = torch.from_numpy(x.mask).to(device)
    y, w = torch.from_numpy(y_np).to(device), torch.from_numpy(w_np).to(device)
    with torch.autocast(device.type, enabled=amp):
        if cfg.manoeuvre_head:
            mean, logvar, logit = model.forward_all(f, 0, mask)
        else:
            mean, logvar = model(f, 0, mask)
    mean, logvar = mean.float(), logvar.float()
    state = beta_nll(mean, logvar, y, w, cfg.beta)
    parts = {"state": state, "mean": mean, "y": y, "w": w}
    if not cfg.manoeuvre_head:
        return state, parts
    parts["manoeuvre"] = manoeuvre_bce(logit.float(), torch.from_numpy(label_np).to(device), w)
    return state + cfg.manoeuvre_weight * parts["manoeuvre"], parts


def evaluate_periods(
    model: Regressor, val: pdata.PeriodTensors, device: torch.device, amp: bool
) -> dict[str, float]:
    """Both loss terms and the median absolute error of ln range over the monitor's tokens."""
    model.eval()
    n = val.f.shape[0]
    tot = {"loss": 0.0, "state_loss": 0.0, "manoeuvre_loss": 0.0}
    e_r = []
    with torch.no_grad():
        for s in range(0, n, 128):
            part = pdata.PeriodTensors(*(getattr(val, k)[s : s + 128] for k in pdata.FIELDS))
            loss, parts = period_loss(model, part, device, amp)
            k = part.f.shape[0]
            tot["loss"] += float(loss) * k
            tot["state_loss"] += float(parts["state"]) * k
            tot["manoeuvre_loss"] += float(parts.get("manoeuvre", torch.zeros(()))) * k
            e_r.append((parts["mean"] - parts["y"])[..., 0][parts["w"] > 0].abs().cpu())
    model.train()
    out = {k: v / n for k, v in tot.items()}
    out["ln_range_abs_median"] = float(torch.cat(e_r).median()) if e_r else math.nan
    return out


def train(
    cfg: RegressorConfig,
    out: Path,
    device_name: str = "cpu",
    resume: Path | None = None,
    limit_seconds: int | None = None,
    git_commit: str | None = None,
) -> dict[str, Any]:
    gp = read_git_provenance()  # before any output
    commit = git_commit or gp.commit  # a remote container has no checkout: the caller's commit
    t0 = time.time()
    limit = cfg.limit_seconds if limit_seconds is None else limit_seconds
    device = torch.device(device_name)
    amp = cfg.precision == "amp" and device.type == "cuda"
    torch.manual_seed(cfg.seed)
    model = Regressor(cfg).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    scaler = torch.amp.GradScaler(device.type, enabled=amp)
    update = 0
    record: dict[str, Any] = {
        "config": cfg.to_json(),
        "config_sha256": config_digest(cfg),
        "segments": [],
        "validation": [],
    }
    if resume is not None:
        st = torch.load(resume / "state.pt", map_location=device, weights_only=False)
        if st["config_sha256"] != record["config_sha256"]:
            raise ValueError("resume: the checkpoint was made with another configuration")
        model.load_state_dict(st["model"])
        opt.load_state_dict(st["opt"])
        scaler.load_state_dict(st["scaler"])
        update = int(st["update"])
        record = json.loads((resume / "run.json").read_text())
    periods = cfg.data == "periods"
    if periods:
        mix = pdata.load_mix(cfg.mix)
        monitor = pdata.monitor(cfg, mix)
    else:
        ranges = load_ranges(cfg.ranges)
        held = load_ranges(cfg.held_ranges) if cfg.held_fraction > 0 else None
        val = validation(cfg, ranges)
    out.mkdir(parents=True, exist_ok=True)
    start_update = update
    seg: dict[str, Any] = {"start_update": update, "started": time.time(), "git_commit": commit}
    rng = np.random.default_rng(cfg.seed * 1_000_003 + update)

    def save(stopped: str) -> None:
        from safetensors.torch import save_file

        seg_now = {**seg, "end_update": update, "seconds": time.time() - t0}
        rec = {**record, "segments": [*record["segments"], seg_now]}
        seen = update * cfg.batch_scenarios
        secs = sum(s["seconds"] for s in rec["segments"])
        rec.update(
            updates=update,
            scenarios_seen=seen,
            train_seconds=secs,
            scenarios_per_second=(update - start_update)
            * cfg.batch_scenarios
            / max(time.time() - t0, 1e-9),
            device=device_name,
            gpu=torch.cuda.get_device_name(0) if device.type == "cuda" else None,
            torch=torch.__version__,
            cuda=torch.version.cuda,
            git_dirty=gp.dirty if git_commit is None else False,
            stopped=stopped,
        )
        sd = {k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}
        save_file(sd, str(out / "checkpoint.safetensors"))
        rec["checkpoint_sha256"] = hashlib.sha256(
            (out / "checkpoint.safetensors").read_bytes()
        ).hexdigest()
        torch.save(
            {
                "model": model.state_dict(),
                "opt": opt.state_dict(),
                "scaler": scaler.state_dict(),
                "update": update,
                "config_sha256": record["config_sha256"],
            },
            out / "state.pt",
        )
        (out / "run.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")

    last_save = time.time()
    stopped = "complete"
    model.train()
    while update < cfg.total_updates:
        if time.time() - t0 > limit:
            stopped = "limit"
            break
        for g in opt.param_groups:
            g["lr"] = lr_at(cfg, update)
        if periods:
            loss, _ = period_loss(model, pdata.batch_at(cfg, mix, update), device, amp)
        else:
            x = batch_at(cfg, ranges, update, held)
            offset = int(rng.integers(0, cfg.patch_rows))
            loss, _, _, _ = _loss(model, x, offset, device, amp)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()  # type: ignore[no-untyped-call]
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        update += 1
        if update % cfg.val_every_updates == 0 or update == cfg.total_updates:
            v = (
                evaluate_periods(model, monitor, device, amp)
                if periods
                else evaluate(model, val, device, amp)
            )
            v.update(update=update, seconds=time.time() - t0, train_loss=float(loss.detach()))
            record["validation"].append(v)
            print(json.dumps(v), flush=True)
        if time.time() - last_save > cfg.checkpoint_seconds:
            save("running")
            last_save = time.time()
    save(stopped)
    result: dict[str, Any] = json.loads((out / "run.json").read_text())
    return result
