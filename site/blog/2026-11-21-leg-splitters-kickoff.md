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

## Updates

- 2026-11-22: from the owner's review of the merged demo:
  - An arrowhead at the end of each track shows which way it is heading.
  - A fourth optional chart, "course & speed", shows both vessels' course or speed (a drop-down:
    course, speed or both) with the estimate dashed. True turns are shaded (blue ownship, red
    target); turns a splitter detected are solid strips: orange target turns on the right edge,
    teal ownship turns on the left. Only Debrief's slicing detects ownship turns, so only it
    draws the teal strips.
  - The error chart's quantity is a drop-down, so the chart is as tall as its neighbours and
    their time axes line up.
  - The Preset drop-down shows the preset the scenario matches, or "custom" once edited.
  - Dragging a waypoint (circle) now keeps the adjacent legs' speeds, so their durations change.
    Dragging a leg's square keeps its duration, so its speed changes.
  - Ctrl-click (⌘-click) deletes a waypoint.
  - Each leg's speed label sits on the leg's north side (west for a north–south leg), clear of
    the square handle and the cursor that drags it. The read-out during a drag sits above and
    to the left of the cursor. It says what is kept and what changes: "Keeping time: speed
    changes" for a square (the leg's minutes, its old and new speed and course), "Keeping speed:
    leg times change" for a circle (each adjacent leg's speed, its old and new minutes). The
    hover tooltips on squares and circles say the same.
  - Schema 0.39.0: `TmaSolution.splitter_ownship_spans`, and the `DemoSplitterInfo` flags
    `detects_target` and `detects_ownship`.
