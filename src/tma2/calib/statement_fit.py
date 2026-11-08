"""Fitting the usable uncertainty statement (spec 009 T006, T013; research R2, R3, R6).

Four quantities per row: the course spread scale a and peaked weight p (the course mixture,
``calib.statement``), and the range and speed interval scales c_r and c_s (95% half-widths
c · sd). Rows are the cache's usable rows (plausible, a usable covariance, finite exact errors).

**Temperature** (the classical control): one (a, p, c_r, c_s) per slice cell (G5 minute × open at
k), stated on sd^β with β per quantity picked from the plan's grid on the tuning rows (β = 1
is the plain temperature). (a, p) minimise the course negative log score in the cell; c_r and
c_s are the cell's 95% quantiles of |e| / sd^β, which minimise the interval score.

**Head**: a small MLP on the cache's features with four outputs, each moving its quantity from the
global temperature value by at most e^(±bound) (p on the logit scale); zero-initialised, so the
untrained head equals the global statement. Loss: the course negative log score and the two
interval scores, each divided by the global statement's mean on the training rows so the three are
commensurate. A shuffled control permutes the rows' errors each epoch.

**Recalibration**: P is mapped through an isotonic map fitted on the tuning rows of whichever
statement produced it.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from . import statement as st
from .data import CalData


@dataclass
class Statement:
    """Per-row statement quantities (before the isotonic map)."""

    a: np.ndarray
    p: np.ndarray
    c_r: np.ndarray
    c_s: np.ndarray


def rows(d: CalData) -> np.ndarray:
    """Rows usable for fitting: a usable covariance and finite exact errors and sds."""
    assert d.sd is not None and d.err is not None
    ok: np.ndarray = d.scalable & np.isfinite(d.err).all(axis=1) & np.isfinite(d.sd).all(axis=1)
    return ok


def _fit_course(e: np.ndarray, sd: np.ndarray, steps: int = 600) -> tuple[float, float]:
    torch.manual_seed(0)
    et, sdt = torch.tensor(e), torch.tensor(sd)
    la = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    lp = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.Adam([la, lp], lr=0.05)
    for _ in range(steps):
        nll = -st.course_log_score_t(et, torch.exp(la), torch.sigmoid(lp), sdt).mean()
        opt.zero_grad()
        nll.backward()  # type: ignore[no-untyped-call]
        opt.step()
    return float(torch.exp(la).detach()), float(torch.sigmoid(lp).detach())


def fit_global(d: CalData) -> dict[str, float]:
    """One statement for every usable row: the head's starting point and the loss scale."""
    assert d.sd is not None and d.err is not None
    m = rows(d)
    a, p = _fit_course(d.err[m, 1], d.sd[m, 1])
    c_r = float(np.quantile(np.abs(d.err[m, 0]) / d.sd[m, 0], 0.95))
    c_s = float(np.quantile(np.abs(d.err[m, 2]) / d.sd[m, 2], 0.95))
    return {"a": a, "p": p, "c_r": c_r, "c_s": c_s}


def cells(d: CalData, keys: list[str]) -> np.ndarray:
    cols = {"minute": d.minute, "open": d.open}
    return np.array(["|".join(f"{k}={cols[k][i]}" for k in keys) for i in range(len(d))])


def _cell_fit(
    d: CalData, lab: np.ndarray, m: np.ndarray, beta: np.ndarray, min_rows: int
) -> dict[str, dict[str, float]]:
    assert d.sd is not None and d.err is not None
    s = d.sd ** beta[None, :]
    out: dict[str, dict[str, float]] = {}
    for c in sorted(set(lab.tolist())):
        i = m & (lab == c)
        if i.sum() < min_rows:
            i = m
        a, p = _fit_course(d.err[i, 1], s[i, 1])
        out[c] = {
            "a": a,
            "p": p,
            "c_r": float(np.quantile(np.abs(d.err[i, 0]) / s[i, 0], 0.95)),
            "c_s": float(np.quantile(np.abs(d.err[i, 2]) / s[i, 2], 0.95)),
        }
    return out


def _component_scores(st_: Statement, d: CalData) -> np.ndarray:
    """Mean course negative log score and the two mean interval scores on the usable rows."""
    assert d.sd is not None and d.err is not None
    m = rows(d)
    e, sd = d.err[m], d.sd[m]
    nll = -st.course_log_score(e[:, 1], st_.a[m], st_.p[m], sd[:, 1])
    r = st.interval_score(np.abs(e[:, 0]), st_.c_r[m] * sd[:, 0])
    q = st.interval_score(np.abs(e[:, 2]), st_.c_s[m] * sd[:, 2])
    return np.array([r.mean(), nll.mean(), q.mean()])


def fit_temperature(
    d: CalData, keys: list[str], beta_grid: list[float] | None = None, min_rows: int = 20
) -> dict[str, Any]:
    """{"global", "cells": {cell: {a, p, c_r, c_s}}, "beta": [log range, course, speed]}.

    Each cell's statement is stated on sd^β (β < 1 tempers the spread of E's sds; research R3a).
    β is chosen per quantity from ``beta_grid`` by the cell fits' mean score on these rows (the
    three quantities' scores are separable). A cell with too few rows takes the fit on all rows.
    ``apply_temperature`` converts back to per-row multiples of sd."""
    g = fit_global(d)
    lab, m = cells(d, keys), rows(d)
    grid = [1.0] if not beta_grid else [float(b) for b in beta_grid]
    trials = []
    for b in grid:
        t = {"global": g, "cells": _cell_fit(d, lab, m, np.full(3, b), min_rows), "beta": [b] * 3}
        trials.append(_component_scores(apply_temperature(t, d, keys), d))
    sc = np.array(trials)  # [grid, 3]
    beta = np.array([grid[int(np.argmin(sc[:, j]))] for j in range(3)])
    out: dict[str, Any] = {
        "global": g,
        "cells": _cell_fit(d, lab, m, beta, min_rows),
        "beta": [float(b) for b in beta],
        "beta_scores": {str(b): [float(x) for x in sc[k]] for k, b in enumerate(grid)},
    }
    return out


def apply_temperature(t: dict[str, Any], d: CalData, keys: list[str]) -> Statement:
    """Per-row (a, p, c_r, c_s) as multiples of the row's own sd: x_cell · sd^(β − 1)."""
    assert d.sd is not None
    lab = cells(d, keys)
    g = t["global"]
    beta = np.asarray(t.get("beta", [1.0, 1.0, 1.0]), dtype=np.float64)
    v = [t["cells"].get(c, g) for c in lab]
    a, p, c_r, c_s = (
        np.array([x[k] for x in v], dtype=np.float64) for k in ("a", "p", "c_r", "c_s")
    )
    f = d.sd ** (beta[None, :] - 1.0)
    return Statement(a * f[:, 1], p, c_r * f[:, 0], c_s * f[:, 2])


def stated(s: Statement, d: CalData, xmax: float) -> dict[str, np.ndarray]:
    """The row's stated X, raw P (before the isotonic map) and half-widths."""
    assert d.sd is not None
    x = st.arc(s.a, d.sd[:, 1], xmax)
    return {
        "x": x,
        "p_raw": st.arc_prob(s.p, s.a, d.sd[:, 1], x),
        "q_r": s.c_r * d.sd[:, 0],
        "q_s": s.c_s * d.sd[:, 2],
    }


def fit_isotonic(
    s: Statement, d: CalData, xmax: float, bins: int
) -> tuple[list[float], list[float]]:
    """The map from stated P to the observed hit rate on these (tuning) rows."""
    assert d.err is not None
    m = rows(d)
    out = stated(s, d, xmax)
    hit = (np.abs(d.err[:, 1]) <= out["x"]).astype(float)
    return st.isotonic_fit(out["p_raw"][m], hit[m], bins)


# ---------------------------------------------------------------- head


class StatementHead(nn.Module):
    base: Tensor
    logit_p: Tensor

    def __init__(self, inputs: int, width: int, bound: float, g: dict[str, float]) -> None:
        super().__init__()
        self.bound = float(bound)
        self.hidden = nn.Linear(inputs, width)
        self.out = nn.Linear(width, 4)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)
        self.register_buffer(
            "base", torch.tensor([g["a"], g["c_r"], g["c_s"]], dtype=torch.float64)
        )
        self.register_buffer("logit_p", torch.tensor(float(np.log(g["p"] / (1 - g["p"])))))

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        o = self.bound * torch.tanh(self.out(torch.tanh(self.hidden(x))))
        a = self.base[0] * torch.exp(o[:, 0])
        p = torch.sigmoid(self.logit_p + o[:, 1])
        return a, p, self.base[1] * torch.exp(o[:, 2]), self.base[2] * torch.exp(o[:, 3])


def head_loss(
    head: StatementHead, x: Tensor, err: Tensor, sd: Tensor, scale: dict[str, float]
) -> Tensor:
    a, p, c_r, c_s = head(x)
    nll = -st.course_log_score_t(err[:, 1], a, p, sd[:, 1])
    is_r = st.interval_score_t(err[:, 0].abs(), c_r * sd[:, 0])
    is_s = st.interval_score_t(err[:, 2].abs(), c_s * sd[:, 2])
    return (nll / scale["course"] + is_r / scale["range"] + is_s / scale["speed"]).mean()


def loss_scale(g: dict[str, float], d: CalData) -> dict[str, float]:
    """The global statement's mean course NLL and interval scores on these rows (positive)."""
    assert d.sd is not None and d.err is not None
    m = rows(d)
    e, sd = d.err[m], d.sd[m]
    nll = -st.course_log_score(
        e[:, 1], np.full(m.sum(), g["a"]), np.full(m.sum(), g["p"]), sd[:, 1]
    )
    return {
        "course": float(abs(nll.mean())) + 1e-9,
        "range": float(st.interval_score(np.abs(e[:, 0]), g["c_r"] * sd[:, 0]).mean()),
        "speed": float(st.interval_score(np.abs(e[:, 2]), g["c_s"] * sd[:, 2]).mean()),
    }


def predict_head(head: StatementHead, d: CalData) -> Statement:
    with torch.no_grad():
        a, p, c_r, c_s = head(torch.tensor(d.x, dtype=torch.float64))
    return Statement(a.numpy(), p.numpy(), c_r.numpy(), c_s.numpy())


def evaluate(head: StatementHead, d: CalData, scale: dict[str, float]) -> float:
    assert d.sd is not None and d.err is not None
    m = rows(d)
    with torch.no_grad():
        return float(
            head_loss(
                head,
                torch.tensor(d.x[m]),
                torch.tensor(d.err[m]),
                torch.tensor(d.sd[m]),
                scale,
            )
        )


def train_statement(
    cfg: Any,
    train: CalData,
    val: CalData,
    ck: Path,
    provenance: dict[str, Any],
    log: Any = print,
) -> dict[str, Any]:
    """Train one head; saves best and last weights and ``meta.json`` (global statement, loss scale,
    the isotonic map fitted on ``val``'s rows with the best weights)."""
    from safetensors.torch import load_file, save_file

    from tma2.segment.gate import sha256_file

    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(1)
    ck.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(cfg.seed)
    g = fit_global(train)
    scale = loss_scale(g, train)
    head = StatementHead(train.x.shape[1], cfg.width, cfg.bound, g).double()
    opt = torch.optim.Adam(head.parameters(), lr=cfg.learning_rate)
    assert train.sd is not None and train.err is not None
    m = rows(train)
    x_all = torch.tensor(train.x[m])
    e_all, sd_all = torch.tensor(train.err[m]), torch.tensor(train.sd[m])
    meta: dict[str, Any] = {"jobs": [provenance], "global": g, "scale": scale, "log": []}
    meta["untrained_val"] = best = evaluate(head, val, scale)
    meta["best_epoch"], stale = 0, 0
    save_file(head.state_dict(), str(ck / "best.safetensors"))
    for e in range(1, cfg.max_epochs + 1):
        rng = np.random.default_rng(cfg.seed * 1000 + e)
        e_ep = e_all[torch.tensor(rng.permutation(len(e_all)))] if cfg.shuffled else e_all
        order = rng.permutation(len(e_all))
        t0, tot = time.time(), 0.0
        for s0 in range(0, len(order), cfg.batch_rows):
            idx = torch.tensor(order[s0 : s0 + cfg.batch_rows])
            loss = head_loss(head, x_all[idx], e_ep[idx], sd_all[idx], scale)
            opt.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            opt.step()
            tot += float(loss.detach()) * len(idx)
        v = evaluate(head, val, scale)
        save_file(head.state_dict(), str(ck / "last.safetensors"))
        if v < best - cfg.min_improvement * abs(best):
            best, meta["best_epoch"], stale = v, e, 0
            save_file(head.state_dict(), str(ck / "best.safetensors"))
        else:
            stale += 1
        rec = {
            "epoch": e,
            "train": tot / max(len(order), 1),
            "val": v,
            "s": round(time.time() - t0, 1),
        }
        log(json.dumps(rec))
        meta["log"].append(rec)
        meta["epoch"], meta["last_val"] = e, v
        if stale >= cfg.patience:
            break
    meta["best_val"] = best
    for which in ("best", "last"):
        head.load_state_dict(load_file(str(ck / f"{which}.safetensors")))
        knots = fit_isotonic(predict_head(head, val), val, cfg.xmax_rad, 10)
        meta[f"isotonic_{which}"] = {"x": knots[0], "y": knots[1]}
        meta[f"{which}_weights_sha256"] = sha256_file(ck / f"{which}.safetensors")
    (ck / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta
