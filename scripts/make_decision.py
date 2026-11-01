"""Write the Gate 1 decision record (spec 003 T018) for a plan, before any training.

    uv run python scripts/make_decision.py --plan configs/gate1/plan.json \
        --tune experiments/20261101-g1-tune/choice.json \
        --forecast "<text>" --out experiments/<date>-g1-decision/decision.json

The record binds the plan by SHA-256, so the plan must be final (its ``decision`` field already
names this record's path). ``tma2-g1`` refuses a decision record whose commit is not an ancestor
of the models' training commit, or a plan whose digest differs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tma2.models.train import load_plan
from tma2.types import dump_record
from tma2.types.generated.tma import Gate1Decision, PhysicsHead

CARRIED_RULE = (
    "Of the three seeds of the carried configuration, the one whose validation median relative "
    "range error at zig + 5 min on sigma = 1 deg rows is the median of the three (not the best, "
    "so the choice is not a selection on noise); ties to the lower seed."
)
GATE_ROWS = (
    "Test split of seed 303 (10% of 100,000 scenarios generated), sigma = 1 deg scenarios: the row "
    "at zig + 5 min for range and course, the row at zig + 10 min for speed; a scenario whose "
    "window ends before a row contributes no row for that metric. Settled slices for efficiency "
    "are the same rows (constant-velocity data: every post-zig row is on a held leg)."
)
CRITERION = (
    "SRD section 5, Gate 1, as amended 2026-11-01: on every metric (median relative range error, "
    "median absolute course error, median absolute speed error) the ratio model / batch least "
    "squares has its point and its whole 95% scenario-clustered paired bootstrap interval below "
    "1.1; the model's gross-error rate (relative range error > 50% or not converged) is at or "
    "below batch least squares' (clustered difference interval upper bound <= 0); and efficiency "
    "(median |error| / bound sd / 0.6745, full-window Cramer-Rao bound) is <= 1.25 on range, "
    "course and speed on the settled slices. Pass needs every check to pass; fail if any check's "
    "interval lies wholly beyond its limit; otherwise inconclusive (one re-score on a larger "
    "fresh seed, then final)."
)
VALIDATION_RULE = (
    "Before the test split is generated: the carried model's validation median range, course and "
    "speed errors at the gate rows must each be below 1.1 x batch least squares on the same "
    "validation rows (point estimates); the shuffled-label control's median range error must be "
    "at least 0.8 x naive's (at naive level: a leakage check); the time-late control's median "
    "range error must be at or below the causal seed-1 model's (constitution IV: it sees the "
    "whole window, so it must score at least as well). If any of these fails, the phase stops "
    "at validation, the test split stays unscored and reserved, and the result is published as "
    "a validation stop."
)
IF_FAILED = (
    "SRD section 5: one further pre-registered iteration (a new decision record, a fresh test "
    "seed), then stop and publish: the physics layer is not learnable end to end as built."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--tune", required=True, help="choice.json from tma2-tune")
    ap.add_argument("--forecast", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    plan, _ = load_plan(a.plan)
    digest = hashlib.sha256(Path(a.plan).read_bytes()).hexdigest()
    if Path(plan.decision) != Path(a.out):
        raise SystemExit(f"the plan names decision {plan.decision}, not {a.out}")
    choice = json.loads(Path(a.tune).read_text())
    carried = [
        m.id
        for m in plan.models
        if m.head == PhysicsHead.physics and m.causal and not m.shuffle_labels
    ]
    controls = [m.id for m in plan.models if m.id not in carried]
    rec = Gate1Decision(
        plan_id=plan.id,
        plan_digest=digest,
        carried_models=carried,
        control_models=controls,
        carried_rule=CARRIED_RULE,
        test_seed=303,
        test_count=100_000,
        gate_rows=GATE_ROWS,
        criterion=CRITERION,
        bootstrap_level=0.95,
        bootstrap_resamples=2000,
        imm=json.dumps(choice["imm"], sort_keys=True),
        ekf=json.dumps(choice["ekf"], sort_keys=True),
        forecast=a.forecast,
        if_failed=IF_FAILED,
        validation_rule=VALIDATION_RULE,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump_record(rec), indent=2, sort_keys=True) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
