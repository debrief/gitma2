---
title: "Slides: leg splitters in the demonstrator"
date: 2026-11-21T22:00
tags: [slides, spec-036]
---

import Slides from "@site/src/components/Slides";

The [demonstrator](/demo) now asks two questions separately: a **leg splitter** says where the
target manoeuvred, and a **TMA solver** fits the window. The physics layer joins its legs across
the splitter's spans. On the page's presets, the joined-legs arctan search came close to the
layer told the truth on two turns between ownship turns. Debrief's 2015 slicing cannot see a
turn made during ownship's turn, and independent slices split between two real turns.
Spec: `specs/036-leg-splitters/`. Not a result: three presets, a few noise draws.

<!-- truncate -->

<Slides slug="2026-11-21-leg-splitters-slides" />

## What was built

- **Two drop-downs.** "Leg splitter → TMA solver". The splitter is disabled for a solver that
  takes no legs. Spec 035's `layer-cv` and `layer-oracle` links still load, as the layer with
  the splitters `none` and `truth`.
- **Six splitters** (`site/static/demo-data/js/splitters.js`, `arctan.js`):
  - **none:** one leg.
  - **truth:** told the true spans and their kinds (the oracle).
  - **Debrief 2015 arctan slicing:** the three-parameter arctan law on each steady ownship
    leg, one split, a 2-minute buffer, ZigRatio 0.6 (our choice: the 2015 default is not on
    file).
  - **Independent slices:** ownship subtracted, recursive.
  - **Joined legs:** position continuous, velocity steps at knots, forward selection with
    every parameter refitted, then re-placement.
  - **C:** spec 005's classical segmenter, spec 021's JavaScript port, its segmentation at the
    window's last bearing.

  Only the truth splitter sees the true spans; a test checks it.
- **Panels:**
  - A legs panel: found within 120 s, missed, false, timing.
  - Orange spans on the charts and diamonds on the track.
  - "Run all splitters", which runs every splitter through the layer on the same window and
    noise draw.
- **Schema and checks:**
  - Schema 0.38.0: `DemoScenario.splitter`, `DemoSpan.stat`, `DemoSplitterInfo`.
  - 23 Node tests and the Chromium run of the built page.

## Readings (presets, σ 1°, seeds 1–5; record `experiments/20261121-demo-splitters/`)

| Preset | Splitter | Found / true | False | Median range RMS |
| --- | --- | --- | --- | --- |
| Two turns between ownship turns | none | 0 / 10 | 0 | 27.0% |
| | Debrief 2015 | 5 / 10 | 0 | 14.5% |
| | independent slices | 3 / 10 | 7 | 37.8% |
| | joined legs | 9 / 10 | 1 | 2.6% |
| | C (3 draws) | 3 / 6 | 4 | 8.2% |
| | truth | 10 / 10 | 0 | 2.0% |
| Turn during ownship's turn | Debrief 2015 | 0 / 5 | 0 | 31.9% |
| | independent slices | 5 / 5 | 0 | 1.4% |
| | joined legs | 3 / 5 | 2 | 3.1% |
| | truth | 5 / 5 | 0 | 1.5% |
| Held course | every splitter | 0 / 0 | 0 | 0.7% |

## Critical reading

- **These are anecdotes, not a ranking.** Three hand-drawn presets and five draws. The
  thresholds (independent slices τ = 40, joined legs τ = 25, in units of σ²) were set on the
  same kind of presets. No false-alarm rate, no interval.
- **No splitter wins everywhere.**
  - Joined legs are best on two turns inside ownship legs.
  - Independent slices are best where the target turns during ownship's turn. There an
    instant knot is placed 2–4 minutes late, which the 120-s rule counts as a miss plus a
    false span.
- **Debrief's limits are structural** (Annex B):
  - It cannot see a turn made during ownship's turn, by design.
  - Its ratio is not tied to the noise.
- **C does poorly here.** It has no zig veto, so ownship's turns become false transitions (C″
  adds the veto). It was tuned for Annex B's targets, not these presets. It also takes about
  3½ minutes per two-hour window in JavaScript.
- **The truth row is told the kinds of change; the splitters are not.** Every splitter span gets
  the layer's speed-continuity prior, C's convention. On the two-turn preset (a speed change
  at the second turn) this handicaps the splitters slightly against the truth.
- The comparison table's figures were computed at commit `69e98c2`. Review fixes since then
  touch only C's cut to four spans, which never fired here, and how knot strengths are shown.

## Next (owner's choice)

1. Score joined legs against C″ and `ctl` on Annex B data on spent seeds (development), and
   register it only if it holds.
2. A finite-length turn (the arc model's) where a knot meets ownship's turn.
3. Or keep this as a teaching tool: the page now shows that finding the legs, not the solve,
   is the hard part.
