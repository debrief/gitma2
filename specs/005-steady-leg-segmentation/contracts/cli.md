# CLI contracts: spec 005

All commands read and write files and are deterministic for fixed inputs. Exit codes:
- **0:** success.
- **2:** usage error, or a refused input (digest mismatch, dirty tree without `--allow-dirty`).
- **3:** `tma2-gs` only: the gate did not pass (fail or inconclusive).

## tma2-segment

Segments the target (and ownship) for every scored prefix of every σ-selected scenario of a split.

```
uv run tma2-segment --in <split.f32pack> --out <segmentations.ndjson>
    --segmenter C | L --params <segment-params.json> [--weights <L dir>]
    [--rows g5|all|<k,…>] [--vessel target|ownship|both] [--workers 4]
    [--work <cache dir>] [--allow-dirty]
```

- **Output.** A header record (provenance, parameters, `segmenter_sha256`), then one
  `Segmentation` per scenario, vessel and prefix row.
- **Cache.** The cost tables and the GLR statistic are cached per scenario under `--work`, keyed by
  commit and data digest, and reused only from a clean tree (spec 002's rule).
- **Refusals.** `--segmenter L` requires `--weights`, whose SHA-256 must match the carried weights
  named in the decision record when used for Gate S.

## tma2-segtrain

Trains L.

```
uv run tma2-segtrain --plan <plan.json> --seed <s> --out <model dir> [--resume] [--shuffled]
```

- **Plan.** It names the training stream (seed 317, digest), the cost-table shards, the
  validation split, the evidence-network configuration, and the loss weights (the CRF, plus the
  auxiliary term at 0.1).
- **Checkpoints** are written per epoch, with Adam state, in the spec 003/004 layout. Weights are
  bound by SHA-256.
- **`--shuffled`** trains the control on permuted truth labels.

## tma2-gs

Scores the segmenters and, with a decision record, applies Gate S.

```
uv run tma2-gs --truth <split.f32pack> --segmentations <seg.ndjson>…
    --experiment <dir> [--decision <decision.json> --plan <plan.json>]
    [--split validation|test]
```

- **Without `--decision`.** It is a diagnostic. It writes `metrics.json` (every metric of FR-060
  to FR-063, per segmenter and stratum) and `report.md`.
- **References.** It always adds the oracle, one-leg and GLR + confirm segmentations. Batch least
  squares and the frozen IMM run on the same rows.
- **With `--decision` and `--split test`:**
  - it refuses a decision whose seed, plan or weights digest does not match the inputs;
  - it writes `verdict.json` (S1–S4) and `manifest.json` (all digests, `git_dirty`);
  - it exits 3 unless every criterion passes.
