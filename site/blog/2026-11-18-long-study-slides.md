---
title: "Slides: long engagements, the registered study"
date: 2026-11-18T15:30
tags: [slides, spec-025]
---

import Slides from "@site/src/components/Slides";

These slides are the illustrated companion to
[the registered study's write-up](/blog/2026/11/18/long-study). Each rule gave its registered
output:
- E1, carrying state: non-inferior by 0.008;
- E2, the untended contact: about 1.5 times worse where it is held;
- E3, IMM drift: not shown.

The panel narrowed all three. Spec: `specs/025-long-study/`.

<!-- truncate -->

<Slides slug="2026-11-18-long-study-slides" />

## What was built

- **The estimands** (`src/tma2/long/study.py`): E1 to E3, the soundness checks and a bootstrap
  over engagements. They were registered in `experiments/20261118-ls-decision/` with the run
  files and code bound by digest.
- **An IMM runner** over whole engagements (`long/realtime.py` `imm_states`), with the CLI
  parts `tma2-long imm` and `tma2-long study`.
- **The study configs** `configs/long/study-{tuning,val,test}.json` (seeds 349, 350, 351).
- **The records**: tuning, validation and test (`experiments/20261118-ls*`), the panel's
  `review.md` and `supplement.json` (`scripts/research/long_study_supplement.py`).

## What was not achieved

- No accuracy gain from carrying state was shown.
- E2 and E3 describe this simulator, whose realism is set by hand.
- Mis-association is not exercised.

## What comes next (the owner's choice)

Recommended: stop the long-engagement track here as a simulation study, and keep `ctl-carry` as
an optional cost measure for tended contacts up to 12 hours. Reopen it only with measured
realism, an ownship steered by its own track, or association.

Figures: `scripts/research/long_study_charts.py`, with a sidecar beside each SVG.
