---
title: "Kickoff: time-late, classical controls and a learned whole-period model"
date: 2026-11-13T18:00
tags: [kickoff, spec-016]
---

The owner has chosen to build the classical controls the last panel asked for and, at the
same time, to train a learned whole-period model on GPU under a plan registered before any
result. The model is scored only once the controls exist. Spec:
`specs/016-time-late-learned/`.

<!-- truncate -->

## Where we are

[Spec 015](/blog/2026/11/13/time-late-repair) repaired the evidence, the edge rule and the
reference and decided the same quantities again on fresh seeds. The registered rule again
gave no GPU budget for identification on Annex B data, and the panel showed that 400 periods
cannot decide a 10% line there. Carried: the repaired evidence-scored search as the standing
time-late system, and C″ read as a track as the control beneath it. Open: against a
reference told the true history the search is 1.7 times worse under a shifted manoeuvre
prior, 1.4 under correlated bearing errors and 1.5 with outliers, and it invents a manoeuvre
on half of quiet targets. No classical remedy has been tried for any of these, and neither
study said anything about hedging.

## Where this task moves to

SRD §1 (the time-late consumer), §3 (the reported estimate comes from a declared read-out)
and §5 (a new row, proposed; the owner merges). Two tracks:

1. **Controls, CPU, nothing trained.** A hedged track (the probability-weighted mean of the
   search's candidates) and a declaration margin; a robust likelihood and a correlated-error
   likelihood in the search; a broadened manoeuvre prior with a mismatch diagnostic. Settings
   on tuning seed 338.
2. **A learned model, GPU.** A sequence model reads the whole period and gives the whole
   track, trained on the fly on a declared mix (Annex B, shifted and broadened statistics,
   quiet targets, correlated errors, outliers), three seeds, within the unspent part of the
   $50 budget.
3. **Registration first.** The model's plan, training mix, comparison and criteria are bound
   by digest in a decision record before the first training job. No criterion is registered
   that the sample size cannot decide.
4. **Controls' validation** (seed 340) is recorded; only then may the model be scored.
5. **One test scoring** (seed 341): the model against the best classical control on each
   split, with the hedged track beside it; a win is named for the control that explains it,
   and only what remains is called learning.
6. Panel, write-up, slides.

Risks: the budget buys too little training to be a fair test; the controls close the gaps
and leave nothing to compare (still a result); a sixth error in the evidence; the model
wins by knowing the simulator's training mix, which is why one condition is held out of it.
We stop before the test seed if the controls' validation run is unsound, and no GPU job runs
beyond the ledger's cap.

## How progress will be shown

- Each control against the plain search on its own split, at two severities (validation 340,
  test 341): paired ratio and share of the gap to the reference closed.
- Held course: false manoeuvres against one-manoeuvre targets called quiet, as a curve over
  the declaration margin (tuning 338).
- The learned model's training curves for three seeds and the ledger in dollars.
- One table per split: plain search, best control, hedged track, learned model, reference.
- Track plots of a few periods where the systems differ, if the tracks are stored this time.
- All from committed experiment folders by a script named in the slides post.

**Update, 2026-11-14.** The study ran. The classical controls remove most of the damage from
outliers and correlated bearing errors and from quiet targets; the learned model's reported
track beats the control on no split, so by the registered rule the controls stand. The
panel approved and showed the loss is the model's untuned manoeuvre detector, not a typical
period. See [the write-up](/blog/2026/11/14/time-late-learned) and
[the slides](/blog/2026/11/14/time-late-learned-slides).
