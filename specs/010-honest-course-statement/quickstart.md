# Quickstart: spec 010

1. **Unit tests.** Run:
   ```
   uv run pytest -q tests/unit/test_statement5.py tests/unit/test_proxy.py tests/unit/test_gate5.py tests/unit/test_calibration_metrics.py
   ```
   They check that the truncated density integrates to 1 and its arc mass equals P, that the proxy
   reads no future bearings, and that the gate logic behaves on synthetic statements.
2. **Synthetic check of the bands (R7).** Run:
   ```
   uv run python scripts/research/g5_synthetic.py --datasets 100 --resamples 500 --seed 7
   ```
3. **Proxy caches.** For each split, run:
   ```
   uv run tma2-g5proxy --data <split.f32pack> --features <cache shards> --out <dir>
   ```
   Use validation seed 314 and the stream seed 318. Regenerate seed 318 at ed428a0 with
   `--count 25000`.
4. **Proxy definition, fitted on tuning rows only.** Run:
   ```
   uv run tma2-g5train proxy --plan configs/gate5/g5-a.json --data <val f32pack> --val <cache> --val-proxy <proxy cache> --out proxy.json
   ```
5. **Baseline (CI).** Push `score/g5-base-val`.
6. **After the decision record:**
   - train on CI by pushing `g5train/g5-a`;
   - for each model and control, run `uv run tma2-g5predict --in <E val file> --features …
     --proxy … --proxy-def experiments/20261109-g5-decision/proxy.json --plan configs/gate5/g5-a.json`
     with one of `--temperature F`, `--classical F`, or `--model ID --run DIR --classical F
     --epoch best|last`;
   - push the files to a results branch, then push `score/g5-a-val`;
   - run `uv run tma2-g5 --scoring <dir> --decision … --split validation --head N=P
     --temperature N=P --classical N=P --raw N=P --encshuf N=P --encshuf N=P --out <dir>`.
7. **References (FR-023, reported only).** Run:
   ```
   uv run python scripts/research/g5_refs.py --scoring <score dir>
   ```
8. **Test.** Not run, because Gate 5 stopped at validation.
