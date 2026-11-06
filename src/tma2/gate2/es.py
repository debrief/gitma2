"""E-s: evidence that shifts C's confirmation threshold, trained over decision tables (spec 007
research R2; task T019).

**Network.** Spec 005's evidence network (``segment.evidence.EvidenceNet``: causal dilated
convolutions, SiLU, zero head) on spec 005's causal features (``scenario_features``). An untrained
E-s emits e = 0 everywhere, so its decisions are C's. C's per-row code is not an input: at the
decision it would encode the decision the evidence is shifting.

**Relaxed acceptance.** For a decision with cost drop Δ and threshold τ′ on candidate rows
[c, min(c + len − 1, a)], the shift is s = clamp(2 Σ e, ± τ/2) and p = σ((Δ − τ′ − s)/T); the
loss is the mean over decision rows of p·e_with + (1 − p)·e_without (``tables.relaxed_loss``,
here vectorised). At inference the decision is hard, through ``segment.confirm``'s evidence
path with C's own nominations. The relaxation holds C's best candidate fixed; at inference the
evidence can also change which start or length is best (one decision at a time, research R2).

**Validation.** The hard loss: the mean over decision rows of e_with where Δ − τ′ − s > 0, else
e_without. At e = 0 it is C's error on those rows.

**Shuffled control.** Each decision row's (e_with, e_without) pair is replaced by a pair drawn
from the whole training set, re-drawn every epoch: the labels no longer belong to the scenario.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from tma2.segment.evidence import EvidenceNet

from .tables import ScenarioTable


@dataclass
class ESExample:
    ordinal: int
    feats: np.ndarray  # [CHANNELS, n]
    start: np.ndarray  # [R] candidate start per decision row
    end: np.ndarray  # [R] last evidence row, min(start + length − 1, a)
    margin: np.ndarray  # [R] Δ − τ′
    e_with: np.ndarray  # [R]
    e_without: np.ndarray  # [R]
    tau: float


def example_of(ordinal: int, feats: np.ndarray, t: ScenarioTable) -> ESExample:
    ds = [t.decisions[r.decision] for r in t.rows]
    return ESExample(
        ordinal=ordinal,
        feats=feats,
        start=np.array([d.start for d in ds], dtype=np.int64),
        end=np.array([min(d.start + d.length - 1, d.row) for d in ds], dtype=np.int64),
        margin=np.array([d.drop - d.threshold for d in ds], dtype=np.float64),
        e_with=np.array([r.e_with for r in t.rows], dtype=np.float64),
        e_without=np.array([r.e_without for r in t.rows], dtype=np.float64),
        tau=t.tau,
    )


def shifts(e: Tensor, x: ESExample) -> Tensor:
    """[R] the threshold shift per decision row from evidence e [n]."""
    ce = torch.cat([e.new_zeros(1), torch.cumsum(e, 0)])
    s = 2.0 * (ce[torch.as_tensor(x.end) + 1] - ce[torch.as_tensor(x.start)])
    return torch.clamp(s, -x.tau / 2.0, x.tau / 2.0)


def terms(
    e: Tensor, x: ESExample, temperature: float, labels: tuple[np.ndarray, np.ndarray] | None
) -> tuple[Tensor, Tensor]:
    """[R] relaxed and hard per-row losses."""
    ew, eo = labels if labels is not None else (x.e_with, x.e_without)
    w, o = torch.as_tensor(ew), torch.as_tensor(eo)
    z = torch.as_tensor(x.margin) - shifts(e, x)
    p = torch.sigmoid(z / temperature)
    return p * w + (1.0 - p) * o, torch.where(z > 0.0, w, o)


def forward(net: EvidenceNet, xs: list[ESExample]) -> list[Tensor]:
    """Evidence per example (padded on the right: causal, so padding never reaches a row)."""
    r = max(x.feats.shape[1] for x in xs)
    a = np.zeros((len(xs), xs[0].feats.shape[0], r))
    for i, x in enumerate(xs):
        a[i, :, : x.feats.shape[1]] = x.feats
    e = net(torch.tensor(a, dtype=torch.float64))
    return [e[i, : x.feats.shape[1]] for i, x in enumerate(xs)]


def evaluate(net: EvidenceNet, xs: list[ESExample], batch: int) -> float:
    """Mean hard loss over decision rows."""
    net.eval()
    tot, n = 0.0, 0
    with torch.no_grad():
        for s in range(0, len(xs), batch):
            part = [x for x in xs[s : s + batch] if x.start.size]
            if not part:
                continue
            for e, x in zip(forward(net, part), part, strict=True):
                _, hard = terms(e, x, 1.0, None)
                tot += float(hard.sum())
                n += int(hard.numel())
    return tot / max(n, 1)


def shuffled_labels(xs: list[ESExample], seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Each decision row's error pair drawn (without replacement) from the whole set."""
    w = np.concatenate([x.e_with for x in xs])
    o = np.concatenate([x.e_without for x in xs])
    perm = np.random.default_rng(seed).permutation(w.size)
    out, at = [], 0
    for x in xs:
        q = perm[at : at + x.e_with.size]
        out.append((w[q], o[q]))
        at += x.e_with.size
    return out


@dataclass
class ESSettings:
    width: int = 32
    kernel: int = 5
    dilations: tuple[int, ...] = (1, 2, 4, 8)
    temperature: float = 1.0
    learning_rate: float = 1e-3
    batch: int = 16
    max_epochs: int = 20
    patience: int = 3
    min_improvement: float = 1e-3
    seed: int = 1
    shuffled: bool = False
    threads: int = 1


def make_net(st: ESSettings, channels: int) -> EvidenceNet:
    return EvidenceNet(
        width=st.width, kernel=st.kernel, dilations=tuple(st.dilations), channels=channels
    ).double()


def train_es(
    st: ESSettings,
    train: list[ESExample],
    val: list[ESExample],
    ck: Path,
    provenance: dict[str, Any],
    epochs: int | None = None,
    max_wall_s: float | None = None,
    log: Any = print,
) -> dict[str, Any]:
    """Train or resume E-s; returns ``meta.json``'s content (as ``train.train_ew``)."""
    from safetensors.torch import load_file, save_file

    from .train import sha256_file

    torch.set_num_threads(st.threads)
    torch.set_default_dtype(torch.float64)
    ck.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(st.seed)
    net = make_net(st, train[0].feats.shape[0])
    opt = torch.optim.Adam(net.parameters(), lr=st.learning_rate)
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
        net.load_state_dict(load_file(str(ck / "weights.safetensors")))
        opt.load_state_dict(torch.load(ck / "optim.pt", weights_only=True))
    if meta["best_val"] is None:
        meta["untrained_val"] = evaluate(net, val, st.batch)
        meta["best_val"] = meta["untrained_val"]
        save_file(net.state_dict(), str(ck / "best.safetensors"))
    t_job = time.time()
    done = 0
    xs_all = [x for x in train if x.start.size]
    while not meta["complete"] and meta["epoch"] < st.max_epochs:
        if epochs is not None and done >= epochs:
            break
        ep = meta["epoch"] + 1
        order = np.random.default_rng(st.seed * 1000 + ep).permutation(len(xs_all))
        labels = shuffled_labels(xs_all, st.seed * 7919 + ep) if st.shuffled else None
        net.train()
        t0 = time.time()
        tot, n = 0.0, 0
        for s in range(0, len(order), st.batch):
            idx = [int(i) for i in order[s : s + st.batch]]
            part = [xs_all[i] for i in idx]
            loss = net.head.weight.sum() * 0.0
            rows = 0
            for e, x, i in zip(forward(net, part), part, idx, strict=True):
                relaxed, _ = terms(e, x, st.temperature, None if labels is None else labels[i])
                loss = loss + relaxed.sum()
                rows += int(relaxed.numel())
            loss = loss / rows
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
            tot += float(loss.detach()) * rows
            n += rows
        v = evaluate(net, val, st.batch)
        meta["epoch"] = ep
        save_file(net.state_dict(), str(ck / "weights.safetensors"))
        torch.save(opt.state_dict(), ck / "optim.pt")
        if v < meta["best_val"] * (1.0 - st.min_improvement):
            meta["best_val"], meta["best_epoch"], meta["stale"] = v, ep, 0
            save_file(net.state_dict(), str(ck / "best.safetensors"))
        else:
            meta["stale"] += 1
        meta["complete"] = meta["stale"] >= st.patience or ep >= st.max_epochs
        meta["weights_sha256"] = sha256_file(ck / "best.safetensors")
        rec = {
            "epoch": ep,
            "train_relaxed": tot / max(n, 1),
            "val_hard": v,
            "seconds": round(time.time() - t0, 1),
            "decision_rows": n,
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
