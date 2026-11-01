"""Write a Gate 1 training plan (spec 003 T017/T018) from the validation split it names.

    uv run python scripts/make_plan.py --preset gate1 --out configs/gate1/plan.json
    uv run python scripts/make_plan.py --preset smoke --out configs/gate1-smoke/plan.json

``gate1``: three seeds of the carried configuration and the controls (a) direct head, (c)
shuffled labels, (d) time-late, at the research R3/R4 defaults. ``smoke``: the workflow's end-to-end
check (research R7): two small models, two short epochs, so the chain, the resume and the
results branch are exercised in minutes and the runner's throughput is recorded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tma2.data.f32pack import read_pack_header
from tma2.data.io import file_digest
from tma2.models.config import model_config
from tma2.types import dump_record
from tma2.types.generated.tma import DatasetRef, PhysicsHead, TrainingPlan

VALIDATION = "data/g1-val/validation.f32pack"
TRAIN_SEED = 310


def models(preset: str) -> list[Any]:
    if preset == "smoke":
        small = {"epochs": 2, "patience": 2, "batch_scenarios": 32}
        return [
            model_config("smoke-physics", **small),
            model_config("smoke-direct", head=PhysicsHead.direct, **small),
        ]
    return [
        model_config("g1-physics-s1", seed=1),
        model_config("g1-physics-s2", seed=2),
        model_config("g1-physics-s3", seed=3),
        model_config("g1-direct", seed=1, head=PhysicsHead.direct),
        model_config("g1-shuffled", seed=1, shuffle_labels=True),
        model_config("g1-timelate", seed=1, causal=False),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=("gate1", "smoke"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--validation", default=VALIDATION)
    ap.add_argument("--decision", default="none")
    a = ap.parse_args()
    header = read_pack_header(a.validation)
    smoke = a.preset == "smoke"
    plan = TrainingPlan(
        id="g1-smoke" if smoke else "g1-a",
        ranges=header.parameter_ranges,
        train_seed=TRAIN_SEED,
        scenarios_per_epoch=1000 if smoke else 50_000,
        validation=DatasetRef(path=a.validation, header=header, digest=file_digest(a.validation)),
        validation_scenarios=200 if smoke else 2000,
        models=models(a.preset),
        decision=a.decision,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump_record(plan), indent=2, sort_keys=True) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
