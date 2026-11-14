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
REPAIR_FILES = (*STUDY_FILES, "match.py", "run3.py")  # spec 015
CONTROL_FILES = (*REPAIR_FILES, "corr.py", "hedge.py", "learned.py", "run4.py")  # spec 016
SHIFT_FILES = (*CONTROL_FILES, "detect.py", "run5.py")  # spec 017
ADAPT_FILES = (*CONTROL_FILES, "detect.py", "adapt.py", "run6.py")  # spec 018


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
    ap.add_argument(
        "--learned",
        action="append",
        default=[],
        metavar="NAME=SHARD",
        help="a tma2-tlpredict shard (without .npz) scored as NAME and NAME-arc (runner run4)",
    )
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
    run5 = plan.get("runner") == "run5"
    run6 = plan.get("runner") == "run6"
    run4 = plan.get("runner") == "run4" or run5 or run6
    run3 = plan.get("runner") == "run3"
    run2 = plan.get("runner") == "run2" or run3
    if run4 and plan["splits"][a.split].get("systems"):  # a split's own controls
        plan["settings"]["systems"] = list(plan["splits"][a.split]["systems"])
    if a.thin:
        plan["settings"]["thinning"] = a.thin
    if a.systems:
        plan["settings"]["systems"] = a.systems.split(",")
    extra: dict[str, Any] = {}
    if run4:
        from tma2.timelate.run4 import run_shard4

        priors = {
            "v3": ManoeuvrePrior.from_ranges(json.loads(Path(plan["prior"]).read_text()), 3),
            "broad": ManoeuvrePrior.from_ranges(
                json.loads(Path(plan["prior_broad"]).read_text()), 3
            ),
        }
        shards = dict(x.split("=", 1) for x in a.learned)
        learned = {k: dict(np.load(f"{v}.npz")) for k, v in shards.items()}
        if run5:
            from tma2.timelate.run5 import run_shard5

            if imm is None or ekf is None or learned:
                raise SystemExit("runner run5 needs the plan's IMM and EKF and takes no --learned")
            sp = plan["splits"][a.split]
            priors["true"] = ManoeuvrePrior.from_ranges(
                json.loads(Path(sp["ranges"]).read_text()), 3
            )
            settings = {**plan["settings"], "edited_reference": bool(sp.get("edited_reference"))}
            arrays, recs = run_shard5(periods, priors, c_params, c2, settings, imm, ekf)
        elif run6:
            from tma2.timelate.adapt import rate_grid
            from tma2.timelate.run6 import run_shard6

            if learned:
                raise SystemExit("runner run6 takes no --learned")
            sp = plan["splits"][a.split]
            if not sp.get("no_true"):  # a quiet split's own statistics allow no manoeuvre
                priors["true"] = ManoeuvrePrior.from_ranges(
                    json.loads(Path(sp["ranges"]).read_text()), 3
                )
            ad = plan["adaptive"]
            priors.update(
                rate_grid(
                    priors["broad"],
                    [float(x) for x in ad["leg_means_s"]],
                    float(ad["leg_sd_ratio"]),
                )
            )
            settings = {**plan["settings"], "rate_weights": ad.get("rate_weights") or {}}
            arrays, recs = run_shard6(periods, priors, c_params, c2, settings)
        else:
            arrays, recs = run_shard4(periods, priors, c_params, c2, plan["settings"], learned)
        extra_learned = {
            k: json.loads(Path(f"{v}.json").read_text())["header"] for k, v in shards.items()
        }
        extra = {
            "runner": "run6" if run6 else ("run5" if run5 else "run4"),
            "prior_kinds": canonical_json(
                {"v3": [3, plan["prior"]], "broad": [3, sha256_file(plan["prior_broad"])]}
            ),
            "thinning": "none",
            "condition": str(plan["splits"][a.split].get("condition", "clean")),
        }
    elif run3:
        from tma2.timelate.run3 import run_shard3

        ranges = json.loads(Path(plan["prior"]).read_text())
        kinds = {
            "v2": (2, "annex-b"),
            "v3": (3, "annex-b"),
            "flat3": (3, "flat"),
            "mix3": (3, "mix"),
        }
        priors = {k: ManoeuvrePrior.from_ranges(ranges, *vk) for k, vk in kinds.items()}
        arrays, recs = run_shard3(periods, priors, c_params, c2, plan["settings"])
        extra = {
            "runner": "run3",
            "prior_kinds": canonical_json({k: list(vk) for k, vk in kinds.items()}),
            "thinning": "none",
            "condition": str(plan["splits"][a.split].get("condition", "clean")),
        }
    elif run2:
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
        search_code_sha256=search_code_digest(
            (ADAPT_FILES if run6 else (SHIFT_FILES if run5 else CONTROL_FILES))
            if run4
            else (REPAIR_FILES if run3 else (STUDY_FILES if run2 else ()))
        ),
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
    doc: dict[str, Any] = {"header": header.model_dump(mode="json"), "periods": recs}
    if run4 and a.learned:
        doc["learned"] = extra_learned
    Path(f"{out}.json").write_text(json.dumps(doc) + "\n")
    print(f"{len(periods)} periods, {arrays['period'].size} scored rows -> {out}.npz, {out}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
