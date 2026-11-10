# CLI contracts: spec 012

```
tma2-rtrain --config <json> --out <dir> [--resume <checkpoint>] [--device cpu|cuda] [--limit-seconds N]
```
Trains from the on-the-fly stream until the limit or the schedule's end; writes
`checkpoint.safetensors`, `state.pt` (optimiser, for resume) and `run.json`. Exit 0 on
`limit` or `complete`.

```
tma2-rpredict --weights <checkpoint> --config <json> --in <split.f32pack> --out <pred.ndjson> [--name reg-s1]
```
Rows at the scorer's prefixes. Refuses a checkpoint whose config digest differs.

```
tma2-rread --errors <errors.npz> --metrics <metrics.json> --regressors reg-s1,reg-s2,reg-s3 --decision <dir> --out <reading.json>
```
Prints the held-course reading and the manoeuvring differences. Exit 0 always (no gate).

```
modal run scripts/modal_train.py --plan configs/regress/<plan>.json [--segment 2]
```
Run by `.github/workflows/gputrain.yml` on `gputrain/<plan>` after the ledger check; results to
`results/gputrain-<plan>-<run id>`.
