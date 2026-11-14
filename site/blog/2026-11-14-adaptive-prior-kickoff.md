---
title: "Kickoff: a manoeuvre prior that adapts to the period, and a hedged track"
date: 2026-11-14T22:00
tags: [kickoff, spec-018]
---

The owner has chosen option B after spec 017: a classical control whose manoeuvre prior is
inferred from the period itself, and beside it a hedged track for the periods where the
bearings cannot decide. Spec: `specs/018-adaptive-prior/`. Nothing is trained and no GPU
is used.

<!-- truncate -->

## Where we are

[Spec 017](/blog/2026/11/14/shifted-gap) was decided by its panel in one round. On targets
busier than Annex B says, the standing control is 2.3 times a fit told the true history,
and that gap is two things. In about two thirds of periods the limit is manoeuvres the
bearings barely show. In under a third the control misses manoeuvres the bearings do show;
about half of those are found by the same search when it is told the targets' own
statistics (1.17 better overall, at the price of more false manoeuvres). The control
stands as the time-late system. Open: a system that is not told the statistics.

## Where this task moves to

SRD §1 and §5; a line in §9 records the owner's decision (proposed; the owner merges).

1. **An adaptive prior.** The search runs under several manoeuvre rates and the period's
   own evidence weighs them, so a busy target is recognised as busy. Not told the split.
2. **Its price.** Annex B targets, targets that never manoeuvre, outliers and correlated
   errors: range, course and speed error, false manoeuvres, one-manoeuvre targets called
   quiet.
3. **A hedged track.** The probability-weighted mean of the candidate histories, across
   rates too, with a stated spread, and a check that the spread covers the truth as often
   as it says.
4. **Registration** before the fresh seeds (346 validation, 347 test): conditions that can
   come out either way at the planned size and that read cost, not counts.
5. Panel, write-up, slides.

If the adaptive control gains on busier targets without harm elsewhere, it is proposed as
the standing system. If it gains with harm, the owner decides. If it does not gain, the
standing control stays. The hedged track becomes an output only if its spread is honest.

Risks: the inferred rate may follow noise, outliers or correlated errors and invent
manoeuvres on quiet targets; the gain available is small (the ceiling is about 1.17 and
sits in a minority of periods), so the test may not separate it; a mean of mirror-image
candidates is a track no target followed.

## How progress will be shown

- The inferred rate against the true rate, by split (tuning seed 345, then test 347).
- Adaptive control ÷ standing control and ÷ the true-prior search on every split, pooled
  and by kind of period, with period counts.
- Manoeuvres missed and false for each, at three matching tolerances.
- The hedged track's error beside the declared track's, and the coverage of its spread.
- Track plots of periods chosen by a rule in the script.
- All from committed experiment folders by a script named in the slides post.
