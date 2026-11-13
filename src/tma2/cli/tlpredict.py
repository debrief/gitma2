"""``tma2-tlpredict``: one shard of the learned whole-period model's output (spec 016 FR-009,
FR-010) on the periods ``tma2-tlsolve`` cuts from the same split and ordinals. Writes
``<out>.npz`` and ``<out>.json`` (the header).

Per period the shard holds the direct track (``learned``: x, y, vx, vy at every 5-second row),
the manoeuvre probability per token and the spans read from it. No error is computed and the
target's truth is not read; the arc read-out (``learned-arc``) is applied by the time-late
runner from these arrays (``tma2.timelate.learned.arc_readout``).

Arrays: ``ordinal``, ``first_row``, ``rows`` [P]; ``row_period`` [N] and ``learned`` [N, 4]
(rows of all periods, in order); ``token_period`` [K], ``token_t`` [K, 2] (s from the period's
start), ``man_prob`` [K], ``token_mean`` and ``token_logvar`` [K, 3] (the model's frame);
``span_period`` [S] and ``spans`` [S, 2] (s).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-tlpredict", description=__doc__)
    ap.add_argument("--weights", required=True, help="checkpoint.safetensors")
    ap.add_argument("--config", required=True, help="the training plan (or its config)")
    ap.add_argument("--in", dest="inp", required=True, help="the split's f32pack")
    ap.add_argument("--plan", help="the time-late plan (with --split: reads the split's `whole`)")
    ap.add_argument("--split", default="", help="the plan's split name (for the header)")
    ap.add_argument("--whole", action="store_true", help="engagements uncut (without --plan)")
    ap.add_argument("--start", type=int, default=0, help="first σ = 1° ordinal")
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", required=True, help="output prefix")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--merge-seconds", type=float, default=60.0)
    ap.add_argument("--max-manoeuvres", type=int, default=10)
    a = ap.parse_args(argv)
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()  # before any output
    import numpy as np
    import torch

    from tma2.data.f32pack import read_pack_header
    from tma2.regress.model import RegressorConfig
    from tma2.regress.period_predict import predict_periods
    from tma2.regress.predict import load_model
    from tma2.regress.train import config_digest
    from tma2.segment.gate import sha256_file
    from tma2.timelate.learned import direct_track, spans_from_logit, token_times
    from tma2.timelate.periods import iter_periods

    raw = json.loads(Path(a.config).read_text())
    cfg = RegressorConfig(**raw.get("config", raw))
    if cfg.data != "periods" or not cfg.manoeuvre_head:
        raise SystemExit(f"{a.config}: not a whole-period model with a manoeuvre head")
    whole = a.whole
    if a.plan:
        plan = json.loads(Path(a.plan).read_text())
        if a.split not in plan["splits"]:
            raise SystemExit(f"split {a.split!r} is not in {a.plan}")
        whole = bool(plan["splits"][a.split].get("whole", False))
    periods = list(iter_periods(a.inp, a.start, a.count, whole=whole))
    if not periods:
        raise SystemExit(f"no σ = 1° periods at {a.start} in {a.inp}")
    torch.set_num_threads(4)
    model = load_model(cfg, Path(a.weights))
    outs = predict_periods(model, periods)
    patch = cfg.patch_rows
    tracks, row_period, token_period, token_t, span_period, spans = [], [], [], [], [], []
    for p, o in zip(periods, outs, strict=True):
        tracks.append(direct_track(o.mean, p, patch))
        row_period.append(np.full(p.rows, p.ordinal, dtype=np.int64))
        tt = token_times(p.rows, p.dt, patch)
        token_t.append(tt)
        token_period.append(np.full(tt.shape[0], p.ordinal, dtype=np.int64))
        sp = spans_from_logit(o.prob, tt, a.threshold, a.merge_seconds, a.max_manoeuvres)
        spans.append(sp)
        span_period.append(np.full(sp.shape[0], p.ordinal, dtype=np.int64))
    header = {
        "record": "header",
        "kind": "learned-period-tracks",
        "split": a.split,
        "whole": whole,
        "dataset_digest": sha256_file(a.inp),
        "seed": int(read_pack_header(a.inp).dataset_seed),
        "ordinal_start": a.start,
        "ordinal_count": len(periods),
        "weights_sha256": sha256_file(a.weights),
        "config_sha256": config_digest(cfg),
        "config_id": cfg.id,
        "plan_sha256": sha256_file(a.plan) if a.plan else None,
        "patch_rows": patch,
        "threshold": a.threshold,
        "merge_seconds": a.merge_seconds,
        "max_manoeuvres": a.max_manoeuvres,
        "torch": torch.__version__,
        "git_commit": g.commit,
        "git_dirty": g.dirty,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        f"{out}.npz",
        ordinal=np.array([p.ordinal for p in periods], dtype=np.int64),
        first_row=np.array([p.first for p in periods], dtype=np.int64),
        rows=np.array([p.rows for p in periods], dtype=np.int64),
        row_period=np.concatenate(row_period),
        learned=np.concatenate(tracks),
        token_period=np.concatenate(token_period),
        token_t=np.concatenate(token_t),
        man_prob=np.concatenate([o.prob for o in outs]).astype(np.float32),
        token_mean=np.concatenate([o.mean for o in outs]),
        token_logvar=np.concatenate([o.logvar for o in outs]),
        span_period=np.concatenate(span_period),
        spans=np.concatenate(spans).reshape(-1, 2),
    )
    Path(f"{out}.json").write_text(json.dumps({"header": header}, sort_keys=True) + "\n")
    n_rows = sum(p.rows for p in periods)
    print(f"{len(periods)} periods, {n_rows} rows -> {out}.npz, {out}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
