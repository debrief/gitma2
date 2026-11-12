# Quickstart: spec 013

1. **Data**: `uv run tma2-generate --seed 329 --count 400 --ranges configs/timelate/tl-ranges.json
   --heldout-ranges configs/timelate/tl-heldout.json --format f32pack --out <dir>`, then
   `uv run tma2-period --in <dir>/train.f32pack --out <dir>/periods.f32pack`.
2. **Tests**: `uv run pytest tests/unit/test_timelate.py -q` (period slice, track read-out,
   bound at the last row, normal points on noise-free data, C's digests).
3. **One period end to end**: `tma2-tlsolve --system reference` and `--system c2-end` on three
   periods, then `tma2-tlscore`; the reference's efficiency on determined rows is near 1.
4. **Tuning**: push `timelate/tl-tune` (seed 329, 150 periods).
5. **Gate**: after the decision record, `timelate/gt-val` (330) then `timelate/gt-test` (331).
