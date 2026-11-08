# CLI contract: spec 008

## Changed

- **`tma2-g2predict`**
  - Rows gain the covariance fields (data-model).
  - `--features <out.npz>` writes the feature cache for the predicted rows.
  - The header gains `model_settings` and `segmentation_sha256`.
- **`tma2-gs` / `tma2-g2`**
  - Re-solved rows (C, one leg, the oracle, GLR + confirm) carry covariances internally.
  - `errors.npz` gains `cal_<name>`: [N, 9] per-row log-range, course and speed errors and
    standard deviations, NEES, `cov_ok` and plausible.
  - `--reuse <errors.npz>` loads re-solved estimators whose (ordinal, k) rows match, and refuses
    otherwise.
  - Gate mode on the test split refuses `start ≠ 0` or `count ≠ sigma1_scenarios`.
- **IMM / EKF predict:** optional covariance out-arrays. The f32 point rows are byte-identical.

## New

- **`tma2-g3train head`**
  - `--plan --model --train <cache…> --val <cache> --checkpoint [--epochs] [--max-wall-s]`;
  - writes `best.safetensors`, `last.safetensors` and `meta.json` (untrained, best and last
    validation scores, epochs).
- **`tma2-g3train temperature`**
  - `--plan --val <cache> --out temperature.json`;
  - fits on tuning ordinals 0–499.
- **`tma2-g3predict`**
  - `--in <E prediction file> --features <cache> --plan --model [--weights|--temperature] --out`;
  - copies each row's point fields and scales its covariance;
  - refuses mismatched rows.
- **`tma2-g3`**
  - `--truth --start --count --e NAME=PATH… [--reuse errors.npz] [--decision --plan --split
    validation|test --model]`;
  - writes calibration records per estimator and slice, `validation.json` or `verdict.json`, and
    `manifest.json`.
  - Exit 3 when the gate is not passed.

## Workflows

- `g2features/<plan>`: E over the stream and validation, with feature caches.
- `g3train/<plan>`: head seeds and shuffled (train-1 / train-2 as `g2train`); the temperature.
- `g3predict/<plan>`.
- `score/<plan>` with kind `g3`.
