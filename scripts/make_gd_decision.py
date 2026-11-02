"""Write the Gate D decision record (spec 004 T022; contracts/decision-record.md) before training.

    uv run python scripts/make_gd_decision.py --plan configs/gate-d/plan.json \
        --tune experiments/20261102-gd-tune/choice.json --imm-far <validation rate> \
        --forecast "<text>" --out experiments/<date>-gd-decision/decision.json

The plan must already name this record's path (``decision``); the record binds the plan by
SHA-256. ``tma2-gd`` refuses a record whose first commit is not an ancestor of every training
job's commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tma2.models.train import load_plan
from tma2.types import dump_record
from tma2.types.generated.tma import GateDDecision

CARRIED_RULE = (
    "Per carried variant (causal, time-late; three seeds each), the seed whose validation "
    "D-downstream-all ratio (median relative range error over all sigma = 1 deg G5 rows, physics "
    "layer fed by the exported knots, / the frozen IMM's) is the median of the three; ties to the "
    "lower seed. The classification-only detector (gd-cls) is a declared control, reported."
)
CONTROLS_RULE = (
    "After training, on validation seed 304: each control's threshold (CUSUM on the per-timestep "
    "least-squares innovations as Annex A section A.2 writes it, the projected windowed GLR with "
    "W = 30, the frozen IMM's mu_CT) is tuned with tma2-controls tune so that its held-leg G5 "
    "false-alarm fraction is closest to the carried variant's own at p_change >= 0.5; the CUSUM on "
    "the frozen EKF's innovations is tuned the same way and reported, not gated. The settings are "
    "recorded by digest in an amendment before the test split is generated; the amendment "
    "changes no criterion."
)
CRITERION = (
    "SRD Annex A section A.5 on the sigma = 1 deg slice of test seed 305 with scenario-clustered "
    "paired bootstraps at 97.5% (2,000 resamples): D-delay median delay / the better of CUSUM and "
    "GLR wholly below 1; D-miss miss rate minus the better control's wholly at or below 0; D-false "
    "fraction of held-leg G5 rows flagged wholly below the D3 limit; D-downstream-all median range "
    "/ IMM's wholly below 1; D-downstream-settled range, course and speed / batch least squares' "
    "each wholly below 1.1; D-kind and D-gap reported. A check passes when its point and whole "
    "interval meet the limit, fails when the interval lies wholly beyond it, else inconclusive. A "
    "variant passes when every gated check passes; Gate D passes when a carried variant passes, "
    "fails when every carried variant fails, else inconclusive (one re-score on a larger fresh "
    "seed, then final). Errors use the one plausibility convergence definition (spec 004 FR-008)."
)
VALIDATION_RULE = (
    "Annex A section A.5: a variant is carried to test only if, on validation seed 304, every "
    "gated check's point meets its limit and no interval lies wholly beyond it (tma2-gd --split "
    "validation). If no variant is carried, the test split is not generated or scored and the "
    "result is published as a validation stop. FR-015: the time-late variant's D-downstream-all "
    "is reported against the causal one's."
)
FOLLOW_ON = (
    "SRD Annex A section A.6, fixed in advance: pass - the detector is frozen and becomes Gate "
    "2's segmentation input, warm start and carried-forward control, and the viewer's hybrid "
    "switch uses p_change; fail on D-false only - one pre-registered iteration changing the "
    "held-leg weighting or the downstream loss weight, nothing else, then Gate 2 with the "
    "CUSUM/GLR segmenter; fail otherwise - publish, Gate 2 proceeds with the CUSUM/GLR segmenter."
)
ARCHITECTURE_CHECK = (
    "FR-035, each check against the detector's architecture: (1) D-downstream-settled is passed "
    "by construction by a detector that exports no knots (it is then batch least squares, ratio "
    "1); it is a non-regression guard, and such a detector fails D-delay and D-miss. (2) D-false "
    "is passed by a detector that never alarms; it then fails D-miss. (3) D-downstream-all is not "
    "met by construction: batch least squares is above the IMM on G5 rows. (4) The time-late "
    "variant reads the bearings after each manoeuvre, so D-delay and D-miss favour it by "
    "construction; a pass carried by the time-late variant alone is reported as an offline "
    "(smoothing) pass beside the causal variant's own result and does not license Annex A "
    "section A.6's online uses (the viewer's hybrid switch). (5) The weak least-squares CUSUM "
    "cannot lower the bar: D-delay and D-miss compare with the better of CUSUM and GLR. (6) The "
    "shuffled-label check is not used (no physics-layer-blind check applies to a segmenter)."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--tune", required=True)
    ap.add_argument("--imm-far", type=float, required=True, help="IMM held-leg G5 rate, mu > 0.5")
    ap.add_argument("--forecast", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    plan, _ = load_plan(a.plan)
    digest = hashlib.sha256(Path(a.plan).read_bytes()).hexdigest()
    if Path(plan.decision) != Path(a.out):
        raise SystemExit(f"the plan names decision {plan.decision}, not {a.out}")
    choice = json.loads(Path(a.tune).read_text())
    dets = plan.detectors or []
    carried = [d.id for d in dets if d.loss_downstream_weight > 0]
    controls = [d.id for d in dets if d.loss_downstream_weight == 0]
    limit = min(0.05, a.imm_far)
    rule = (
        "D3: 5%, or the frozen IMM's own held-leg G5 false-alarm fraction at mu_CT > 0.5 on "
        f"validation seed 304 if lower; measured {a.imm_far:.6f}, so the limit is {limit:.6f}."
    )
    rec = GateDDecision(
        plan_id=plan.id,
        plan_digest=digest,
        carried_variants=carried,
        control_models=controls,
        carried_rule=CARRIED_RULE,
        threshold=0.5,
        tolerance_s=60.0,
        knot_threshold=0.5,
        bootstrap_level=0.975,
        bootstrap_resamples=2000,
        false_alarm_limit_rule=rule,
        false_alarm_limit=limit,
        validation_seed=304,
        test_seed=305,
        test_count=100_000,
        held_leg_weight=dets[0].held_leg_weight,
        controls_rule=CONTROLS_RULE,
        imm=choice["imm"]["name"],
        ekf=choice["ekf"]["name"],
        criterion=CRITERION,
        validation_rule=VALIDATION_RULE,
        follow_on=FOLLOW_ON,
        forecast=a.forecast,
        architecture_check=ARCHITECTURE_CHECK,
    )
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump_record(rec), indent=2, sort_keys=True) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
