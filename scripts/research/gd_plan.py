"""Spec 038: write the scoring plans of a stage from configs/gd/protocol.json, one per split
(a split has its own ranges file, so its own workflow run).

    uv run python scripts/research/gd_plan.py dev-a     # the grids, on the in-distribution split
    uv run python scripts/research/gd_plan.py dev-b     # the chosen settings and their neighbours
    uv run python scripts/research/gd_plan.py test      # the chosen settings only

Plans go to configs/headroom/gd-<stage>-<split>.json; push `headroom/gd-<stage>-<split>` to run
one. Every list of names in a plan is built from that plan's own runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FT = ["ft-s1", "ft-s2", "ft-s3"]
REG = ["reg-s1", "reg-s2", "reg-s3"]


def thr(x: float) -> dict[str, Any]:
    return {
        "kind": "robust",
        "segmentation": "c2r",
        "name": f"c2-thr{x:g}",
        "robust_confirm": {"robust": False, "tau_factor": x},
    }


def edit(tag: str, cfg: dict[str, bool], x: float | None = None) -> dict[str, Any]:
    r: dict[str, Any] = {"kind": "robust", "segmentation": "c2", "name": f"c2-{tag}", "edit": cfg}
    if x is not None:
        r |= {"segmentation": "c2r", "robust_confirm": {"robust": False, "tau_factor": x}}
        r["name"] = f"c2-{tag}-thr{x:g}"
    return r


def own_hybrid(w: float, name: str | None = None) -> dict[str, Any]:
    return {
        "kind": "hybrid",
        "segmentation": "c2",
        "name": name or f"own-hyb-w{w:g}",
        "prior_from": "own",
        "prior_weight": w,
    }


def runs_for(proto: dict[str, Any], stage: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base: list[dict[str, Any]] = [
        {"kind": "nominal", "segmentation": "c2", "name": "c2", "dump": True},
        {"kind": "robust", "segmentation": "c2", "name": "c2-robust"},
        {"kind": "robust", "name": "robust-true"},
        {"kind": "nominal", "name": "plain-true"},
        {
            "kind": "hybrid",
            "segmentation": "c2",
            "name": "hyb-s1",
            "prior_from": "ft-s1",
            "prior_weight": proto["hybrid_prior_weight"],
        },
    ]
    g = proto["grid"]
    if stage == "dev-a":
        hard = [thr(x) for x in g["threshold"]] + [edit(t, c) for t, c in g["edit"].items()]
        own = [own_hybrid(w) for w in g["own_prior_weight"]]
        own_name = own[len(own) // 2]["name"]
    else:
        ch = proto["chosen"]
        if not ch:
            raise SystemExit("protocol.json: 'chosen' is not set (choose on dev-a first)")
        hard = [thr(ch["threshold"]), edit(ch["edit"], g["edit"][ch["edit"]])]
        hard[0]["name"], hard[1]["name"] = "c2-thr", "c2-edit"
        if ch.get("combined"):
            hard.append(edit(ch["edit"], g["edit"][ch["edit"]], ch["threshold"]))
            hard[-1]["name"] = "c2-edit-thr"
        own = [own_hybrid(ch["own_prior_weight"], "own-hyb")]
        own_name = "own-hyb"
        if stage == "dev-b":  # the neighbours of each choice, to see the choice was not an edge
            for x in ch.get("threshold_neighbours", []):
                hard.append(thr(x))
            for w in ch.get("own_prior_weight_neighbours", []):
                own.append(own_hybrid(w))
    runs = base + hard + own
    names = {r["name"] for r in runs}
    decomp = {
        "comparator": "c2-robust",
        "regressors": FT,
        "unchanged": REG,
        "own": "own",
        "own_hybrid": own_name,
        "hybrids": ["hyb-s1"],
        "hardened": [r["name"] for r in hard] + [r["name"] for r in own if r["name"] != own_name],
        "true": "robust-true",
        "segments": "c2",
    }
    for key in ("own_hybrid", "true", "segments", "comparator"):
        assert decomp[key] in names, decomp[key]
    assert set(decomp["hardened"]) | set(decomp["hybrids"]) <= names
    return runs, decomp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("dev-a", "dev-b", "test"))
    ap.add_argument("--protocol", default="configs/gd/protocol.json")
    a = ap.parse_args()
    proto = json.loads((ROOT / a.protocol).read_text())
    st = proto["stages"][a.stage]
    runs, decomp = runs_for(proto, a.stage)
    n, size = int(st["ordinals"]), int(proto["shard_size"])
    for split, conds in st["splits"].items():
        plan = {
            "description": f"Spec 038 {a.stage}, split '{split}' ({proto['splits'][split]['what']}): "
            f"seed {st['seed']}, the first {n} sigma = 1 deg engagements per condition. Written "
            f"by scripts/research/gd_plan.py from {a.protocol}.",
            "stage": a.stage,
            "plan": proto["gate_h_plan"],
            "conditions_file": proto["conditions_file"],
            "ranges": proto["splits"][split]["ranges"],
            "split": "tuning",
            "seed": st["seed"],
            "count": st["count"],
            "data_split": "train",
            "start": 0,
            "ordinals": n,
            "shards": -(-n // size),
            "shard_size": size,
            "segments_cache": True,
            "conditions": conds,
            "runs": runs,
            "imm": proto["imm"],
            "ekf": proto["ekf"],
            "checkpoints": proto["checkpoints"],
            "interval_scale": proto["interval_scale"],
            "decomp": {**decomp, "split": split},
        }
        out = ROOT / f"configs/headroom/gd-{a.stage}-{split}.json"
        out.write_text(json.dumps(plan, indent=2) + "\n")
        print(out.relative_to(ROOT), len(runs), "runs", conds)


if __name__ == "__main__":
    main()
