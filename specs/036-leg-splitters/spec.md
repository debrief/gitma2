# Spec 036: leg splitters in the demonstrator

**Created**: 2026-11-21

**Status**: built. Not a gate, not a registered study; nothing trained, no seed used (the page's
own noise generator). Development readings only, on the demonstrator's presets.

**Input**: the owner, 2026-11-21: "in the browser demo that is told about the legs, the TMA
performance is great. can we invest some effort into target leg identification? Remember the
arctan paper." Then, on the options offered: "ok, let's have a demo of the leg solvers, so we can
compare them. Hmm, maybe the solver drop-down could have two blocks: leg splitters and TMA
solvers?"

**SRD traceability**: §1 (a demonstrator of the solvers on mock data), Annex A (steady-leg
segmentation), Annex B's background table (Debrief ArcTan slicing 2015; the multi-leg slicing
note 2017); research note 07 (the arctan law; "the window to notice, the whole history to decide").

## Summary

Spec 035's demonstrator offers a segmented solve only when the page tells it the true manoeuvre
times. This spec splits the solve into two stages a user chooses separately: a **leg splitter**
that states where the target manoeuvred, then a **TMA solver** that fits the window. The
physics layer takes its legs from the splitter; the other solvers take none. A legs panel reads
the splitter's spans against the truth and a comparison runs every splitter through the layer on
the same window and noise draw.

## Decisions

| # | Topic | Decision (and why) |
| --- | --- | --- |
| 1 | Layout | Two drop-downs in one box, "Leg splitter → TMA solver" (the owner's "two blocks"); the splitter is disabled for a solver that takes no legs |
| 2 | Solvers | Spec 035's `layer-cv` and `layer-oracle` become one solver, `layer`, whose spans come from the splitter; old links and JSON map to `layer` + `none` / `truth` |
| 3 | Splitters | none; truth (the oracle); Debrief 2015 arctan slicing; a multi-leg slicing with independent slices; the arctan law with joined legs, searched over the window; C (spec 005, spec 021's port) |
| 4 | Debrief variant | Kept faithful to its known limits (Annex B): one split per steady ownship leg, a fixed 2-minute buffer, the three-parameter arctan law, ZigRatio 0.6 on the score per bearing (the 2015 default is not on file: our choice, stated on the page) |
| 5 | Independent slices | Kept as the instructive failure: on two turns its best single split lands between them (the 2017 note), and short slices without an ownship turn absorb a misplaced break through their free range (research R1) |
| 6 | Joined legs | Position continuous, velocity steps at instants (2 parameters per knot); forward selection with every parameter refitted, then each knot re-placed with the others held; τ = 25 σ², at most four knots (the layer's eight) |
| 7 | C | Unchanged code (frozen parameters, no evidence, no zig veto); its segmentation at the window's last bearing; confirmation through `viewer-data/layer.onnx`. About 3–4 minutes on a two-hour window |
| 8 | Truth | Only the truth splitter is given the problem's true spans; the worker strips them for every other splitter (tested) |
| 9 | Matching | A stated span is a found manoeuvre when within 120 s of a true one (each matched once, nearest centres first), the convention of specs 013–019 |
| 10 | Rows | Splitters run on 10-second rows (C's parameters are in rows of 10 s), at most 720 |

## Requirements

- FR-001: the toolbar shows a leg-splitter drop-down and a TMA-solver drop-down; changing either
  re-solves; the splitter drop-down is disabled for solvers that take no legs.
- FR-002: the worker runs the splitter, then the solver with the splitter's spans; the solution
  carries `splitter`, `splitter_spans`, `splitter_runtime_ms`, `splitter_message` (schema 0.38.0).
- FR-003: a "Target legs" panel: stated, found, missed, false, median timing offset; the truth's
  and the splitter's spans as times; the splitter's run time and notes.
- FR-004: the splitter's spans are shaded orange on the error, bearing and residual charts (the
  truth's red) and marked as diamonds on the estimated track.
- FR-005: "Run all splitters" runs every splitter through the layer on the current window and
  tabulates found/missed/false, range, course and speed RMS and run time; a changed scenario
  stops it; it can be cancelled.
- FR-006: a preset with two target turns inside ownship legs (not in spec 035's golden problem
  set, whose digest is bound).
- FR-007: `DemoScenario.splitter` (optional; absent means none), `DemoSpan.stat`,
  `DemoSplitterInfo`; spec 035 links and files still load.

## Acceptance

1. Node (`conformance/onnx/demo_node.mjs`): splitters other than the truth never read the true
   spans; no arctan splitter states a manoeuvre on held course (two presets, σ 1° and 2°, two
   draws); on the two-turn preset joined legs find both turns and the layer's range error is under
   3% (one leg over 10%); Debrief misses a target turn made during ownship's turn; C runs with the
   confirmation layer.
2. Chromium (`demo_page.mjs`): each splitter feeds the layer in the built page; the legs panel
   reads them; the comparison tabulates five splitters; legacy solver names load.

## Not in scope

The time-late standing system `ctl` (arc model, prior, evidence search: minutes per window in
Python, not ported); note 07's sliding-window split test as a separate splitter (C's GLR is the
same test at the whole-history fit); any claim beyond the presets: the readings are anecdotes.
