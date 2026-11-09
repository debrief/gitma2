"""tma2-g5train: spec 010's fits (research R1, R6).

    uv run tma2-g5train proxy --plan P --data VAL.f32pack --val CACHE --val-proxy PROXY --out F
    uv run tma2-g5train temperature --plan P --val CACHE --val-proxy PROXY --out F
    uv run tma2-g5train classical --plan P --train CACHE --train-proxy PROXY
                                  --val CACHE --val-proxy PROXY --out F
    uv run tma2-g5train head --plan P --model ID --classical F --train CACHE --train-proxy PROXY
                             --val CACHE --val-proxy PROXY --checkpoint DIR

Every fit on validation uses the plan's tuning ordinals only. ``proxy`` fits the unsettled proxy
for the truth "not settled" and sets its threshold at the tuning base rate. ``temperature`` and
``classical`` also fit their Platt maps on the tuning rows; ``head`` writes ``meta.json`` with the
Platt maps of its best and last weights. Each output records the plan digest, the inputs' digests,
the commit and the dirty flag (read before anything is written).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.provenance import read_git_provenance


def _plan(path: str) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _digest_files(paths: list[str]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(Path(p).read_bytes())
    return h.hexdigest()


def _inputs(plan: dict[str, Any], cache: list[Any], prox: list[Any], tune: bool) -> Any:
    from tma2.calib import data, proxy, statement5

    d = data.load(cache)
    if tune:
        a, b = plan["tuning_ordinals"]
        d = d.select((d.ordinal >= a) & (d.ordinal < b))
    pf = proxy.load_aligned(prox, d.ordinal, d.k)
    return d, statement5.inputs(d, pf)


def cmd_proxy(a: argparse.Namespace) -> int:
    from tma2.calib import proxy
    from tma2.eval.rows import settled_row
    from tma2.segment.score import iter_selected

    g = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    d, inp = _inputs(plan, a.val, a.val_proxy, tune=True)
    lo, hi = int(d.ordinal.min()), int(d.ordinal.max())
    metas = {j: m for j, m, *_ in iter_selected(a.data, lo, hi - lo + 1)}
    y = np.array(
        [not settled_row(metas[int(o)], int(k)) for o, k in zip(d.ordinal, d.k, strict=True)]
    )
    m = inp.ok
    defn = proxy.fit_proxy(inp.design[m], y[m])
    s = proxy.score(defn, inp.design[m])
    thr = float(np.quantile(s, 1.0 - y[m].mean()))
    defn["threshold"] = thr
    defn["flag_share_tuning"] = float((s > thr).mean())
    rec = {
        **defn,
        "base_rate_tuning": float(y[m].mean()),
        "rows": int(m.sum()),
        "plan_sha256": plan_sha,
        "val_sha256": _digest_files(a.val),
        "val_proxy_sha256": _digest_files(a.val_proxy),
        "git_commit": g.commit,
        "git_dirty": g.dirty,
    }
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({"threshold": thr, "flag_share": rec["flag_share_tuning"]}))
    return 0


def cmd_temperature(a: argparse.Namespace) -> int:
    from tma2.calib import statement5 as s5

    g = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    cfg = plan["temperature"]
    xmax = float(cfg["xmax_rad"])
    _, inp = _inputs(plan, a.val, a.val_proxy, tune=True)
    t = s5.fit_temperature5(inp, list(cfg["slices"]), list(cfg["beta_grid"]), xmax)
    t["platt"] = list(s5.fit_platt(s5.apply_temperature5(t, inp), inp, xmax))
    t.update(plan_sha256=plan_sha, val_sha256=_digest_files(a.val), git_commit=g.commit,
             git_dirty=g.dirty, rows=int(inp.ok.sum()))  # fmt: skip
    Path(a.out).write_text(json.dumps(t, indent=2) + "\n")
    print(json.dumps({"beta": t["beta"], "platt": t["platt"]}))
    return 0


def cmd_classical(a: argparse.Namespace) -> int:
    from tma2.calib import statement5 as s5

    g = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    cfg = plan["classical"]
    xmax = float(cfg["xmax_rad"])
    _, tr = _inputs(plan, a.train, a.train_proxy, tune=False)
    _, val = _inputs(plan, a.val, a.val_proxy, tune=True)
    start = s5.global_start(tr, xmax)
    rec = s5.fit_classical(tr, start, xmax, float(cfg["l2"]), int(cfg["steps"]))
    rec["start"] = start
    rec["platt"] = list(s5.fit_platt(s5.apply_classical(rec, val), val, xmax))
    rec.update(plan_sha256=plan_sha, train_sha256=_digest_files(a.train),
               val_sha256=_digest_files(a.val), git_commit=g.commit, git_dirty=g.dirty)  # fmt: skip
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({"final_loss": rec["final_loss"], "platt": rec["platt"]}))
    return 0


def cmd_head(a: argparse.Namespace) -> int:
    from types import SimpleNamespace

    from tma2.calib import statement5 as s5

    g = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    m = plan["models"].get(a.model)
    if m is None:
        print(f"{a.model} is not in the plan", file=sys.stderr)
        return 2
    cfg = SimpleNamespace(
        **{**plan["head"], "seed": m["seed"], "shuffle": m.get("shuffle", "none")}
    )
    classical = json.loads(Path(a.classical).read_text())
    if classical.get("plan_sha256") != plan_sha:
        print("--classical was fitted under another plan", file=sys.stderr)
        return 2
    _, tr = _inputs(plan, a.train, a.train_proxy, tune=False)
    _, val = _inputs(plan, a.val, a.val_proxy, tune=True)
    prov = {"git_commit": g.commit, "git_dirty": g.dirty, "plan_sha256": plan_sha,
            "classical_sha256": hashlib.sha256(Path(a.classical).read_bytes()).hexdigest(),
            "train_rows": int(tr.ok.sum()), "val_rows": int(val.ok.sum())}  # fmt: skip
    ck = Path(a.checkpoint)
    meta = s5.train_head5(cfg, classical, tr, val, ck, prov)
    xmax = float(cfg.xmax_rad)
    for which in ("best", "last"):
        st = s5.apply_head5(meta, ck / f"{which}.safetensors", classical, val, cfg)
        meta[f"platt_{which}"] = list(s5.fit_platt(st, val, xmax))
    (ck / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({"model": a.model, "best_epoch": meta["best_epoch"], "epoch": meta["epoch"]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g5train", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("proxy")
    p.add_argument("--data", required=True)
    for s in (p,):
        s.add_argument("--plan", required=True)
        s.add_argument("--val", nargs="+", required=True)
        s.add_argument("--val-proxy", nargs="+", required=True)
        s.add_argument("--out", required=True)
    t = sub.add_parser("temperature")
    t.add_argument("--plan", required=True)
    t.add_argument("--val", nargs="+", required=True)
    t.add_argument("--val-proxy", nargs="+", required=True)
    t.add_argument("--out", required=True)
    for name in ("classical", "head"):
        s = sub.add_parser(name)
        s.add_argument("--plan", required=True)
        s.add_argument("--train", nargs="+", required=True)
        s.add_argument("--train-proxy", nargs="+", required=True)
        s.add_argument("--val", nargs="+", required=True)
        s.add_argument("--val-proxy", nargs="+", required=True)
        if name == "classical":
            s.add_argument("--out", required=True)
        else:
            s.add_argument("--model", required=True)
            s.add_argument("--classical", required=True)
            s.add_argument("--checkpoint", required=True)
    a = ap.parse_args(argv)
    import torch

    torch.set_num_threads(1)  # AGENTS.md: oversubscribed OpenMP threads run 50-100x slower
    torch.set_default_dtype(torch.float64)
    run = {"proxy": cmd_proxy, "temperature": cmd_temperature, "classical": cmd_classical,
           "head": cmd_head}  # fmt: skip
    return run[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
