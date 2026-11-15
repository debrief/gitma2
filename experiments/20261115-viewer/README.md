# Spec 020: the browser viewer, checked

Not a gate and not a result. These files record what the viewer page runs and how it was
checked.

- `browser-leg.json`: `conformance/onnx/viewer_leg.mjs` on the built site, headless Chromium
  153 in this project's container, 2026-11-15. It covers 181 rows of six engagements:
  - state within 2.7e-6 of Python's onnxruntime element-wise;
  - covariance within 3.2e-6 on its own scale, and 3.2e-5 element-wise on one row
    (engagement 4, row 432; research R6);
  - flags identical;
  - graph loaded in 0.8 to 1.0 s, first estimate after 1.5 to 1.7 s, about 0.27 s a row;
  - ellipse off by default, and the warning shown with it.
- `vs-gate2.json`: `scripts/research/viewer_vs_gate2.py`. On the 24 G5 rows of the six
  engagements, the demo's E (Python's onnxruntime on the builder's hand-over) against Gate 2's
  committed E predictions (`results/g2predict-g2-a-test-42406326175`, `e-s3.ndjson`, torch in
  the run's chunks). Range within 2.0e-7 relative, course within 1.3e-6 rad, speed within
  6.4e-7 m/s. The demo's host-side inputs are the ones Gate 2 scored.
- The data itself: `site/static/viewer-data/manifest.json` (built at 440311e from a clean tree).
  Seed 319's test split was regenerated with the command the manifest names. Its file digest
  differs from Gate 2's only by the header's commit (AGENTS.md gotcha), and `vs-gate2.json`
  confirms the scenarios are the same.

To regenerate:

```
uv run tma2-generate --seed 319 --count 100000 --ranges configs/man2-ranges.json --heldout-ranges configs/man2-heldout.json --format f32pack --out <dir>
uv run python -m tma2.gate2.export --out <export> --plan configs/gate2/g2-a.json --weights experiments/20261107-g2-val/models/ew-s3/best.safetensors
uv run tma2-viewer-data --split <dir>/test.f32pack --export <export> --out site/static/viewer-data
```

The builder takes about 26 minutes on one core: C, E-s and C″ on a chunk of 16 scenarios at
about 1,000 rows.

Not yet checked: that a second build reproduces every digest (SC-004). The packing is
deterministic by unit test, since gzip carries no timestamp. Whether the export reproduces the
same graph is checked in CI: `cmp` against a fresh export of the carried weights.

2026-11-15, after the review: the data folder was renamed from `site/static/viewer/` to
`site/static/viewer-data/`, so that it no longer shares a name with the page's path. The
manifest's `built.command` still names the old folder. No file changed: every digest is the
same, and both checks were re-run after the move with no failures.
