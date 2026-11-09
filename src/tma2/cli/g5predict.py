"""tma2-g5predict: E's prediction file with spec 010's truncated course statement.

    uv run tma2-g5predict --in <E prediction.ndjson> --features <cache.npz>… --proxy <proxy.npz>…
        --plan <g5 plan> --proxy-def <proxy.json>
        (--temperature <temperature.json> | --classical <classical.json>
         | --model <id> --run <training dir> --classical <classical.json> [--epoch best|last])
        --out <file>

Each row of the file's scenarios that has a usable covariance gains these fields:
- ``course_arc_rad`` (X), ``course_arc_prob`` (P, after the statement's Platt map) and
  ``course_conc`` (κ), with ``course_form`` "truncated": the arc mass is exactly P;
- ``range_ratio_q95`` and ``speed_q95_mps``;
- the proxy's ``unsettled_score`` and ``unsettled_flag``.

Every point field is copied unchanged.

The header gains ``calibration``:
- the kind and the model id (``<model>-<epoch>`` for a head);
- the weights' or rule's digest, the proxy definition's digest and the plan's digest;
- ``max_mass_error``: the largest |arc mass − P| over the stated rows, computed by integrating
  the stated density numerically;
- this run's commit and dirty flag, read before anything is written.

Refuses a cache made from other E weights, or a file scenario without cache rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mass_error(x: np.ndarray, p: np.ndarray, kappa: np.ndarray, n: int = 2001) -> float:
    """max |∫_{−X}^{X} density − P| by the trapezoid rule on the stated density."""
    from tma2.calib.statement import truncated_log_score

    worst = 0.0
    for i in range(len(x)):
        g = np.linspace(-x[i], x[i], n)
        dens = np.exp(truncated_log_score(g, np.full(n, x[i]), np.full(n, p[i]),
                                          np.full(n, kappa[i])))  # fmt: skip
        worst = max(worst, abs(float(np.trapezoid(dens, g)) - float(p[i])))
    return worst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g5predict", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--features", nargs="+", required=True)
    ap.add_argument("--proxy", nargs="+", required=True)
    ap.add_argument("--proxy-def", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--temperature")
    ap.add_argument("--classical")
    ap.add_argument("--model")
    ap.add_argument("--run")
    ap.add_argument("--epoch", choices=("best", "last"), default="best")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import torch

    torch.set_num_threads(1)  # AGENTS.md: oversubscribed OpenMP threads run 50-100x slower
    torch.set_default_dtype(torch.float64)
    kinds = [a.temperature is not None, a.run is not None, a.classical is not None and not a.run]
    if sum(kinds) != 1:
        print("give exactly one of --temperature, --classical, or --model/--run", file=sys.stderr)
        return 2

    from types import SimpleNamespace

    from tma2.calib import data, proxy
    from tma2.calib import statement5 as s5
    from tma2.calib.predict import write_fields
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()  # before anything is written
    raw = Path(a.plan).read_bytes()
    plan, plan_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    d = data.load(a.features)
    with open(a.inp, encoding="utf-8") as fh:
        ph = json.loads(fh.readline())
        ords = {int(json.loads(line)["ordinal"]) for line in fh}
    uncovered = sorted(ords - set(d.ordinal.tolist()))
    if uncovered:
        print(f"{a.inp}: {len(uncovered)} scenarios have no cache rows, e.g. {uncovered[:5]}",
              file=sys.stderr)  # fmt: skip
        return 2
    if ph.get("weights_sha256") != d.header.get("weights_sha256"):
        print(f"{a.inp}: the cache was made from other E weights", file=sys.stderr)
        return 2
    keep = np.isin(d.ordinal, sorted(ords))
    d = d.select(keep)
    pf = proxy.load_aligned(a.proxy, d.ordinal, d.k)
    inp = s5.inputs(d, pf)
    pdef = json.loads(Path(a.proxy_def).read_text())
    score = proxy.score(pdef, inp.design)
    xmax = float(plan["head"]["xmax_rad"])
    cal: dict[str, Any]
    if a.temperature:
        t = json.loads(Path(a.temperature).read_text())
        stmt, platt = s5.apply_temperature5(t, inp), tuple(t["platt"])
        cal = {"kind": "temperature", "model": "temperature", "weights_sha256": _sha(a.temperature)}
    elif a.run is None:
        c = json.loads(Path(a.classical).read_text())
        stmt, platt = s5.apply_classical(c, inp), tuple(c["platt"])
        cal = {"kind": "classical", "model": "classical", "weights_sha256": _sha(a.classical)}
    else:
        import torch

        torch.set_default_dtype(torch.float64)
        run = Path(a.run)
        meta = json.loads((run / "meta.json").read_text())
        c = json.loads(Path(a.classical).read_text())
        m = plan["models"][a.model]
        cfg = SimpleNamespace(**{**plan["head"], "seed": m["seed"]})
        w = run / f"{a.epoch}.safetensors"
        stmt = s5.apply_head5(meta, w, c, inp, cfg)
        platt = tuple(meta[f"platt_{a.epoch}"])
        cal = {"kind": "head", "model": f"{a.model}-{a.epoch}", "weights_sha256": _sha(w),
               "classical_sha256": _sha(a.classical)}  # fmt: skip
    out = stmt.stated(inp.sd, xmax, (float(platt[0]), float(platt[1])))
    stated = np.where(d.scalable & np.isfinite(inp.sd).all(axis=1) & np.isfinite(score))[0]
    rng = np.random.default_rng(0)
    probe = rng.choice(stated, size=min(200, len(stated)), replace=False) if len(stated) else stated
    cal |= {
        "proxy_def_sha256": _sha(a.proxy_def),
        "plan_sha256": plan_sha,
        "max_mass_error": mass_error(out["x"][probe], out["p"][probe], out["kappa"][probe]),
        "git_commit": g.commit,
        "git_dirty": g.dirty,
    }
    thr = float(pdef["threshold"])
    fields: dict[tuple[int, float], dict[str, Any]] = {}
    for i in stated:
        fields[(int(d.ordinal[i]), float(d.t[i]))] = {
            "course_arc_rad": float(out["x"][i]),
            "course_arc_prob": float(out["p"][i]),
            "course_conc": float(out["kappa"][i]),
            "course_form": "truncated",
            "range_ratio_q95": float(out["q_r"][i]),
            "speed_q95_mps": float(out["q_s"][i]),
            "unsettled_score": float(score[i]),
            "unsettled_flag": bool(score[i] > thr),
        }
    n = write_fields(Path(a.inp), Path(a.out), fields, cal)
    print(json.dumps({"rows_stated": n, "out": a.out, **cal}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
