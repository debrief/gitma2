# CLI contracts: Gate 2

All CLIs:
- read provenance (commit and dirty flag) before writing any output;
- refuse a dirty tree for gate inputs unless `--allow-dirty` (local experiments only);
- write NDJSON or npz with a typed header.

## tma2-dtables (E-s decision tables)

```
tma2-dtables --in <split.f32pack> --segmentations <C.ndjson> --plan <plan.json> --start N --count N --out <tables.npz> [--workers 4]
```

- **Purpose:** re-runs C's confirmation on each scenario and records every decision with the
  downstream errors with and without it (research R2).
- **Refuses:** a segmentation file whose parameter or code digest differs from the plan's.

## tma2-g2train

```
tma2-g2train train --plan <plan.json> --model <id> --data <stream dir> --tables <tables dir> --val <val tables> --checkpoint <dir> [--epochs N] [--max-wall-s S]
```

- **Behaviour:** resumable, writing checkpoints and meta after every epoch, and stopping at the
  wall budget.
- **Seeding:** seeded by the plan's model seed. The shuffled model trains on another scenario's
  truth labels.

## tma2-g2predict

```
tma2-g2predict --in <split.f32pack> --segmentations <C.ndjson> --weights <best.safetensors> --plan <plan.json> --start N --count N --rows g5 --out <pred.ndjson>
```

- **Output:** E's per-row predictions. E-s's decisions are applied first (C's confirmation with
  the shifted threshold), then E-w's weights.
- **Untrained weights:** reproduce C's errors exactly (a test).

## tma2-g2 (scoring and gate)

```
tma2-g2 --truth <split> --start N --count N --c <C.ndjson> --e NAME=<pred.ndjson>... --glr-confirm <dir>:<cfg> --imm <id> --ekf <id> --naive-train <split>[:a:c] [--detectability] --experiment <dir> [--decision <Gate2Decision> --plan <plan> --split test]
```

- **Scoring mode:** writes `metrics.json`, `report.md`, `inputs.json` and `errors.npz`.
- **Gate mode** adds `verdict.json` and `manifest.json`, and exits 3 unless G2-a…G2-d all pass.
- **Refuses:** a mismatched decision, plan, seed, data, weights, parameter or code digest; a
  segmentation or prediction from a dirty tree.

## Workflows

- **`segment.yml`:** C on the training stream and on the test split, with existing plans.
- **`g2train.yml`:** `g2train/<plan>`, a matrix of models, chained jobs, results to
  `results/g2-<plan>-<run>`.
- **`score.yml`:** a plan kind `g2` runs `tma2-g2`.
