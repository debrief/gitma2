---
title: "Time-late, classical controls and a learned model: the controls stand, and what the learned model's loss is made of"
date: 2026-11-14
tags: [write-up, spec-016]
---

The owner asked for two things at once: the classical controls the last panel wanted, and a
learned whole-period model trained in parallel under a plan fixed before any result. Both
are done. On a fresh test seed the learned model's reported track beats the classical
control on no split and loses to it on clean data, so by the registered rule the classical
controls stand and the learned track stops. The review panel approved that outcome and
changed what it means: the loss is not a typical period, it is the model's untuned
manoeuvre detector, and the comparison we registered was narrower than "learned against
classical". The illustrated companion is
[the slides post](/blog/2026/11/14/time-late-learned-slides).

<!-- truncate -->

## What was built

**Classical controls**, nothing trained, composed from the search spec 015 left standing:

- wild bearings edited out before the search;
- one larger bearing sd when the bearings' second differences show the errors are
  correlated in time;
- the search run under Annex B's manoeuvre prior and a broadened one, pooled;
- a manoeuvre declared only when it is worth an evidence margin of 1, with a stated 1%
  chance that the target never manoeuvres;
- a hedged track: the probability-weighted mean of the candidates.

Settings came from a tuning seed. The combined control is not told which condition it is
in.

**A learned model**: a bidirectional transformer reading a whole period of 5-second
bearings and giving the target's state every 30 seconds and a manoeuvre probability. Three
seeds, 12.5 million simulated periods each (Annex B, randomised manoeuvre statistics,
quiet targets, correlated errors and outliers), a T4 each, $14 in all. Its reported track
is the arc model fitted to the bearings at the manoeuvres the model declares.

The plan, the training mix, the criteria and the code were bound by digest before the first
training run and before the validation and test seeds existed. The scorer refused to score
a learned track until the controls' own validation was on record.

## The registered outcome (test seed 341, 2,860 periods)

Declared control ÷ learned track, paired per period, three seeds (above 1: the learned
track is better):

| Split | Ratio | Verdict |
| --- | --- | --- |
| Shifted prior | 0.82, 0.80, 0.82 | not shown |
| Shifted prior 2 | 0.87, 0.87, 0.94 | not shown |
| Correlated errors | 0.83, 0.83, 0.84 | not shown |
| Outliers | 0.78, 0.77, 0.81 | not shown |
| Bias, absent from training | 0.98, 1.00, 0.97 | not shown |
| Annex B | 0.82, 0.81, 0.82 | harm |
| Held course | 1.06, 1.06, 1.06 | no harm |

Learning is shown on no split and there is harm on Annex B data: **the classical controls
stand as the time-late system, and the learned track stops.** The forecast written before
training said this was the most likely outcome.

## What the classical controls did

Against the search they started from, the declared control is 1.68 [1.46, 1.94] better
with 2% outliers, 2.44 [2.03, 3.00] with 5%, 1.33 [1.16, 1.53] with correlated errors and
1.70 [1.48, 1.95] on targets that never manoeuvre (false manoeuvres in 8% of periods
against 49%). These replicate across the tuning, validation and test seeds. This is the
result the panel says is worth carrying.

It has limits the first record understated. Under a slowly varying bias it does nothing
(1.00). On clean data its range error is not separated from the search's over three seeds
(0.96 to 1.09). It calls a one-manoeuvre target quiet more often, markedly so with
correlated errors (0.29 against 0.05). Its correlated-error form knows the simulator's
error family. And under a shifted manoeuvre prior it gains nothing (1.03): the control is
still 1.7 to 2.1 times a fit told the true history, whichever way that reference is fitted.

## What the learned model's loss is made of

Five reviewers recomputed the outcome and it holds: all 42 ratios reproduce, no verdict is
near its boundary, the registration held. Then they took the 20% apart.

**The typical period is a tie.** The median per-period ratio is 1.00 on every split. Where
the model declares the same number of manoeuvres as the control, the two tracks are level
(0.95 on Annex B, 1.01 under the shifted prior), because the read-out is then the same
classical fit. Where the model declares fewer, in a quarter to a half of periods, its
track is about twice as bad. The whole loss is there.

**So the registered comparison measured a detector.** The model's manoeuvre probability
was thresholded at 0.5, a value never tuned, while the control's margin and quiet
probability were tuned. That asymmetry was in the registration and was mine. A reviewer
tried the obvious repairs on spent tuning data: a lower threshold makes the read-out worse
(the fit can no more remove a false manoeuvre than add a missed one), and a broader prior
changes nothing. Starting the control's own search from the model's answer equals the
control at a third of the search time, and does not beat it.

**The model as an estimator** (its own output, reported beside and deciding nothing) is
0.71 of the control on Annex B data. Under the shifted prior it is level in range, 1.01,
but behind in course and speed (0.79, 0.77), and the level figure is a cancellation: it
beats the control where the bearings determine little and is nearly three times worse
where they determine much. That is the signature of an estimator that leans on what it
learned about targets in general, which this project has now seen three times.

**The "mismatch" was the classical side's only.** The shifted, correlated and outlier
conditions all lie inside the model's training ranges. The model lost in-distribution.

## What was not delivered

- A working prior-mismatch diagnostic: the one computed is not a Bayes factor and fires on
  quiet targets, not on a shifted prior.
- A Huber cost and a whitened fit (editing and an effective sd stand in), and the repair
  of the evidence at the edges of the prior's support.
- The export check on the trained models (it ran on a toy), IMM and EKF tracks beside, and
  the weights' digests in the test record.
- Unit tests for the runner and the scorer.
- Two launches of the GPU pilot failed at start-up on a launcher form that had never been
  run; the ledger under-counts a run whose container is replaced (39 cents against the
  owner's dashboard).

## What this does and does not show

It shows that a small direct model, trained on the simulator, does not beat an evidence
search that knows the motion model, in or out of the conditions it was trained on, and
that classical editing and an honest bearing sd remove most of the damage from outliers
and correlated errors.

It does not show that learning cannot help the time-late consumer. A learned proposer
inside the search, the model's probabilities as a prior, training through the arc model,
and a larger budget were not tested. Nor does it show that the shifted-prior gap can be
closed by anything: busier targets with smaller turns may simply not be identifiable from
bearings, and that is the cheapest next thing to find out.

Across specs 012 to 016 the founding question stands at "not shown, at small budgets, with
direct models". Each large gain so far has gone to a classical element.

## Records

`experiments/20261113-tl4-tuning/`, `-tl4-decision/` (two addenda), `-tl4-val/`,
`experiments/20261114-tlm-runs/`, and the test record `experiments/20261114-tl4/`
(`review.md`). Seeds 338 to 341 are used; the next fresh seed is 342. GPU spending in
November stands at about $41 of the owner's $50.
