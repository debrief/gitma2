# Quickstart: Gate 1

```bash
uv sync
uv run pytest -q
```

1. **Data**: generate the validation and test splits (digests go into the plan and decision):

```bash
uv run tma2-generate --seed 302 --count 100000 --out data/g1-val --ranges tests/fixtures/gitma/iter4-seed777/ranges.json --heldout-ranges tests/fixtures/gitma/iter4-seed777/heldout-ranges.json --format f32pack
```

2. **References**: tune and freeze the EKF and IMM on validation:

```bash
uv run tma2-tune --validation data/g1-val/validation.f32pack --out experiments/<date>-g1-tune
```

3. **Budget**: one short epoch locally, then check the recorded seconds per 10⁵ scenarios:

```bash
uv run tma2-train --plan configs/gate1/plan.json --model g1-seed1 --checkpoint /tmp/ck --scenarios 2000 --epochs 1
```

4. **Pre-register**: commit `experiments/<date>-g1-decision/decision.json` before pushing the plan.

5. **Train**: push `train/g1-a`; results arrive on `results/g1-a-<run>`.

6. **Gate**: generate seed 303, predict with the carried and control models, run `tma2-g1`, then
   the agent panel.

Expected: with untrained heads the model's predictions equal batch least squares'; the epoch
budget is under an hour on four cores; the gate record holds every reference on the same rows.
