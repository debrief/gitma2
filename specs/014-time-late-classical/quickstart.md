# Quickstart: validating spec 014

1. Gate T unchanged: `uv run pytest tests/unit/test_timelate2.py -k fixture` (prior version 1
   reproduces the pinned candidates).
2. Local smoke (seconds to minutes; 3 periods): generate seed 333 with
   `configs/timelate/tl-ranges.json` and `tl-quiet-ranges.json`, then
   `uv run tma2-tlsolve ... --systems c2,c2-refit,search2,search-flat,history-fixed,history-map,ekf-rts --classify`
   and `uv run tma2-tlscore ... --study configs/timelate/tl-c.json --errors`.
   Expect: every system has a track on every period; counts at three tolerances; a class for
   every wrong period; `errors.npz` written.
3. CI smoke: push `timelate/tl-c-smoke`; results on `results/timelate-tl-c-smoke-<run id>`.
4. Tuning: `timelate/tl-c-tune` (seed 333). Records under `experiments/` for the prior
   correction, the controls and classes, and the thinning study.
5. Registered runs: `timelate/tl-c-val` (seed 334; stops if the reference is unsound), then
   `timelate/tl-c-test` (seed 335, once).
