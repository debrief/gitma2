# CLI contracts: spec 009

- **`tma2-g3train statement --plan --model --train <cache> --val <cache> --checkpoint`**: trains the
  statement head (course mixture + interval scales) on exact errors; tuning ordinals from the plan.
- **`tma2-g3train statement-temperature --plan --val <cache> --out temperature.json`**: the classical
  control per slice, and the shared isotonic map for P (both from tuning ordinals only).
- **`tma2-g3predict --in <E file> --features <cache> --plan (--model --weights | --temperature) --out`**:
  writes the statement fields; points copied; header records its own commit and dirty flag.
- **`tma2-g2/gs` scoring**: writes the statement measures into `calibration.json` and the per-row
  arrays into `errors.npz`; `--reuse` as spec 008.
- **`tma2-g4 --scoring --decision --split --head --temperature --raw --shuffled...`**: Gate 4's
  verdict from stored arrays; `validation.json` / `verdict.json` name the producing commit and CPU.
