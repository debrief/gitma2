---
title: "Kickoff: the long-engagement track as a whole"
date: 2026-11-21T13:00
tags: [kickoff, spec-034]
---

The long-engagement track has run through seven specs, from one engagement per length (spec 023)
to the ownship holding legs longer than the window (spec 032). The owner has adopted 2-hour
`ctl-prior` for the tended contact. This task writes the track up as a whole and closes it, as
spec 019 did for the time-late track. Spec: `specs/034-long-synthesis/`.

<!-- truncate -->

## Where we are

- **Standing:**
  - time-late `ctl` on 2-hour windows overlapping 30 minutes, stitched;
  - `ctl-prior` (the previous window's state and covariance as a prior, with a guard) adopted for
    the tended contact, up to 12 hours.
- **Decided along the way:** spec 026 (carried start, untended contact, the IMM over hours), spec
  028 (carried prior), spec 029 (blind 1-hour windows), spec 031 (against longer windows and a
  joint solve) and spec 032 (legs longer than the window).

## Where this task moves to

- **One account,** built from the figures of record in the registered test records. Each figure
  is read by a script and quoted with its convention and its panel's wording.
- **Beside the gains:** what stands with its faults, what was withdrawn, what was never tested,
  and what would justify reopening the track.
- **Nothing new is run:** no new seed, no registered result.

## How progress will be shown

- One chart of the decided ratios across the track, with their intervals.
- Median errors of the standing systems against their comparators.
- A short deck.
