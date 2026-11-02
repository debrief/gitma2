---
title: Steady-leg detector
---

# The steady-leg detector

Sources:

- `src/tma2/models/` (detector, detector_labels, detector_inputs, detector_loss, detector_train,
  detector_predict, detector_export);
- `src/tma2/detect/` (controls, matching, downstream) and `src/tma2/eval/gd.py` (Gate D).

Requirements: SRD Annex A and spec 004. The [physics layer](physics-layer.md) consumes the
detector's output.

The detector answers one question about the target's track: where its velocity changed, and how.
It does not estimate the target's state. Its outputs become the physics layer's knots and its
speed-continuity prior. The estimate is the physics layer's, with trivial per-bearing weights, so
the detector is credited only for segmentation.

## Inputs

One window has R = 360 rows (60 min at 10 s). Each row has 13 channels, every one with a fixed
scale, so no statistic is taken from the data:

- the bearing as sin z · v and cos z · v, and the valid flag v;
- ownship position relative to the first row, ÷ 10 km;
- ownship course as sin and cos, and ownship speed ÷ 10 m/s;
- time ÷ 1 h;
- the window mask;
- the trailing least-squares bearing rate over 18 rows (gitma's derived channel, ÷ 10⁻³ rad/s),
  with its validity flag;
- the bearing-line intercept oₓ cos z − o_y sin z, ÷ 10 km.

The features are computed inside the exported graph.

## Encoder and heads

The encoder is the Gate 1 model's: a linear embedding to width 64, two pre-norm transformer
blocks with four heads, and a layer norm. The causal variant masks future rows. The time-late
variant sees the whole window and is asked its question at the last row.

On the encoder output h, with one vector per row:

- `p_change[k] = σ(MLP(h_k))` is the probability that a manoeuvre is in progress at k or began
  within the last 60 s.
- `w_change[k, j] = σ(b + (Q h_k)·(K h_j)/√d)` for 0 < j ≤ k is a soft changepoint weight at
  row j, as judged from row k. The asking row k has seen the bearings after j, which is where a
  course change becomes visible.
- `p_kind[k, j]` has the same bilinear form. It is the probability that a changepoint at j is a
  course change rather than a speed change.

Every MLP is Linear → tanh → zero-initialised Linear; tanh cannot die, as Gate 1's ReLU heads
did. In each pairwise head the key projection starts at zero and b starts at −10. So the untrained
detector gives p_change = p_kind = 0.5 and w_change ≈ 4.5·10⁻⁵ everywhere. It exports no knot, and
the physics layer then reduces to batch least squares.

## From segmentation to the physics layer

At a scored row k:

- the layer's changepoint input is `w_change[k, :]`, and it keeps the 8 largest weights as knots;
- the speed-continuity weight and its skip at knot j are both `p_kind[k, j]`. A course change ties
  the speed after the knot to the speed before the previous one.

Research R4 measured this mapping on truth boundaries: 0.442 × batch least squares' median range
error on G5 rows, against the exact oracle's 0.435.

The exported knots are the local maxima of `w_change[k, :]` at or above 0.5, the 8 largest. A
plateau counts once, at its first row, so a one-row speed change gives one knot. A knot with
p_kind ≥ 0.5 is a course change.

## Labels and losses

Labels come from the stored manoeuvre spans; both the start and the end of a span are
boundaries.

- `now[k]` is 1 when a span is in progress at k or began within 60 s.
- The pairwise target is a triangular kernel of ±60 s around each boundary at or before k.
- The kind target is that of the nearest past boundary.

The loss has four terms, each with weight 1:

- binary cross-entropy for `now`, with held-leg rows weighted 3;
- binary cross-entropy for the pairwise boundaries;
- binary cross-entropy for kind, weighted by the boundary target;
- the downstream loss.

The downstream loss is the primary objective. It runs the physics layer, fed the soft
segmentation, at two scored rows per scenario: one G5 row and one random post-zig row. Its error
in log range, vx and vy is divided by the known-manoeuvres Cramér–Rao bound (a numba port, 0.4 ms
per scenario), squared and capped. Gradients reach the detector through the implicit Newton step.
A detector trained without this term is the declared control.

## Controls

Gate D compares the detector with three detectors that an engineer would build without learning.
Each threshold is tuned on validation to the detector's own held-leg false-alarm rate.

- **CUSUM** on the per-timestep least-squares innovations, as Annex A writes it. Because the
  one-leg fit is wrong after the first manoeuvre, it is weak on manoeuvring data: it detects 10%
  of spans at a 5% false-alarm rate. A CUSUM on the EKF's innovations is reported beside it.
- **GLR**: a velocity change in the last 30 samples, linearised at the per-timestep
  least-squares estimate. The window's one-leg fit is projected out, so only a change inside the
  window counts. It detects 57% of spans at 5%.
- **The IMM's turn-mode probability** μ_CT from the frozen reference.

## Gate D

The gate is scored on σ = 1° test rows with scenario-clustered 97.5% intervals:

| Check | Statistic | Limit |
| --- | --- | --- |
| D-delay | median detection delay ÷ the better control's | wholly below 1 |
| D-miss | miss rate − the better control's | wholly at or below 0 |
| D-false | share of held-leg G5 rows flagged | wholly below D3's limit |
| D-downstream-all | median range error ÷ the IMM's, all G5 rows | wholly below 1 |
| D-downstream-settled | median range, course and speed ÷ batch least squares', settled G5 rows | each wholly below 1.1 |

D3's limit is the frozen IMM's own rate on validation, 0.28%, because that is below 5%.

## Export

The detector exports alone to ONNX: double precision, a 360-row window, dynamic batch, and no
`Loop` or `If`. Python onnxruntime, onnxruntime-web (WASM) and Java agree with torch to 1e-13.
WASM takes 0.10 s per window, against Annex A's one-second limit; CI checks this.
