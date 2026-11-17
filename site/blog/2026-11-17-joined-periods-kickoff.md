---
title: "Kickoff: time-late over several periods of one target, joined through the gaps"
date: 2026-11-17
tags: [kickoff, spec-025]
---

Contact on a target comes and goes. Until now every time-late study gave the standing system
one period per target. This task gives it two or three periods of the same target separated
by gaps with no bearings, and asks whether solving them together, with the target's track
continuous through the gaps, gives each period a better whole-period solution than solving
each alone. The owner chose it on 2026-11-17 (option C: motion continuity only, no
target-specific prior). It is classical work on CPU; nothing is trained.

<!-- truncate -->

## Where we are

- The time-late track was written up as a whole in
  [the time-late account](/blog/2026/11/15/time-late-synthesis). The standing system is the
  classical control `ctl` (evidence-scored search over manoeuvre histories with the arc
  model, declared at an evidence margin of 1), with its recorded faults. A learned time-late
  model was not shown to help, at this budget.
- The account named more information as one reason to look again: "several periods of the
  same target". This is that study.
- Open: whatever a gap hides. A manoeuvre in a gap can only be inferred from how the periods
  disagree.

## Where this task moves to

- SRD §1 (the time-late consumer), §5 (paired statistics, fresh seeds, registration before
  results), §9 (the owner's decision); spec folder `specs/025-joined-periods/`.
- Judged by a rule registered before the fresh seeds exist: on each split, the paired
  per-period ratio of median range error, `ctl` alone ÷ joint, with an interval that
  resamples engagements. *Gain* if wholly above 1; *harm* if wholly below 1 in range,
  course or speed on any split.
- Plan:
  1. Lay engagements out as two or three periods with gaps of about 5 to 30 minutes, from a
     stream of their own (the generator untouched).
  2. Build the joint solve: one search over histories across the whole span, with
     manoeuvres allowed in the gaps and bearings only in the periods.
  3. Tune span settings on seed 349; register the rule; validate on 350 (soundness); test
     on 351, once.
  4. Panel review, write-up and slides.
- Risks: a long gap may leave the joined track no better constrained than the periods
  alone, and an invented manoeuvre in a gap may cost more than the join gains. We stop at
  validation if the span reference or the joint solve fails its soundness checks.

## How progress will be shown

- Track plots of engagements with gaps: truth, `ctl` per period, the joint track (drawn
  through the gaps, dashed where there are no bearings), with true and declared manoeuvres.
- Charts of the per-period ratio by split, by whether the period holds an ownship
  manoeuvre of its own, by gap length, and by whether the target manoeuvred in the gap.
- Data: the test record on seed 351 (tuning 349, validation 350), Annex B, shifted-prior,
  wild-bearing and held-course splits.
