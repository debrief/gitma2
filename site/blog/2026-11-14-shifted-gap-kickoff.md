---
title: "Kickoff: the standing time-late control, and is the shifted-prior gap identifiability?"
date: 2026-11-14T18:00
tags: [kickoff, spec-017]
---

The owner has chosen the panel's recommendation after study L: the classical control
becomes the standing time-late system, and one cheap classical study asks whether the gap
left under a shifted manoeuvre prior can be closed by anyone. Spec:
`specs/017-shifted-gap/`. Nothing is trained and no GPU is used.

<!-- truncate -->

## Where we are

[Study L](/blog/2026/11/14/time-late-learned) was decided by its panel in one round. The
classical control stands: it removes most of the damage from outliers and correlated
bearing errors and from quiet targets. The learned model's reported track beat it nowhere,
and the panel showed that loss was the model's untuned manoeuvre detector. Open for every
system: on targets that manoeuvre more often and less sharply than Annex B says, the
control's error is 1.7 to 2.1 times that of a fit told the true history, with half the
manoeuvres missed.

## Where this task moves to

SRD §1 and §5; a line in §9 records the standing system (proposed; the owner merges).

1. **Detectability.** For every true manoeuvre, how much worse the bearings are fitted
   when it is left out of the true history. No search, no evidence approximation.
2. **The gap, split.** A reference told only the detectable manoeuvres. The part of the
   gap that remains for it is identifiability; the part between it and the control is what
   a better search or evidence could win.
3. **The true prior.** The control's search given the shifted targets' own statistics: what
   knowing them is worth.
4. **Registration** of the rule, thresholds and sizes before the fresh seeds (343
   validation, 344 test), with the rule's power stated.
5. **What study L's record owes**: the scored weights' digests, the export check on the
   trained models, IMM and EKF tracks beside, a reference fitted to edited bearings, tests
   for the runner and scorer.
6. Panel, write-up, slides.

If the gap is mostly identifiability, the learned-proposer idea is not taken and the
time-late track is written up. If it is mostly attainable, a proposer study using the
three trained models is proposed to the owner.

Risks: "detectable" depends on a threshold (three are registered and the result is given
at each); the reference told the true history drifts in a quarter of shifted periods (its
times are held, and the share stated); a split may come out mixed, which is a result.

## How progress will be shown

- The distribution of detectability for Annex B and shifted manoeuvres, and the control's
  miss rate against it (tuning 342, then test 344).
- The gap as two stacked parts per split and threshold, with intervals.
- The true-prior search beside the control.
- Track plots of periods with undetectable manoeuvres, chosen by a rule in the script.
- All from committed experiment folders by a script named in the slides post.

**Update, 2026-11-14 (evening).** Done. Validation on seed 343 passed soundness; the test
on seed 344 was scored once and decided by the panel in one round. The result and what the
panel made of it are in [the write-up](/blog/2026/11/14/shifted-gap) and
[the slides](/blog/2026/11/14/shifted-gap-slides).
