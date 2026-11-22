# Quickstart: checking spec 037

1. `uv run pytest -q tests/unit/test_mismatch_kinds.py`: existing conditions byte-identical;
   the new kinds change the bearing and have the stated sd.
2. `uv run pytest -q tests/unit/test_regress_mixture.py tests/unit/test_intervals.py
   tests/unit/test_mread.py tests/unit/test_hybrid.py`.
3. Step 1: push `rmis/smoke`, then `rmis/dev-321`; the record's `reading.json` holds sixteen
   conditions and the rule's output.
4. A toy fine-tune on CPU from a toy checkpoint: `uv run tma2-rtrain --config
   configs/regress/ft-toy.json --out /tmp/ft` writes a checkpoint the predictor reads.
5. The ledger: `uv run python -m tma2.regress.ledger --cap-usd 49 --plan
   configs/regress/ft-s1.json` prints the total and accepts or refuses.
6. Test: `rmis/test-371` is refused without `experiments/<date>-rmis-decision/`.
