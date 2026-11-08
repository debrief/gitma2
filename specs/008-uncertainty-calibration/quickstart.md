# Quickstart: spec 008 (uncertainty calibration)

Prerequisites: `uv sync`; seed 314 validation regenerated
(`scripts/ci/regen_split.sh configs/g2predict/g2-a-val.json "p['data']" <dir>`); C's validation
segmentation (`results/segment-c3-val-42268379557`). Long runs go on CI.

1. **Unit tests:**

   ```bash
   uv run pytest -q tests/unit/test_uncertainty.py tests/unit/test_calibration_metrics.py tests/unit/test_calib_*.py tests/unit/test_gate3.py tests/unit/test_followons.py
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
4. **Calibration (CI):** `g2features/<plan>`, `g3train/<plan>`, `g3predict/<val plan>`,
   `score/<g3 val plan>` (gate mode, split validation).
5. **The gate:** after the decision record and `carried.json`, generate seed 320, then segment,
   predict with features, calibrate and score in gate mode on the test split.
