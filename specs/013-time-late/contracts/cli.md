# CLI contracts: spec 013

```
tma2-period --in <split.f32pack> --out <periods.f32pack> [--min-seconds 1200]
```
Cuts one period from each engagement (its own seeded stream). Existing files are not touched.

```
tma2-tlsolve --in <periods> --system reference|c2-end|c2-full|one-leg|imm|regressor
             [--points fixed:2] [--plan <gate T plan>] [--weights <ckpt> --config <json>]
             --start N --count N --out <tracks.ndjson>
```
Writes a TrackSolution per period. `reference` reads the manoeuvre times and nothing else of
the truth; every other system reads none of it.

```
tma2-tlscore --truth <periods> --tracks NAME=<file>... [--plan <plan> --decision <dir>] --out <dir>
```
Writes `metrics.json`, `errors.npz`, `report.md`; with a decision, `gate.json`; exit 3 when
T-a fails.

Workflow `timelate/**` → `.github/workflows/timelate.yml`, plans under `configs/timelate/`.
