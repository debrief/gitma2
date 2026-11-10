# Quickstart: spec 010

1. Mismatch off is 0.6.0:
   `uv run pytest tests/unit/test_mismatch.py -q -k off` (files equal for three seeds).
2. One kind on, statistics as declared:
   `uv run pytest tests/unit/test_mismatch.py -q -k statistics` (autocorrelation, bias sd, σ
   range, outlier rate within sampling error on 200 scenarios).
3. Estimators cannot see the truth:
   `uv run pytest tests/unit/test_headroom.py -q -k refus`.
4. Ceilings equal the oracle with mismatch off:
   `uv run pytest tests/unit/test_headroom.py -q -k ceilings`.
5. A small end-to-end run (20 scenarios, primary condition):
   generate with `--mismatch ...#all-central`, run `tma2-hpredict ceiling` twice and `robust`,
   then `tma2-gh --split tuning`; `headroom.json` holds R with an interval.
6. Tuning, validation and test splits are generated and scored on CI (`headroom/**`, plans in
   `configs/headroom/`).
