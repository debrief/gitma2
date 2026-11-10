---
title: "Slides: Gate H, headroom under bearing-error mismatch"
date: 2026-11-10
tags: [slides, gate-h, spec-010]
---

import Slides from "@site/src/components/Slides";

The illustrated companion to [the Gate H write-up](/blog/2026/11/10/gate-h): the four kinds of
bearing-error mismatch, the three estimators that share one solve, the verdict on the test seed
(headroom not material) and what the review panel narrowed.

<!-- truncate -->

<Slides slug="2026-11-10-gate-h-slides" />

## What the figures show

- **Mismatch.** The bearing error of one engagement (tuning seed 320, the first with a stated σ
  of 1°) with no mismatch, then under correlated error, slow bias and outliers at central
  severity, then all four together.
- **Track plot.** Engagement 3 of a demo split under the primary condition: ownship blue, target
  red, and the trails of the plain solve, the robust control and the error-model-informed fit
  from the zig, with marks and 1-σ ellipses at zig + 10 and + 20 min.
- **Every condition.** Median relative range error of the three estimators on the 16 validation
  conditions (seed 321, 1,000 engagements each, true segmentation).
- **Verdict.** R, the control's median range error over the informed fit's, with its 97.5%
  interval on the six test conditions (seed 322), against the 10% threshold.
- **By range.** R by quartile of true range on the test seed's primary condition. Post hoc.

## Reproducing the figures

The four charts are drawn by `scripts/research/gh_charts.py` from the committed records under
`experiments/20261110-gh-val/` and `experiments/20261110-gh/` and from one engagement generated
in the script; the range-band record is made by `scripts/research/gh_range_bands.py` from the
test run's `errors.npz`. The track plot's demo split:

```bash
uv run tma2-generate --seed 320 --count 400 --out demo --ranges configs/man2-ranges.json \
  --heldout-ranges configs/man2-heldout.json --format f32pack \
  --mismatch configs/gateh/conditions.json#all-central
uv run tma2-hpredict --in demo/train.f32pack --kind nominal --start 0 --count 16 --out demo/nominal.ndjson
uv run tma2-hpredict --in demo/train.f32pack --kind robust --plan configs/gateh/gh-a.json --start 0 --count 16 --out demo/robust.ndjson
uv run tma2-hpredict --in demo/train.f32pack --kind attainable --mismatch-truth demo/train.mismatch.npz --start 0 --count 16 --out demo/informed.ndjson
uv run tma2-plot track --truth demo/train.f32pack --predictions demo/nominal.ndjson demo/robust.ndjson demo/informed.ndjson \
  --labels "plain solve,robust control,error-model-informed fit" --scenario 3 --at 2060,2660 \
  --out site/static/img/2026-11-10-gate-h-slides/track-3.svg
```

Sidecars next to each SVG name the digests, the command and the commit (clean tree).

## Not achieved

- Nothing was shown about other error families, target-motion mismatch or real data.
- The solve's 25% distance from the Cramér–Rao bound is unexplained.
- The comparison on the segmenter's own output was delivered after the verdict.
- No error-against-time figure: the estimators answer at four scored times only.

## Next

- Learning the bearing-error model for this solve is not pursued; the robust control is kept.
- Recommended next, if the owner does not object: the same harness on the segmenter's output
  with a zig-coupled bias and bursty outliers. Then the scaled end-to-end regressor.
