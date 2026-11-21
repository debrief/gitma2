---
title: "Kickoff: an interactive TMA demonstrator"
date: 2026-11-21T16:00
tags: [kickoff, spec-035]
---

The owner asked for a page where stakeholders drag an ownship and a target, narrow an analysis
window and watch a time-late solution respond. The aim is a feel for where the solvers do well,
and where the geometry or a target manoeuvre breaks them, without reading gate reports. Spec:
`specs/035-interactive-demonstrator/` (the owner's draft is kept beside it).

<!-- truncate -->

## Where we are

- **Both research tracks are closed.** The time-late track stopped with `ctl` standing (spec 019).
  The long-engagement track stopped with `ctl-prior` adopted (spec 034).
- **The browser work exists already.** Specs 020 and 021 run Gate 2's E end to end in ONNX
  Runtime Web. Spec 021 ported batch least squares and C's host code to JavaScript and checked
  them decision for decision.

## Where this task moves to

- **SRD:** §1 (a demonstrator on mock data) and §7 step 5 (the browser artefact).
- **Owner's decisions (interview):**
  - **Solvers:** JavaScript least squares and ONNX solvers, both now. The ONNX ones are the
    physics layer (one leg, or told the true manoeuvre times) and E.
  - **Settings:** bearings every 5 s at 1°.
  - **Errors:** read across the whole window (RMS and worst) beside the Cramér–Rao bound, not at
    one reference time.
  - **Ellipses:** off by default.
- **Acceptance:** the draft's six criteria. Every preset solves with every panel. Noise-free good
  geometry is under 0.1% in range. No zig shows red. A target turn raises the mismatch flag, and
  one target leg clears it. The URL and JSON round trips agree. The build and PR preview work.
- **Plan:**
  1. LinkML types.
  2. Track, bearing and metric modules, tested in Node.
  3. A time-late export of the physics layer.
  4. The page.
  5. Golden least-squares vectors from Python, and a Chromium check in CI.
- **Risks:**
  - Two least-squares implementations drifting apart (answered by the golden vectors).
  - One noise draw misread (answered by the bound beside the error).
  - E's run time in a browser.

## How progress will be shown

The slides post will carry track plots made by the page's own code from its presets:

- good geometry with least squares;
- no zig;
- a target turn, with one leg against the oracle told the turn.

It will also carry the turn's range error against time (time down the left, as on the page).

**2026-11-21, later.** The owner, looking at the learned model's wandering own track: "it's most likely
that the target tends to travel in straight legs; have we considered examining the points in the
TMA solution and predicting steady legs?" Spec 016 did, from the model's manoeuvre head rather than
its points (`learned-arc`: the arc model fitted at the spans where the head's probability is over
0.5), and the classical control beat it. The demonstrator now offers that read-out's shape beside
the own track: **read as steady legs** (`tlm-s1-legs`, `-s2-`, `-s3-`), the same network's spans
(`spans_from_logit` ported to `tlm.js` and checked against Python's on the golden logits) handed to
the physics layer, which fits constant-velocity legs joined at them. Two things to know before
choosing it. First, it is the chord model of Gates 1–2, not spec 016's arc model with Annex B's
prior, so it reproduces the read-out's design and not its figures. Second, on every preset the head
stays well under 0.5 at every token, so at
the registered threshold it declares no manoeuvre there and the legs read-out is one leg: the page
now says the largest probability it found, and the owner asked for the threshold as a slider: it is
one (shown for the learned solvers, 0.05 to 0.95, kept in the link), so the detector can be tuned by
eye on the page, which is a demonstration and not a result. That is spec 016's finding in miniature: the comparison
measured the model's untuned detector. The points themselves are not segmented: a change-point fit
on a smoothed track double-smooths and discards the bearings; what the points could do is propose
times to a search, which is on three panels' lists and not built.

**2026-11-21, later still.** Two more changes at the owner's word. The course and speed error charts
now carry the ownship's own course and speed in blue, on a scale of their own, so its turns can be
read against the error. And the target-turn preset no longer has the target turning at 60 minutes,
the same moment as an ownship turn ("feasible, but it shouldn't be the basis of our analysis"): the
target now zigs at 50 minutes, between the ownship's turns at 30 and 60. What the page then shows,
over three noise draws (a demonstration, not a result): one leg 21 to 22% RMS range error, told the
turn 0.3 to 0.5%, the model's own track 11 to 17%. The model's manoeuvre head states 0.00 to 0.02
within three minutes of the true turn, on all three training seeds; where seed 3 states anything
(0.2 to 0.4) it is at 30 to 34 minutes, an ownship turn. With the threshold at 0.1, seed 3 declares
spans near 30 and 58 to 61 minutes, both ownship turns, and the legs fitted there reach 4 to 8%,
because two free breaks either side of the true turn can absorb it; that is not the head finding
the turn. A classical scan of one free break gives a chi-square of 731 to 748 on 715 bearings
anywhere from 30 to 60 minutes against 4,815 for one leg: that the target manoeuvred is certain,
when is weakly determined by a chord with four free unknowns.

