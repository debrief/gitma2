# Quickstart: spec 009

1. Unit tests: `uv run pytest -q tests/unit/test_statement.py tests/unit/test_gate4.py`
   (the mixture's P equals its integral; P = 0 gives the uniform; the isotonic map is monotone; the
   interval-score loss is minimised at the 95% quantile; points unchanged).
2. Tuning evidence: `uv run python scripts/research/g4_tuning.py --cache <val cache>` reproduces
   research R1–R3 on ordinals 0–499.
3. Baseline (CI): `score/<g4 baseline plan>` with `--reuse` (E raw and references on 500–1499).
4. After the amendment and the decision record: `g3train/<g4 plan>` (CI), `tma2-g3predict` for each
   model, `score/<g4 val plan>`, `tma2-g4 --split validation`.
5. Test (only if validation passes): seed 320, then as Gate 3's quickstart step 5.
