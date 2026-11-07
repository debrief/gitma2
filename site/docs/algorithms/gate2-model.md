---
title: Gate 2 model
---

# The Gate 2 model (E)

Sources:

- `src/tma2/gate2/`: `model.py` and `train.py` (E-w), `tables.py` and `es.py` (E-s),
  `predict.py`, `gate.py`;
- the CLIs `tma2-dtables`, `tma2-g2train`, `tma2-g2predict` and `tma2-g2`.

Requirements: SRD §5 (the Gate 2 row) and §7 step 4, Annex A §A.9, and spec 007.

E adds learning to the classical segmenter C ([segmentation](segmentation.md)) in the two places
where C decides. The [physics layer](physics-layer.md) still produces the estimate, with C's knots
(a cap of 12). Both parts start at zero, so an untrained E *is* C. This is tested end to end:
untrained E minus C scores 0 to 1e-9 in gap recovered.

## E-w: weights on C's hand-over

At each scored row k, C hands the physics layer a segmentation of [0, k]. That hand-over gives
knots at the transitions, masked transition bearings and a grid start. E-w adds two things:

- **Per-bearing log-weights.** For each row, `weight_bound · tanh(head)` is added to C's
  log-weights, so a masked bearing stays masked.
- **A start correction** at row k: Δ log range, Δ course and Δ log speed applied to C's grid
  start. The correction is applied as a difference from the zero correction, so zero heads give
  C's start bit for bit.

The encoder is Gate 1's causal transformer ([Gate 1 model](gate1-model.md)) with one extra input
channel: C's code at prefix k (steady 0, transition 1, unknown 0.5, and 0 after k). Inputs after
row k are zeroed and attention is causal, and the physics layer masks rows after k, so nothing
after the prefix reaches the estimate (tested by perturbing every later row).

**Training.** The loss is the [CRB](crb.md)-normalised squared error of (log range, vx, vy) at
the row, for each prefix:

- each term is capped at 100;
- prefixes whose solve failed (cost above 20 × their bearings) are excluded;
- an auxiliary term trains the start correction, because implicit differentiation gives the
  start no gradient;
- early stopping uses the trimmed mean of the validation loss.

E-w trains on C's segmentation of the training stream.

## E-s: evidence on C's confirmation

C accepts a nominated transition when its cost drop Δ beats a χ² threshold τ′ (τ = 13.8 for a
transition that has ended, 4 degrees of freedom; see [segmentation](segmentation.md)). E-s is
spec 005's causal evidence network. It emits e per row, and e > 0 means steady. The evidence
shifts the threshold by s = clamp(2 Σ e, ± τ/2) over the candidate's rows. C's own nominations
are kept: E-s acts on decisions, not on candidates.

**Decision tables.**
- `tma2-dtables` re-runs C and records every decision: row a, start, length, Δ, τ′, accepted.
- A decision within τ/2 of its threshold can be flipped by evidence. For each such decision, the
  table holds the bound-normalised error at every later scored row twice: once with the
  transition and once without it, keeping C's other decisions as C made them.
- Decisions further than τ/2 from their threshold cannot flip, so their rows are constants of
  the loss.

**Relaxed acceptance.**
- The loss is the mean over decision rows of p·e_with + (1 − p)·e_without, where
  p = σ((Δ − τ′ − s)/T) and T is a declared temperature.
- At e = 0 and T → 0 this is C's error.
- Validation uses the hard rule (accept if Δ − τ′ − s > 0), which is what inference does.

**Limits of the relaxation.** It takes one decision at a time:
- a decision's effect on later decisions is ignored;
- it holds C's best candidate fixed, while at inference the evidence can also move the best
  start or length.

## E = E-s, then E-w

At inference, E-s's evidence goes into C's confirmation, and E-w then weights the hand-over of
the resulting segmentation. E-w is trained on C's segmentation rather than E-s's. Training it on
E-s's would cost a full re-segmentation of the training stream per E-s seed, and E-s changes
only near-threshold decisions. E-w alone, on C's segmentation, is reported as an ablation.

## The gate

`tma2-g2` scores E's prediction files beside C, one leg, the oracle, GLR + confirm, the frozen
IMM and EKF, and naive, on the same rows. Every physics-layer solve uses the 12-knot cap.

| Check | Measure | Rule |
| --- | --- | --- |
| G2-a | E / IMM, median range and course, all G5 rows | wholly below 1 |
| G2-b | E / one leg, range, course and speed, settled rows | wholly below 1.1 |
| G2-c | E's gap recovered (median range, one leg to oracle) | wholly above 0.5 |
| G2-d | E − C in gap recovered | wholly above 0; void if the shuffled control beats C |

Each interval is a scenario-clustered paired bootstrap: 97.5%, 2,000 resamples, `inverted_cdf`
medians.
