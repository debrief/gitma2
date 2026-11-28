---
title: "Kickoff: where the regressor's gain comes from"
date: 2026-11-27T10:00
tags: [kickoff, spec-038]
---

Spec 037 found a learned regressor twice as good as the classical real-time system under
bearing errors, and its review panel found the comparison could not say why. This task measures
the two explanations left standing: that the classical segmenter was never hardened against
those errors, and that the regressor knows the simulator's manoeuvre statistics while the
classical system is told nothing. Nothing is trained and no GPU time is used. Spec:
`specs/038-gain-decomposition/`.

<!-- truncate -->

## Where we are

- [Spec 037](/blog/2026/11/26/regressor-mismatch): under the primary mismatch condition C″ with
  the robust final solve is 1.95 times the fine-tuned regressor's range error, and 2.29 times
  on error kinds outside its training mix. Three reviewers approved with findings.
- The panel's narrowing: a classical robust solve told the true manoeuvre times equals the
  regressor in range and beats it in course and speed, so the factor of two is C's segmenter
  failing; and whether the regressor's gain is prior knowledge or reading the bearings is open.
  The comparator meant to test that was too loose to move the solve.
- Standing: C″ for real-time estimates, C frozen since Gate 2. Nothing was carried from spec
  037. About $46.75 of the owner's $50 GPU budget is spent; none is needed here.

## Where this task moves to

- SRD §5 and §7; a registered study, not a gate. Nothing is carried by it.
- Plan:
  1. Two classical controls around the frozen C: a raised confirmation threshold; and wild
     bearings edited out with an effective bearing sd. Each with the robust final solve,
     settings chosen on spent seeds.
  2. The pure prior: spec 012's ownship-only regressor, which reads no bearings, scored alone
     and as the prior inside C″'s solve.
  3. The existing weights and the controls where the simulator's prior is wrong: busier
     targets, and geometry outside the training ranges.
  4. The readings spec 037 owed: by time since the last target change, by a wild first
     bearing, by whether C″'s segmentation was right, efficiency by how tight the bound is.
  5. Register estimands and forecasts, then score fresh seed 372 once; three reviewers.
- Judged by: the share of the gap to the regressor that a hardened classical control closes;
  the share of the regressor's gain that the prior inside a classical solve obtains; whether
  the lead holds, shrinks or reverses where the prior is wrong.
- Risks: the ownship-only regressor was trained on clean data only, which is harmless because
  bearing errors cannot reach it, and is tested; the shifted and held-out ranges may leave no
  rows at the scored prefixes; each classical segmenter run costs most of an hour per hundred
  engagements, which caps the test at about 500 engagements a split.
- Stop rule: if a hardened control closes at least half the gap on development data, it
  becomes the headline comparator before the test, and the record says the earlier headline
  was a property of an unhardened segmenter.

## How progress will be shown

- A stacked chart of the regressor's gain over C″: prior alone, prior inside C″'s solve, what
  is left for the bearings; clean and under mismatch, on test seed 372.
- Range error by condition for C″, each hardened control, the regressors and the solve told
  the true manoeuvre times.
- The regressor's lead on the in-distribution, shifted-prior and held-out-geometry splits.
- Track plots of one test engagement under the primary condition: C″, the best hardened
  control, the regressor.
