"""``tma2-tlsolve``: one shard of Gate T's systems (spec 013): C″ read as a track, the evidence
search with its candidate tracks, and the true-history reference, on periods cut from the
given split. Writes ``<out>.npz`` (errors at the scored rows) and ``<out>.json`` (header and
one record per period)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SEARCH_FILES = (
    "arc.py",
    "bound.py",
    "periods.py",
    "points.py",
    "prior.py",
    "retest.py",
    "run.py",
    "score.py",
    "search.py",
    "systems.py",
    "track.py",
)


STUDY_FILES = (
    "controls.py",
    "counts.py",
    "run2.py",
    "smooth.py",
    "thin.py",
)  # spec 014's additions


def search_code_digest(extra: tuple[str, ...] = ()) -> str:
    """SHA-256 over the time-late modules, in name order (``extra``: spec 014's modules)."""
    root = Path(__file__).resolve().parents[1] / "timelate"
    h = hashlib.sha256()
    for name in sorted(SEARCH_FILES + extra):
        h.update(name.encode())
        h.update((root / name).read_bytes())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-tlsolve", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True, help="the split's f32pack")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--split", required=True, help="the plan's split name (for the header)")
    ap.add_argument("--start", type=int, default=0, help="first σ = 1° ordinal")
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", required=True, help="output prefix")
    ap.add_argument("--thin", help="spec 014: overrides the plan's settings.thinning")
    ap.add_argument("--systems", help="spec 014: overrides the plan's settings.systems")
    a = ap.parse_args(argv)
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()  # before any output
    import numpy as np
    import torch

    from tma2.cli.controls import parse_ekf_name
    from tma2.data.canonical import canonical_json
    from tma2.data.f32pack import read_pack_header
    from tma2.detect.controls import parse_imm_name
    from tma2.segment.gate import sha256_file
    from tma2.timelate.periods import iter_periods
    from tma2.timelate.prior import ManoeuvrePrior
    from tma2.timelate.run import run_shard
    from tma2.timelate.systems import c_parameters
    from tma2.types.generated.tma import RecordKind, TimeLateShardHeader
    from tma2.types.generated.version import SCHEMA_VERSION

    torch.set_default_dtype(torch.float64)
    plan = json.loads(Path(a.plan).read_text())
    if a.split not in plan["splits"]:
        raise SystemExit(f"split {a.split!r} is not in {a.plan}")
    prior = ManoeuvrePrior.from_ranges(json.loads(Path(plan["prior"]).read_text()))
    c_params, c2 = c_parameters(plan["gh_plan"])
    whole = bool(plan["splits"][a.split].get("whole", False))
    periods = list(iter_periods(a.inp, a.start, a.count, whole=whole))
    if not periods:
        raise SystemExit(f"no σ = 1° periods at {a.start} in {a.inp}")
    refs = plan.get("references") or {}
    imm = parse_imm_name(refs["imm"]) if refs.get("imm") else None
    ekf = parse_ekf_name(refs["ekf"]) if refs.get("ekf") else None
    run2 = plan.get("runner") == "run2"
    if a.thin:
        plan["settings"]["thinning"] = a.thin
    if a.systems:
        plan["settings"]["systems"] = a.systems.split(",")
    extra: dict[str, Any] = {}
    if run2:
        from tma2.timelate.run2 import run_shard2

        ranges = json.loads(Path(plan["prior"]).read_text())
        kinds = {"v1": (1, "annex-b"), "v2": (2, "annex-b"), "flat": (2, "flat"), "mix": (2, "mix")}
        priors = {k: ManoeuvrePrior.from_ranges(ranges, *vk) for k, vk in kinds.items()}
        arrays, recs = run_shard2(periods, priors, c_params, c2, plan["settings"], ekf)
        extra = {
            "runner": "run2",
            "prior_kinds": canonical_json({k: list(vk) for k, vk in kinds.items()}),
            "thinning": str(plan["settings"].get("thinning", "none")),
            "condition": str(plan["splits"][a.split].get("condition", "clean")),
        }
    else:
        arrays, recs = run_shard(periods, prior, c_params, c2, plan["settings"], imm, ekf)
    head = read_pack_header(a.inp)
    header = TimeLateShardHeader(
        record=RecordKind.header,
        schema_version=SCHEMA_VERSION,
        plan_sha256=sha256_file(a.plan),
        split=a.split,
        dataset_digest=sha256_file(a.inp),
        seed=int(head.dataset_seed),
        ordinal_start=a.start,
        ordinal_count=len(periods),
        c_code_sha256=str(c2.get("code_sha256", "")),
        search_code_sha256=search_code_digest(STUDY_FILES if run2 else ()),
        prior_sha256=sha256_file(plan["prior"]),
        settings=canonical_json(plan["settings"]),
        git_commit=g.commit,
        git_dirty=g.dirty,
        **extra,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = dict(arrays)
    np.savez_compressed(f"{out}.npz", **payload)
    Path(f"{out}.json").write_text(
        json.dumps({"header": header.model_dump(mode="json"), "periods": recs}) + "\n"
    )
    print(f"{len(periods)} periods, {arrays['period'].size} scored rows -> {out}.npz, {out}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
