---
title: "Kickoff: leg splitters in the demonstrator"
date: 2026-11-21T20:00
tags: [kickoff, spec-036]
---

In the [demonstrator](/demo), the physics layer told the target's true manoeuvre times is
excellent: about 1% range error where one leg gives 25–35%. Real systems are not told the times.
The owner asked for effort on target leg identification, remembering Debrief's arctan slicing,
and for a demo where leg splitters and TMA solvers are chosen separately so they can be compared.
This is spec 036.

<!-- truncate -->

## Where we are

- The demonstrator (spec 035) offers JavaScript least squares, the physics layer with one leg or
  with the true manoeuvre times, and spec 016's learned whole-period model.
- The project's own leg identification:
  - C, the classical segmenter: Gate S, then Gate 2's segmenter, frozen.
  - The time-late evidence search `ctl`, the standing time-late system.
  - The finding of specs 013–019: much of the remaining gap is ambiguity in the bearings, not
    a weak search.
- Research note 07 tried the arctan law as a sliding-window detector. Alarms used directly as
  knots failed. A window nominating a change and the whole history confirming it worked, and
  that became C.

## Where this task moves to

- Spec `specs/036-leg-splitters/`: SRD §1, Annex A, and Annex B's background table.
- Acceptance:
  - Splitters other than the truth never see the true times.
  - No false split on held-course presets.
  - On a two-turn preset the best splitter's layer solve comes close to the oracle's.
  - All of it runs in the built page.
- Plan:
  1. Two drop-downs: leg splitter → TMA solver.
  2. Splitters:
     - Debrief's 2015 arctan slicing, as published.
     - A multi-leg slicing.
     - The arctan law with joined legs, searched over the whole window.
     - C, in the browser.
  3. A legs panel and a "run all splitters" comparison.
- Risks:
  - C is slow in a browser (minutes).
  - Thresholds set on a few presets are not false-alarm rates.
  - Nothing here is a result.

## How progress will be shown

- A dot chart of range error per splitter on three presets over five noise draws.
- A track plot of the two-turn preset with each splitter's track and knots.
- Data: `scripts/research/demo_splitters.mjs` on the page's own presets, recorded in
  `experiments/20261121-demo-splitters/`.

## 2026-11-22: bearings lost in ownship's turns

The owner noted that bearings are lost while ownship turns and for two minutes after each turn
ends. The demonstrator now drops them by default. A scenario's `turn_loss_s` sets the tail
(120 s); null keeps every bearing, and a checkbox under the noise controls turns the loss off.
Lost bearings keep their rows, flagged in the problem's `bearing_valid` (schema 0.39.0), so every
solver and splitter keeps its regular time grid and skips them, as Python's `valid` column does.
Least squares, the physics layer, C, the arctan splitters and the learned model's inputs all
ignore them, and the plot, bearings chart and residuals hide them. The noise is still drawn for
every row, so the bearings that are kept do not change. On the good-geometry preset, 120 of
1,429 bearings are lost (three turns of 1 to 1.5 minutes, each plus two minutes).

Spec 035's golden problems and spec 036's readings and figures kept every bearing, so their
scripts and tests pin `turn_loss_s: null`. With the loss on, joined legs on the two-turn preset
places the first turn at 50 min instead of 46.5 on seed 1, outside the 120 s match. Seeds 2, 3
and 5 still find both turns. This is one draw, not a result.
