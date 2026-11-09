# Quickstart: spec 008 (uncertainty calibration)

Prerequisites: `uv sync`; seed 314 validation regenerated
(`scripts/ci/regen_split.sh configs/g2predict/g2-a-val.json "p['data']" <dir>`); C's validation
segmentation (`results/segment-c3-val-42268379557`). Long runs go on CI.

1. **Unit tests:**

   ```bash
   uv run pytest -q tests/unit/test_uncertainty.py tests/unit/test_calibration_metrics.py tests/unit/test_calib.py tests/unit/test_gate3.py tests/unit/test_followons.py tests/unit/test_tracker_covariance.py
   ```

   Expected:
   - standard deviations match finite differences;
   - coverage and NEES equal hand-computed values on synthetic Gaussians;
   - the untrained head equals the raw covariance;
   - calibrated files leave every point field unchanged.
2. **Covariances in rows:** re-run `tma2-g2predict` on 4 validation scenarios (as spec 007's
   quickstart). Expected: every plausible row carries `cov_xyvv`, the three standard deviations
   and `cov_ok`; the point fields equal spec 007's file for the same rows.
3. **Validation baseline (CI):** push `g2predict/<val plan with covariances>`, then
   `score/<g3 baseline plan>`. Expected: calibration records for C, E, E-w, C″, the IMM, the EKF
   and the oracle on scoring ordinals 500–1499.
4. **Calibration:** feature caches by `g2predict/<plan>` with `"features": true`
   (`configs/g2predict/g3-feat-{stream,val}.json`); `g3train/<plan>` (CI); `tma2-g3predict` for
   each head and the temperature (seconds, in the session); `score/<g3 val plan>` with `reuse`
   (CI); then `tma2-g3 --split validation` on that run's `errors.npz`.
5. **The gate:** after the decision record and `carried.json`, generate seed 320, then segment,
   predict with features, calibrate and score on the test split, and run `tma2-g3 --split test`.
   (Not run in spec 008: the validation rule was not met, `experiments/20261108-g3-val/`.)

## Run record (T037, 2026-11-08)

- Step 1: 26 tests passed (27 s).
- Step 2: `tma2-g2predict` for e-s3 on validation ordinals 500–503 (16 rows, 177 s): every row
  carries `cov_xyvv`, `cov_ok` and the standard deviations; points equal Gate 2's CI file
  (`results/g2predict-g2-a-val-42385722106`) to 2.2e-9 relative.
- Steps 3–4: run on CI during the gate (`experiments/20261108-g3-base-val/`,
  `experiments/20261108-g3-val/`). Step 5: not run (validation stop).
