# Quickstart: spec 012

1. **Toy run on CPU** (minutes): `uv run tma2-rtrain --config configs/regress/toy.json --out /tmp/r-toy --device cpu`;
   the validation loss in `run.json` falls.
2. **Tests**: `uv run pytest tests/unit/test_regress.py -q` (causality, frame invariance, stream
   determinism, resume).
3. **Predict and score a small split**: `tma2-rpredict` on 50 scenarios, then the scorer with
   `--predictions reg=<file>`; `tma2-rread` prints a reading (meaningless at toy size; it proves
   the path).
4. **GPU**, once the owner's secrets exist: push to `gputrain/pilot`; expect a results branch
   with `run.json` naming the GPU, the seconds used and the scenarios per second.
5. **Seeds and controls**: `gputrain/r-a-s1` … after the decision record; then prediction and
   scoring on seed 327, and seed 328 once per trained seed.
