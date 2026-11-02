# Design rethink after Gate D

Status: draft for the owner, 2 November 2026. Written at the owner's request ("pause for a design
rethink") before any Gate 2 spec. It sets out the evidence from Gate 1 and Gate D, the likely
causes, and five options to choose between. Nothing here has been trained or pre-registered.

## 1. Where we are

The prize is real and measured. On validation seed 304 (MAN data, σ = 1°, G5 rows), median range
error:

| Estimator | All rows | Settled rows |
| --- | --- | --- |
| batch least squares | 12.1% | 6.8% |
| IMM, frozen and re-tuned | 9.5% | 7.5% |
| EKF, frozen | 10.0% | 7.4% |
| the trained detector feeding the physics layer | 11.5% | 6.6% |
| **oracle** (true segmentation into the same physics layer) | **5.2%** | **4.0%** |

The oracle is 0.55 × the IMM, as research note 05 found on gitma's data. Good segmentation is
worth almost half the IMM's error, and the physics layer turns it into an estimate exactly.

The learned components have so far learned nothing usable:

- **Gate 1** (constant velocity) passed because the heads died: the model *is* batch least
  squares.
- **Gate D** stopped at validation. The panel verified that the detector's "manoeuvre now"
  probability reads only time since the zig. It does not respond to how strongly a manoeuvre
  bends the bearings, at σ = 1° or 2°. The time-late variant sees the future and is still at
  chance. Downstream it is 0.95 × batch least squares, 1.21 × the IMM.
- Non-learned detectors do find manoeuvres. On validation, at a 5% held-leg false-alarm rate:

  | Detector | Spans detected |
  | --- | --- |
  | windowed GLR | 57% |
  | IMM mode probability | 48% |
  | least-squares CUSUM | 10% |

  So the information is in the bearings. The network did not extract it.

## 2. Why it failed: three hypotheses

The panel's evidence supports all three. They are not exclusive.

1. **Where the knots go gets no gradient.** The physics layer keeps the top-k changepoint weights
   as knots. The implicit gradient reaches the *weights* of the knots it chose, but not the
   *choice*: no gradient says "put a knot two minutes earlier". Untrained, every weight is equal
   and tiny, so the chosen knots are arbitrary. Only the classification losses could move them.
   But the downstream term outweighed those classification terms about 1000:1 in the shared
   encoder's gradient. (The panel measured this.)
2. **The inputs make the network solve TMA before it can detect.** The encoder sees bearings,
   ownship positions and time. A target manoeuvre shows up only as a change in the bearing
   residual *after* the target's own motion is accounted for. The network would have to learn a
   bearings-only solver internally to see it. The classical detectors are handed exactly that
   residual (innovations, a one-leg fit's misfit).
3. **The labels and thresholds asked for the impossible.** The "now" label is a 60-second window,
   but the bearing signal of a turn builds over minutes: the median signal-to-noise proxy over
   turn + 60 s is 1.4. Rows just after a turn, where the evidence appears, were trained as
   negatives. The held-leg ×3 weighting deflated probabilities, and the hard 0.5 export threw away
   about half the soft segmentation's learned gain.

## 3. Options

| | Option | What changes | Cost | Chance it beats the IMM | Needs the owner |
| --- | --- | --- | --- | --- | --- |
| **A** | **Classical segmenter, physics layer, no learning** | GLR (or IMM mode) alarms become knots for the physics layer; kinds from the fitted increment | days | unknown: diagnostic below | no (a baseline) |
| **B** | **Learn on top of the classical statistics** | The detector's inputs gain the residual channels (least-squares innovations, the GLR statistic along the window, IMM μ_CT); it is trained on classification only, with labels re-defined at a minutes scale, and scored soft (no 0.5 export) | 1–2 weeks | moderate | yes: an Annex A amendment |
| **C** | **Fix the end-to-end design** (SRD Gate 2 as written) | Soft knots over all rows, or a fixed knot grid every N rows with learned weights, so placement is differentiable; per-term gradient normalisation; longer training; soft scoring | 2–3 weeks | low to moderate: tests the SRD's central hypothesis directly | no, if kept within Gate 2 |
| **D** | **Hypothesis bank over the physics layer** | For each candidate change row in a recent window, solve with and without a knot. A small learned scorer (or the likelihood ratio alone) picks among the solutions, so the physics layer's own residuals are the evidence: a learned, multi-leg GLR | 2–3 weeks | moderate to good | yes: an SRD amendment |
| **E** | **Close the question and move on** | Publish "learned segmentation did not beat classical at this budget"; use A as the segmenter; continue SRD §7 step 5 (uncertainty calibration, realistic bearing error, the viewer) | days | — | yes: a change of plan |

Notes:

- **A** is the floor every other option must beat. It may already beat the IMM, because the
  GLR finds 57% of manoeuvres and the physics layer is exact once knots are right. In that case
  most of Gate 2's prize is classical, and learning must justify itself against A.
- **B** keeps the detector small and gives it what the controls use. It is the most direct fix
  for hypotheses 2 and 3, and it can be piloted on validation in a day.
- **C** is the only option that keeps "end to end through physics" as the claim. It repeats the
  Gate 1 and Gate D pattern unless placement is made differentiable (hypothesis 1).
- **D** turns the physics layer from a consumer of segmentation into its source of evidence. It
  is the most principled answer to hypothesis 2. It costs compute: one extra solve per candidate
  row, mitigated by warm starts and a short window.
- Every option keeps the free-runner budget, the pre-registration, the panel and the export.

## 4. Diagnostics that decide between them

These need no training and no money, about an hour on validation seed 304, σ = 1° G5 rows:

1. **A's number:** GLR alarms (5% held-leg rate) → knots → physics layer, and the same with the IMM
   mode probability.
2. **The soft-segmentation number:** the trained Gate D detector's *soft* w_change → physics
   layer. Does the learned signal help once it is not thresholded?
3. **Knot tolerance:** truth knots with random misses and false alarms at the GLR's measured rates.
   How much of the oracle survives realistic detection?

Reading:

- **If A ≤ the IMM,** a learned increment (B or D) has a concrete target.
- **If A is far above the oracle but below the IMM,** E is defensible.
- **If 3 shows the oracle collapses at realistic error rates,** no segmenter, learned or not, will
  reach half the gap. Gate 2's criterion would then need the owner's review before any spec.

## 5. Recommendation

1. **Run the three diagnostics first.** No training, no spend, and they settle which option is
   worth building.
2. **Then, by default, A as the baseline and B as the learned increment,** piloted on validation
   before any pre-registration.
3. **D if B's pilot cannot beat A.**
4. **C only if the owner wants the end-to-end claim tested as the SRD wrote it.**

## 6. Decisions for the owner

To be asked one at a time:

1. Run the diagnostics before choosing (recommended), or choose now.
2. Which option: A + B (recommended), C, D or E.
3. If B or D: amend Annex A or the SRD before the next spec. The owner merges SRD and annex
   amendments.
