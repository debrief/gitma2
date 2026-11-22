# CLI and workflow contracts: spec 037

- `tma2-rpredict ... [--scale FILE]`: rows gain the interval fields; without `--scale` the
  scales are 1.
- `tma2-hpredict --kind hybrid --segmentation c2 --prior-from PRED.ndjson --prior-weight W`:
  C″'s final solve with the regressor's rows as start and prior; header kind `hybrid`.
- `tma2-rmread --errors errors.npz --truth SPLIT [--mismatch-truth FILE] --regressors a,b,c
  --control NAME --references ... [--decision DIR --plan FILE --split validation|test]
  --out reading.json`: exit 0; readings are outcomes, never an exit code.
- `tma2-generate --mismatch FILE#id`: accepts the new condition fields.
- Workflow `rmis/**` → `rmis.yml`, plan `configs/rmis/<name>.json`; results
  `results/rmis-<name>-<condition>-<run id>`; a test plan is refused without its decision
  record and when a results branch for it already exists.
- Workflow `gputrain/**` unchanged; fine-tune plans carry `init_from`.
