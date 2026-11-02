"""Write a Gate D training plan (spec 004 T021/T022) from the validation split it names.

    uv run python scripts/make_detector_plan.py --preset gd --out configs/gate-d/plan.json
    uv run python scripts/make_detector_plan.py --preset bench --out configs/gate-d-bench/plan.json

``gd``: three seeds of each carried variant (causal, time-late; D2) and the classification-only
control (one seed), at the research R2–R5 defaults (``tma2.models.detector_config``), on training
stream 311 and validation seed 304. ``smoke``: two small detectors, two short epochs, to exercise the training workflow end to end
(train, detect, downstream, results branch). ``bench``: the causal configuration and the
classification-only
control for two epochs of 4,000 scenarios on the runner (T021; the second epoch has compiled
kernels).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tma2.data.f32pack import read_pack_header
from tma2.data.io import file_digest
from tma2.models.detector_config import detector_config
from tma2.types import dump_record
from tma2.types.generated.tma import DatasetRef, DetectorVariant, TrainingPlan

VALIDATION = "data/gd-val/validation.f32pack"
TRAIN_SEED = 311


def detectors(preset: str) -> list[Any]:
    if preset == "smoke":
        small = {"epochs": 2, "patience": 2, "batch_scenarios": 32}
        return [
            detector_config("smoke-causal", **small),
            detector_config("smoke-cls", loss_downstream_weight=0.0, **small),
        ]
    if preset == "bench":
        return [
            detector_config("bench-causal", epochs=2, patience=2),
            detector_config("bench-late", variant=DetectorVariant.time_late, epochs=2, patience=2),
            detector_config("bench-cls", loss_downstream_weight=0.0, epochs=2, patience=2),
        ]
    out = []
    for seed in (1, 2, 3):
        out.append(detector_config(f"gd-causal-s{seed}", seed=seed))
    for seed in (1, 2, 3):
        out.append(
            detector_config(f"gd-late-s{seed}", seed=seed, variant=DetectorVariant.time_late)
        )
    out.append(detector_config("gd-cls", seed=1, loss_downstream_weight=0.0))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=("gd", "bench", "smoke"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--validation", default=VALIDATION)
    ap.add_argument("--decision", default="none")
    a = ap.parse_args()
    header = read_pack_header(a.validation)
    bench = a.preset == "bench"
    smoke = a.preset == "smoke"
    plan = TrainingPlan(
        id="gd-bench" if bench else "gd-smoke" if smoke else "gd-a",
        ranges=header.parameter_ranges,
        train_seed=TRAIN_SEED,
        scenarios_per_epoch=4000 if bench else 500 if smoke else 50_000,
        validation=DatasetRef(path=a.validation, header=header, digest=file_digest(a.validation)),
        validation_scenarios=1000 if bench else 100 if smoke else 2000,
        detectors=detectors(a.preset),
        decision=a.decision,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump_record(plan), indent=2, sort_keys=True) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
