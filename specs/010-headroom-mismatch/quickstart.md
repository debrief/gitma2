# Quickstart: spec 010

1. Mismatch off is 0.6.0:
   `uv run pytest tests/golden/test_mismatch_off.py -q` (data bytes equal for three seeds).
2. One kind on, statistics as declared:
   `uv run pytest tests/unit/test_mismatch_stats.py -q` (autocorrelation, bias sd, σ range,
   outlier rate within sampling error on 200 scenarios).
3. Estimators cannot see the truth:
   `uv run pytest tests/unit/test_mismatch_isolation.py -q`.
4. Ceilings equal the oracle with mismatch off:
   `uv run pytest tests/unit/test_ceilings_off.py -q`.
5. A small end-to-end run (20 scenarios, primary condition):
   generate with `--mismatch ...#all-central`, run `tma2-hpredict ceiling` twice and `robust`,
   then `tma2-gh --split tuning`; `headroom.json` holds R with an interval.
6. Tuning, validation and test splits are generated and scored on CI (`score/**`, kind `gh`).
