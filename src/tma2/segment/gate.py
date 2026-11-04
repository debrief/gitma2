"""Gate S (spec 005 FR-071, T037): input checks, verdict rules and the manifest's amendments.

The decision record (``experiments/<date>-gs-decision/decision.json``, a ``GateSDecision``) fixes
the criteria. Everything here is pure, so the refusals and the pass / fail / inconclusive logic
are unit-tested without data (``tests/unit/test_gs_gate.py``).

* **Above zero** (S2, S4): pass if the point and the whole interval lie above zero; fail if the
  whole interval lies at or below zero; otherwise inconclusive.
* **Within a limit** (S1, each S3 measure): pass if the point and the upper bound are at or below
  the limit; fail if the lower bound is above it; otherwise inconclusive. S3 passes only if all its
  measures pass and fails if any fails.
* **Carried weights** (``carried.json`` beside the decision, an amendment written by T036): the
  carried model, its weights' SHA-256 and the shuffled rule's outcome. A failed shuffled rule
  means S4 is not passed whatever its interval.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PASS, FAIL, INCONCLUSIVE = "pass", "fail", "inconclusive"
CARRIED = "carried.json"
CORE = ("decision.json", "README.md")


@dataclass(frozen=True)
class Interval:
    value: float
    lo: float
    hi: float

    @staticmethod
    def of(d: dict[str, float]) -> Interval:
        return Interval(float(d["value"]), float(d["lo"]), float(d["hi"]))


def above_zero(iv: Interval) -> str:
    if iv.value > 0 and iv.lo > 0:
        return PASS
    if iv.hi <= 0:
        return FAIL
    return INCONCLUSIVE


def within_limit(iv: Interval, limit: float) -> str:
    if iv.value <= limit and iv.hi <= limit:
        return PASS
    if iv.lo > limit:
        return FAIL
    return INCONCLUSIVE


def all_of(verdicts: list[str]) -> str:
    if any(v == FAIL for v in verdicts):
        return FAIL
    if all(v == PASS for v in verdicts):
        return PASS
    return INCONCLUSIVE


def s4_verdict(iv: Interval, shuffled_rule: str) -> str:
    """S4 with the shuffled rule applied: a control that beats C makes S4 not passed."""
    v = above_zero(iv)
    if shuffled_rule != PASS and v == PASS:
        return FAIL
    return v


def reference(s2: str, gap_c: float, gap_glr: float) -> str:
    """S3 and S4's reference: C if S2 passes, else the better of the two by gap recovered."""
    if s2 == PASS:
        return "C"
    return "C" if gap_c >= gap_glr else "glr_confirm"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def amendments(decision_dir: str | Path) -> list[dict[str, str]]:
    """Every file beside the decision record other than the record and its README, by digest."""
    d = Path(decision_dir)
    return [
        {"file": f.name, "sha256": sha256_file(f)}
        for f in sorted(d.iterdir())
        if f.is_file() and f.name not in CORE
    ]


def expected_l_sha(params_sha: str, weights_sha: str, plan: dict[str, Any]) -> str:
    """The segmenter digest ``tma2-segment --segmenter L`` writes for these weights."""
    net = json.dumps(plan["evidence_network"])
    return hashlib.sha256(f"{params_sha}:{weights_sha}:{net}".encode()).hexdigest()


def check_inputs(
    decision: dict[str, Any],
    plan_sha: str,
    split: str,
    truth_sha: str,
    test_digest: str | None,
    headers: dict[str, dict[str, Any]],
    params_sha: str,
    carried: dict[str, Any] | None,
    plan: dict[str, Any],
) -> list[str]:
    """Refusals (FR-071, T037): every reason the inputs do not match the decision."""
    errs = []
    if plan_sha != decision["plan_digest"]:
        errs.append("the plan's SHA-256 is not the decision's plan_digest")
    if split == "test":
        if test_digest is None:
            errs.append("no committed test digest (seed315-digests.json) beside the decision")
        elif truth_sha != test_digest:
            errs.append("the truth file is not the decision's test split")
    elif split == "validation":
        if truth_sha != decision["validation_digest"]:
            errs.append("the truth file is not the decision's validation split")
    else:
        errs.append(f"unknown split {split}")
    for name in ("C", "L"):
        if name not in headers:
            errs.append(f"no segmentation named {name}")
    for name, h in headers.items():
        if h.get("dataset_digest") != truth_sha:
            errs.append(f"{name}: segmented a different data file")
        if h.get("git_dirty"):
            errs.append(f"{name}: segmented from a dirty tree")
    if "C" in headers and headers["C"].get("segmenter_sha256") != params_sha:
        errs.append("C: parameters differ from the decision's")
    if "L" in headers:
        if carried is None:
            errs.append(f"no {CARRIED} (the carried weights) beside the decision")
        else:
            want = expected_l_sha(params_sha, str(carried["weights_sha256"]), plan)
            if headers["L"].get("segmenter_sha256") != want:
                errs.append("L: not the carried weights with the decision's parameters")
    return errs
