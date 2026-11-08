"""Spec 009 research R1–R3a on validation tuning ordinals 0–499 only (T002; no SciPy).

    uv run python scripts/research/g4_tuning.py --plan configs/gate4/g4-a.json \
        --val <feature cache shards *.npz> [--head <checkpoint dir>]

Prints JSON: R1 the course-error shares and single-signal AUCs; R2 the per-slice statement's
reliability overall and in five bins of P (before the isotonic map); R3a the temperature's
component scores by sd power β (the fit's own grid) and the β it picks; with ``--head``, the head's
and the shuffled control's standardised summed score beside the temperature's on the same rows.
Everything is in sample on the tuning rows: it sets the design, it is not a result.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def auc(score: np.ndarray, label: np.ndarray) -> float:
    """Rank AUC (ties averaged)."""
    order = np.argsort(score, kind="stable")
    ranks = np.empty(len(score))
    s = score[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    pos = label.astype(bool)
    n1, n0 = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--val", nargs="+", required=True)
    ap.add_argument("--head", help="checkpoint dir holding <model>/best.safetensors, meta.json")
    a = ap.parse_args()

    from tma2.calib import data
    from tma2.calib import statement_fit as sf
    from tma2.cli.g3train import _tuning

    plan = json.loads(Path(a.plan).read_text())
    v = _tuning(plan, data.load(sorted(a.val)))
    assert v.err is not None and v.sd is not None
    m = sf.rows(v)
    e = np.abs(v.err[m])
    out: dict[str, object] = {"rows": int(len(v)), "usable": int(m.sum())}
    bad = e[:, 1] > math.radians(30)
    out["r1"] = {
        "course_over_30deg": float(bad.mean()),
        "course_over_90deg": float((e[:, 1] > math.radians(90)).mean()),
        "auc_course_sd": auc(v.sd[m, 1], bad),
        "auc_log_range_sd": auc(v.sd[m, 0], bad),
        "auc_open": auc(v.open[m].astype(float), bad),
        "auc_minute": auc(v.minute[m].astype(float), bad),
    }
    keys = list(plan["temperature"]["slices"])
    xmax = float(plan["temperature"]["xmax_rad"])
    plain = sf.fit_temperature(v, keys)
    s = sf.stated(sf.apply_temperature(plain, v, keys), v, xmax)
    hit = (np.abs(v.err[:, 1]) <= s["x"]).astype(float)
    order = np.argsort(s["p_raw"][m], kind="stable")
    bins = [
        {"p": float(s["p_raw"][m][i].mean()), "hit": float(hit[m][i].mean())}
        for i in np.array_split(order, 5)
    ]
    out["r2"] = {
        "mean_p": float(s["p_raw"][m].mean()),
        "hit": float(hit[m].mean()),
        "mean_arc_deg": float(np.degrees(s["x"][m].mean())),
        "bins": bins,
    }
    t = sf.fit_temperature(v, keys, list(plan["temperature"].get("beta_grid") or []))
    out["r3a"] = {"beta": t["beta"], "scores_by_beta": t["beta_scores"]}
    if a.head:
        heads = {}
        for model in sorted(p.name for p in Path(a.head).iterdir() if p.is_dir()):
            meta = json.loads((Path(a.head) / model / "meta.json").read_text())
            heads[model] = {"untrained": meta["untrained_val"], "best": meta["best_val"],
                            "best_epoch": meta["best_epoch"], "scale": meta["scale"]}  # fmt: skip
        if heads:
            sc = next(iter(heads.values()))["scale"]
            comp = sf._component_scores(sf.apply_temperature(t, v, keys), v)
            out["head"] = heads
            out["temperature_standardised"] = float(
                comp[0] / sc["range"] + comp[1] / sc["course"] + comp[2] / sc["speed"]
            )
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
