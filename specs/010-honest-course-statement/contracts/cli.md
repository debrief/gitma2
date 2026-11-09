# CLI contract: spec 010

## `tma2-g5proxy`

Builds the proxy cache for the feature cache's rows.

```
tma2-g5proxy --data <split.f32pack> --features <cache shards *.npz> --segmentation <C ndjson>
             --out <dir>
```

- Writes one `.npz` per feature shard, with the same row order.
- Refuses on these conditions:
  - a row with no C segmentation at (ordinal, k);
  - a data digest that differs from the cache header's;
  - a dirty tree, unless `--allow-dirty` is given.

## `tma2-g3train`

The new subcommands share the plan `configs/gate5/<name>.json`:

```
tma2-g3train proxy5 --plan <plan> --val <cache> --proxy <proxy cache> --out <proxy.json>   # R1 fit, tuning rows
tma2-g3train statement5 --plan <plan> --model <id> --train <cache> --train-proxy <proxy> --val <cache> --val-proxy <proxy> --checkpoint <dir>
tma2-g3train classical5 --plan <plan> --train <cache> --train-proxy <proxy> --val <cache> --val-proxy <proxy> --out <classical.json>
tma2-g3train temperature5 --plan <plan> --val <cache> --val-proxy <proxy> --out <temperature.json> [--errors-of <estimator file>]
```

- `temperature5 --errors-of` fits a reference's own temperature, for the oracle and the IMM, from
  that estimator's prediction file on tuning rows.
- `statement5` with `shuffle: encoder` in the model entry is the encoder-only control.

## `tma2-g4predict`

The existing command, extended for the truncated form.

- New flags: `--proxy <proxy cache>` and `--classical <classical.json>`.
- **Output fields:** `course_arc_rad`, `course_arc_prob`, `course_kappa`, `course_form`,
  `unsettled_score`, `unsettled_flag`, `range_ratio_q95` and `speed_q95_mps`.
- **Header:** the model kind, the weights or rule digest, the proxy digest, the plan digest, the
  commit and the dirty flag.

## `tma2-g5`

```
tma2-g5 --scoring <dir> --decision <decision.json> --split validation|test
        --head NAME=PATH --temperature NAME=PATH --classical NAME=PATH --raw NAME=PATH
        --encshuf NAME=PATH --encshuf NAME=PATH --out <dir>
```

- **Validation:** writes `validation.json`. It contains the criteria, the per-slice table, the
  encoder-shuffle rule, the producing commit and the CPU.
- **Test:** writes `verdict.json`. Exit 3 when the gate is not passed.
