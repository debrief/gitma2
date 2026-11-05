---
title: Steady-leg segmentation (C, O, L)
---

# Steady-leg segmentation: C, O and L

Source: `src/tma2/segment/`; CLIs `tma2-segment`, `tma2-segtrain` and `tma2-gs`.
Requirements: SRD Annex A §A.9 (Gate S), Annex B (the owner's manoeuvre definitions) and spec
005.

The problem is to label, at each scored row k and using bearings up to k only, every earlier row
of the target's track as **steady**, **transition** or **unknown**. The labels then go to the
physics layer, which fits one constant-velocity leg per steady piece. Three components do the
labelling:

- **O** labels ownship legs from navigation data.
- **C** is the classical target segmenter.
- **L** is C with learned per-bearing evidence added.

## Definitions (Annex B)

- **Steady leg:** at least `L_min` = 30 rows (5 min), with course within ± 5° and speed within
  ± 0.5 kt of the leg mean.
- **Transition:** at least `T_min` = 6 rows (60 s). Its length is estimated.
- **Unknown:** rows the evidence cannot decide. For the target, every row up to the ownship's
  first zig is unknown: before it, one leg cannot be told from two.

Truth labels come from the generator's manoeuvre spans, widened to `T_min`. A steady piece
shorter than `L_min` becomes unknown.

## O: ownship legs

A coarse pass compares 1-min moving averages of course and speed with D = 10° and D_S = 1 kt to
find deliberate changes. A fine walk then finds each transition's edges:
- it starts from the steepest row and walks outward;
- it stops where the rate changes sign, or where the track enters the neighbouring leg's ± 5°
  band.

A change is kept only if the change in leg means exceeds D and a signed test across the
transition rows confirms it. Thirty seconds are trimmed from each leg end. On MAN2, O finds every
ownship turn within 30 s with zero contamination; helm wander and autopilot oscillation call no
transition.

## C: nominate, then confirm by the coupled cost

1. **Nominators.**
   - **GLR alarms.** GLR is the spec 004 control, on per-timestep batch least squares. Its
     threshold is tuned on validation to a 20% held-leg exceedance; a raised alarm is re-tested
     every 6 rows.
   - **An additive search** over legs, each scored by its own constant-velocity fit. It is run
     on prefixes every 30 rows, on a 6-row grid anchored at the scored rows, so one cost table
     serves every prefix. A per-leg penalty of 30 holds false transitions to 3.5% of prefixes.
2. **Confirmation.**
   - **The test.** Each nomination is tested by the physics-layer solve on its own prefix, a
     coupled fit with knots at both transition ends.
   - **Search order.** Starts are searched at the middle transition length, then every length is
     tried at the best start.
   - **Acceptance.** An open transition (start knot only) is accepted if its cost drop exceeds
     τ = 13.8, the 0.1% point of χ² with 2 degrees of freedom; a closed one (two knots) against
     the 4-degree-of-freedom point with the same tail probability, 18.45. Both boundaries are
     then polished by ± 3 rows.
   - **Causality.** Closing an open transition polishes its start with bearings up to the
     closing row, so prefixes before the close keep the start as it was accepted (FR-002; the
     Gate S panel found the start being rewritten for earlier prefixes, fixed in 7fe8874).
3. **Segmentation of each prefix.** Accepted transitions become transitions, near misses become
   unknown, and the rest is steady.

The search alone is a weak nominator on MAN2: it finds 13% of changes within ± 60 s. C's accepted
transitions come from both nominators; the share from each has not been counted.

## Hand-over to the physics layer: gap or chord

A transition [s, e] gives the physics layer knots at s and e. An open transition at prefix k is
[s, k], so it gets its second knot, and in chord mode the speed prior, at k itself; the oracle
and confirmation instead treat an open span as a start knot only. Either way the state at k is
weakly determined. Gate 2 must fix one convention for both. A segmenter reports no kinds, so the
speed prior is applied across every transition, speed changes included.
- **Gap:** the bearings inside the transition are excluded.
- **Chord:** the bearings are kept, with the speed-continuity prior across a course-only
  transition.

The mode is fixed on validation: gap had the lower median range error, 0.120 against 0.123.

**Known defect (Gate S panel round 1).** The search's cost table warm-starts each leg's fit from
the shorter leg's and takes a fresh grid start only every fourth step, so some entries are failed
fits: a longer leg costs less than a nested shorter one (by more than 100 χ² for 3,191 pairs in
500 validation scenarios). It weakens the search nominator for C and L alike, and is fixed before
Gate 2.

**Scoring conventions.** Contamination counts a segmenter's unknown rows as steady, and a truth
transition [start_index, end_index] includes the first row on the new leg. Both are conservative
and the same for every segmenter.

## L: learned evidence

- **The network.** A small causal dilated 1-D convolution: width 32, kernel 5, dilations 1, 2, 4
  and 8, SiLU activations and a zero-initialised head.
- **Its inputs:**
  - the bearing;
  - ownship position and time;
  - O's online label: for each row r, O run on rows 0 … r alone;
  - the per-timestep least-squares innovation.
- **Its output.** For each row, a log-likelihood ratio e of steady against transition.
- **Where e enters C:**
  - the search's costs, as −2Σe on legs and +2Σe on transitions;
  - the confirmation threshold, which shifts by twice e summed over the candidate's rows,
    capped at ± τ/2.

An untrained L emits e = 0 and equals C exactly.

**Training** minimises the semi-Markov negative log-likelihood of the truth segmentation on the
search's lattice (`segment/crf.py`), plus 0.1 × a per-bearing cross-entropy term.
- The normaliser is a log-sum-exp forward recursion over every segmentation the lattice allows.
- The truth path is the lattice segmentation that agrees with the most labelled rows, with ties
  broken by the cost.
- The **shuffled control** trains on another scenario's labels.

It exports to ONNX with each convolution written as matrix products, because onnxruntime has no
double-precision `Conv`.

## Measures

- **Contamination:** the share of a reported leg's rows that the truth labels as transition.
- **Coverage:** the share of truth-steady rows inside reported legs.
- **False split:** any transition on a scenario with no target change.
- **Gap recovered:** (median one-leg error − median segmentation error) ÷ (median one-leg error −
  median oracle error), on σ = 1° G5 rows. One leg scores 0 and the oracle 1.

Every measure is stratified by **detectability**, the oracle's cost drop for each change (note
08's bands: below 13.3, 13.3–50, 50–200, at least 200).
