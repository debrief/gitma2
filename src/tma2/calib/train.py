"""Training the calibration head (spec 008 T022; FR-022, FR-060).

Adam on β-NLL over usable training rows, in seeded mini-batches; early stopping on the
validation tuning rows' score (``loss.score``), with patience. Each epoch saves the current
weights (``last.safetensors``) and the best so far (``best.safetensors``); a shuffled control
permutes the rows' NEES each epoch, and its last epoch is kept as well as its best (panel G4).
Resumes from ``meta.json``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.types.generated.tma import CalibrationHeadConfig

from .data import CalData
from .head import CalHead
from .loss import beta_nll, score


def predict_s(head: CalHead, x: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        out: np.ndarray = head(torch.tensor(x, dtype=torch.float64)).numpy()
    return out


def evaluate(head: CalHead, d: CalData, cap: float) -> float:
    u = d.usable
    s = torch.tensor(predict_s(head, d.x[u]))
    return score(s, torch.tensor(d.q[u]), cap)


def train_head(
    cfg: CalibrationHeadConfig,
    train: CalData,
    val: CalData,
    ck: Path,
    provenance: dict[str, Any],
    epochs: int | None = None,
    max_wall_s: float | None = None,
    log: Any = print,
) -> dict[str, Any]:
    from safetensors.torch import load_file, save_file

    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(1)
    ck.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(cfg.seed)
    head = CalHead(cfg, train.x.shape[1]).double()
    opt = torch.optim.Adam(head.parameters(), lr=cfg.learning_rate)
    meta_p = ck / "meta.json"
    meta: dict[str, Any] = (
        json.loads(meta_p.read_text())
        if meta_p.exists()
        else {"epoch": 0, "best_epoch": 0, "best_val": None, "stale": 0, "complete": False}
    )
    meta.setdefault("jobs", []).append(provenance)
    if meta["epoch"] > 0:
        head.load_state_dict(load_file(str(ck / "last.safetensors")))
        opt.load_state_dict(torch.load(ck / "optim.pt", weights_only=True))
    if meta["best_val"] is None:
        meta["untrained_val"] = evaluate(head, val, cfg.cap)
        meta["best_val"] = meta["untrained_val"]
        save_file(head.state_dict(), str(ck / "best.safetensors"))
    tr = train.select(train.usable)
    x_all = torch.tensor(tr.x)
    q_all = torch.tensor(tr.q)
    t_job, done = time.time(), 0
    while not meta["complete"] and meta["epoch"] < cfg.max_epochs:
        if epochs is not None and done >= epochs:
            break
        e = meta["epoch"] + 1
        rng = np.random.default_rng(cfg.seed * 1000 + e)
        q_e = q_all[torch.tensor(rng.permutation(len(tr)))] if cfg.shuffled else q_all
        order = rng.permutation(len(tr))
        t0, tot = time.time(), 0.0
        for s0 in range(0, len(order), cfg.batch_rows):
            idx = torch.tensor(order[s0 : s0 + cfg.batch_rows])
            loss = beta_nll(head(x_all[idx]), q_e[idx], cfg.beta, cfg.cap)
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
            tot += float(loss.detach()) * len(idx)
        v = evaluate(head, val, cfg.cap)
        meta["epoch"] = e
        save_file(head.state_dict(), str(ck / "last.safetensors"))
        torch.save(opt.state_dict(), ck / "optim.pt")
        if v < meta["best_val"] - cfg.min_improvement * abs(meta["best_val"]):
            meta["best_val"], meta["best_epoch"], meta["stale"] = v, e, 0
            save_file(head.state_dict(), str(ck / "best.safetensors"))
        else:
            meta["stale"] += 1
        meta["last_val"] = v
        meta["complete"] = meta["stale"] >= cfg.patience or e >= cfg.max_epochs
        rec = {
            "epoch": e,
            "train": tot / max(len(tr), 1),
            "val": v,
            "seconds": round(time.time() - t0, 1),
        }
        log(json.dumps(rec))
        meta.setdefault("log", []).append(rec)
        meta_p.write_text(json.dumps(meta, indent=2) + "\n")
        done += 1
        if max_wall_s is not None and time.time() - t_job > max_wall_s:
            break
    from tma2.segment.gate import sha256_file

    meta["weights_sha256"] = sha256_file(ck / "best.safetensors")
    meta["last_weights_sha256"] = sha256_file(ck / "last.safetensors")
    meta_p.write_text(json.dumps(meta, indent=2) + "\n")
    return meta
