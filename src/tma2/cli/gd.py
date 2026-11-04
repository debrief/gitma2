"""``tma2-gd``: Gate D, or its validation report (spec 004 FR-029–FR-031; contracts/cli.md).

    tma2-gd --decision experiments/<id>/decision.json --plan configs/gate-d/plan.json
            --split test|validation --truth <split.f32pack>
            --variant <id>=<meta.json>,<detector.ndjson>,<downstream.ndjson>  (one per variant)
            --control cusum=<rows.ndjson> --control glr=<rows.ndjson> [--control imm_mode=…]
            --least-squares p --imm p [--ekf p] [--naive p] --oracle p
            [--amendment path]… --experiment experiments/<id>

It refuses: a plan whose SHA-256 is not the decision's, or that names another decision; a variant
the decision does not carry; a checkpoint that is not the complete one of this plan, or trained
from a commit the decision's first commit does not precede; on ``test``, a split whose seed or
count is not the decision's (``validation``: not the decision's validation seed); a detector or
downstream file bound to another split, another detector or other weights; a control file bound
to another split, or whose settings are in no amendment given; reference predictions bound to
another split, or an IMM/EKF other than the decision's frozen settings.

``test`` writes Gate D's verdict (a variant passes when all its gated checks pass; the gate when a
variant passes); exit 3 when it did not pass. ``validation`` applies Annex A §A.5's validation
rule per variant and writes which variants are carried; exit 3 when none is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any

import numpy as np

from tma2.cli.g1 import RefusedError, _git, decision_commit
from tma2.data.canonical import canonical_json
from tma2.data.f32pack import iter_pack_raw, read_pack_header
from tma2.data.io import AtomicFile, file_digest
from tma2.detect.downstream import read_detector_file
from tma2.detect.matching import ScenarioDetection, score_scenario, summary
from tma2.eval.errors import Truth
from tma2.eval.experiment import Check, Experiment
from tma2.eval.gd import (
    GATED,
    METRICS,
    downstream_rows,
    g5_rows,
    gate_result,
    validation_carries,
    variant_checks,
    variant_result,
)
from tma2.eval.predictions import check_bound, iter_predictions_raw
from tma2.eval.rows import G5_SLICE_SIGMA_RAD
from tma2.eval.stats import ascending, percentile
from tma2.kinds import KIND_CODES, kind_name
from tma2.models.detector_labels import row_labels
from tma2.models.train import load_plan
from tma2.sim import scenario as sc_
from tma2.types import RecordError, dump_record, parse_record
from tma2.types.generated.tma import CheckpointMeta, GateDDecision

GATED_CONTROLS = ("cusum", "glr")


def _variant(spec: str) -> tuple[str, Path, Path, Path]:
    vid, _, rest = spec.partition("=")
    parts = rest.split(",")
    if not vid or len(parts) != 3:
        raise ValueError(f"--variant {spec}: expected <id>=<meta>,<detector>,<downstream>")
    return vid, Path(parts[0]), Path(parts[1]), Path(parts[2])


def _control(spec: str) -> tuple[str, str, str]:
    """``[<variant>:]<kind>=<path>`` → (variant or "", kind, path): a control tuned to one
    variant's false-alarm rate, or shared by every variant."""
    head, _, path = spec.partition("=")
    vid, _, kind = head.rpartition(":")
    if not kind or not path:
        raise ValueError(f"--control {spec}: expected [<variant>:]<kind>=<path>")
    return vid, kind, path


def _controls_for(
    vid: str, controls: dict[tuple[str, str], list[ScenarioDetection]]
) -> dict[str, list[ScenarioDetection]]:
    kinds = {k for _, k in controls}
    return {
        k: controls[(vid, k)] if (vid, k) in controls else controls[("", k)]
        for k in kinds
        if (vid, k) in controls or ("", k) in controls
    }


def _sigma1(meta: dict[str, Any]) -> bool:
    return abs(float(meta["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) <= 1e-6


def check_inputs(a: argparse.Namespace) -> tuple[GateDDecision, dict[str, CheckpointMeta]]:
    dec_path = Path(a.decision)
    decision = parse_record(GateDDecision, json.loads(dec_path.read_text()), str(dec_path), 1)
    plan, plan_digest = load_plan(a.plan)
    if plan_digest != decision.plan_digest:
        raise RefusedError(
            f"plan digest {plan_digest} is not the decision's {decision.plan_digest}"
        )
    if Path(plan.decision) != dec_path:
        raise RefusedError(f"the plan names decision {plan.decision}, not {dec_path}")
    header = read_pack_header(a.truth)
    if a.split == "test":
        if header.split != "test" or str(header.dataset_seed) != str(decision.test_seed):
            raise RefusedError(
                f"{a.truth}: split {header.split} seed {header.dataset_seed}, not test seed "
                f"{decision.test_seed}"
            )
        created = shlex.split(header.created_by or "")
        count = created[created.index("--count") + 1] if "--count" in created[:-1] else None
        if count != str(decision.test_count):
            raise RefusedError(f"{a.truth}: not generated with --count {decision.test_count}")
    elif header.split != "validation" or str(header.dataset_seed) != str(decision.validation_seed):
        raise RefusedError(
            f"{a.truth}: not the validation split of seed {decision.validation_seed}"
        )
    first = decision_commit(dec_path)
    metas: dict[str, CheckpointMeta] = {}
    for spec in a.variant:
        vid, meta_p, det_p, down_p = _variant(spec)
        if vid not in decision.carried_variants:
            raise RefusedError(f"{vid} is not a carried variant of the decision")
        meta = parse_record(CheckpointMeta, json.loads(meta_p.read_text()), str(meta_p), 1)
        if meta.model_id != vid or meta.plan_digest != plan_digest or not meta.complete:
            raise RefusedError(f"{meta_p}: not the complete {vid} of this plan")
        if not meta.jobs or not meta.weights_digest:
            raise RefusedError(f"{meta_p}: no job records or no weights digest")
        for job in meta.jobs:
            try:
                _git("merge-base", "--is-ancestor", first, job.git_commit)
            except Exception as e:  # noqa: BLE001
                raise RefusedError(
                    f"decision commit {first[:7]} is not an ancestor of training commit "
                    f"{job.git_commit[:7]}"
                ) from e
        dh, _ = read_detector_file(det_p)
        if dh.dataset_digest != file_digest(a.truth):
            raise RefusedError(f"{det_p}: bound to another split")
        if dh.detector != vid or dh.weights_digest != meta.weights_digest:
            raise RefusedError(f"{det_p}: detector {dh.detector} / weights not {vid}'s")
        if dh.knot_threshold != decision.knot_threshold:
            raise RefusedError(f"{det_p}: knot threshold {dh.knot_threshold}, not the decision's")
        ph = check_bound(down_p, a.truth)
        if ph.estimator != f"{vid}-downstream" or ph.weights_digest != meta.weights_digest:
            raise RefusedError(f"{down_p}: not {vid}'s downstream predictions")
        metas[vid] = meta
    allowed: list[dict[str, Any]] = []
    for am in a.amendment:
        body = json.loads(Path(am).read_text())
        allowed.extend(body.get("controls", []))
    for spec in a.control:
        _, kind, path = _control(spec)
        ch, _ = read_detector_file(path)
        if ch.dataset_digest != file_digest(a.truth):
            raise RefusedError(f"{path}: bound to another split")
        if ch.control is None or ch.control.kind != kind:
            raise RefusedError(f"{path}: not a {kind} control file")
        if dump_record(ch.control) not in allowed:
            raise RefusedError(f"{path}: control settings are in no amendment given")
    for name in ("least_squares", "imm", "ekf", "naive", "oracle"):
        p = getattr(a, name)
        if p:
            h = check_bound(p, a.truth)
            if name in ("imm", "ekf") and h.estimator != getattr(decision, name):
                raise RefusedError(f"{p}: {h.estimator}, not the frozen {getattr(decision, name)}")
    return decision, metas


def load_g5_predictions(path: str, wanted: dict[int, set[float]]) -> dict[int, dict[float, Any]]:
    out: dict[int, dict[float, Any]] = {}
    for _, p in iter_predictions_raw(path):
        idx = int(p["scenario_index"])
        keep = wanted.get(idx)
        if keep:
            out[idx] = {
                float(r["timestamp_s"]): r for r in p["rows"] if float(r["timestamp_s"]) in keep
            }
    return out


def score_detector_file(
    path: str | Path, metas: dict[int, dict[str, Any]], name: str, decision: GateDDecision
) -> list[ScenarioDetection]:
    _, recs = read_detector_file(path)
    out = []
    for rec in recs:
        meta = metas.get(int(rec["scenario_index"]))
        if meta is None:
            continue
        n = int(meta["samples"])
        spans = np.full((1, sc_.MAX_TM, 3), -1, dtype=np.int32)
        for j, s in enumerate(meta.get("manoeuvres") or []):
            spans[0, j] = (KIND_CODES[kind_name(s["kind"])], s["start_index"], s["end_index"])
        now = row_labels(spans, np.array([n]), np.array([float(meta["parameters"]["dt_s"])]), n)
        out.append(
            score_scenario(meta, rec, name, decision.threshold, decision.tolerance_s, now.now[0])
        )
    if len(out) != len(metas):
        raise RefusedError(f"{path}: {len(out)} σ = 1° scenarios, the split has {len(metas)}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-gd")
    ap.add_argument("--decision", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--split", choices=("test", "validation"), required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--variant", action="append", required=True)
    ap.add_argument("--control", action="append", required=True)
    ap.add_argument("--least-squares", dest="least_squares", required=True)
    ap.add_argument("--imm", required=True)
    ap.add_argument("--oracle", required=True)
    ap.add_argument("--ekf")
    ap.add_argument("--naive")
    ap.add_argument("--amendment", action="append", default=[])
    ap.add_argument("--experiment", required=True)
    a = ap.parse_args(argv)
    try:
        specs = [_control(c) for c in a.control]
        for v in a.variant:
            vid = _variant(v)[0]
            have = {k for cv, k, _ in specs if cv in ("", vid)}
            if not set(GATED_CONTROLS) <= have:
                raise RefusedError(f"{vid}: Gate D needs the cusum and glr controls")
        decision, metas = check_inputs(a)
    except (RefusedError, RecordError, OSError, ValueError) as e:
        print(f"tma2-gd: refused: {e}", file=sys.stderr)
        return 2
    folder = Path(a.experiment)
    exp = Experiment(id=folder.name, folder=folder)
    exp.command_lines.append("tma2-gd " + " ".join(sys.argv[1:] if argv is None else argv))
    exp.add_dataset(a.truth, dump_record(read_pack_header(a.truth)))
    exp.add_artefact(a.decision, "decision")
    exp.add_artefact(a.plan, "plan")
    for am in a.amendment:
        exp.add_amendment(am)
    truths: list[Truth] = []
    sigma1: dict[int, dict[str, Any]] = {}
    for _, m, own, tgt, _obs in iter_pack_raw(a.truth):
        t = Truth.from_block(m, own, tgt)
        truths.append(t)
        if _sigma1(m):
            sigma1[t.index] = m
    wanted: dict[int, set[float]] = {}
    for t, k, _ in g5_rows(truths):
        wanted.setdefault(t.index, set()).add(float(t.own[k, 0]))
    preds: dict[str, Any] = {}
    for name in ("least_squares", "imm", "ekf", "naive", "oracle"):
        p = getattr(a, name)
        if p:
            exp.add_artefact(p, f"predictions: {name}")
            preds[name] = load_g5_predictions(p, wanted)
    controls: dict[tuple[str, str], list[ScenarioDetection]] = {}
    for cv, kind, path in specs:
        exp.add_artefact(path, f"control: {cv + ':' if cv else ''}{kind}")
        controls[(cv, kind)] = score_detector_file(path, sigma1, kind, decision)
    variants: dict[str, Any] = {}
    reported: dict[str, Any] = {
        "controls": {(f"{cv}:{k}" if cv else k): summary(v) for (cv, k), v in controls.items()}
    }
    for spec in a.variant:
        vid, meta_p, det_p, down_p = _variant(spec)
        exp.add_artefact(meta_p, f"checkpoint meta: {vid}")
        exp.add_artefact(det_p, f"detector outputs: {vid}")
        exp.add_artefact(down_p, f"predictions: {vid}-downstream")
        exp.add_estimator(vid, {"weights_digest": metas[vid].weights_digest, "role": "carried"})
        preds[f"{vid}-downstream"] = load_g5_predictions(str(down_p), wanted)
        det = score_detector_file(det_p, sigma1, vid, decision)
        rows = downstream_rows(truths, preds)
        checks = variant_checks(
            det,
            {k: _controls_for(vid, controls)[k] for k in GATED_CONTROLS},
            rows,
            f"{vid}-downstream",
            decision.false_alarm_limit,
            decision.bootstrap_level,
            decision.bootstrap_resamples,
        )
        variants[vid] = checks
        reported[vid] = summary(det)
        _write_detections(folder / f"detections-{vid}.ndjson", det)
        for c in checks:
            exp.checks.append(
                Check(
                    f"{vid}:{c.name}",
                    c.result if c.name in GATED else "reported",
                    f"{c.n} n" + (f"; {c.detail}" if c.detail else ""),
                    value=c.value,
                    threshold=c.limit,
                    ci_low=c.lo,
                    ci_high=c.hi,
                    ci_level=decision.bootstrap_level,
                )
            )
    rows = downstream_rows(truths, preds)
    reported["downstream_medians"] = {
        name: {
            scope: {m: percentile(ascending(v[m][mask]), 0.5) for m in METRICS}
            for scope, mask in (("all", np.ones_like(rows.settled)), ("settled", rows.settled))
        }
        for name, v in rows.errors.items()
    }
    reported["held_leg_false_alarm_imm_mode"] = {
        (f"{cv}:{k}" if cv else k): summary(v)["held_leg_g5_false_alarm"]
        for (cv, k), v in controls.items()
        if k == "imm_mode"
    }
    per_variant = {vid: variant_result(c) for vid, c in variants.items()}
    if a.split == "test":
        exp.result = gate_result(variants)
        reported["variant_results"] = per_variant
    else:
        carried = [vid for vid, c in variants.items() if validation_carries(c)]
        reported["validation_carried"] = carried
        reported["variant_results"] = per_variant
        exp.result = "pass" if carried else "fail"
    exp.metrics = {"reported": reported, "split": a.split}
    exp.metrics["decision_sha256"] = hashlib.sha256(Path(a.decision).read_bytes()).hexdigest()
    verdict = exp.write("GD")
    print(json.dumps({"result": verdict["result"], "variants": per_variant}, indent=2))
    return 0 if verdict["result"] == "pass" else 3


def _write_detections(path: Path, scores: list[ScenarioDetection]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    f = AtomicFile(path)
    for sc in scores:
        f.write((canonical_json(dump_record(sc.record)) + "\n").encode("utf-8"))
    f.commit()


if __name__ == "__main__":
    raise SystemExit(main())
