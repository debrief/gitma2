# Quickstart: steady-leg detector and Gate D

1. Data: `uv run tma2-generate --seed 304 --count 100000 --out data/gd-val --ranges
   tests/fixtures/gitma/phase4-seed777/ranges.json --heldout-ranges
   tests/fixtures/gitma/phase4-seed777/heldout-ranges.json --format f32pack`; pin the validation
   digest in the plan.
2. References: `uv run tma2-tune --validation data/gd-val/validation.f32pack --criterion g5
   --experiment experiments/<date>-gd-tune` from a clean tree.
3. Liveness and learnability: `uv run pytest -q tests/unit/test_heads.py` (a dead model fails,
   a trained one passes).
4. Throughput: push `bench/gd` (the bench workflow with the detector plan); one epoch over 10⁵
   scenarios must project under an hour.
5. Pre-register: `scripts/make_gd_plan.py` and `scripts/make_gd_decision.py`; commit the decision
   record; push `train/gd-a`.
6. Validation: push `validate-gd/<run id>`: detector outputs, control tuning (amendment by digest),
   the validation report with the carried rule and the validation rule.
7. Gate: if the report says proceed, push `gate-gd/gd-a`: test seed 305, every detector and
   reference on the test split, `tma2-gd`, the record pushed to a results branch.
8. Panel, `review.md`, `decided_by`, write-up.
