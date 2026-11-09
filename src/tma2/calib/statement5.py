"""Spec 010: the truncated-form statement (research R2, R3, R6).

Per row, four quantities in the same form for every statement:

* a: the course spread scale. X = min(Xmax, 1.96 · a · sd_c), κ = 1 / (a · sd_c)².
* logit P: the arc probability (the truncated density puts exactly P inside ±X).
* c_r, c_s: range and speed 95% half-widths are c · sd.

The loss is the negative truncated log score of the course plus the two 95% interval scores,
each divided by its mean under the starting statement.

Three statements produce these:

* **Temperature** (R6.1): one value of each quantity per cell (G5 minute × open at k), stated on
  sd^β with β per quantity from the plan's grid, fitted on tuning rows.
* **Classical rule** (R6.2):
  - log a, log c_r and log c_s are quadratics in the three standardised log sds (10 terms each);
  - logit P is the same quadratic plus linear terms in the proxy design (R1) and the minute.

  It is fitted on the training stream.
* **Head** (R6, R3): the classical rule plus a bounded residual, bound · tanh(MLP), on E-w's
  encoder state, the log sds, C's code and the proxy design. Its output layer starts at zero, so
  the untrained head equals the classical rule.
  - `shuffle: encoder` permutes the encoder-state columns across rows each epoch (the learning
    control).
  - `shuffle: errors` permutes the errors.

A two-parameter Platt map on logit P, fitted on tuning rows, finishes every statement.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from . import statement as st
from .data import CalData

Z95 = st.Z95


@dataclass
class Inputs:
    """Per-row inputs: log sds [N, 3], the proxy design [N, D] (NaN-free), E-w's encoder state
    [N, H] and C's code [N, 1], the exact errors [N, 3] and sds [N, 3], and the fit mask."""

    log_sd: np.ndarray
    design: np.ndarray
    h: np.ndarray
    code: np.ndarray
    err: np.ndarray
    sd: np.ndarray
    ok: np.ndarray
    minute: np.ndarray
    open: np.ndarray

    def select(self, m: np.ndarray) -> Inputs:
        return Inputs(*(getattr(self, f)[m] for f in self.__dataclass_fields__))


def inputs(d: CalData, proxy_feats: dict[str, np.ndarray]) -> Inputs:
    from .proxy import design

    assert d.sd is not None and d.err is not None
    log_sd = np.log(d.sd)
    des = design(proxy_feats, d.open, np.nan_to_num(log_sd), d.minute)
    ok = (
        d.scalable
        & np.isfinite(d.err).all(axis=1)
        & np.isfinite(d.sd).all(axis=1)
        & np.isfinite(des).all(axis=1)
    )
    hdim = d.x.shape[1] - 4  # x = [h, log sds (3), code_k]
    return Inputs(
        log_sd=np.nan_to_num(log_sd),
        design=np.nan_to_num(des),
        h=d.x[:, :hdim],
        code=d.x[:, -1:],
        err=d.err,
        sd=d.sd,
        ok=ok,
        minute=d.minute,
        open=d.open,
    )


def quad(z: np.ndarray) -> np.ndarray:
    """[N, 10]: 1, z_i, z_i z_j (i ≤ j) for three standardised log sds."""
    cols = [np.ones(len(z))] + [z[:, i] for i in range(3)]
    cols += [z[:, i] * z[:, j] for i in range(3) for j in range(i, 3)]
    return np.stack(cols, axis=1)


# ---------------------------------------------------------------- losses


def loss_terms(
    err: Tensor, sd: Tensor, a: Tensor, logit_p: Tensor, c_r: Tensor, c_s: Tensor, xmax: float
) -> tuple[Tensor, Tensor, Tensor]:
    x = torch.clamp(Z95 * a * sd[:, 1], max=xmax)
    kappa = torch.clamp(1.0 / (a * sd[:, 1]) ** 2, max=1e8)
    nll = -st.truncated_log_score_t(err[:, 1], x, torch.sigmoid(logit_p), kappa)
    is_r = st.interval_score_t(err[:, 0].abs(), c_r * sd[:, 0])
    is_s = st.interval_score_t(err[:, 2].abs(), c_s * sd[:, 2])
    return nll, is_r, is_s


def total(terms: tuple[Tensor, Tensor, Tensor], scale: dict[str, float]) -> Tensor:
    nll, is_r, is_s = terms
    return (nll / scale["course"] + is_r / scale["range"] + is_s / scale["speed"]).mean()


@dataclass
class Statement5:
    a: np.ndarray
    logit_p: np.ndarray
    c_r: np.ndarray
    c_s: np.ndarray

    def stated(self, sd: np.ndarray, xmax: float, platt: tuple[float, float] | None) -> dict:  # type: ignore[type-arg]
        x = np.minimum(xmax, Z95 * self.a * sd[:, 1])
        p = 1.0 / (1.0 + np.exp(-self.logit_p))
        if platt is not None:
            p = st.platt_apply(p, platt)
        return {
            "x": x,
            "p": p,
            "kappa": np.minimum(1.0 / (self.a * sd[:, 1]) ** 2, 1e8),
            "q_r": self.c_r * sd[:, 0],
            "q_s": self.c_s * sd[:, 2],
        }


def scores(s5: Statement5, inp: Inputs, xmax: float) -> dict[str, float]:
    """Mean course NLL and interval scores of a statement on the fit rows (its loss scale)."""
    m = inp.ok
    with torch.no_grad():
        t = loss_terms(
            torch.tensor(inp.err[m]),
            torch.tensor(inp.sd[m]),
            torch.tensor(s5.a[m]),
            torch.tensor(s5.logit_p[m]),
            torch.tensor(s5.c_r[m]),
            torch.tensor(s5.c_s[m]),
            xmax,
        )
    return {
        "course": float(abs(t[0].mean())) + 1e-9,
        "range": float(t[1].mean()),
        "speed": float(t[2].mean()),
    }


# ---------------------------------------------------------------- temperature (R6.1)


def _fit_course_cell(e: np.ndarray, s: np.ndarray, xmax: float) -> tuple[float, float]:
    """(a, logit P) maximising the truncated log score on a cell's rows (s: sd^β)."""
    et, st_ = torch.tensor(e), torch.tensor(s)
    la = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    lp = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([la, lp], max_iter=200, line_search_fn="strong_wolfe")

    def closure() -> Tensor:
        opt.zero_grad()
        a = torch.exp(la)
        x = torch.clamp(Z95 * a * st_, max=xmax)
        kap = torch.clamp(1.0 / (a * st_) ** 2, max=1e8)
        loss = -st.truncated_log_score_t(et, x, torch.sigmoid(lp), kap).mean()
        loss.backward()  # type: ignore[no-untyped-call]
        return loss

    opt.step(closure)  # type: ignore[no-untyped-call]
    return float(torch.exp(la).detach()), float(lp.detach())


def cells(inp: Inputs, keys: list[str]) -> np.ndarray:
    cols = {"minute": inp.minute, "open": inp.open}
    return np.array(["|".join(f"{k}={cols[k][i]}" for k in keys) for i in range(len(inp.ok))])


def fit_temperature5(
    inp: Inputs, keys: list[str], beta_grid: list[float], xmax: float, min_rows: int = 20
) -> dict[str, Any]:
    lab, m = cells(inp, keys), inp.ok
    grid = [float(b) for b in beta_grid] or [1.0]

    def fit(beta: np.ndarray) -> dict[str, dict[str, float]]:
        s = inp.sd ** beta[None, :]
        out: dict[str, dict[str, float]] = {}
        for c in sorted(set(lab.tolist())):
            i = m & (lab == c)
            if i.sum() < min_rows:
                i = m
            a, lp = _fit_course_cell(inp.err[i, 1], s[i, 1], xmax)
            out[c] = {
                "a": a,
                "logit_p": lp,
                "c_r": float(np.quantile(np.abs(inp.err[i, 0]) / s[i, 0], 0.95)),
                "c_s": float(np.quantile(np.abs(inp.err[i, 2]) / s[i, 2], 0.95)),
            }
        return out

    trials = []
    for b in grid:
        t = {"cells": fit(np.full(3, b)), "beta": [b] * 3, "slices": keys}
        trials.append(_component_means(apply_temperature5(t, inp), inp, xmax))
    sc = np.array(trials)  # [grid, 3]: range, course, speed
    beta = np.array([grid[int(np.argmin(sc[:, j]))] for j in range(3)])
    t = {"cells": fit(beta), "beta": [float(b) for b in beta], "slices": keys}
    t["beta_scores"] = {str(b): [float(v) for v in sc[k]] for k, b in enumerate(grid)}
    return t


def apply_temperature5(t: dict[str, Any], inp: Inputs) -> Statement5:
    lab = cells(inp, list(t["slices"]))
    beta = np.asarray(t["beta"], dtype=np.float64)
    first = next(iter(t["cells"].values()))
    v = [t["cells"].get(c, first) for c in lab]
    a, lp, cr, cs = (np.array([x[k] for x in v]) for k in ("a", "logit_p", "c_r", "c_s"))
    f = inp.sd ** (beta[None, :] - 1.0)
    return Statement5(a * f[:, 1], lp, cr * f[:, 0], cs * f[:, 2])


def _component_means(s5: Statement5, inp: Inputs, xmax: float) -> list[float]:
    sc = scores(s5, inp, xmax)
    return [sc["range"], sc["course"], sc["speed"]]


# ---------------------------------------------------------------- classical rule (R6.2)


class Classical(nn.Module):
    """log a, logit P, log c_r, log c_s as quadratics in the standardised log sds; logit P also
    linear in the standardised proxy design."""

    mu: Tensor
    sdv: Tensor
    dmu: Tensor
    dsd: Tensor

    def __init__(self, mu: np.ndarray, sdv: np.ndarray, dmu: np.ndarray, dsd: np.ndarray) -> None:
        super().__init__()
        self.register_buffer("mu", torch.tensor(mu))
        self.register_buffer("sdv", torch.tensor(sdv))
        self.register_buffer("dmu", torch.tensor(dmu))
        self.register_buffer("dsd", torch.tensor(dsd))
        self.w = nn.Parameter(torch.zeros(10, 4, dtype=torch.float64))
        self.v = nn.Parameter(torch.zeros(len(dmu), dtype=torch.float64))

    def forward(self, log_sd: Tensor, design: Tensor) -> Tensor:
        z = (log_sd - self.mu) / self.sdv
        cols = [torch.ones_like(z[:, 0])] + [z[:, i] for i in range(3)]
        cols += [z[:, i] * z[:, j] for i in range(3) for j in range(i, 3)]
        q = torch.stack(cols, dim=1)
        out = q @ self.w
        dz = (design - self.dmu) / self.dsd
        return out + torch.stack(
            [torch.zeros_like(out[:, 0]), dz @ self.v, torch.zeros_like(out[:, 0]),
             torch.zeros_like(out[:, 0])], dim=1)  # fmt: skip


def _params(out: Tensor) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    return torch.exp(out[:, 0]), out[:, 1], torch.exp(out[:, 2]), torch.exp(out[:, 3])


def fit_classical(
    train: Inputs, start: dict[str, float], xmax: float, l2: float, steps: int
) -> dict[str, Any]:
    """Fit on the stream rows; ``start`` (a, logit_p, c_r, c_s) sets the intercepts and the
    loss scale."""
    m = train.ok
    mu, sdv = train.log_sd[m].mean(0), train.log_sd[m].std(0) + 1e-12
    dmu, dsd = train.design[m].mean(0), train.design[m].std(0) + 1e-12
    model = Classical(mu, sdv, dmu, dsd)
    with torch.no_grad():
        model.w[0] = torch.tensor(
            [math.log(start["a"]), start["logit_p"], math.log(start["c_r"]), math.log(start["c_s"])]
        )
    s0 = Statement5(*(np.full(len(m), v) for v in (start["a"], start["logit_p"],
                                                  start["c_r"], start["c_s"])))  # fmt: skip
    scale = scores(s0, train, xmax)
    ls, ds = torch.tensor(train.log_sd[m]), torch.tensor(train.design[m])
    e, sd = torch.tensor(train.err[m]), torch.tensor(train.sd[m])
    opt = torch.optim.Adam(model.parameters(), lr=0.02)
    for _ in range(steps):
        loss = total(loss_terms(e, sd, *_params(model(ls, ds)), xmax), scale)
        loss = loss + l2 * ((model.w[1:] ** 2).sum() + (model.v**2).sum())
        opt.zero_grad()
        loss.backward()  # type: ignore[no-untyped-call]
        opt.step()
    return {
        "mu": mu.tolist(),
        "sdv": sdv.tolist(),
        "dmu": dmu.tolist(),
        "dsd": dsd.tolist(),
        "w": model.w.detach().numpy().tolist(),
        "v": model.v.detach().numpy().tolist(),
        "scale": scale,
        "final_loss": float(loss.detach()),
    }


def classical_module(rec: dict[str, Any]) -> Classical:
    model = Classical(*(np.asarray(rec[k]) for k in ("mu", "sdv", "dmu", "dsd")))
    with torch.no_grad():
        model.w.copy_(torch.tensor(rec["w"]))
        model.v.copy_(torch.tensor(rec["v"]))
    return model


def apply_classical(rec: dict[str, Any], inp: Inputs) -> Statement5:
    model = classical_module(rec)
    with torch.no_grad():
        a, lp, cr, cs = _params(model(torch.tensor(inp.log_sd), torch.tensor(inp.design)))
    return Statement5(a.numpy(), lp.numpy(), cr.numpy(), cs.numpy())


def global_start(inp: Inputs, xmax: float) -> dict[str, float]:
    m = inp.ok
    a, lp = _fit_course_cell(inp.err[m, 1], inp.sd[m, 1], xmax)
    return {
        "a": a,
        "logit_p": lp,
        "c_r": float(np.quantile(np.abs(inp.err[m, 0]) / inp.sd[m, 0], 0.95)),
        "c_s": float(np.quantile(np.abs(inp.err[m, 2]) / inp.sd[m, 2], 0.95)),
    }


# ---------------------------------------------------------------- head (R6, R3)


class Head5(nn.Module):
    def __init__(self, classical: Classical, n_in: int, width: int, bound: float) -> None:
        super().__init__()
        self.classical = classical
        for p in self.classical.parameters():
            p.requires_grad_(False)
        self.bound = float(bound)
        self.hidden = nn.Linear(n_in, width).double()
        self.out = nn.Linear(width, 4).double()
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, feats: Tensor, log_sd: Tensor, design: Tensor) -> Tensor:
        base: Tensor = self.classical(log_sd, design)
        out: Tensor = base + self.bound * torch.tanh(self.out(torch.tanh(self.hidden(feats))))
        return out


def head_features(inp: Inputs, fmu: np.ndarray | None = None, fsd: np.ndarray | None = None
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:  # fmt: skip
    f = np.concatenate([inp.h, inp.log_sd, inp.code, inp.design], axis=1)
    if fmu is None or fsd is None:
        fmu, fsd = f[inp.ok].mean(0), f[inp.ok].std(0) + 1e-9
    return (f - fmu) / fsd, fmu, fsd


def train_head5(
    cfg: Any,
    classical_rec: dict[str, Any],
    train: Inputs,
    val: Inputs,
    ck: Path,
    provenance: dict[str, Any],
    log: Any = print,
) -> dict[str, Any]:
    from safetensors.torch import save_file

    from tma2.segment.gate import sha256_file

    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(1)
    ck.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(cfg.seed)
    xmax = float(cfg.xmax_rad)
    ft, fmu, fsd = head_features(train)
    fv, _, _ = head_features(val, fmu, fsd)
    hdim = train.h.shape[1]
    head = Head5(classical_module(classical_rec), ft.shape[1], cfg.width, cfg.bound)
    scale = classical_rec["scale"]
    m = train.ok
    tf = torch.tensor(ft[m])
    tl, td = torch.tensor(train.log_sd[m]), torch.tensor(train.design[m])
    te, ts = torch.tensor(train.err[m]), torch.tensor(train.sd[m])
    mv = val.ok
    vf = torch.tensor(fv[mv])
    vl, vd = torch.tensor(val.log_sd[mv]), torch.tensor(val.design[mv])
    ve, vs = torch.tensor(val.err[mv]), torch.tensor(val.sd[mv])
    params = [p for p in head.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=cfg.learning_rate)

    def evaluate() -> float:
        with torch.no_grad():
            return float(total(loss_terms(ve, vs, *_params(head(vf, vl, vd)), xmax), scale))

    shuffle = (cfg.shuffle or "none").lower()
    meta: dict[str, Any] = {"jobs": [provenance], "scale": scale, "shuffle": shuffle, "log": []}
    meta["feature_mu"], meta["feature_sd"] = fmu.tolist(), fsd.tolist()
    meta["untrained_val"] = best = evaluate()
    meta["best_epoch"], stale = 0, 0
    save_file(_state(head), str(ck / "best.safetensors"))
    for ep in range(1, cfg.max_epochs + 1):
        rng = np.random.default_rng(cfg.seed * 1000 + ep)
        perm = torch.tensor(rng.permutation(int(m.sum())))
        f_ep, e_ep = tf, te
        if shuffle == "encoder":
            f_ep = tf.clone()
            f_ep[:, :hdim] = tf[perm][:, :hdim]
        elif shuffle == "errors":
            e_ep = te[perm]
        order = rng.permutation(int(m.sum()))
        t0, tot = time.time(), 0.0
        for s0 in range(0, len(order), cfg.batch_rows):
            idx = torch.tensor(order[s0 : s0 + cfg.batch_rows])
            out = head(f_ep[idx], tl[idx], td[idx])
            loss = total(loss_terms(e_ep[idx], ts[idx], *_params(out), xmax), scale)
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
            tot += float(loss.detach()) * len(idx)
        v = evaluate()
        save_file(_state(head), str(ck / "last.safetensors"))
        if v < best - cfg.min_improvement * abs(best):
            best, meta["best_epoch"], stale = v, ep, 0
            save_file(_state(head), str(ck / "best.safetensors"))
        else:
            stale += 1
        rec = {"epoch": ep, "train": tot / max(len(order), 1), "val": v,
               "s": round(time.time() - t0, 1)}  # fmt: skip
        log(json.dumps(rec))
        meta["log"].append(rec)
        meta["epoch"], meta["last_val"] = ep, v
        if stale >= cfg.patience:
            break
    meta["best_val"] = best
    for which in ("best", "last"):
        meta[f"{which}_weights_sha256"] = sha256_file(ck / f"{which}.safetensors")
    (ck / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def _state(head: Head5) -> dict[str, Tensor]:
    return {k: v.contiguous() for k, v in head.state_dict().items()}


def apply_head5(
    meta: dict[str, Any], weights: Path, classical_rec: dict[str, Any], inp: Inputs, cfg: Any
) -> Statement5:
    from safetensors.torch import load_file

    f, _, _ = head_features(inp, np.asarray(meta["feature_mu"]), np.asarray(meta["feature_sd"]))
    head = Head5(classical_module(classical_rec), f.shape[1], cfg.width, cfg.bound)
    head.load_state_dict(load_file(str(weights)))
    with torch.no_grad():
        a, lp, cr, cs = _params(
            head(torch.tensor(f), torch.tensor(inp.log_sd), torch.tensor(inp.design))
        )
    return Statement5(a.numpy(), lp.numpy(), cr.numpy(), cs.numpy())


def fit_platt(s5: Statement5, inp: Inputs, xmax: float) -> tuple[float, float]:
    """The Platt map for P on these (tuning) rows."""
    out = s5.stated(inp.sd, xmax, None)
    hit = (np.abs(inp.err[:, 1]) <= out["x"]).astype(float)
    m = inp.ok
    return st.platt_fit(out["p"][m], hit[m])
