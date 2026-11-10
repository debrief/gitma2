# Quickstart: spec 011

1. **C unchanged**: `uv run pytest tests/unit/test_segment_robust.py -q` asserts C's code and
   parameter digests, that C-r with unit weights, the stated σ and factor 1 reproduces C's
   segmentation on the fixture scenarios, and that C-r's segmentation of prefix k is unchanged
   by bearings after k.
2. **Smoke** (CI, 3 engagements): push to `gater/smoke`; expect results branches for `off` and
   `all-central` with `gate.json` naming the three systems.
3. **Pilot**: push to `gater/pilot` (seed 323, 60 engagements); read the settings table in
   `experiments/<date>-gr-pilot/`.
4. **Gate**: after the decision record, `gater/gr-val` (seed 324) then `gater/gr-test`
   (seed 325); `tma2-gr --decision` prints R-a, the share closed and the remainder.
