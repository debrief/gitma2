"""Spec 039: write the scoring plans of a stage, one per split.

    uv run python scripts/research/pic_plan.py dev     # the read-out's variants, seed 370
    uv run python scripts/research/pic_plan.py test    # the bound variant only

Plans go to configs/headroom/pic-<stage>-<split>.json; push `headroom/pic-<stage>-<split>` to run
one. Settings come from configs/pic/protocol.json; checkpoints and splits from spec 038's
protocol (configs/gd/protocol.json).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FT = ["ft-s1", "ft-s2", "ft-s3"]
REG = ["reg-s1", "reg-s2", "reg-s3"]
EDIT = {"wild": True}


def prof(
    name: str, settings: dict[str, Any], seg: str | None = None, edit: bool = False
) -> dict[str, Any]:
    r: dict[str, Any] = {"kind": "profile", "name": name, "profile": settings}
    if seg:
        r["segmentation"] = seg
    if edit:
        r["edit"] = EDIT
    return r


def runs_for(proto: dict[str, Any], stage: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_p = {"prior": proto["prior"], "grid": proto["grid"]}
    runs: list[dict[str, Any]] = [
        {"kind": "nominal", "segmentation": "c2", "name": "c2", "dump": True},
        {"kind": "robust", "segmentation": "c2", "name": "c2-robust"},
        {"kind": "robust", "name": "robust-true"},
        {"kind": "nominal", "name": "plain-true"},
        {"kind": "robust", "segmentation": "c2", "name": "c2-edit", "edit": EDIT},
    ]
    if stage == "dev2":  # the cut time-late control beside the plain systems (part 3)
        runs = [r for r in runs if r["name"] != "c2-edit"] + [{"kind": "cut", "name": "cut-ctl"}]
        pairs = [
            ["c2-robust", "fine_tuned"], ["robust-true", "fine_tuned"], ["cut-ctl", "fine_tuned"],
            ["c2-robust", "cut-ctl"], ["cut-ctl", "robust-true"], ["c2-robust", "robust-true"],
        ]  # fmt: skip
        return runs, {
            "comparator": "c2-robust",
            "regressors": FT,
            "unchanged": REG,
            "hardened": ["cut-ctl"],
            "true": "robust-true",
            "segments": "c2",
            "pairs": pairs,
        }
    if stage == "dev":
        variants = {"": {}, "-t": {"temper": "effective"}}
        true_names, c2_names = [], []
        for tag, extra in variants.items():
            runs.append(prof(f"true-prior{tag}", {**base_p, **extra}))
            runs.append(prof(f"c2-prior{tag}", {**base_p, **extra}, "c2"))
            true_names.append(f"true-prior{tag}")
            c2_names.append(f"c2-prior{tag}")
        runs.append(prof("true-flat", {**base_p, "flat": True}))
        runs.append(prof("c2-edit-prior-t", {**base_p, "temper": "effective"}, "c2", True))
        true_names.append("true-flat")
        c2_names.append("c2-edit-prior-t")
    else:
        ch = proto["chosen"]
        if not ch:
            raise SystemExit("configs/pic/protocol.json: 'chosen' is not set")
        p = {**base_p, **ch["profile"]}
        runs += [
            prof("true-prior", p),
            prof("c2-prior", p, "c2"),
            {"kind": "cut", "name": "cut-ctl"},
        ]
        true_names, c2_names = ["true-prior"], ["c2-prior", "cut-ctl"]
    pairs = [
        ["robust-true", "fine_tuned"],
        ["c2-robust", "fine_tuned"],
        ["c2-robust", "robust-true"],
    ]
    for n in true_names:
        pairs += [[n, "fine_tuned"], ["robust-true", n]]
    for n in c2_names:
        pairs += [[n, "fine_tuned"], ["c2-robust", n], [n, "robust-true"]]
    names = {r["name"] for r in runs}
    shares = [
        {"name": f"{n} removes of robust-true to fine-tuned", "num": ["robust-true", n],
         "den": ["robust-true", "fine_tuned"]}
        for n in true_names
    ] + [
        {"name": f"{n} closes of c2-robust to fine-tuned", "num": ["c2-robust", n],
         "den": ["c2-robust", "fine_tuned"]}
        for n in c2_names
    ] + [
        {"name": f"{n} closes of c2-robust to robust-true", "num": ["c2-robust", n],
         "den": ["c2-robust", "robust-true"]}
        for n in c2_names
    ]  # fmt: skip
    decomp = {
        "shares": shares,
        "comparator": "c2-robust",
        "regressors": FT,
        "unchanged": REG,
        "hardened": ["c2-edit", *c2_names, *true_names],
        "true": "robust-true",
        "segments": "c2",
        "pairs": pairs,
    }
    assert set(decomp["hardened"]) <= names and decomp["true"] in names
    assert all(c in names and (y in names or y == "fine_tuned") for c, y in pairs)
    return runs, decomp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("dev", "dev2", "test"))
    a = ap.parse_args()
    proto = json.loads((ROOT / "configs/pic/protocol.json").read_text())
    gd = json.loads((ROOT / "configs/gd/protocol.json").read_text())
    st = proto["stages"][a.stage]
    runs, decomp = runs_for(proto, a.stage)
    n, size = int(st["ordinals"]), int(proto["shard_size"])
    cks = [c for c in gd["checkpoints"] if c["name"] in FT + REG]
    for split, conds in st["splits"].items():
        plan = {
            "description": f"Spec 039 {a.stage}, split '{split}': seed {st['seed']}, the first {n} "
            "sigma = 1 deg engagements per condition. Written by scripts/research/pic_plan.py "
            "from configs/pic/protocol.json.",
            "stage": a.stage,
            "plan": gd["gate_h_plan"],
            "conditions_file": gd["conditions_file"],
            "ranges": gd["splits"][split]["ranges"],
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
            "imm": gd["imm"],
            "ekf": gd["ekf"],
            "checkpoints": cks,
            "interval_scale": gd["interval_scale"],
            "decomp": {**decomp, "split": split},
        }
        out = ROOT / f"configs/headroom/pic-{a.stage}-{split}.json"
        out.write_text(json.dumps(plan, indent=2) + "\n")
        print(out.relative_to(ROOT), len(runs), "runs", conds)


if __name__ == "__main__":
    main()
