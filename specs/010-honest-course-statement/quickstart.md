# Quickstart: spec 010

1. Unit tests:
   ```
   uv run pytest -q tests/unit/test_statement5.py tests/unit/test_proxy.py tests/unit/test_gate5.py tests/unit/test_calibration_metrics.py
   ```
   They check that:
   - the truncated density integrates to 1 and its arc mass equals P;
   - the proxy uses no future bearings;
   - the gate's synthetic check passes (R7).
2. Tuning evidence, R1 to R4 on ordinals 0–499:
   ```
   uv run python scripts/research/g5_tuning.py --data <val f32pack> --val <cache> --segmentation <C tuning ndjson>
   ```
3. The proxy caches. Validation 0–1499 runs in the session; the stream (seed 318) runs on CI via `g5proxy/<plan>`.
4. Baseline (CI): push `score/g5-base-val` with `--reuse` of the Gate 4 validation scoring.
5. After the amendment and the decision record:
   - train on CI with `g5train/g5-a`;
   - run `tma2-g4predict` for each model and control, and push the files to a results branch;
   - score with `score/g5-a-val`;
   - run `tma2-g5 --split validation`.
6. Test, only if validation passes: generate seed 320, then run its features, proxy and segmentation on CI, then the scoring, then `tma2-g5 --split test`.
