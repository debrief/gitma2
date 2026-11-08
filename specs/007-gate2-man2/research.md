# Research: Gate 2 on MAN2

All measurements are on seed 314 validation (tuning ordinals 0–499, scoring ordinals 500–1499),
or on fixtures where stated. Items marked **(CI)** are run as the first implementation tasks,
because local runs of more than a few minutes die on container restarts. Their decisions are
fixed here, conditional on the stated outcome.

## R1. Which learned segmentation is built first

**Decision.** Build E-s as form (b): evidence that shifts C's confirmation threshold, trained
through confirmation's decisions (R2). Build form (a), a learned nominator, only if the nominator
ceiling below shows recall is a lever. The ceiling feeds C's confirmation the true change starts
as extra nominations, keeping C's acceptance rule, and measures C's gap recovered **(CI)**. The
condition is a ceiling gain of at least +0.02 over C on the scoring ordinals.

**Rationale.**
- **Where C loses.** Gate S located C's loss:
  - rows ending inside an open transition: 0.66 of the gap against 0.91 elsewhere, with all of
    L − C on those rows;
  - weakly detectable changes: 0.76 in the lowest band.
- **What each form can reach.** A nominator can only add candidates, and C's misses are
  concentrated where bearings barely show the change. Confirmation's decisions, and how the state
  at k is handed over, act on the rows that matter. The open-at-k rows are mainly a hand-over and
  weighting problem, which E-w addresses directly.
- **Cost.** Form (b) costs nothing extra at inference: one threshold shift per candidate. Form (a)
  costs physics solves per extra candidate.

**Measured (T003, `experiments/20261106-nominator-ceiling/`).** The ceiling gains +0.0164
[+0.0071, +0.0277] in gap recovered (range), below the +0.02 rule, so form (a) is not built.

**Alternatives considered.**
- Form (a) first: rejected unless the ceiling shows recall gains.
- Gate S's L design (evidence through the additive search's lattice): rejected, because Gate S
  showed it adds nothing.

## R2. The gradient path

**Decision.**
- **E-w:** the physics layer's implicit differentiation at C's knot set (spec 003's path, with
  knots). Gradients flow to the per-bearing log-weights and the initial-state correction. The
  segmentation is an input, not differentiated.
- **E-s:** a relaxed acceptance over **decision tables**. For each confirmation decision of C on a
  training scenario (the candidate, its row a, cost drop Δ and threshold τ′), the table stores
  the bound-normalised downstream error at the scored rows the decision affects, with and without
  the transition, holding C's other decisions fixed. The loss is
  Σ [p·e_with + (1 − p)·e_without], with p = σ((Δ − τ′ − s)/T), s = clamp(2Σe, ±τ/2): positive
  evidence (steady) raises the threshold. The evidence e is summed over
  the candidate's rows, capped at ±τ/2 as in spec 005, and T is a declared temperature.
  - At e = 0 the hard decisions are C's, so an untrained E-s is C.
  - At inference the decision is hard: accept if Δ − τ′ − s > 0. (Corrected after the Gate 2
    panel, round 1: an earlier draft had the opposite sign; the code always subtracted s.)
- **Joint model:** E = E-s's segmentation, then E-w's weights. Each is a separate training job.
  - **Amended before the decision record (2026-11-06, implementation):** E-w trains on C's
    segmentation, not E-s's, and the two train in parallel; E seed s pairs E-s seed s with E-w
    seed s (the shuffled E pairs the two shuffled controls). Reason: E-s's segmentation of the
    stream costs a full C re-run (about C's own stream run) per E-s seed, while E-s changes only
    decisions within τ/2 of their threshold, a small share of rows. The cost is a distribution
    shift for E-w on the rows E-s flips. E-w alone is scored on C's segmentation as before.
    Alternative (the original order) kept open if validation shows E worse than E-w alone.
- **E-s inputs:** spec 005's causal features; C's per-row code is not an input (at a decision
  it would encode the decision being shifted). The relaxation holds C's best candidate fixed;
  at inference the evidence can also move the best start or length.

**Rationale.**
- Back-propagating through confirmation's argmax over candidates is not defined. Score-function
  estimators are high-variance at this data size.
- The one-decision-at-a-time relaxation is exact for isolated decisions (most MAN2 changes are
  25 min apart) and cheap at training time, since it reads tables.
- Gate S's lesson: train where the decision is made.

**Alternatives considered.**
- A straight-through estimator through the whole confirmation: no gradient for rejected
  candidates.
- REINFORCE over C's run: variance and cost.
- Joint training of E-s and E-w: one job, but entangled; kept as a later option.

## R3. The encoder

**Decision.** The Gate 1 encoder (`models.gate1`: causal transformer, width 64, smooth heads that
cannot die, zero last layers; spec 004's fixes) on per-timestep features of the 720-row MAN2
window. There is one extra input channel: C's per-row code at prefix k (steady, transition,
unknown, computed causally). Weights are not carried from Gate 1, which was trained on CV data.

**Rationale.** It is reused, exportable (spec 003 R2), and equal to C at initialisation (the zero
heads). The extra channel lets the weights depend on where C thinks the transitions are.

**Alternatives considered.** A convolution as spec 005's L: cheaper, but causal attention lets a
row look back across a leg. Its cost is measured in the throughput task.

## R4. Throughput and the training stream

**Measurements (local, 16 validation scenarios, 64 G5 prefixes, r_max 656).** The physics layer
with knots costs:

| Threads | Forward per prefix | Backward per prefix |
| --- | --- | --- |
| 1 | 57 ms | 0.2 ms |
| 4 | 29 ms | 0.06 ms |

Gradients are finite.

**Decision.**
- **Training stream.** Seed 318, `--count 12500` (a train split of 10,000, as Gate S's stream).
  The stream is segmented once by C on CI: about 10 s per scenario, 16 shards.
- **Prefixes.** Training uses the G5 prefixes plus 2 prefixes sampled per scenario per epoch,
  seeded.
- **Epoch budget.** About 60,000 prefixes per epoch at 57 ms each is about 1 h on one thread.
  With 4 worker processes at one thread each it is about 15 min.
- **Robust loss.** A prefix's per-component loss is clipped at a declared cap (100 in
  bound-normalised units). A prefix whose physics-layer cost exceeds 20 × its valid bearing count
  (a failed fit) is excluded. Early stopping uses the trimmed mean (10% each tail) of the
  validation loss, with patience 3 and a relative improvement of 1e-3 on that robust scale.

**Measured (T016, `results/g2-throughput-42295011455`, one 4-core runner, Xeon 8370C).** One
epoch of E-w over stream ordinals 0–999 (3,905 G5 prefixes, batch 32, 4 threads) took 254 s
including the validation pass over tuning ordinals 0–499: about 65 ms per prefix, no failed fits
excluded. The trimmed validation loss moved from 38.10 (untrained, C) to 37.86. A full epoch over
the stream's 39,054 prefixes is therefore about 45 min, so `max_epochs` is 12 (about 9 h, within
two chained jobs of 345 min) rather than 20; patience 3 usually stops earlier.

**Rationale.** Gate S's L was stopped early by one 96,000-nat prefix. A trimmed statistic and a
cap make one prefix unable to decide.

**Alternatives considered.** Re-drawing noise every epoch: rejected, because C's segmentation
would then have to be recomputed each epoch.

## R5. C, the frozen control

**Decision.**
- **Open-transition hand-over:** chosen by `score/c3-val` (FR-002), the lowest median range over
  G5 rows among `knot_at_k`, `start_masked` and `start_chord`. Recorded in
  `experiments/20261106-c3-val/`: **`knot_at_k`** (it ties `start_masked` on median range,
  0.120299, and is best on the 210 open-at-k rows, 0.695 against 0.653 and 0.680).
- **Knot cap:** raised from 8 to 12 in every Gate 2 scoring and in E. Measured on validation: 7 of
  3,934 G5 prefixes need more than 8 knots, for the oracle and for C alike (maximum 10).
- **Freezing:** C's parameter digest and code digest (`segment/codeid.py`) are frozen in the
  decision record. Gate 2's CLI refuses segmentations whose digests differ.

**Rationale.** These are the Gate S panel's prerequisites. The knot cap is a pre-existing limit
found while planning; it affected Gate S negligibly and equally.

## R6. Gate scoring

**Decision.** `tma2-g2` follows `tma2-gs`.
- **Inputs:** C's segmentation file, E's prediction files (per-row state and covariance from
  `tma2-g2predict`), and the reference set: naive, one leg, IMM, EKF, GLR + confirm and the
  oracle.
- **Gate mode:** G2-a…G2-d, the shuffled rule, the validation rule's record, and refusals of
  mismatched decision, plan, seed, data, weights, parameter or code digests. Provenance is read
  first; `inputs.json` and the manifest bind every file.
- **Scoring:** on CI with `score.yml`, extended by a `g2` job kind.

**Rationale.** It reuses tested machinery: errors, strata, efficiency and bootstrap.

## R7. The decision record and forecast

**Decision.** `Gate2Decision` holds:
- seeds and digests (314, 318, 319);
- C's parameters, parameter digest and code digest, and the open-transition hand-over;
- E's configurations;
- the training plan digest;
- criteria and limits (G2-a…G2-d), the shuffled rule and the carried-seed rule (median by
  validation gap recovered);
- the validation rule, the re-score policy (not taken; the minimum-effect argument) and the
  temperature T;
- the knot cap;
- a forecast.

**Forecast (to be refined with validation numbers before the record).** E-w should help on the
open-at-k rows, worth about +0.01 to +0.02 of the gap. E-s adds little. E − C is about
+0.01 [−0.005, +0.025], so G2-d is more likely inconclusive than a pass (probability of a pass
about 35%). G2-a to G2-c pass, as C does.
