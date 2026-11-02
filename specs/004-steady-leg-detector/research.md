# Research: steady-leg detector and Gate D (spec 004)

Measurements were made on the training stream (seed 311, phase-4 ranges) or on fixtures, never on
validation seed 304 or test seed 305. "Locally" means a 4-thread Xeon at 2.1 GHz; GitHub's 4-core
runners (AMD EPYC 7763) ran spec 003's training step 1.8 × slower.

## R1. Heads that cannot die (Gate 1 prerequisite)

**Decision**: hidden head layers use **tanh** in front of the zero-initialised output layer; the
activation is a configuration field (`head_activation`: relu | tanh), so Gate 1's committed weights
(ReLU) still load and re-score unchanged, and every new configuration uses tanh. A training-time
**liveness check** runs on the validation batch after every epoch and at the end. It records two
figures: the share of hidden units whose activation varies across rows (|Δ| > 1e-3), and the
standard deviation across rows of each head's output. A test trains a tiny model for a few hundred
steps on detector labels and asserts both floors (alive share ≥ 0.5, output sd ≥ 1e-3); a model
with its heads zeroed fails the same check.

**Rationale**: Gate 1's heads ended with 0 of 64 ReLU units active. A ReLU unit whose input stays
negative has zero gradient for every input and never recovers; tanh's derivative is never zero.
A zero-initialised output layer still makes the untrained detector inert (no knots, p = 0.5),
which keeps "untrained = batch least squares" for the downstream solve.

**Alternatives**: SiLU or GELU (double `Erf` and `Sigmoid` kernels are not all present in the web
runtime; tanh already passes the three-runtime conformance in the Gate 1 export); leaky ReLU
(cannot die, but its kink adds nothing here); no hidden layer (loses capacity the pairwise heads
need).

## R2. Detector heads

**Decision**: the encoder is spec 003's causal transformer (width 64, 2 pre-norm blocks, 4 heads),
widened to 13 input channels (the raw and derived channels of Annex A §A.1, fixed scales). On its
output h (one vector per row):

- `p_change[k] = σ(MLP(h_k))`;
- `w_change[k, j] = σ(b + (Q h_k)·(K h_j)/√d)` for 0 < j ≤ k, 0 elsewhere: a bilinear pairwise
  score, so the row k at which the question is asked can revise its belief about an earlier row j
  that it has seen more bearings after;
- `p_kind[k, j] = σ(b' + (Q' h_k)·(K' h_j)/√d)`: the probability that a changepoint at j is a course
  change rather than a speed change.

Every MLP is Linear → tanh → zero-initialised Linear; the pairwise projections end in
zero-initialised bias terms set so the untrained detector outputs w_change = 0 (no knots) and
p_change = p_kind = 0.5. The time-late variant drops the causal mask and asks every question at
the window's last row.

**Rationale**: a per-row changepoint score from a causal encoder sees only bearings up to j, but a
course change is visible only some minutes later; pairing h_k (the asking row) with h_j (the
candidate) lets the evidence after j count. The bilinear form is two matrix products: [B, R, R]
for R = 360, cheap to train and to export.

**Alternatives**: an attention head per candidate (more parameters, same expressiveness here); a
per-row score from the time-late encoder only (no causal variant).

## R3. Labels

**Decision**: from the stored spans (columns kind, start_index, end_index; the manoeuvre begins
at row start − 1 and ends at row end):

- `now[k] = 1` when a span is in progress at k (start ≤ k < end) or began within the last 60 s
  (k − start < 60 / dt);
- `w_target[k, j]` for j ≤ k: 1 at each span boundary (start and end) that is ≤ k, spread by a
  triangular kernel of half-width ±60 s (D1) and capped at 1;
- `kind[j]` at boundary rows: 1 for a course change, 0 for a speed change.

Held legs are rows before the first manoeuvre or more than 300 s after the last (`settled_row`,
Annex C §C.5); settled rows are the held legs after at least one manoeuvre.

## R4. From soft segmentation to physics inputs

**Decision**: for a scored row k, the physics layer's changepoint input is `w_change[k, :]` (the
layer keeps the 8 largest weights ≤ k as knots, as P0); the speed-continuity weight and its skip at
a knot j are both `p_kind[k, j]` (course change: the speed after the knot is tied to the speed
before the previous knot). The exported segmentation is the local maxima of `w_change[k, :]` above
the decision record's knot threshold (default 0.5), with their kinds (p_kind ≥ 0.5 is a course
change).

**Measured** (seed 311, 947 σ = 1° G5 rows, truth spans, median range error ratio to the
no-knot solve):

| Inputs | Ratio | Gross |
| --- | --- | --- |
| no knots (batch least squares) | 1.000 | 19.5% |
| knots at span boundaries, no speed prior | 0.516 | 2.4% |
| P0's oracle: speed prior with skip on each course span's end knot only | 0.435 | 2.7% |
| speed prior with skip on **every** course-span knot (start and end) | 0.442 | 3.1% |
| speed prior on end knots without the skip | 0.496 | 2.5% |
| P0's oracle with knots jittered by up to ±30 s | 0.454 | 3.0% |

**Rationale**: the detector cannot tell a turn's start knot from its end knot, but applying the
prior at every course-change knot costs only 0.007 against the oracle, so `p_kind` can drive the
prior directly with Annex A's meaning. Timing errors of ±30 s cost 0.02, which supports the ±60 s
tolerance.

## R5. Training objective and throughput

**Decision**: loss per batch =

- downstream: the CRB-normalised squared error of log range, vx and vy at the scored rows
  (known-manoeuvre bound, as P0), the physics layer fed by the soft segmentation with trivial
  per-bearing weights and the grid start, gradients by the implicit Newton step (spec 003 R1),
  weight 1;
- classification: binary cross-entropy for `now` (held-leg rows weighted 3, the "held-leg
  weighting" of Annex A §A.4), for `w_change` against the triangular targets (all pairs j ≤ k at
  the scored rows) and for `p_kind` at boundary rows; weight 1 each.

The classification-only control drops the downstream term. Per scenario: one noise draw, the
classification terms at every row (cheap), the downstream term at two rows (one G5 row and one
random post-zig row), a 50-iteration training solve with 8 knots (spec 003 R4), prediction at 100.

**Measured** (locally, 192 rows of 64 scenarios, implicit forward + backward of the layer):
0 knots K = 50: 2.3 ms per row; 8 knots K = 50: 7.8 ms; 8 knots K = 100: 11.6 ms; 4 knots K = 50:
4.3 ms. Two downstream rows per scenario at 8 knots, K = 50 cost about 16 ms per scenario for the
solve locally; with the encoder, labels and pairwise heads the step is measured in T012's
benchmark on the runner before the plan is fixed (budget: under an hour per 10⁵ scenarios, i.e.
36 ms per scenario on the runner).

**Measured after implementation** (T014, local 4 cores, nothing else running; the full step:
batch inputs, encoder, pairwise heads, two downstream rows at 8 knots and K = 50, backward):

| Batch | Inputs | Step | Total per scenario | Epoch of 10⁵ |
| --- | --- | --- | --- | --- |
| 32, tensor grid start | 1 ms | 63 ms | 64 ms | 107 min |
| 32, numba grid start | 11 ms | 29 ms | 40 ms | 66 min |
| 32, numba grid start in parallel | 4 ms | 30 ms | 34 ms | 57 min |
| 64, numba grid start in parallel | 4 ms | 23 ms | 27 ms | 45 min |

The grid start in tensors cost more than the solve (14 ms per row); it carries no gradient, so
training uses gitma's numba one (equal to 1e-9; the tensor one stays for the exported graph). In
the step, the 50 damped iterations take 62%, of which `atan2_export` is 18%; replacing it with
`torch.atan2` in eager mode would break the spec 003 invariant that the eager solve equals the
exported graph bit for bit, so it is not done. At the runner's ≈ 1.8× the batch-64 step is about
80 min per 10⁵ scenarios: T021 measures it on the runner, and if it is over the hour the plan uses
R5's levers in this order before registration: one downstream row per scenario (the G5 row), then
40 training iterations.

**Measured on the runner** (T021, `bench-gd/t021`, run 41417887072, AMD EPYC 9V74, 4 threads,
batch 64, second epoch of 4,000 scenarios): causal 117.2 s training (29.3 ms per scenario),
time-late 117.0 s (29.3 ms), classification-only 55.6 s (13.9 ms); validation of 1,000 scenarios
≈ 30 s. One epoch of 10⁵ scenarios therefore takes about 49 min for the carried detectors (23 min
for the control), under the hour, so neither lever is used: the plan keeps two downstream rows,
8 knots and K = 50. This runner type is faster than the local machine (the 1.8× of spec 003 was
measured on another CPU family); `cpu_model` is in every job record. All heads were alive after
two short epochs (now head output sd 0.006, pairwise logits 0.14 and 0.04).

**Alternatives**: three scored rows (≈ 23 ms per scenario locally for the solve, likely over
budget on the runner); 4 knots (half the cost; three manoeuvres need six knots).

## R6. Controls

**Decision** (revised during implementation, before registration; measurements on the first 300
σ = 1° scenarios of validation seed 304, per-span detection at a matched 5% held-leg false-alarm
rate):

- **CUSUM** (gated) on the normalised innovations of the per-timestep batch least squares, as
  Annex A §A.2 writes it: ν_k = wrap(z_k − b̂_k|k−1) / σ, where b̂_k|k−1 is the bearing predicted
  at t_k from the estimate at k − 1; S_k = max(0, S_{k−1} + ν_k² − 1 − δ) with δ = 0.5; alarm while
  S_k > h. The single-leg fit is wrong after a scenario's first manoeuvre, so its innovations stay
  biased and S grows on later held legs: h = 72, 10% of spans detected. This is a property of the
  Annex's definition, reported as such; the R6 draft's "reset after 60 s" is dropped (the drift
  ends an episode; episodes less than 60 s apart are merged for every detector when rising edges
  are counted).
- **CUSUM on the frozen EKF's innovations** (reported, not gated): the same recursion on
  ν² / (H P Hᵀ + σ²) from the frozen EKF (Bar-Shalom's χ² detector), which re-converges after a
  manoeuvre. Annex A names the least-squares CUSUM, so this one is a diagnostic.
- **GLR** for a velocity change in the last W = 30 samples (5 min), linearised at the per-timestep
  least-squares estimate θ̂_k: r_i the normalised residuals over the window, one-leg columns
  A_i = (g_i, (t_i − t_k) g_i), change columns J_i(τ) = (t_i − t_τ)⁺ g_i, g_i = ∂b_i/∂(x, y) / σ. The
  window's one-leg fit is projected out (P = I − UUᵀ, U an orthonormal basis of A, modified
  Gram–Schmidt with a 1e-6 rank tolerance), Λ(τ) = (Pr)ᵀPJ(JᵀPJ)⁻¹JᵀPr, the statistic max_τ Λ(τ).
  The R6 draft had no projection, which tests the whole-window fit's error rather than a change in
  the window. Measured: 57% of spans at 5% (W = 60: 29%, so W = 30 stays).
- **IMM mode probability**: the frozen IMM's coordinated-turn probability μ_CT at each row
  (``imm_predict(mu_ct_out=…)``); alarm while μ_CT > h: 44% of spans at 5%.

Each threshold h is tuned on validation (``tma2-controls tune``) so that the control's held-leg
false-alarm fraction on σ = 1° G5 rows is closest to the detector's at its declared operating
point (D1: p_change ≥ 0.5), and frozen (by digest) before the test split. The IMM's mode
probability is also reported at μ_CT > 0.5, its natural threshold, for D3. D-delay and D-miss
compare the detector with the better of CUSUM and GLR, so the weak literal CUSUM does not lower
the bar.

**Rationale**: a literal refit of one and two legs at every candidate τ and every row would take
about 6·10⁷ solves per test split (≈ 33 h); the linearised likelihood ratio is the same test to
first order (Ru, Jilkov, Li and Bashi also linearise), in closed form, and runs in numba in
minutes. This is recorded as the interpretation of Annex A §A.2's "windowed fit of one versus two
legs".

**Alternatives**: a Willsky–Jones mean-shift GLR on the innovations (simpler, but tests a bias in
bearings, not a velocity change); a literal refit at a stride of 6 rows (still about 6 h, and
coarser delays); proposing an Annex amendment to gate the EKF CUSUM (the owner's call: offered in
the write-up, not assumed).

## R7. References re-tuned for manoeuvring data

**Decision**: `tma2-tune` gains a G5 criterion (median range error over all σ = 1° G5 rows, as
gitma's phase-4 research) and is run on validation seed 304 over a grid around P0's phase-4
setting (σ_cv ∈ {0.003, 0.01, 0.03}, σ_ct ∈ {0.01, 0.03, 0.1}, ω ∈ {0.003, 0.01, 0.03},
switch ∈ {0.0003, 0.001, 0.003}, r ∈ {2, 8, 16}; EKF σ_a over 7 values × r over 3), with the rule
from spec 003: a frozen setting on a grid edge must sit on a plateau.

## R8. Metrics

**Decision**: alarms are the rows where `p_change ≥ 0.5` (D1). A manoeuvre is detected at the
first alarm in [start − 1, end + 30 rows] (300 s); delay = (alarm row − (start − 1)) × dt; a span
whose end + 30 rows lies beyond the window and has no alarm is unresolved (reported, not a miss).
Held-leg false alarms: the fraction of held-leg σ = 1° G5 rows with an alarm, and rising edges per
hour of held-leg time. Kind accuracy: `p_kind ≥ 0.5` at the exported knot nearest each detected
span's start. Segmentation F1: exported knots at each scenario's last row against span boundaries,
matched one-to-one within ±60 s. Downstream error: the physics layer with trivial weights fed by
the exported knots and kinds at the G5 rows, against batch least squares, the IMM, the EKF and the
oracle. Calibration: expected calibration error of `p_change` against `now` over all σ = 1° rows
(10 bins) and of `p_kind` at boundary rows.

**Intervals**: scenario-clustered paired bootstraps at 97.5% (D2), 2,000 resamples. D-delay is the
ratio of the detector's median delay to the lower of CUSUM's and GLR's on test, each over the
manoeuvres it detects; D-miss the difference of miss rates against the control with the lower miss
rate; both resample scenarios.

## R9. Seeds and data

**Decision**: validation seed 304 and test seed 305 (100,000 scenarios generated each; the 10%
splits are scored), training stream seed 311; all phase-4 ranges from
`tests/fixtures/gitma/phase4-seed777` (20–60 min windows, 360 rows at 10 s). Seeds 301–303 and 310
are used; 304, 305 and 311 appear in no earlier record.

## R10. Carried rule and variants

**Decision**: two variants are carried (D2): causal and time-late, three seeds each, plus the
classification-only control (one seed). The carried seed of each variant is the one whose
validation D-downstream-all ratio (median range error over all G5 rows ÷ the IMM's) is the median
of three. Gate D passes if either variant passes.

## R11. Gate 1 follow-ups

**Decision**, one line each:

- minimum improvement: an epoch improves only if the validation loss falls by ≥ 1e-3 relative
  (`min_improvement`), which would have stopped Gate 1's seed 2 at epoch 5;
- weights digest: SHA-256 of `best.safetensors` in `CheckpointMeta`, the prediction header and the
  gate manifest; the gate commands refuse a mismatch; `load_model` refuses a missing best file in
  gate use;
- `JobRecord.git_dirty`;
- gate manifests list each amendment of the decision record by path and digest;
- one median convention: reported medians use the same percentile function as the bootstrap's
  point estimate;
- one convergence definition: an estimate is converged when it is finite and plausible (range ≤
  the plausibility limit, speed ≤ the limit) for every estimator, the LM flag of least squares
  reported separately; gross rows by cause in every gate report.

## R12. Export

**Decision**: the detector exports alone (inputs: the 13 channels for one 360-row window; outputs:
`p_change` [B, R], `w_change` and `p_kind` [B, R, R]) through spec 003's export harness and the
three conformance legs; the browser leg times one window and the conformance test fails above one
second. No physics layer is in the detector's graph (the downstream solve is the Gate 1 export's
Loop).
