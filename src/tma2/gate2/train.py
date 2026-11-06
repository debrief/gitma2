"""E-w's training data and training (spec 007 T015; research R4).

**Examples.** One per scored prefix (σ = 1° G5 rows): the scenario's bearing arrays, C's
hand-over inputs at the prefix (``gate2.inputs``), C's code channel, the truth state at the row,
the known-manoeuvres Cramér–Rao covariance at the row and the valid-bearing count. Built once per
shard on CI (``tma2-g2train tables``) from C's segmentation file, saved as npz.

**Training.** Adam on ``gate2.loss.e_loss`` over batches of prefixes, in a seeded order; the
physics layer differentiated implicitly. After every epoch: the robust validation loss (the
trimmed mean of the capped per-prefix terms, ``trimmed_mean``), weights, Adam state, the best
weights and ``meta.json`` (weights bound by SHA-256, commit, dirty flag, CPU model), so a chained
job resumes. Early stopping on the robust loss (patience, relative improvement).

**Shuffled control.** Each prefix's target is replaced by another prefix's, moved to this
prefix's ownship position (relative position and velocity kept), with a seeded permutation:
what the control learns cannot depend on the bearings' relation to the truth.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.physics.layer import PhysicsInputs
from tma2.references.classical import bearing_data_from_arrays
from tma2.types.generated.tma import PhysicsModelConfig

from .inputs import code_channel, prefix_inputs
from .loss import e_loss, trimmed_mean
from .model import EWeights

ARRAYS = ("t", "ox", "oy", "z", "valid", "cp", "sw", "lw", "sk", "code")


@dataclass
class Prefix:
    ordinal: int
    k: int
    sigma: float
    t: np.ndarray
    ox: np.ndarray
    oy: np.ndarray
    z: np.ndarray
    valid: np.ndarray
    cp: np.ndarray
    sw: np.ndarray
    lw: np.ndarray
    sk: np.ndarray
    code: np.ndarray
    theta0: np.ndarray  # [4]
    truth: np.ndarray  # [4] x, y, vx, vy at k
    bound_cov: np.ndarray  # [4, 4]
    n_valid: int


def build_prefixes(
    pack: str | Path,
    segs: dict[tuple[int, int], list[Any]],
    start: int,
    count: int,
    mode: str,
    open_handover: str | None,
) -> list[Prefix]:
    """Examples for σ = 1° ordinals start … start + count − 1 with a segmentation record."""
    from tma2.references.crb import crb_rows
    from tma2.segment.score import g5_rows, iter_selected

    out: list[Prefix] = []
    for j, m, own, tgt, obs in iter_selected(pack, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = [k for k in g5_rows(m, d.n) if (j, k) in segs]
        if not ks:
            continue
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
        for k, c in zip(ks, crb, strict=True):
            ivs = segs[(j, k)]
            inp = prefix_inputs(d, k, ivs, mode, open_handover)
            if inp is None or c.state_cov is None or c.singular:
                continue
            course, speed = tg[k, 3], tg[k, 4]
            out.append(
                Prefix(
                    ordinal=j,
                    k=k,
                    sigma=d.sigma,
                    t=d.t,
                    ox=d.ox,
                    oy=d.oy,
                    z=d.z,
                    valid=d.valid.astype(np.float64),
                    cp=inp.changepoint,
                    sw=inp.speed_weight,
                    lw=inp.log_weight,
                    sk=inp.speed_skip if inp.speed_skip is not None else np.zeros(d.n),
                    code=code_channel(ivs, k, d.n),
                    theta0=inp.theta0,
                    truth=np.array(
                        [tg[k, 1], tg[k, 2], speed * math.sin(course), speed * math.cos(course)]
                    ),
                    bound_cov=np.asarray(c.state_cov, dtype=np.float64),
                    n_valid=int(d.valid[: k + 1].sum()),
                )
            )
    return out


def save_prefixes(path: str | Path, xs: list[Prefix], header: dict[str, Any]) -> None:
    arrays: dict[str, Any] = {"header": np.array(json.dumps(header, sort_keys=True))}
    for q, x in enumerate(xs):
        arrays[f"{q}/meta"] = np.array([x.ordinal, x.k, x.n_valid], dtype=np.int64)
        arrays[f"{q}/sigma"] = np.array(x.sigma)
        for a in ARRAYS:
            arrays[f"{q}/{a}"] = getattr(x, a)
        arrays[f"{q}/theta0"] = x.theta0
        arrays[f"{q}/truth"] = x.truth
        arrays[f"{q}/bound_cov"] = x.bound_cov
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def load_prefixes(path: str | Path) -> tuple[dict[str, Any], list[Prefix]]:
    with np.load(path, allow_pickle=False) as z:
        header: dict[str, Any] = json.loads(str(z["header"]))
        n = len({k.split("/")[0] for k in z.files if "/" in k})
        xs = []
        for q in range(n):
            o, k, nv = (int(v) for v in z[f"{q}/meta"])
            xs.append(
                Prefix(
                    ordinal=o,
                    k=k,
                    sigma=float(z[f"{q}/sigma"]),
                    **{a: z[f"{q}/{a}"] for a in ARRAYS},
                    theta0=z[f"{q}/theta0"],
                    truth=z[f"{q}/truth"],
                    bound_cov=z[f"{q}/bound_cov"],
                    n_valid=nv,
                )
            )
    return header, xs


@dataclass
class Batch:
    x: PhysicsInputs
    code: torch.Tensor
    truth: torch.Tensor
    bound_cov: torch.Tensor
    okx: torch.Tensor
    oky: torch.Tensor
    n_valid: torch.Tensor


def batch_of(xs: list[Prefix], truth: np.ndarray | None = None) -> Batch:
    """Padded double tensors for a list of prefixes (``truth`` overrides the targets)."""
    r = max(x.t.size for x in xs)

    def pad(a: np.ndarray) -> np.ndarray:
        return np.pad(np.asarray(a, dtype=np.float64), (0, r - a.size))

    def t(a: Any) -> torch.Tensor:
        return torch.tensor(np.asarray(a, dtype=np.float64), dtype=torch.float64)

    stack = {a: t(np.stack([pad(getattr(x, a)) for x in xs])) for a in ARRAYS}
    k = torch.tensor([x.k for x in xs], dtype=torch.int64)
    rows = torch.arange(len(xs))
    pin = PhysicsInputs(
        bearing=stack["z"],
        valid=stack["valid"],
        own=torch.stack([stack["ox"], stack["oy"]], dim=2),
        t=stack["t"],
        sigma=t([x.sigma for x in xs]),
        k=k,
        changepoint=stack["cp"],
        speed_weight=stack["sw"],
        log_weight=stack["lw"],
        theta0=t(np.stack([x.theta0 for x in xs])),
        speed_skip=stack["sk"],
    )
    tr = truth if truth is not None else np.stack([x.truth for x in xs])
    return Batch(
        pin,
        stack["code"],
        t(tr),
        t(np.stack([x.bound_cov for x in xs])),
        stack["ox"][rows, k],
        stack["oy"][rows, k],
        torch.tensor([x.n_valid for x in xs], dtype=torch.int64),
    )


def shuffled_truth(xs: list[Prefix], seed: int) -> np.ndarray:
    """Each prefix's target taken from another prefix, at the same position relative to its own
    ownship at k (the shuffled-label control)."""
    perm = np.random.default_rng(seed).permutation(len(xs))
    out = np.empty((len(xs), 4))
    for i, j in enumerate(perm):
        a, b = xs[i], xs[int(j)]
        rel = b.truth[:2] - np.array([b.ox[b.k], b.oy[b.k]])
        out[i, :2] = np.array([a.ox[a.k], a.oy[a.k]]) + rel
        out[i, 2:] = b.truth[2:]
    return out


@dataclass
class TrainSettings:
    learning_rate: float = 1e-3
    batch: int = 32
    max_epochs: int = 20
    patience: int = 3
    min_improvement: float = 1e-3
    trim: float = 0.1
    cap: float = 100.0
    init_weight: float = 0.1
    seed: int = 1
    shuffled: bool = False
    threads: int = 1


def evaluate(model: EWeights, xs: list[Prefix], batch: int, cap: float) -> float:
    """The robust validation loss: trimmed mean of the capped per-prefix terms."""
    model.eval()
    model.set_implicit(False)
    terms = []
    with torch.no_grad():
        for s in range(0, len(xs), batch):
            b = batch_of(xs[s : s + batch])
            out = model(b.x, b.code)
            loss = e_loss(out, b.truth, b.bound_cov, b.okx, b.oky, b.n_valid, cap=cap)
            terms.append(loss.per_prefix)
    model.train()
    return trimmed_mean(torch.cat(terms)) if terms else math.nan


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def train_ew(
    cfg: PhysicsModelConfig,
    st: TrainSettings,
    train: list[Prefix],
    val: list[Prefix],
    ck: Path,
    provenance: dict[str, Any],
    epochs: int | None = None,
    max_wall_s: float | None = None,
    log: Any = print,
) -> dict[str, Any]:
    """Train or resume E-w; returns ``meta.json``'s content."""
    from safetensors.torch import load_file, save_file

    torch.set_num_threads(st.threads)
    torch.set_default_dtype(torch.float64)
    ck.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(st.seed)
    model = EWeights(cfg).double()
    opt = torch.optim.Adam(model.parameters(), lr=st.learning_rate)
    meta_p = ck / "meta.json"
    meta: dict[str, Any] = (
        json.loads(meta_p.read_text())
        if meta_p.exists()
        else {
            "epoch": 0,
            "best_epoch": 0,
            "best_val": None,
            "stale": 0,
            "complete": False,
            "jobs": [],
        }
    )
    if meta["epoch"] > 0:
        model.load_state_dict(load_file(str(ck / "weights.safetensors")))
        opt.load_state_dict(torch.load(ck / "optim.pt", weights_only=True))
    if meta["best_val"] is None:
        meta["untrained_val"] = evaluate(model, val, st.batch, st.cap)
        meta["best_val"] = meta["untrained_val"]
        save_file(model.state_dict(), str(ck / "best.safetensors"))
    t_job = time.time()
    done = 0
    while not meta["complete"] and meta["epoch"] < st.max_epochs:
        if epochs is not None and done >= epochs:
            break
        e = meta["epoch"] + 1
        order = np.random.default_rng(st.seed * 1000 + e).permutation(len(train))
        truth_all = shuffled_truth(train, st.seed * 7919 + e) if st.shuffled else None
        model.set_implicit(True)
        t0 = time.time()
        tot, n, failed = 0.0, 0, 0
        for s in range(0, len(order), st.batch):
            idx = order[s : s + st.batch]
            xs = [train[int(i)] for i in idx]
            b = batch_of(xs, None if truth_all is None else truth_all[idx])
            out = model(b.x, b.code)
            loss = e_loss(
                out, b.truth, b.bound_cov, b.okx, b.oky, b.n_valid, st.cap, st.init_weight
            )
            failed += loss.excluded_failed_fits
            if int(loss.kept.sum()) == 0:
                continue
            opt.zero_grad()
            loss.total.backward()  # type: ignore[no-untyped-call]
            opt.step()
            tot += float(loss.total) * int(loss.kept.sum())
            n += int(loss.kept.sum())
        v = evaluate(model, val, st.batch, st.cap)
        meta["epoch"] = e
        save_file(model.state_dict(), str(ck / "weights.safetensors"))
        torch.save(opt.state_dict(), ck / "optim.pt")
        improved = v < meta["best_val"] * (1.0 - st.min_improvement)
        if improved:
            meta["best_val"], meta["best_epoch"], meta["stale"] = v, e, 0
            save_file(model.state_dict(), str(ck / "best.safetensors"))
        else:
            meta["stale"] += 1
        meta["complete"] = meta["stale"] >= st.patience or e >= st.max_epochs
        meta["weights_sha256"] = sha256_file(ck / "best.safetensors")
        rec = {
            "epoch": e,
            "train": tot / max(n, 1),
            "val_trimmed": v,
            "excluded_failed_fits": failed,
            "seconds": round(time.time() - t0, 1),
            "prefixes": n,
        }
        log(json.dumps(rec))
        meta.setdefault("log", []).append(rec)
        meta_p.write_text(json.dumps(meta, indent=2) + "\n")
        done += 1
        if max_wall_s is not None and time.time() - t_job + (time.time() - t0) > max_wall_s:
            break
    meta["jobs"].append({**provenance, "epochs_run": done, "at_epoch": meta["epoch"]})
    meta_p.write_text(json.dumps(meta, indent=2) + "\n")
    return meta
