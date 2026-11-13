---
title: "Kickoff: time-late, repair and re-registration"
date: 2026-11-13
tags: [kickoff, spec-015]
---

Spec 014's study reproduced, and its review panel found two defects in the code it was
registered on. The owner has chosen the smallest next step: repair them, and decide the same
questions again on fresh seeds. Spec 015 trains nothing.

<!-- truncate -->

## Where we are

- [Spec 014](/blog/2026/11/13/time-late-classical) was decided by the panel in one round,
  five approve with findings. The whole-period search halves the track error of C″; about
  half of that gain is available without a search; the search declared a manoeuvre on 76% of
  targets that made none.
- Carried: C and C″, frozen; Gate T's and spec 014's searches, kept runnable as registered.
- Open: the evidence credits a manoeuvre's duration with about 600 seconds of room where the
  prior allows 20 to 120, which rewards small short manoeuvres (re-ranked, the 76% is 47% to
  57%). The classing counts manoeuvres cut by the period's edge. The fit "told the true
  history" drifts into another history in 13% of periods. What the decided numbers are
  without these faults is not known.

## Where this task moves to

- SRD §5 and §9 (owner, 2026-11-13); the spec is `specs/015-time-late-repair/`.
- Judged by: every prior factor's density times its volume equal to 1 in a test; no reading
  built on a reference that fails the match rule; the four decided quantities stated again on
  a fresh test seed beside spec 014's, at every registered sensitivity value; tables
  generated from the summary file.
- Plan:
  1. A new prior version in which every factor without a Gaussian residual gets the volume
     its density implies; the two smaller inconsistencies fixed with it.
  2. One rule for cut manoeuvres, used by the classing, the candidates and the counts.
  3. A reference that is held to the true times when it drifts, and flagged.
  4. A refit control that falls back to C″'s track when its fit diverges.
  5. The effect of each repair on the spent seeds 333 to 335.
  6. Register (forecasts first), validation seed 336, test seed 337, panel.
- Risks: a fifth volume error; the repaired evidence may under-count manoeuvres more than
  the old one over-counted; forecasts from spent seeds may again be wrong. We stop, as
  before, if the reference is not sound on validation.

## How progress will be shown

- False-manoeuvre rate on held course by period length, old evidence against repaired
  (test seed 337).
- The four decided quantities, spec 014 beside spec 015, with intervals.
- Headroom at each class threshold and on each split.
- Manoeuvring targets declared quiet, by number of true manoeuvres, for each prior.
- All from committed experiment folders by a script named in the slides post.
