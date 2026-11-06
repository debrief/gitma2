# Quickstart: Gate 2 on MAN2

Prerequisites:
- `uv sync`;
- the validation split `data/man2-val/validation.f32pack` (seed 314);
- C's validation segmentation (`results/segment-c3-val-*`).

Long runs go on CI (AGENTS.md: container restarts).

1. **Unit and golden tests**

   ```bash
   uv run pytest -q tests/unit/test_gate2_*.py tests/unit/test_segment_c_fixes.py
   ```

   Expected: untrained E equals C; causal cut tests pass; gradients are finite; the decision
   tables' "with" error equals C's error when C accepted.
2. **C on validation with the chosen hand-over:** push `score/c3-val`. Expected: the record in
   `experiments/20261106-c3-val/`, with the choice and its open-at-k stratum.
3. **Training stream:** push `segment/<plan>` for seed 318, then the decision tables on CI.
4. **Smoke training, locally, 20 scenarios:**

   ```bash
   uv run tma2-g2train train --plan configs/gate2/smoke.json --model e-s1 --data <dir> --tables <dir> --val <dir> --checkpoint /tmp/ck --epochs 1
   ```

   Expected: a checkpoint, and a robust validation loss that does not increase.
5. **Validation scoring:** push `score/<g2-val plan>`. Expected: G2-a…G2-d points on validation;
   the carried-seed and shuffled rules applied.
6. **The gate:** after the decision record and the amendments, generate seed 319, segment and
   predict on CI, then push `score/<g2-gate plan>`.
