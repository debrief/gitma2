# Quickstart: spec 009

1. Unit tests: `uv run pytest -q tests/unit/test_statement.py tests/unit/test_statement_fit.py
   tests/unit/test_gate4.py tests/unit/test_calibration_metrics.py` (the mixture's P equals its
   integral; P = 0 gives the uniform; the isotonic map is monotone; the interval-score loss is
   minimised at the 95% quantile; the statement columns and Gate 4's criteria on synthetic rows).
2. Tuning evidence: `uv run python scripts/research/g4_tuning.py --plan configs/gate4/g4-a.json
   --val <validation feature cache shards> [--head <training run dir>]` reproduces research R1, R2
   and R3a on ordinals 0–499.
3. Baseline (CI): push `score/g4-base-val` (`configs/score/g4-base-val.json`, `--reuse` of the Gate 3
   baseline's `errors.npz`): raw estimators' statements on 500–1499.
4. After the decision record: push `g4train/g4-a` (CI, `.github/workflows/g4train.yml`); for each
   model `uv run tma2-g4predict --in <E validation file> --features <cache> --plan
   configs/gate4/g4-a.json --model <id> --run <run dir>/<id> --epoch best|last --out <file>` (or
   `--temperature <temperature.json>`); push the files to a results branch and `score/g4-a-val`;
   then `uv run tma2-g4 --scoring <score dir> --decision
   experiments/20261108-g4-decision/decision.json --split validation --head NAME=PATH
   --temperature NAME=PATH --raw NAME=PATH --shuffled NAME=PATH --shuffled NAME=PATH --out <dir>`.
5. Test (only if validation passes): seed 320, then as Gate 3's quickstart step 5. Not run: Gate 4
   stopped at validation.
