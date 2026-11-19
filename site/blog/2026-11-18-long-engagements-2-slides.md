---
title: "Slides: long engagements, carrying state, an incremental C, realism"
date: 2026-11-18T03:00
tags: [slides, spec-024]
---

import Slides from "@site/src/components/Slides";

Note 12's three recommendations, built and measured on the same four engagements. Carrying state
between time-late windows makes the search cheaper but not more accurate. The incremental C
is 1.7 times cheaper but loses accuracy, so it is not adopted. With realism, the contact the
ownship tends keeps its accuracy, and a contact it does not tend drifts away and is three to five times
worse where it can be solved at all. An investigation, not a gate. Spec: `specs/024-long-carry-incremental-realism/`.

<!-- truncate -->

<Slides slug="2026-11-18-long-engagements-2-slides" />

## What was built

- **`ctl-carry`** (`src/tma2/long/carry.py`): the standing control with its start from nothing
  replaced by the previous window's declared track and manoeuvres. It is solved beside `ctl`
  on every window, and that `ctl` equals spec 023's runner within 1 mm.
- **An incremental C** (`src/tma2/long/incremental.py`): one confirmation per 2-hour block of
  estimates, cropped to each estimate's window. With blocks of one it equals the per-window run.
- **Realism** (`configs/long/realistic.json`): the ownship steers on what it measures; contact
  gaps; detection fading with range; a second contact with mis-association where the two cross.
  It is drawn from its own random stream, so contact 1 is spec 023's target.
- A set selector on the long-engagement sections of [the viewer](/viewer) and
  [the time-late page](/timelate), research note 13, and the record `experiments/20261117-long2/`.

## What was found

- **Carry**: the median ratio of `ctl` to `ctl-carry` per window is 1.00 in every set. Wins and
  losses are mixed: 15 to 20 on spec 023's engagements, 22 to 11 on realistic contact 1. The
  start from the carry costs about 55% of the search it replaces.
- **Incremental C**: E and C″ cost 32–42 s an estimate against 53–73 s per window. Median range
  error is worse at 24 and 48 hours (E 29.8% and 35.6% against 14.3% and 20.9%).
  - The first estimate of each block matches the per-window run.
  - The later ones are 2 to 4 times worse.
  - The cause lies in the longer history before the crop and is not established.
- **Realism**:
  - Contact 1 is held 67–85% of the time, and `ctl` stays at 1.5–2.2% (spec 023's: 1.6–2.1%).
  - Contact 2 drifts to a median 27–147 km and is held 10–22% of the time beyond 6 hours. On the windows
    with at least five minutes of its bearings, `ctl` is at 6–8%, and the true-history fit is at 2–4.5%.

## What was not achieved

- No accuracy gain from carrying state, and the incremental C is not usable as built.
- Mis-association is barely exercised (0–8 swapped bearings an engagement).
- One engagement per length: these are anecdotes, not rates.

## What comes next (the owner's choice)

Recommended: a registered study on 6- and 12-hour realistic engagements (seeds 349 to 351,
about 160 CPU-hours). It would test carry non-inferiority, the cost of an untended contact and
the IMM's drift. Or measure shorter incremental blocks on tuning data first, or stop the
long-engagement track here.

Figures: `scripts/research/long2_charts.py`, with a sidecar beside each SVG.
