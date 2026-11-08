# Quickstart: Gate 2 on MAN2

Run end to end on 2026-11-08 (T034); the long steps were run on CI and their records are named.

Prerequisites:
- `uv sync`;
- seed 314 validation regenerated at its commit and checked against its digest:
  `scripts/ci/regen_split.sh configs/g2predict/g2-a-val.json "p['data']" <dir>` (about a minute;
  prints the split's path);
- C's segmentation of validation ordinals 500–1499:
  `git fetch origin results/segment-c3-val-42268379557` and
  `git show FETCH_HEAD:experiments/segment-runs/c3-val-42268379557/segmentations.ndjson > c.ndjson`.

Long runs go on CI (AGENTS.md: container restarts; 20 concurrent jobs).

1. **Unit tests** (about 10 minutes):

   ```bash
   uv run pytest -q tests/unit/test_gate2_*.py tests/unit/test_segment_c_fixes.py
   ```

   Expected: untrained E equals C; E is causal end to end (every row after k perturbed); gradients
   are finite; the decision tables' "with" error equals C's error when C accepted; the classical
   controls (zig veto, fade) reduce to C when empty.
2. **C on validation with the chosen hand-over:** `score/c3-val` (record
   `experiments/20261106-c3-val/`).
3. **Training stream and decision tables (CI):** `segment/g2-stream-c` (seed 318), then
   `dtables/<plan>` for the stream and the validation tuning ordinals.
4. **Smoke E-w training, locally, 30 validation scenarios** (training and validation tables must
   be different files):

   ```bash
   uv run tma2-g2train tables --in <dir>/validation.f32pack --segmentations c.ndjson --plan configs/gate2/g2-a.json --start 500 --count 20 --out tbl.npz
   uv run tma2-g2train tables --in <dir>/validation.f32pack --segmentations c.ndjson --plan configs/gate2/g2-a.json --start 520 --count 10 --out tbl_val.npz
   uv run tma2-g2train train --plan configs/gate2/g2-a.json --model ew-s1 --train tbl.npz --val tbl_val.npz --checkpoint ck --epochs 1
   ```

   Expected (8 November): 80 training and 40 validation prefixes; trimmed validation loss 58.26
   untrained, 55.54 after one epoch (about 5 minutes); `ck/meta.json`, `best.safetensors`.
5. **Training (CI):** `g2train/g2-a` (run 42352638177, `results/g2-g2-a-42352638177`).
6. **Smoke prediction, locally, 4 scenarios** (carried weights in
   `experiments/20261107-g2-val/models/`):

   ```bash
   uv run tma2-g2predict --in <dir>/validation.f32pack --segmentations c.ndjson --plan configs/gate2/g2-a.json --model e-s3 --es-weights experiments/20261107-g2-val/models/es-s3/best.safetensors --ew-weights experiments/20261107-g2-val/models/ew-s3/best.safetensors --start 500 --count 4 --out pred.ndjson
   ```

   Expected: a header with the plan, code, parameter and dataset digests and `weights_sha256`
   `a5485318…`, then four scenarios (about 40 s each: E re-runs C).
7. **Validation (CI):** `g2predict/g2-a-val`, then `score/g2-a-val` (gate mode, split validation;
   record `experiments/20261107-g2-val/`, `validation.json`): the carried-seed, shuffled and
   validation rules; `carried.json` beside the decision.
8. **The gate (CI):** generate seed 319 at a commit holding `carried.json`, record
   `test-digest.json`, then `segment/g2-test-c`, `glr-confirm/g2-test-glr`, `g2predict/g2-a-test`
   and `score/g2-a-test` (record `experiments/20261107-g2/`).
9. **Classical controls (CI; panel round 1):** `g2predict/g2-veto-{val,test}`,
   `g2predict/g2-fade-{val,test}`, `score/g2-veto-{val,test}`, then paired differences:

   ```bash
   uv run python scripts/research/g2_paired_gaps.py errors.npz e-s3-C e-s3-veto-w6-fade ew-s3-fade
   ```

   (record `experiments/20261107-g2-veto/`).
10. **Export (T033):**

    ```bash
    uv run python -m tma2.segment.evidence_export --out es --plan configs/gate2/g2-a.json --weights experiments/20261107-g2-val/models/es-s3/best.safetensors
    uv run python -m tma2.gate2.export --out ew --weights experiments/20261107-g2-val/models/ew-s3/best.safetensors
    ```

    Expected: Python legs within 1e-5 (6e-16 and 3.4e-8); E-w's graph has one `Loop` and loads in
    under a second (about 5 minutes in all: the golden batch runs C). CI runs the browser and
    Java legs.
