"""Training L (spec 005 FR-042, FR-044, research R6; tasks T032–T033).

**Examples.** One per scenario: its scored prefixes (G5 rows), the search's cost table on one
grid anchored at the first of them (``search.anchored_grid``: every prefix's lattice is a
leading block of it), the bearings' validity, the truth codes of each prefix, and the causal
features (``evidence.scenario_features``). The cost tables are the expensive part (seconds per
scenario), so they are made once, on CI shards (``tma2-segtrain tables``), and the noise is the
one generated draw (the plan records this).

**Loss.** Per prefix, the semi-Markov negative log-likelihood of the truth segmentation on the
search's lattice (``crf.Lattice``) plus 0.1 × the auxiliary per-bearing term; the mean over the
batch's prefixes. Evidence comes from one causal forward pass per scenario, so every prefix of a
scenario shares it (FR-002).

**Shuffled control** (constitution IV): each scenario's truth codes are replaced by another
scenario's (a seeded permutation), cut or padded with unknown to its length. Evidence trained on
those labels has nothing true to learn, so it must not beat C.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors.torch import load_file

from tma2.data.f32pack import iter_pack_raw
from tma2.eval.experiment import run_environment
from tma2.models.train import Checkpoint, git_state, improved
from tma2.references.classical import bearing_data_from_arrays
from tma2.types.generated.tma import CheckpointMeta, JobRecord, SegmentParameters

from . import UNKNOWN
from .crf import Lattice, aux_loss
from .evidence import CHANNELS, EvidenceNet, scenario_features
from .score import g5_rows, sigma1
from .search import anchored_grid, cost_table
from .truth import truth_codes

AUX_WEIGHT = 0.1
GRAD_CLIP = 10.0


@dataclass
class Example:
    """One scenario's training data (see the module docstring)."""

    key: int  # position in its file (all scenarios) or σ = 1° ordinal
    ks: list[int]
    grid: np.ndarray  # int64 [g]
    cost: np.ndarray  # float32 [g, g]
    valid: np.ndarray  # bool [n]
    codes: list[np.ndarray]  # int8 [k + 1] per prefix, target truth codes
    features: np.ndarray  # float32 [CHANNELS, n]


def iter_scenarios(
    path: str | Path, start: int, count: int, sigma1_only: bool
) -> Iterator[tuple[int, dict[str, Any], np.ndarray, np.ndarray, np.ndarray]]:
    """(key, meta, own, tgt, obs): file positions start … start + count − 1, or with
    ``sigma1_only`` σ = 1° ordinals (``score.iter_selected``'s numbering)."""
    j = 0
    for i, meta, own, tgt, obs in iter_pack_raw(path):
        if sigma1_only and not sigma1(meta):
            continue
        key = j if sigma1_only else i
        j += 1
        if key >= start + count:
            return
        if key >= start:
            yield key, meta, own, tgt, obs


def make_example(
    key: int, meta: dict[str, Any], own: np.ndarray, obs: np.ndarray, p: SegmentParameters
) -> Example | None:
    d = bearing_data_from_arrays(meta, own, obs)
    ks = g5_rows(meta, d.n)
    if not ks:
        return None
    grid = anchored_grid(max(ks), ks[0], p.search_step_rows)
    cost = cost_table(d, grid, p.l_min_rows).astype(np.float32)
    codes = [truth_codes(meta, "target", p.l_min_rows, p.t_min_rows, n=k + 1) for k in ks]
    feats = scenario_features(d, own, p).astype(np.float32)
    return Example(key, ks, grid, cost, d.valid.astype(bool), codes, feats)


def save_examples(path: str | Path, examples: list[Example], header: dict[str, Any]) -> None:
    arrays: dict[str, Any] = {"header": np.array(json.dumps(header, sort_keys=True))}
    for q, ex in enumerate(examples):
        arrays[f"{q}/key"] = np.array(ex.key, dtype=np.int64)
        arrays[f"{q}/ks"] = np.asarray(ex.ks, dtype=np.int64)
        arrays[f"{q}/grid"] = ex.grid
        arrays[f"{q}/cost"] = ex.cost
        arrays[f"{q}/valid"] = ex.valid
        arrays[f"{q}/features"] = ex.features
        for r, c in enumerate(ex.codes):
            arrays[f"{q}/codes{r}"] = c
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def load_examples(path: str | Path) -> tuple[dict[str, Any], list[Example]]:
    with np.load(path, allow_pickle=False) as z:
        header: dict[str, Any] = json.loads(str(z["header"]))
        n = len({k.split("/")[0] for k in z.files if "/" in k})
        out = []
        for q in range(n):
            ks = [int(x) for x in z[f"{q}/ks"]]
            out.append(
                Example(
                    int(z[f"{q}/key"]),
                    ks,
                    z[f"{q}/grid"],
                    z[f"{q}/cost"],
                    z[f"{q}/valid"],
                    [z[f"{q}/codes{r}"] for r in range(len(ks))],
                    z[f"{q}/features"],
                )
            )
    return header, out


def shuffled_codes(examples: list[Example], seed: int) -> list[list[np.ndarray]]:
    """The shuffled control's labels: scenario i takes scenario π(i)'s last prefix's codes, cut or
    padded with unknown to each of its own prefixes."""
    perm = np.random.default_rng([seed, 317]).permutation(len(examples))
    out = []
    for ex, j in zip(examples, perm, strict=True):
        src = examples[int(j)].codes[-1]
        cs = []
        for k in ex.ks:
            c = np.full(k + 1, UNKNOWN, dtype=np.int8)
            m = min(k + 1, src.shape[0])
            c[:m] = src[:m]
            cs.append(c)
        out.append(cs)
    return out


def prefix_lattice(ex: Example, k: int, p: SegmentParameters) -> Lattice:
    m = int(np.searchsorted(ex.grid, k, side="right"))
    if int(ex.grid[m - 1]) != k:
        raise ValueError(f"row {k} is not on the example's grid")
    cost = ex.cost[:m, :m].astype(np.float64)
    return Lattice(
        ex.grid[:m],
        cost,
        ex.valid,
        p.search_penalty,
        p.t_min_rows,
        max(p.t_lengths_rows),
    )


def batch_loss(
    net: EvidenceNet,
    examples: list[Example],
    codes: list[list[np.ndarray]],
    p: SegmentParameters,
    aux_weight: float = AUX_WEIGHT,
) -> tuple[torch.Tensor, int]:
    """Mean per-prefix loss over the batch (CRF NLL + aux_weight × auxiliary) and the prefix
    count."""
    r = max(ex.features.shape[1] for ex in examples)
    x = np.zeros((len(examples), CHANNELS, r))
    for i, ex in enumerate(examples):
        x[i, :, : ex.features.shape[1]] = ex.features
    dtype = next(net.parameters()).dtype
    e = net(torch.tensor(x, dtype=dtype))
    terms = []
    for i, ex in enumerate(examples):
        for k, c in zip(ex.ks, codes[i], strict=True):
            lat = prefix_lattice(ex, k, p)
            ek = e[i, : k + 1]
            nll = lat.nll(ek, c)
            terms.append(nll + aux_weight * aux_loss(ek, c, k + 1))
    return torch.stack(terms).mean(), len(terms)


def evaluate(
    net: EvidenceNet, examples: list[Example], p: SegmentParameters, batch: int = 16
) -> float:
    """Mean per-prefix loss on true labels (validation; early stopping)."""
    tot, n = 0.0, 0
    with torch.no_grad():
        for a in range(0, len(examples), batch):
            exs = examples[a : a + batch]
            loss, m = batch_loss(net, exs, [ex.codes for ex in exs], p)
            tot += float(loss) * m
            n += m
    return tot / max(n, 1)


@dataclass
class TrainConfig:
    model_id: str
    plan_id: str
    plan_digest: str
    seed: int
    shuffled: bool
    learning_rate: float
    batch_scenarios: int
    max_epochs: int
    patience: int
    min_improvement: float
    width: int
    kernel: int
    dilations: tuple[int, ...]
    threads: int = 1  # the recursion is many small ops: more threads only contend


def config_from_plan(plan: dict[str, Any], digest: str, model_id: str) -> TrainConfig:
    """``model_id`` is ``segL-s<seed>`` or ``segL-shuffled``."""
    tr, net = plan["training"], plan["evidence_network"]
    if model_id == "segL-shuffled":
        seed, shuffled = int(tr["shuffled_control_seed"]), True
    elif model_id.startswith("segL-s") and int(model_id[6:]) in tr["seeds"]:
        seed, shuffled = int(model_id[6:]), False
    else:
        raise ValueError(f"{model_id}: not a model of plan {plan['id']}")
    es = tr["early_stopping"]
    return TrainConfig(
        model_id=model_id,
        plan_id=str(plan["id"]),
        plan_digest=digest,
        seed=seed,
        shuffled=shuffled,
        learning_rate=float(tr["learning_rate"]),
        batch_scenarios=int(tr["batch_scenarios"]),
        max_epochs=int(tr["max_epochs"]),
        patience=int(es["patience_epochs"]),
        min_improvement=float(es["relative_min_improvement"]),
        width=int(net["width"]),
        kernel=int(net["kernel"]),
        dilations=tuple(int(x) for x in net["dilations"]),
    )


def make_net(cfg: TrainConfig) -> EvidenceNet:
    torch.manual_seed(cfg.seed)
    return EvidenceNet(width=cfg.width, kernel=cfg.kernel, dilations=cfg.dilations).double()


def train_l(
    cfg: TrainConfig,
    p: SegmentParameters,
    train: list[Example],
    val: list[Example],
    checkpoint: str | Path,
    max_wall_s: float = 1e12,
    epochs: int | None = None,
    log: Callable[[str], None] = print,
) -> CheckpointMeta:
    """Train or resume one L model; returns the checkpoint metadata after the last epoch run."""
    t_start = time.time()
    started = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(cfg.threads)
    torch.use_deterministic_algorithms(True)
    max_epochs = min(epochs or cfg.max_epochs, cfg.max_epochs)
    ck = Checkpoint(Path(checkpoint))
    net = make_net(cfg)
    opt = torch.optim.Adam(net.parameters(), lr=cfg.learning_rate)
    best: dict[str, torch.Tensor] | None = None
    if ck.exists():
        meta = ck.load_meta()
        if (meta.plan_id, meta.model_id, meta.plan_digest) != (
            cfg.plan_id,
            cfg.model_id,
            cfg.plan_digest,
        ):
            raise ValueError(f"{checkpoint}: checkpoint is for {meta.plan_id}/{meta.model_id}")
        net.load_state_dict(load_file(str(ck.folder / "weights.safetensors")))
        opt.load_state_dict(torch.load(ck.folder / "optim.pt", weights_only=True))
        if (ck.folder / "best.safetensors").exists():
            best = load_file(str(ck.folder / "best.safetensors"))
    else:
        meta = CheckpointMeta(
            model_id=cfg.model_id,
            plan_id=cfg.plan_id,
            plan_digest=cfg.plan_digest,
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
    labels = shuffled_codes(train, cfg.seed) if cfg.shuffled else [ex.codes for ex in train]
    while not meta.complete and meta.epoch < max_epochs:
        e = meta.epoch + 1
        last = (meta.epoch_seconds or [0.0])[-1]
        if e > first_epoch and time.time() - t_start + last > max_wall_s:
            log(f"wall-clock cap: stopping before epoch {e}")
            break
        t0 = time.time()
        net.train()
        order = np.random.default_rng([cfg.seed, e]).permutation(len(train))
        losses = []
        for a in range(0, len(order), cfg.batch_scenarios):
            idx = [int(i) for i in order[a : a + cfg.batch_scenarios]]
            loss, _m = batch_loss(net, [train[i] for i in idx], [labels[i] for i in idx], p)
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(net.parameters(), GRAD_CLIP)
            opt.step()
            losses.append(float(loss.detach()))
        train_s = time.time() - t0
        net.eval()
        v = evaluate(net, val, p)
        secs = time.time() - t0
        meta.epoch = e
        meta.train_losses = [*(meta.train_losses or []), float(np.mean(losses))]
        meta.val_losses = [*(meta.val_losses or []), v]
        meta.epoch_seconds = [*(meta.epoch_seconds or []), secs]
        if improved(v, meta.best_val_loss, cfg.min_improvement):
            meta.best_val_loss, meta.best_epoch = v, e
            best = {k: t.detach().clone().contiguous() for k, t in net.state_dict().items()}
        if e - meta.best_epoch >= cfg.patience or e >= cfg.max_epochs:
            meta.complete = True
        ck.save(net, best, opt, meta)
        log(
            json.dumps(
                {
                    "model": cfg.model_id,
                    "epoch": e,
                    "train": meta.train_losses[-1],
                    "val": v,
                    "seconds": round(secs, 1),
                    "train_seconds": round(train_s, 1),
                    "scenarios": len(train),
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
    ck.save(net, best, opt, meta)
    return meta
