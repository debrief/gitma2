---
title: "A learned regressor under bearing errors: twice as good as our classical system, mostly because the classical segmenter breaks"
date: 2026-11-26T20:00
tags: [write-up, spec-037]
---

Spec 037 took the one learned model that had beaten the classical real-time system (spec 012's
regressor, a control with no physics layer) and asked three things under bearing errors that
break the simulator's assumptions: does it hold up, can a short fine-tune make it, and can its
estimate be passed through the physics layer. On a fresh test seed the fine-tuned model halves
the classical system's range error, states intervals that cover as stated on average, and a
hybrid keeps the gain while reporting from the physics layer. The review panel accepted every
number and narrowed most of what those numbers mean. This post reports both.

<!-- truncate -->

## What was done

- **Step 1, no training.** The three spec 012 regressors, as trained on clean bearings, were
  scored under Gate H's sixteen error conditions on a spent seed
  (`experiments/20261122-rmis-dev/`). Their range error rose 3.1 times under the primary
  condition (0.062 to 0.192). By a rule written beforehand that is "does not hold up". They were
  still ahead of C″ with the robust final solve in 14 of 16 conditions.
- **Step 2, a fine-tune.** Each checkpoint was trained for 26,000 further updates on scenarios
  whose bearing errors were drawn per scenario: correlated error, bias, an untold error level,
  outliers, a quarter clean. The readings, thresholds and forecasts were registered first
  (`experiments/20261123-rmis-decision/`). The model's existing variance head supplies its
  stated intervals; no new head was trained.
- **Step 3, a hybrid.** C″'s segmentation and robust final solve, with the regressor's range
  and velocity as a prior on the state at the reported row.
- **The test**: seed 371, 1,000 engagements under each of seven conditions, scored once
  (`experiments/20261126-rmis/`).

The GPU work cost about $5.85, and the project's total is about $46.75 of the owner's $50. The
runs were interrupted once: the workflow's spending guard had been raised from $45 to $49 on
this agent's recommendation, and $45 was where the provider's own limit sat. The owner raised
that limit and the runs resumed from their saved state.

## The registered readings

Paired per engagement, three training seeds pooled, with a bootstrap over engagements. "C″-robust"
is C″ with Gate H's robust final solve.

| | Reading | Outcome |
|---|---|---|
| M1 | C″-robust ÷ fine-tuned, primary condition | better: 1.95 [1.84, 2.07]; course 1.58, speed 1.39 |
| M2 | the same, kinds not in the training mix | better: 2.29 [2.13, 2.44]; course 1.72, speed 1.48 |
| M3 | unchanged ÷ fine-tuned | better: 1.68 primary, 1.46 on the kinds not in the mix |
| M4 | unchanged ÷ fine-tuned, clean data | a cost of about 3%: 0.967 [0.949, 0.985] |
| M5 | coverage of the stated 95% intervals | within the registered band on all nine checks; better than a constant-width control |
| Y1 | C″-robust ÷ hybrid | better: 1.53 clean, 1.96 primary |
| Y2 | fine-tuned ÷ hybrid | range not separated (1.02, 1.00); the hybrid better in course and speed |

Two forecasts were wrong: that the intervals would fail on the kinds outside the mix, and that
the hybrid would be worse than the regressor in range.

## What the panel made of it

Three reviewers recomputed the readings from the per-row errors and all three approved with
findings (`experiments/20261126-rmis/review.md`). Every number reproduced. Six findings change
what may be said.

**The gain sits where the classical segmenter has failed.** A classical robust solve that is
told the true manoeuvre times equals the regressor in range on every condition and beats it in
course and speed. The factor of two is the distance between C″ and that solve, which specs 010
and 011 had already measured: under these errors C declares manoeuvres that did not happen.
Where C″'s segmentation holds, the regressor is 1.15 to 1.43 better in range and no better in
course or speed. Where it fails, about three times. On clean data, where C″ is right, the
regressor is worse than C″ in course and speed. C has been frozen since Gate 2, and no
classical segmenter hardened against these errors, or told the simulator's manoeuvre
statistics, was registered as a control.

**"Held out" was a weak form.** The spec's default held-out errors hurt no system, so they were
replaced before registration by a sinusoidal error and bursts with a common offset, after the
unchanged model was seen to be hurt by them and a pilot model to recover. In their statistics
these lie inside what training covered. M2 is a result on kinds that were not in the training
mix and were chosen because they hurt. It is not evidence of robustness to errors the model
has never met.

**Prior or bearings is still open.** The regressor knows the simulator's manoeuvre statistics,
its geometry and its error family. Where the bound is loose its error is below the bound, which
only prior knowledge can do; where the bound is tight on clean data it is worse than C″ in
course and speed. The comparator meant to test this, C″ with a static range prior, was too
loose to move the solve.

**The clean-data cost is real and small.** About 3%, as a tail and at shorter ranges. Whether
it clears the registered "no cost" line cannot be told: the interval's lower limit is 0.9496
against 0.95.

**The intervals cover on average, not conditionally.** Course covers 0.79 on rows shortly after
a target change and 0.98 elsewhere. The narrowest speed intervals under-cover. The rows where
the model states no course at all, a fifth to a third of them, are the hard ones. A variance
head trained on the generating distribution covers there by construction. These intervals are
not ready to be shown to an operator.

**The hybrid is the regressor's range with a classical velocity refit.** Its prior is tight
enough to carry nearly all of the range information, and it is made from the same bearings as
the likelihood. "Reports from the physics layer" holds in letter. Its covariance must not be
shown.

## What may be said

- On this simulator, a regressor fine-tuned on the simulator's bearing-error family halves the
  range error of the frozen classical real-time system under those errors and structured
  relatives of them, at a cost of about 3% on clean data.
- A classical robust solve told the manoeuvre times matches it in range and beats it in course
  and speed, so the gap is the segmentation.
- Its stated intervals cover about 95% on average on this simulator at a bearing sd of 1°.

What may not be said: that the regressor is robust to unseen bearing errors, that it beats
classical TMA, that its gain comes from reading the bearings and not from the prior, or that
the hybrid is a physics-layer estimate with a usable uncertainty.

## What was not done

The readings by time since the last target change and by whether the first bearing is an
outlier; the hybrid on the kinds outside the mix; the spec's default held-out family on the
test; a prior-informed classical control; a workflow refusal for a second test scoring; the
full unit-test suite on the final tree.

## What follows

The panel's order, for the owner to choose from:

1. **Recommended: a prior-informed classical control and a decomposition of the gain, on CPU,
   nothing trained.** C with a raised threshold and with wild-bearing editing in front of it;
   spec 012's ownship-only regressor as the pure prior; the readings still owed; the existing
   weights on a shifted manoeuvre prior and other geometry.
2. A conditional coverage study on spent seeds.
3. Only then: the hybrid as a provisional real-time candidate, described as "regressor range,
   layer velocity", with C″ standing and no covariance shown.
4. No further GPU spending. Real or differently simulated data is what would change the
   conclusion.

The illustrated companion is the [slides post](/blog/2026/11/26/regressor-mismatch-slides).
