---
title: "Slides: Gate 3, uncertainty calibration"
date: 2026-11-08
tags: [slides, gate-3, spec-008]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the Gate 3 write-up](/blog/2026/11/08/gate-3): what each estimate now
states about its own uncertainty, what a learned calibration did to it, two validation scenarios
drawn with their 1-σ ellipses, the validation verdict and the time-late check.

<!-- truncate -->

<Slides slug="2026-11-08-gate-3-slides" />

## What the figures show

- **Calibration chart.** For the oracle, the frozen IMM, E raw, the temperature and the carried
  head: the share of the 3,934 validation rows whose error lies inside the stated 95% interval in
  log range, course and speed, and the share within the χ²₄ 95% NEES point. The shaded band is
  Gate 3's [0.92, 0.98]. From the committed records `experiments/20261108-g3-val/` and
  `experiments/20261108-g3-base-val/`.
- **Track plot, ordinal 648** (validation seed 314, scenario 81299): a settled target leg. Marks
  and ellipses at zig + 5 and 15 min. Raw E's ellipses are too small to see; the calibrated ones
  are long slivers along the line of sight, covering the truth but wide in range.
- **Track plot, ordinal 514** (scenario 81048): a target manoeuvre mid-window. E's course error
  reaches 67°; the reference estimators (batch least squares, the frozen IMM) do far worse in
  range, and the oracle, with the true segmentation, does best.
- **Errors against time, ordinal 514.** Range, course and speed errors; E's raw and calibrated
  rows share their points (calibration changes only the covariance).

Track plots: ownship blue, target red, each estimator's trail from the zig with its marker and
1-σ ellipse at the marked times. Rows before the zig are hidden.

## Reproducing the figures

The demo split holds two scenarios of validation seed 314 (`configs/man2-ranges.json`,
`configs/man2-heldout.json`, generated at d72cb81, digest `e8150cb0…`), cut by
`scripts/research/g3_demo_split.py`. E's files come from `results/g2predict-g3-base-val-42471500526`
(raw) and `results/g3predict-g3-a-val` (calibrated).

```bash
uv run tma2-generate --seed 314 --count 100000 --ranges configs/man2-ranges.json --heldout-ranges configs/man2-heldout.json --format f32pack --out val314
uv run python scripts/research/g3_demo_split.py --pack val314/validation.f32pack --ordinals 514,648 --out demo --predictions e-raw=e-s3.ndjson e-cal=cal-s3.ndjson
uv run tma2-solve --in demo/demo.f32pack --out demo/lsq.ndjson --per-timestep
uv run tma2-track --in demo/demo.f32pack --out demo/imm.ndjson --filter imm --sigma-cv 0.03 --sigma-ct 1 --sigma-omega 0.01 --switch 0.0003 --p0-scale 4 --r-scale 2
uv run tma2-oracle --truth demo/demo.f32pack --out demo/oracle.ndjson
uv run tma2-plot track --truth demo/demo.f32pack --bound-to val314/validation.f32pack --predictions demo/lsq.ndjson demo/imm.ndjson demo/oracle.ndjson demo/e-raw.ndjson demo/e-cal.ndjson --labels "batch LS,IMM (frozen),oracle,E raw,E calibrated (cal-s3)" --scenario 81299 --at 2810,3410 --out site/static/img/2026-11-08-gate-3-slides/track-648.svg
uv run python scripts/research/g3_calibration_chart.py --out site/static/img/2026-11-08-gate-3-slides/calibration.svg
```

Figures were written from a clean worktree at the commit their sidecars name, to a scratch folder, then copied here. The other track plot and the error curve differ only in `--scenario 81048 --at 4580,5180` and
`tma2-plot errors`. The `.json` sidecar next to each SVG names the inputs' digests, the command
and the commit.

## Not achieved

- An honest joint uncertainty: 0.835 of rows within the χ²₄ 95% point against 0.92 required,
  mostly because the calibration keeps the solve's near-singular correlations.
- Meaningful course intervals: on half the rows the 95% course interval is the whole circle.
- Learning: the head is nearly a constant and no better than a per-slice temperature.
- Time-late E-w: no gain over the causal model (−0.0018 [−0.0082, +0.0057] in gap recovered).

## Next

Spec 009, recommended and adopted unless the owner objects: course reported as circular or as
undetermined; the stated uncertainty gated on observability by a causal proxy, with a
"manoeuvre suspected" flag; correlation shrinkage and training on the exact errors the gate
scores. E's points stand; its raw covariance must not be shown as an uncertainty.
