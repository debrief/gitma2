---
title: "Kickoff: carrying state across gaps, against joining through them"
date: 2026-11-18
tags: [kickoff, spec-026]
---

Spec 025 showed that one solve over several periods of a target beats solving each alone. The
cheaper thing an analyst would do instead is to solve period by period and hand each answer on
to the next. This task measures that carry against the joint solve, as a registered study on
fresh seeds (owner, option B). Nothing is trained.

<!-- truncate -->

## Where we are

- [Spec 025](/blog/2026/11/18/joined-periods): the joint solve gains on every split (Annex B
  3.10 [2.22, 4.58]), mostly by making periods without their own ownship turn answerable; its
  panel asked first for a comparison with carrying state.
- Spec 024 (another session) built `ctl-carry` for overlapping windows; across a gap it has
  nothing to carry, so it is not this comparison.

## Where this task moves to

- Spec `specs/026-carry-across-gaps/`. Carry: each later period starts its search from the
  previous period's declared state, run forward at constant velocity through the gap.
- Registered: carry ÷ joint (is joining better?) and alone ÷ carry (does carrying help?),
  per split, with engagement intervals.
- Plan: build the carry and test that without a carried start it equals `ctl`; tune on spent
  seed 353; decision record; validation seed 360; test seed 361; panel; write-up.
- Risk: a manoeuvre in the gap makes the carried state wrong, and a carry can only start a fit
  that uses the period's own bearings, so a period without its own turn may stay unanswerable.

## How progress will be shown

- Charts of carry ÷ joint and alone ÷ carry by split, by kind of period and on rows a period
  determines alone; one engagement's tracks with all three systems.
