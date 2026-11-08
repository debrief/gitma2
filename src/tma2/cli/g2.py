"""tma2-g2: Gate 2 scoring and gate (spec 007 FR-030–FR-033, T023; contracts/cli.md).

    uv run tma2-g2 --truth <split.f32pack> --start S --count N --c <C.ndjson>
        --e NAME=<pred.ndjson>... --imm <id> --ekf <id> --glr-confirm <dir>:<cfg>
        --naive-train <split>[:a:c] [--detectability] --experiment <dir>
        [--decision <decision.json> --plan <plan.json> --split validation|test --model NAME]

**Scoring** is ``tma2-gs``'s, with E's prediction files as estimators (``--predictions``) beside C
and every physics-layer solve at the decision's knot cap: ``metrics.json``, ``report.md``,
``inputs.json`` and ``errors.npz``.

**With a decision**, the inputs are checked first (FR-033): the plan's digest; the truth's (the
decision's validation digest, or ``test-digest.json`` beside the decision for the test split);
C's segmentation (parameter and code digests, clean tree); each prediction (data, C, plan and
code digests, clean tree). Provenance is read before anything is written.
* ``--split validation`` adds ``validation.json``: each E's G2-a…G2-d points and intervals and
  the validation rule (FR-032), and the shuffled rule for a plan model marked ``shuffled``.
* ``--split test`` is the gate: ``--model`` names the carried E, whose weights digest must be
  ``carried.json``'s (an amendment beside the decision, with the shuffled rule's outcome); it
  writes ``verdict.json`` (a ``Gate2Record`` with the details) and ``manifest.json``, and exits
  3 unless G2-a…G2-d all pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

COLS = ("range", "course_deg", "speed_kt")


def _iv(d: dict[str, float] | None) -> Any:
    from tma2.segment.gate import Interval

    if d is None:
        return Interval(math.nan, math.nan, math.nan)
    return Interval(float(d.get("value", d.get("ratio", math.nan))), float(d["lo"]), float(d["hi"]))


def criteria(rec: dict[str, Any], decision: Any, shuffled: str) -> dict[str, Any]:
    """G2-a…G2-d for one E estimator's metrics record."""
    from tma2.gate2 import gate
    from tma2.segment.gate import all_of

    vs_imm = {c: _iv(rec["vs_imm"].get(c)) for c in ("range", "course_deg")}
    vs_one = {c: _iv(rec["vs_one_leg_settled"].get(c)) for c in COLS}
    gap = _iv(rec["gap_recovered"]["range"])
    minus_c = _iv(rec.get("gap_minus", {}).get("C", {}).get("range"))
    out: dict[str, Any] = {
        "g2a": gate.g2a(vs_imm, decision.g2a_limit),
        "g2b": gate.g2b(vs_one, decision.g2b_limit),
        "g2c": gate.g2c(gap, decision.g2c_limit),
        "g2d": gate.g2d(minus_c, shuffled),
        "intervals": {
            "g2a": {c: v.__dict__ for c, v in vs_imm.items()},
            "g2b": {c: v.__dict__ for c, v in vs_one.items()},
            "g2c": gap.__dict__,
            "g2d": minus_c.__dict__,
        },
    }
    out["overall"] = all_of([out[k] for k in ("g2a", "g2b", "g2c", "g2d")])
    points = {
        "g2a_range": vs_imm["range"].value,
        "g2a_course": vs_imm["course_deg"].value,
        **{f"g2b_{c}": v.value for c, v in vs_one.items()},
        "g2c": gap.value,
        "g2d": minus_c.value,
    }
    limits = {
        "g2a_range": ("below", decision.g2a_limit),
        "g2a_course": ("below", decision.g2a_limit),
        **{f"g2b_{c}": ("below", decision.g2b_limit) for c in COLS},
        "g2c": ("above", decision.g2c_limit),
        "g2d": ("above", 0.0),
    }
    out["validation_rule"] = gate.validation_rule(points, limits)
    out["points"] = points
    return out


def _preflight(a: argparse.Namespace) -> dict[str, Any] | None:
    """Every refusal at once (FR-033); None after printing them."""
    from tma2.cli import gs
    from tma2.gate2.gate import RefusedError, check_segmentation
    from tma2.segment.gate import sha256_file
    from tma2.types.generated.tma import Gate2Decision

    bad: list[str] = []
    dpath = Path(a.decision)
    decision = Gate2Decision.model_validate_json(dpath.read_text())
    plan_raw = Path(a.plan).read_bytes()
    plan_sha = hashlib.sha256(plan_raw).hexdigest()
    plan = json.loads(plan_raw)
    if plan_sha != decision.plan_digest:
        bad.append(f"{a.plan}: not the decision's plan")
    if (decision.bootstrap_level, decision.bootstrap_resamples) != (gs.LEVEL, gs.RESAMPLES):
        bad.append("the scorer's bootstrap is not the decision's")
    truth_sha = sha256_file(a.truth)
    want = decision.validation_digest
    if a.split == "test":
        td = dpath.parent / "test-digest.json"
        want = json.loads(td.read_text())["dataset_digest"] if td.exists() else ""
        if not want:
            bad.append("test-digest.json (the test split's digest) is not beside the decision")
    if truth_sha != want:
        bad.append(f"{a.truth}: not the decision's {a.split} split")
    c_header, _ = gs.read_segmentations(a.c)
    try:
        check_segmentation(
            c_header, truth_sha, decision.c_parameters_sha256, decision.c_code_sha256
        )
    except RefusedError as err:
        bad.append(str(err))
    carried = None
    if a.split == "test":
        cp = dpath.parent / "carried.json"
        if not cp.exists():
            bad.append("carried.json is not beside the decision")
        else:
            carried = json.loads(cp.read_text())
            if a.model != carried.get("model"):
                bad.append(f"--model {a.model} is not the carried {carried.get('model')}")
    names = []
    for spec in a.e:
        name, _, path = spec.partition("=")
        names.append(name)
        with open(path, encoding="utf-8") as f:
            h = json.loads(f.readline())
        for key, v in (
            ("dataset_digest", truth_sha),
            ("parameters_sha256", decision.c_parameters_sha256),
            ("code_sha256", decision.c_code_sha256),
            ("plan_sha256", plan_sha),
        ):
            if h.get(key) != v:
                bad.append(f"{name}: {key} is not the decision's")
        if h.get("git_dirty") is not False:
            bad.append(f"{name}: made from a dirty tree")
        if h.get("model") not in plan.get("models", {}):
            bad.append(f"{name}: model {h.get('model')} is not in the plan")
        if carried is not None and name == a.model:
            if h.get("weights_sha256") != carried.get("weights_sha256"):
                bad.append(f"{name}: weights are not the carried weights")
    if a.split == "test" and a.model not in names:
        bad.append(f"the carried {a.model} has no prediction file (--e {a.model}=...)")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return None
    return {
        "decision": decision,
        "decision_sha256": sha256_file(dpath),
        "plan": plan,
        "plan_sha256": plan_sha,
        "truth_sha256": truth_sha,
        "carried": carried,
        "c_header": c_header,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g2", description=__doc__)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--c", required=True, help="C's segmentation file")
    ap.add_argument("--e", nargs="*", default=[], metavar="NAME=PATH")
    ap.add_argument("--imm", required=True)
    ap.add_argument("--ekf")
    ap.add_argument("--glr-confirm", metavar="WORK:CONFIG")
    ap.add_argument("--naive-train", metavar="PATH[:START:COUNT]")
    ap.add_argument("--detectability", action="store_true")
    ap.add_argument("--knots", type=int, default=12)
    ap.add_argument("--reuse", help="spec 008: an earlier scoring's errors.npz (tma2-gs --reuse)")
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--decision")
    ap.add_argument("--plan")
    ap.add_argument("--split", choices=["validation", "test"])
    ap.add_argument("--model", help="test: the carried E")
    a = ap.parse_args(argv)

    from tma2.cli import gs
    from tma2.data.provenance import read_git_provenance

    gi = None
    if a.decision:
        if not (a.plan and a.split):
            print("--decision needs --plan and --split", file=sys.stderr)
            return 2
        gi = _preflight(a)
        if gi is None:
            return 2
        a.knots = gi["decision"].knots
        gi["git"] = read_git_provenance()  # before anything is written
    args = ["--truth", a.truth, "--start", str(a.start), "--count", str(a.count)]
    args += ["--segmentations", f"C={a.c}", "--predictions", *a.e, "--knots", str(a.knots)]
    args += ["--imm", a.imm, "--experiment", a.experiment]
    for flag, v in (("--ekf", a.ekf), ("--glr-confirm", a.glr_confirm)):
        if v:
            args += [flag, v]
    if a.naive_train:
        args += ["--naive-train", a.naive_train]
    if a.detectability:
        args.append("--detectability")
    if a.reuse:
        args += ["--reuse", a.reuse]
    rc = gs.main(args)
    if rc != 0 or gi is None:
        return rc
    return _decide(a, gi)


def _decide(a: argparse.Namespace, gi: dict[str, Any]) -> int:
    from tma2.gate2 import gate
    from tma2.segment.gate import amendments, sha256_file
    from tma2.types.generated.tma import Gate2Record, Gate2Verdicts, Split

    out = Path(a.experiment)
    d = gi["decision"]
    metrics = json.loads((out / "metrics.json").read_text())
    segs = metrics["segmenters"]
    names = [s.partition("=")[0] for s in a.e]
    models = gi["plan"]["models"]
    if a.split == "validation":
        res: dict[str, Any] = {"decision_sha256": gi["decision_sha256"], "estimators": {}}
        for n in names:
            c = criteria(segs[n], d, gate.PASS)
            if models.get(n, {}).get("shuffled"):
                c["shuffled_rule"] = gate.shuffled_rule(_iv(segs[n]["gap_minus"]["C"]["range"]))
            res["estimators"][n] = c
        (out / "validation.json").write_text(json.dumps(res, indent=2) + "\n")
        print(json.dumps({n: v["validation_rule"] for n, v in res["estimators"].items()}))
        return 0
    carried = gi["carried"]
    shuffled = str(carried.get("shuffled_rule", gate.FAIL))
    c = criteria(segs[a.model], d, shuffled)
    metrics_sha = sha256_file(out / "metrics.json")
    pred_headers = {}
    for spec in a.e:
        name, _, path = spec.partition("=")
        with open(path, encoding="utf-8") as f:
            pred_headers[name] = json.loads(f.readline())
    rec = Gate2Record(
        decision_sha256=gi["decision_sha256"],
        split=Split(a.split),
        seed=d.test_seed,
        dataset_digest=gi["truth_sha256"],
        model=a.model,
        weights_sha256=pred_headers[a.model]["weights_sha256"],
        metrics_sha256=metrics_sha,
        shuffled_rule=shuffled,
        verdicts=Gate2Verdicts(
            g2a=c["g2a"], g2b=c["g2b"], g2c=c["g2c"], g2d=c["g2d"], overall=c["overall"]
        ),
    )
    detail = {
        "record": json.loads(rec.model_dump_json(exclude_none=True)),
        "intervals": c["intervals"],
        "limits": {"g2a": d.g2a_limit, "g2b": d.g2b_limit, "g2c": d.g2c_limit, "g2d": 0.0},
        "others": {n: criteria(segs[n], d, shuffled) for n in names if n != a.model},
    }
    (out / "verdict.json").write_text(json.dumps(detail, indent=2) + "\n")
    gp = gi["git"]
    manifest = {
        "decision": a.decision,
        "decision_sha256": gi["decision_sha256"],
        "plan": a.plan,
        "plan_sha256": gi["plan_sha256"],
        "truth": a.truth,
        "truth_sha256": gi["truth_sha256"],
        "c": {
            k: gi["c_header"].get(k)
            for k in ("segmenter_sha256", "code_sha256", "git_commit", "dataset_digest")
        },
        "predictions": {
            n: {
                k: h.get(k)
                for k in ("model", "weights_sha256", "plan_sha256", "code_sha256", "git_commit")
            }
            for n, h in pred_headers.items()
        },
        "carried": carried,
        "amendments": amendments(Path(a.decision).parent),
        "inputs": json.loads((out / "inputs.json").read_text()),
        "metrics_sha256": metrics_sha,
        "git_commit": gp.commit,
        "git_dirty": gp.dirty,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: c[k] for k in ("g2a", "g2b", "g2c", "g2d", "overall")}))
    return 0 if c["overall"] == gate.PASS else 3


if __name__ == "__main__":
    raise SystemExit(main())
