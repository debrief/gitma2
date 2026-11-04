# Research: Steady-leg segmentation and Gate S

Phase 0 for [plan.md](plan.md). Measurements are on validation seed 304 (σ = 1° scenarios, file
order). "Tuning" means ordinals 0–299 and "scoring" ordinals 500–799. Both are inside note 08's
tuning and scoring sets, so they can be compared with its records. Scripts:
`scripts/research/seg_search.py` (R1) and `scripts/research/seg_refine.py` (R2). Summaries:
`experiments/20261103-spec005-research/`.

A turn counts as found if a transition's midpoint lies in the manoeuvre ± 3 min. Precision is the
share of transitions that are found turns. False splits are counted on scenarios with no target
change.

## R1. C's search stage: independent leg costs and dynamic programming

**Prototype.** Each candidate leg is scored by a constant-velocity fit of its own. Legs end on a
grid every 3 rows, and the fit is gitma's LM, warm-started as the leg grows, with a grid restart
every 4 steps. Dynamic programming then tiles [0, k]:
- legs of at least 12 rows (2 min);
- transitions of 3–18 rows (30 s – 3 min), whose bearings are excluded but charged 1 χ² unit each;
- a penalty per extra leg, and per transition left open at k.

**Timing** (one core per process, four processes at once; 123–360 rows):
- the cost table takes 3.1 s median and 8.3 s at most per full history;
- the search takes ≤ 0.01 s for every penalty.

The table for a prefix [0, k] is a sub-table of the full one once k is on the grid. So all of a
scenario's scored prefixes cost one table, which fits the 10 s budget at 300 rows. Scaling is
about n^2.5, so 600 rows would take about 30 s. That case is out of the generator's range and is
recorded as a risk.

**Penalty.** A per-hypothesis χ² point is far too small, because the search tries thousands of
segmentations. At penalty 20, 45% of engagements with no target change were split. At 30 it was
2.6% (1 of 38), and at 45 or more, none. The penalty must therefore be calibrated, like a
threshold, to a declared false-split rate on a tuning set.

**Quality** on the 300 scoring scenarios:

| | False splits | Recall | Precision | F1 | Recall by detectability band: 0–13, 13–50, 50–200, ≥ 200 |
| --- | --- | --- | --- | --- | --- |
| C search, penalty 30 | 1/37 | 0.56 | 0.78 | 0.65 | 0.28, 0.62, 0.72, 0.92 |
| C search, penalty 45 | 0/37 | 0.52 | 0.83 | 0.64 | 0.20, 0.58, 0.72, 0.93 |
| GLR 20% + confirm (note 08) | 0/37 | **0.67** | **0.97** | **0.79** | 0.30, **0.88, 0.95**, 0.94 |

**Why it is weaker.** Two-thirds of C's false transitions lie before the ownship's zig.
- **Before the zig**, an independent leg is weakly constrained, so splitting it absorbs noise.
- **After the zig**, independent legs discard the coupling between legs that gives detection
  power inside one ownship leg.

Transitions also run long (median 14 of at most 18 rows), so the per-bearing charge needs tuning.

**Decision.** The additive search is kept as a **second nominator**, not as the segmenter. On
the 319 detectable manoeuvres of these 300 scenarios:

| Found by | Count |
| --- | --- |
| both | 220 |
| GLR + confirm only | 74 |
| C's search only | 19 |
| neither | 6 |

Taking the union of both nominators could raise recall on detectable changes from 92% to 98%,
if the coupled test confirms them.

**Alternatives rejected:**
- **Search as the segmenter (the spec's FR-022 as written).** It measured well below the
  existing classical segmenter.
- **An exact coupled dynamic programme.** The coupled cost is not additive over legs.

## R2. Coupled refinement

| Refinement of the search's transitions (penalty 30) | Recall | Precision | F1 |
| --- | --- | --- | --- |
| Whole-history test of each transition, in time order | 0.54 | 0.79 | 0.64 |
| Test on the prefix ending 18 rows after it | 0.44 | 0.94 | 0.60 |
| Test on the prefix ending 6 rows after it | 0.31 | 0.93 | 0.46 |

The whole-history test accepts false transitions. Once real turns are missed, the whole-history
model is wrong, and any extra pair of knots absorbs that misfit. Testing on the transition's own
prefix fixes precision but loses recall: the search places transitions too loosely for a test
at a fixed position.

GLR + confirm works because its test **searches positions** (12 candidates per alarm) on the
prefix ending at the alarm.

**Decision: C is a coupled nominate-and-confirm segmenter.**
- **Nominators:** GLR alarm episodes (20% of held rows), re-tested every 6 rows while an episode
  stays raised (note 08 §5 item 10), plus the search's transitions.
- **Confirmation:** on the prefix ending at the nomination time (the alarm row, or 18 rows after
  the search's transition):
  - the candidates are transitions (start c, length L), with c on a 3-row grid over the last
    36 rows and L in {0, 3, 6, 12, 18} rows (L = 0 is a point knot);
  - knots go at c and c + L;
  - the best candidate is accepted if its cost drop exceeds the χ² point for its degrees of
    freedom (2 for a point knot, 4 for a transition) at τ's tail probability.
- **Boundary polish:** after acceptance, each transition's ends are re-optimised one at a time
  (±3 rows) under the coupled cost.
- **Labels:** rows in accepted transitions are transitions. Rows before the first reliable fit
  (range sd ≫ range) or within a margin of an undecided candidate are unknown. All others are
  steady.

This keeps the spec's intent: a joint search over count, boundaries and lengths, then a coupled
decision. The coupled cost places the boundaries, and the additive search only nominates.
Spec FR-021 and FR-022 are amended accordingly (see the spec's Clarifications), and S2 is
unchanged: C must still beat plain GLR + confirm.

**Cost.** Note 08's confirmation took about 5 s per scenario on one core with 12 candidates.
Five lengths raise that to roughly 25 s. It is an offline cost, computed once per scenario with
prefix answers reused (`knots_at`). The 10 s budget (FR-024) is met by parallel batching: 4
cores at about 6 s each. If the measured time per prefix exceeds 10 s, L falls to {0, 6, 18}.

## R3. Gap or chord

- **Evidence so far.** P0, seed 301, the oracle with noise: masked turns 0.539 [0.519, 0.561]
  against the chord's 0.531 [0.510, 0.554] on all G5 rows. Course was 0.461 against 0.438 and
  speed 0.380 against 0.393 (`experiments/20261101-p0-r4/review.md`). The windows of note 08 §6
  used the chord and gained 7% on speed over point knots.
- **Decision.** Measure both modes with C's segmentation on the 1,000 scoring scenarios. Carry the
  mode with the lower median range error over G5 rows (ties go to the chord, the simpler model).
  The choice goes into the decision record before any test scoring.
- **Alternative.** Fixing the chord now: rejected, because the spec makes this a measured choice.

## R4. Truth labels (Annex B FR-034)

On 300 scenarios, the rows where the true course or speed differs from the previous row are
exactly the generator's span rows [start_index, end_index] (row agreement 1.000, no row outside
or missing).

**Decision.** Truth labels are a deterministic function of the stored true track:
- **Transitions:** rows where course or speed changes, merged, and widened symmetrically to at
  least T_min = 3 rows.
- **Legs:** the rest, if at least L_min = 12 rows long. A shorter piece is unknown.
- **Prior:** rows before the first ownship zig's end are steady for the target, but are labelled
  unknown when scoring contamination. There the target's range is undetermined, and spec Edge
  Cases forbids inventing a transition.

The tolerances C = 2° and S = 0.5 kt are checked against the leg mean. With exact kinematics and
no wander they hold trivially, and a test asserts it. The function is unit-tested on constructed
tracks and golden-tested on fixture scenarios. No generator change is needed (FR-050).

## R5. O: ownship steady legs

Annex B (4 Nov 2026) fixes O's method: a coarse pass on adjacent 1-minute moving averages with
threshold D = 10° (and D_S on speed), then a fine walk back and forward to the turn's ends using
the smoothed turn rate's sign and the preceding leg's ± C band, and a signed-change acceptance
test. Ownship navigation is exact on generator 0.5.0, where this reduces to marking rows whose
course or speed differs from the previous row, as `ownship_legs` already does.

**Decision.** Implement Annex B's two passes as specified, with:
- the moving-average window 6 rows (1 min at 10 s), D = 10°, D_S = 1 kt;
- the smoothed turn rate from a 3-row central difference of unwrapped course;
- acceptance when the net signed change is at least 90% of the total absolute change;
- L_min, T_min and the 30 s trim as the decision record fixes them.

It must agree with `ownship_legs` on generator 0.5.0 data (under test), and it is unit-tested on
constructed tracks: irregular wander and cyclic oscillation inside ± 5° (no transition), and
10–15° and 30° turns at 0.5–3°/s (boundaries within the fine pass's window). S1 is a sanity check
until generator 0.6.0 produces wander.

**Alternative rejected.** The penalised change-point search of the first plan: equivalent on
exact tracks, but not what Annex B specifies, and its penalty would need its own calibration on
wander.

## R6. L: semi-Markov likelihood

- **Lattice.** Steady legs (≥ 12 rows) and transitions (3–18 rows) on the 3-row grid, the same
  lattice the search uses.
- **Segment scores:** −½ × the independent leg cost (or the transition charge), plus the evidence
  summed over the segment's bearings (+ for steady, − for transition).
- **Loss.** The negative log-likelihood of the truth segmentation, with a log-sum-exp forward
  recursion as normaliser. Both are differentiable in the evidence.

At zero evidence, the gradient is the difference between the truth's expected feature counts and
the model's, which is generally non-zero, so the head learns from step one (SC-003). A unit test
checks it against finite differences.

**Training data.** Training is on a fresh stream (seed 313), regenerated per epoch from stored
truth with fresh noise (spec 003's on-the-fly path).

**Cost.**
- **Cost tables (R1)** cost about 3 s per scenario. With 10⁴ training scenarios and their tables
  precomputed once, that is about 2.5 h on 4 cores, done as one CI job.
- **The forward recursion** is O(grid × lengths) ≈ 120 × 40 per scenario, under 10 ms in torch.
- **The evidence network** is a small causal 1-D convolution or the Gate 1 encoder, under 10 ms.

One epoch over 10⁴ scenarios is therefore minutes. Its throughput is measured in implementation
against a budget of one hour per epoch.

**Alternatives rejected:**
- **A hard decoder with a straight-through gradient:** biased, and Gate D's failure mode.
- **A per-bearing classification loss alone:** it trains the evidence but not the way C combines
  it. It is kept as an auxiliary term with weight 0.1 (decision record).

**Inference.** L's evidence reaches C in two places. Both are zero for an untrained L, so L
equals C (SC-003).
- **Nomination.** The search runs with the evidence added, and its transitions join the
  nominations.
- **Confirmation.** The threshold for a candidate transition is lowered or raised by twice the
  evidence summed over its rows: a prior log-odds, as in a likelihood-ratio test with a prior.
  The shift is capped at ± τ/2, so the physics-layer cost drop still decides.

## R7. Metrics, Gate S scoring and seeds

- **Contamination and coverage** are computed per row on σ = 1° scenarios, against truth labels
  from rows after the first ownship zig's end. Medians and P90 are taken over scenarios.
- **False split:** any transition on a scenario with no target change.
- **Leg-count accuracy:** on scenarios whose changes are all detectable (≥ 13.3).
- **Gap recovered** in range and velocity, from medians over σ = 1° G5 rows, as defined in the
  spec. The decision record fixes CRB normalisation **off** (raw medians). Reason: the gap is a
  ratio of differences, so normalisation adds variance without changing the sign. Efficiency is
  reported beside it.
- **Intervals:** scenario-clustered paired bootstraps (2,000 resamples, 97.5%), using
  `bootstrap_clustered_quantile_ratio` and the paired difference for the S2 and S4 differences.
- **Seeds**, each pinned by digest in the plan file:
  - 312: Gate S test (10,000 scenarios);
  - 313: L's training stream;
  - 304: validation;
  - 305 stays reserved, and 311 was used by spec 004.

## R8. Export

L's evidence network exports to ONNX as spec 003's models do (Loop-free, fixed window, dynamic
batch), with three-runtime conformance to 1e-5. The search, confirmation and physics layer stay
in host code: the physics layer is already exported separately, and the decoder is not part of
the deployable graph (FR-045).

## Summary of decisions that change or fill in the spec

| Item | Spec said | Plan decides | Reason |
| --- | --- | --- | --- |
| C's design (FR-021, FR-022) | additive search, then top-k coupled refinement | coupled nominate-and-confirm, with the search as a second nominator and boundaries polished | R1 and R2: the additive search is much weaker than GLR + confirm, and the refinement cannot recover it |
| Search penalty | BIC-style from σ | calibrated to a declared false-split rate (≤ 5%) on a tuning set | R1: per-hypothesis χ² gives a 45% false-split rate |
| Re-test while raised | — | every 6 rows | note 08 §5 item 10 |
| Gap normalisation (FR-061) | decision record | raw medians, efficiency beside | R7 |
| L's loss (FR-042) | semi-Markov likelihood | the same, plus an auxiliary per-bearing term at 0.1 | R6 |
