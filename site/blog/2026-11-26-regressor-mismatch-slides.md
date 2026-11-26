---
title: "Slides: the regressor under bearing-error mismatch"
date: 2026-11-26T21:00
tags: [slides, spec-037]
---

import Slides from "@site/src/components/Slides";

Spec 037 fine-tuned spec 012's regressor under simulated bearing errors, asked it for
intervals, and passed its estimate through the physics layer as a prior. The deck shows the
test record and what the review panel made of it. The critical account is the
[write-up](/blog/2026/11/26/regressor-mismatch); this post is its illustrated companion.

<!-- truncate -->

<Slides slug="2026-11-26-regressor-mismatch" />

## What the figures show

- **Range error by condition**: the median over 1,000 test engagements, for C″ with the robust
  final solve, the unchanged and fine-tuned regressors, and the robust solve told the true
  manoeuvre times. The fine-tuned regressor sits beside that last solve; C″ sits well above it.
- **The registered readings**: each paired ratio with its 95% interval. Green is wholly above
  1, orange wholly below.
- **Coverage**: the average coverage of the stated 95% intervals on clean data, the primary
  condition and the kinds outside the training mix. The panel found it does not hold slice by
  slice.
- **Track plots**: engagement 20 of the test seed (scenario 51), clean and under the primary
  condition, with marks at 3,670 s and 4,270 s. Ownship blue, target red. It was chosen because
  C″ is right on clean data (4.5% range error) and fooled under mismatch (28%), while the
  regressor and the hybrid stay within 5%. It is one engagement picked to show the mechanism,
  not a typical one. Ellipses are off: the hybrid's covariance must not be shown.

## Reproducing the figures

```bash
# charts, from the committed record
uv run python scripts/research/rmis_charts.py --out-dir site/static/img/2026-11-26-regressor-mismatch

# track plots: the test split regenerated at the test's commit (b5aeaf9, a git worktree),
# predictions from results/headroom-rm-test-371-<condition>-plan-45819634327 (predictions/1, ft-s1, 4)
uv run tma2-generate --seed 371 --count 5600 --ranges configs/man2-ranges.json \
  --heldout-ranges configs/man2-heldout.json --format f32pack --out <dir> \
  --mismatch configs/rmis/all-conditions.json#all-central
uv run tma2-plot track --truth <dir>/train.f32pack \
  --predictions c2-robust.ndjson ft-s1.ndjson hyb-s1.ndjson \
  --labels "C″ robust,regressor (fine-tuned),hybrid" --scenario 51 --at 3670,4270 --no-ellipses \
  --out site/static/img/2026-11-26-regressor-mismatch/track-20-all-central.svg
```

Sidecars next to each SVG name the digests, the scenario, the command and the commit.

## Not achieved

- A classical control that is told what the regressor is told. The gain over C″ is mostly C's
  segmenter breaking.
- A test on errors outside what training covered in their statistics.
- Intervals that hold slice by slice.
- The readings by time since the last target change, and the hybrid on the kinds outside the
  mix.

## Next

- Recommended, the owner's choice: a prior-informed classical control and a decomposition of
  the gain into prior and bearings, on CPU, nothing trained. No further GPU spending.
