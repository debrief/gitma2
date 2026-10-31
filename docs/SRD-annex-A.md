# SRD Annex A: Steady-leg detector and Gate D

Draft 2026-10-31 · owner decision of the same date: the detector is its own annex and spec inside
gitma2, not a separate repository · status: proposed

## A.0 Status and scope

A **steady-leg detector** marks, from bearings and ownship state alone, the timesteps at which
the target's constant-velocity leg ends and a new one begins, and what kind of manoeuvre
separates them. Once trained it pre-processes a bearing window for any downstream estimator:
batch least squares, the hybrid, the viewer, or the gitma2 physics layer.

Why it is first: the oracle experiment (`docs/research/05`) showed that segmentation alone takes
a piecewise batch solve from 1.15 × the frozen IMM's median range error to 0.64 ×, and knowing the
manoeuvre kind to 0.53 ×. Detection is a classification task, which gitma's networks did well
(phase 3b detected real turns with a 70 s median delay and 0.5% misses); what failed was the
false-alarm rate on held-course legs (29–31%), because the flag was trained on a label whose
cost it could not see. This annex gates that number.

In scope: the detector, its controls, its metrics, its gate and its use by the physics layer.
Out of scope: anything about ownship manoeuvres (known exactly), multi-target, and realistic
bearing error (deferred as in §1).

## A.1 Problem

- **Input.** A causal window of gitma's feature channels up to timestep k (bearing sin/cos,
  ownship position, course, speed, time, valid, mask, and the derived channels: bearing rate, its
  validity flag, bearing-line intercept), on MAN data (generator 0.5.0 semantics, phase-4 ranges,
  σ ∈ {1°, 2°}, 0–10% dropouts). A non-causal variant over the full window is allowed as the
  time-late counterpart and must do at least as well.
- **Output, per timestep k:**
  1. `p_change[k]`: the probability that a manoeuvre is in progress or began within the last
     Δ = 60 s (the "now" detector, for alarms and for the hybrid switch);
  2. `w_change[k, j]` for j ≤ k: a soft changepoint weight over earlier timesteps (the
     segmentation the physics layer consumes; at export time, knots are the local maxima above a
     threshold fixed in the decision record);
  3. `p_kind[k, j]`: for each candidate changepoint, the probability that it is a course change
     (speed carried through) rather than a speed change.
- **Truth.** `ManoeuvreSpan` (start_index, end_index, kind) from the stored target track; a
  manoeuvre counts as detected when `p_change` first exceeds the declared threshold within
  [start_index, end_index + 300 s].
- **Operating regimes** that must both be measured: *held legs* (rows before the first manoeuvre,
  and rows more than 5 min after the last; in 0.5.0 about 44% of G5 rows), and *post-manoeuvre
  rows*.

## A.2 Controls

- **CUSUM** on the per-timestep batch least-squares innovations (the single-CV solve warm-started
  as gitma's `tma-solve --per-timestep`), threshold tuned on validation to the same false-alarm
  rate as the detector's declared operating point.
- **GLR** manoeuvre-onset detector (Ru, Jilkov, Li, Bashi, IEEE TAES 2009): a windowed fit of
  one versus two constant-velocity legs over the last W samples, likelihood-ratio thresholded,
  tuned the same way.
- **The IMM's mode probability** from the frozen reference tracker, thresholded.
- **gitma phase 3b's flag** on its own validation split, reported for continuity.

The detector must beat CUSUM and GLR, which are what an engineer would build without learning.

## A.3 Metrics

All on the σ = 1° slice of a fresh MAN test seed, with scenario-clustered paired bootstraps at
97.5% (two variants may be carried).

| Metric | Definition |
| --- | --- |
| Detection delay | median and P90 of (first alarm time − manoeuvre start), over detected manoeuvres, by manoeuvre kind and angle band |
| Miss rate | manoeuvres with no alarm within end_index + 300 s |
| **False-alarm rate on held legs** | alarms per hour of held-leg time, and the fraction of held-leg G5 rows (zig + 5, 10, 15, 20 min) at which `p_change` exceeds the threshold |
| Kind accuracy | fraction of detected manoeuvres whose kind is right, by kind |
| Segmentation quality | F1 of exported knots against truth spans at ± 60 s tolerance |
| **Downstream error** | median range, course and speed error of the physics layer with trivial weights, fed by the exported knots and kinds, against: batch LS (no knots), the IMM, and the oracle ceiling, on all G5 rows and on settled rows |
| Calibration | reliability of `p_change` and `p_kind` (expected calibration error) |

## A.4 Design constraints

- **Soft outputs, not a flag.** The detector outputs probabilities and weights (A.1) so that the
  physics layer can consume them continuously and a later spec can fine-tune the detector end to
  end through the estimation loss (constitution III).
- **Training loss sees the cost.** Besides the span-derived classification losses (with the
  ± 60 s tolerance and a held-leg weighting declared in advance), the primary training objective
  includes the **downstream error of the piecewise solve** fed by the soft segmentation, computed
  with the physics layer in the loop and the truth state as target, normalised by the Cramér–Rao
  bound. A detector trained on the classification losses alone is a declared control.
- **Threshold fixed in advance.** The operating threshold on `p_change` is declared in the
  decision record (default 0.5); it is not tuned on validation.
- **Encoder shared with the main model.** The detector's encoder is the gitma2 encoder
  (standard ops, causal mask), so Gate 2's model can start from its weights.
- **Export.** The detector exports alone (ONNX, fixed window, dynamic batch) and passes the
  cross-runtime conformance test; it must run in the browser viewer on a 360-row window in under
  one second on WASM.
- **Compute.** As §4: one epoch over 10^5 scenarios in under an hour on a 4-core runner.

## A.5 Gate D

Judged on a fresh MAN test seed, σ = 1°, after P0 and before Gate 2; intervals as A.3.

| Check | Statistic | Limit |
| --- | --- | --- |
| D-delay | median detection delay, detector / best of CUSUM and GLR at matched false-alarm rate | wholly below 1 |
| D-miss | miss rate, detector − best control | wholly at or below 0 |
| D-false | fraction of held-leg G5 rows flagged | wholly below 5% (gitma phase 3b: 29–31%; the IMM's own mode probability is reported) |
| D-kind | kind accuracy | reported, not gated |
| D-downstream-all | median range error of the physics layer fed by the detector, / the IMM's, all G5 rows | wholly below 1 |
| D-downstream-settled | median range, course and speed on settled rows, / batch least squares' | wholly below 1.1 |
| D-gap | share of the gap between batch LS and the oracle ceiling recovered on all G5 rows, median range | reported; Gate 2 gates it at 0.5 |

- **Pass:** D-delay, D-miss, D-false, D-downstream-all and D-downstream-settled all pass for at
  least one carried variant.
- **Fail:** for each carried variant, at least one of those fails.
- **Inconclusive** otherwise; one re-score on a larger fresh seed, then final.
- **Validation rule.** A variant is carried only if every gated check's point meets its limit on
  validation and no interval lies wholly beyond it. If none is carried, the test split is not
  scored.

**Why the bar is fair.** The controls are tuned to the detector's own false-alarm rate, so the
comparison is at matched operating points; the downstream checks use the physics layer with
trivial weights, so the detector is credited only for segmentation, not for anything learned
about the estimate; and the IMM gets its validation-tuned setting.

## A.6 What follows Gate D

Fixed here so the result cannot choose its follow-on.

- **If Gate D passes:** the detector is frozen and becomes (1) the segmentation input and the
  warm start for Gate 2's end-to-end model, and (2) the carried-forward control at Gate 2, so the
  end-to-end fine-tuning must beat "detector, then solve" to claim anything. The hybrid switch in
  the viewer uses `p_change` in place of gitma's fixed 50% rule.
- **If Gate D fails on D-false only** (it detects but false-alarms): one pre-registered iteration
  is allowed that changes the held-leg weighting or the downstream loss weight, nothing else; then
  Gate 2 proceeds with the CUSUM/GLR control as its segmenter and the learned detector reported.
- **If Gate D fails otherwise:** publish; Gate 2 proceeds with the CUSUM/GLR segmenter; the
  end-to-end model may still learn segmentation through the estimation loss, and that result
  stands on its own.

## A.7 Amendments to the main body (apply when this annex is accepted)

- §4 heads: the segmentation and kind heads are those of A.1.
- §5 gates: Gate D row (present).
- §7 step 3 (present).

## A.8 Decisions with defaults (adopted unless the owner objects before the decision record)

The agent writing the detector spec adopts these defaults, records them in the decision record
with a one-line reason each, and proceeds (`AGENTS.md`, Autonomy and owner input). The owner may
overrule any of them on the spec's PR.

- **D1** Operating threshold and tolerance: **0.5 and ± 60 s**.
- **D2** Variants carried: **both** the causal and the time-late detector, each at 97.5%.
- **D3** Held-leg false-alarm limit: **5%**. If the frozen IMM's own mode-probability false-alarm
  rate on validation is below 5%, the limit becomes that rate, and the decision record says so.
- **D4** Test seed: a **fresh seed from 301 onward** (gitma's 201–212 and the oracle
  experiment's 777 stay reserved), its digest pinned in the plan.
