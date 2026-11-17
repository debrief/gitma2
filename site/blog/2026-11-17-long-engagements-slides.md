---
title: "Slides: longer engagements, 6 to 48 hours"
date: 2026-11-17T17:00
tags: [slides, spec-023]
---

import Slides from "@site/src/components/Slides";

Issue #42 asked what it would take to run our TMA on engagements of 6 to 48 hours. On four
simulated engagements (seed 348), every standing system ran to the end, on windows of the size
it was built for. The time-late control keeps its accuracy at every length. Running it on a whole
long period does not work as written, and several parts of the code assume one ownship zig. An
investigation, not a gate. Spec: `specs/023-long-engagements/`.

<!-- truncate -->

<Slides slug="2026-11-17-long-engagements-slides" />

## What was built

- **A long-engagement simulator** (`src/tma2/long/sim.py`), separate from generator 0.6.0, whose
  output stays byte-identical. The target follows Annex B's statistics. The ownship turns at the
  start of each 20–40 minute leg and keeps the target at 3–25 km, steering on the true target
  position.
- **Windows** (`src/tma2/long/windows.py`) in the form every estimator already reads, and C″'s zig
  veto applied at every ownship turn.
- **Real-time and time-late runners** (`src/tma2/long/realtime.py`, `timelate.py`), the
  `tma2-long` CLI and the `long.yml` workflow.
- **Long-engagement sections** on [the viewer](/viewer) and [the time-late page](/timelate),
  precomputed in Python.
- **Research note 12** (`docs/research/12-long-engagements.md`) and the record
  `experiments/20261117-long/` (`tables.md` generated from `summary.json`).

## What was found

| | 6 h | 12 h | 24 h | 48 h |
|---|---|---|---|---|
| time-late `ctl`, median range error | 2.0% | 1.9% | 2.7% | 1.6% |
| time-late C″ | 20.5% | 15.0% | 8.5% | 9.0% |
| real-time E, every 10 min | 17.4% | 17.5% | 14.3% | 20.9% |
| real-time C″ | 23.2% | 17.1% | 13.2% | 19.9% |
| real-time IMM (answered) | 19.0% (1.00) | 35.2% (1.00) | 15.0% (0.96) | 30.9% (0.81) |

- `ctl` on one long period: 1 min for half an hour, 114 min for 6 hours, and at most ten
  manoeuvres (6 hours held 16).
- The real-time model re-solves its 2-hour window for every estimate: 27–37 s on one core.
- The IMM over the whole engagement took 426 s at 48 hours against 6 s at 6; the cause is not
  established.
- The Cramér–Rao bound over a whole engagement needs 4.5 GB at 48 hours.

## What was not achieved

- One engagement per duration: these are anecdotes, not rates.
- The scenario is kind: the ownship steers on the truth, contact is never lost, one target.
- No whole-engagement solve, and E does not run in the browser on these engagements.

## What comes next (the owner's choice)

Recommended: carry state between windows (each window starts from the previous solution), then
an incremental C so a real-time estimate costs the same at hour 48 as at hour 2; realism (an
ownship steering on its own solution, contact gaps, a second target) before any registered study.
The next fresh seed is 349.

Figures: `scripts/research/long_charts.py`, with a sidecar beside each SVG.
