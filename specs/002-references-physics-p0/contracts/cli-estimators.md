# Contract: estimator, evaluation and gate CLIs

All mirror gitma's commands (`packages/classical/src/cli-*.ts`, `packages/eval/src/cli-*.ts`).
Exit codes: 0 success; 2 usage error or refusal; 3 gate not passed (`tma2-p0`); 1 unexpected.

## `tma2-naive`

```
tma2-naive fit   --train <train.f32pack|ndjson> --out <naive.json>
tma2-naive predict --model <naive.json> --in <split> --out <pred.ndjson> [--per-timestep]
```

## `tma2-solve`

```
tma2-solve --in <split.f32pack|ndjson> --out <pred.ndjson> [--per-timestep] [--max-iter n]
```

Estimator name `classical`; mode `final` or `per_timestep`; rows as gitma (research R1).

## `tma2-track`

```
tma2-track --in <split> --out <pred.ndjson>
           (--filter ekf --sigma-a <m/s²> | --filter imm --sigma-cv <m/s²> --sigma-ct <m/s²>
            --sigma-omega <rad/s/√s> --switch <1/s>) [--p0-scale k] [--r-scale k]
```

Estimator names `ekf-sa<…>[-p<k>][-r<k>]`, `imm-cv<…>-ct<…>-w<…>-s<…>[-p<k>][-r<k>]`.

## `tma2-crb`

```
tma2-crb --in <split> --out <crb.ndjson> [--per-leg]
```

One record per scenario with per-row bounds (research R4); consumed by `tma2-eval`.

## `tma2-eval`

```
tma2-eval --truth <split> --predictions <pred.ndjson>... [--crb <crb.ndjson>]
          [--points 300,600] [--curve-step 60] [--bootstrap] [--level 0.95] --out <dir>
```

Writes `metrics.csv`, `metrics.json`, `curves.csv`, and with `--bootstrap` `bootstrap.json`
(gitma's layouts plus the efficiency columns). Refuses a prediction file whose `dataset_digest`
does not match the truth file.

## `tma2-oracle`

```
tma2-oracle --truth <split> --out <pred.ndjson> [--speed-prior] [--iterations K]
```

The physics layer with truth segmentation (knots at span starts and ends), as a per-timestep
estimator named `oracle-physics[-sp]`, for the ceiling and for P0.

## `tma2-p0`

```
tma2-p0 --experiment experiments/<id> [--oracle-data <dir with validation.f32pack>]
```

Runs every P0 check (spec FR-016), writes `manifest.json`, `metrics.json`, `verdict.json`
(`decided_by: "machine"` until the panel sets it), prints the check table; exit 3 if any check
fails. The oracle check is skipped with an explicit `skipped` result when `--oracle-data` is
absent (local quick runs); CI passes it.
