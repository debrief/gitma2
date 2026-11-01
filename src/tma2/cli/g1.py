"""``tma2-g1``: Gate 1 on the constant-velocity test split (spec 003 FR-020, FR-021).

    tma2-g1 --decision experiments/<id>/decision.json --plan configs/gate1/plan.json
            --carried <model id> --model-meta <checkpoint meta.json>
            --test <test.f32pack> --model <pred.ndjson> --least-squares <pred.ndjson>
            [--naive p] [--ekf p] [--imm p] [--oracle p] --experiment experiments/<id>

Before scoring it refuses: a plan whose SHA-256 is not the decision's, or that names another
decision; a carried model the decision does not list; a test split whose seed or count is not
the decision's; a decision record not committed before every training job of the carried model
(its first commit must be an ancestor of each job's commit); and prediction files bound to
another split, or a model file from another estimator. Exit 3: the gate did not pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from tma2.data.f32pack import iter_pack_raw, read_pack_header
from tma2.eval.errors import Truth
from tma2.eval.experiment import Check, Experiment
from tma2.eval.g1 import Gate1Result, gate_rows, gate_timestamps, load_gate_rows, score
from tma2.eval.predictions import check_bound
from tma2.models.train import load_plan
from tma2.references.crb import crb_rows
from tma2.types import RecordError, dump_record, parse_record
from tma2.types.generated.tma import CheckpointMeta, Gate1Decision


class RefusedError(Exception):
    pass


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def decision_commit(path: Path) -> str:
    """The commit that first added the decision record."""
    out = _git("log", "--diff-filter=A", "--format=%H", "--", str(path)).split()
    if not out:
        raise RefusedError(f"{path} is not committed")
    return out[-1]


def check_inputs(a: argparse.Namespace) -> tuple[Gate1Decision, CheckpointMeta]:
    dec_path = Path(a.decision)
    decision = parse_record(Gate1Decision, json.loads(dec_path.read_text()), str(dec_path), 1)
    plan, plan_digest = load_plan(a.plan)
    if plan_digest != decision.plan_digest:
        raise RefusedError(
            f"plan digest {plan_digest} is not the decision's {decision.plan_digest}"
        )
    if Path(plan.decision) != dec_path:
        raise RefusedError(f"the plan names decision {plan.decision}, not {dec_path}")
    if a.carried not in decision.carried_models:
        raise RefusedError(f"{a.carried} is not a carried model of the decision")
    meta = parse_record(CheckpointMeta, json.loads(Path(a.model_meta).read_text()), a.model_meta, 1)
    if meta.model_id != a.carried or meta.plan_digest != plan_digest or not meta.complete:
        raise RefusedError(f"{a.model_meta}: not the complete {a.carried} of this plan")
    first = decision_commit(dec_path)
    if not meta.jobs:
        raise RefusedError(
            f"{a.model_meta}: no job records, so training ancestry cannot be checked"
        )
    for job in meta.jobs:
        try:
            _git("merge-base", "--is-ancestor", first, job.git_commit)
        except subprocess.CalledProcessError as e:
            raise RefusedError(
                f"decision commit {first[:7]} is not an ancestor of training commit "
                f"{job.git_commit[:7]}"
            ) from e
    header = read_pack_header(a.test)
    if header.split != "test" or str(header.dataset_seed) != str(decision.test_seed):
        raise RefusedError(
            f"{a.test}: split {header.split} seed {header.dataset_seed}, not test seed "
            f"{decision.test_seed}"
        )
    created = shlex.split(header.created_by or "")
    count = created[created.index("--count") + 1] if "--count" in created[:-1] else None
    if count != str(decision.test_count):
        raise RefusedError(f"{a.test}: not generated with --count {decision.test_count}")
    for name in ("model", "least_squares", "naive", "ekf", "imm", "oracle"):
        p = getattr(a, name)
        if p:
            h = check_bound(p, a.test)
            if name == "model" and h.estimator != a.carried:
                raise RefusedError(f"{p}: estimator {h.estimator}, not {a.carried}")
    return decision, meta


def load_truths(test: str) -> tuple[list[Truth], dict[tuple[int, int], Any], Any]:
    truths = []
    bounds: dict[tuple[int, int], Any] = {}
    for _, m, own, tgt, obs in iter_pack_raw(test):
        t = Truth.from_block(m, own, tgt)
        truths.append(t)
        ks = sorted({g.k for metric in ("range_rel", "speed_kt") for g in gate_rows([t], metric)})
        if ks:
            sigma = float(m["parameters"]["noise_sigma_rad"])
            rows = crb_rows(own, tgt, obs, sigma, int(m["zig_index"]), None, ks, "full_window")
            for k, b in zip(ks, rows, strict=True):
                bounds[(t.index, k)] = b
    return truths, bounds, read_pack_header(test)


def record(exp: Experiment, res: Gate1Result, level: float) -> None:
    for c in res.checks:
        exp.checks.append(
            Check(
                c.name,
                c.result,
                f"{c.rows} rows" + (f"; {c.detail}" if c.detail else ""),
                value=c.value,
                threshold=c.limit,
                ci_low=c.lo,
                ci_high=c.hi,
                ci_level=level,
            )
        )
    exp.metrics = {"reported": res.reported, "result": res.result}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g1")
    ap.add_argument("--decision", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--carried", required=True)
    ap.add_argument("--model-meta", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--least-squares", dest="least_squares", required=True)
    for name in ("naive", "ekf", "imm", "oracle"):
        ap.add_argument(f"--{name}")
    ap.add_argument("--experiment", required=True)
    a = ap.parse_args(argv)
    try:
        decision, meta = check_inputs(a)
    except (RefusedError, RecordError, OSError, ValueError) as e:
        print(f"tma2-g1: refused: {e}", file=sys.stderr)
        return 2
    folder = Path(a.experiment)
    exp = Experiment(id=folder.name, folder=folder)
    exp.command_lines.append("tma2-g1 " + " ".join(sys.argv[1:] if argv is None else argv))
    truths, bounds, header = load_truths(a.test)
    wanted = gate_timestamps(truths)
    exp.add_dataset(a.test, dump_record(header))
    exp.add_artefact(a.decision, "decision")
    exp.add_artefact(a.plan, "plan")
    exp.add_artefact(a.model_meta, "carried model checkpoint meta")
    preds = {}
    for name in ("model", "least_squares", "naive", "ekf", "imm", "oracle"):
        p = getattr(a, name)
        if p:
            exp.add_artefact(p, f"predictions: {name}")
            preds[name] = load_gate_rows(p, wanted)
    exp.add_estimator(a.carried, {"plan_digest": decision.plan_digest, "role": "carried"})
    exp.add_estimator("imm", json.loads(decision.imm))
    exp.add_estimator("ekf", json.loads(decision.ekf))
    others = {k: v for k, v in preds.items() if k not in ("model", "least_squares")}
    res = score(
        truths,
        preds["model"],
        preds["least_squares"],
        bounds,
        others,
        decision.bootstrap_level,
        decision.bootstrap_resamples,
    )
    record(exp, res, decision.bootstrap_level)
    exp.metrics["decision_sha256"] = hashlib.sha256(Path(a.decision).read_bytes()).hexdigest()
    exp.metrics["training_commits"] = sorted({j.git_commit for j in meta.jobs or []})
    verdict = exp.write("G1")
    print(json.dumps({"result": verdict["result"], "checks": verdict["checks"]}, indent=2))
    return 0 if verdict["result"] == "pass" else 3


if __name__ == "__main__":
    raise SystemExit(main())
