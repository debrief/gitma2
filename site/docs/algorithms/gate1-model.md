---
title: Gate 1 model
---

# The Gate 1 model

Sources:

- `src/tma2/models/` (rows, model, loss, train, predict, export);
- the physics layer it drives: [physics layer](physics-layer.md).

Requirements: SRD §4 and §5 (Gate 1), constitution principles III and VI, and spec 003.

The model is a small causal transformer that reads the bearing history and supplies three
inputs that physics cannot know. The [physics layer](physics-layer.md) produces the estimate,
with no knots: Gate 1's data is constant velocity. The last layer of every head starts at zero,
so the untrained model is batch least squares from the classical grid start (tested).

## Inputs and features

One window of R = 240 rows (40 min at 10 s) gives these inputs:

- bearings z, with valid flags v;
- ownship positions (oₓ, o_y) and times t;
- the noise σ;
- the row k whose state is wanted.

Samples after k are ignored.

Each row has seven features. Every scale is fixed: no statistic is taken from the data.

- sin z · v and cos z · v;
- v;
- (oₓ − oₓ,₀) / 10 km and (o_y − o_y,₀) / 10 km;
- t / 1 h;
- σ / 2°.

## Encoder

A linear embedding to width W = 64 is followed by two pre-norm blocks and a final layer norm.
Each block is written out in standard operators, so an independent port can reproduce it. With
h the [R, W] activations, LN the layer norm and 4 heads of size d = 16:

- **Attention.** Q, K, V = LN(h)·W_q, LN(h)·W_k, LN(h)·W_v, then
  h ← h + W_o · concat_heads softmax(QKᵀ/√d + M)·V.
  M is −∞ where key j > query i (causal), and 0 elsewhere.
- **Feed-forward.** h ← h + W₂ · relu(W₁ · LN(h)), with an inner width of 128.

The time-late control (d) uses no causal mask. It masks padded rows as keys instead.

## Heads

Each head is Linear(W, W) → ReLU → Linear(·), and its last layer is zero-initialised.

- **Per-bearing log-weight**, from row i's activation: ℓ_i = 2 tanh(·), so each bearing's
  weight exp(ℓ_i) lies in [e⁻², e²].
- **Initial-state correction**, from row k's activation: (Δ log range, Δ course, Δ log speed),
  applied to the grid start's state at row k.
  - Range from ownship is multiplied by exp(Δ log range).
  - The velocity is rotated clockwise by Δ course and scaled by exp(Δ log speed).
  - The corrected state at k is mapped back to the window-start state θ₀ = (p_k − u t_k, u),
    which starts the solve.
- **Covariance log-scale**, from row k's activation: s = 2 tanh(·). The reported covariance is
  the layer's covariance × e^(2s).

The grid start is gitma's coarse grid along the first valid bearing up to k:

- 12 log-spaced ranges from 1 to 40 km;
- 8 courses;
- speeds of 2, 5 and 9 m/s;
- the candidate with the lowest cost is chosen, the first one on ties.

The exported graph computes it in tensor operations (`grid_start_tensor`). It equals the numba
version to 1e-14.

## Physics

The [physics layer](physics-layer.md) runs with M = 0 knots and the log-weights ℓ, from θ₀, for
K = 100 damped Gauss–Newton iterations in double precision. The output is the state
(x, y, vₓ, v_y) at row k and its covariance σ²(JᵀJ)⁻¹ mapped to row k, plus two flags:

- `cov_ok`: the covariance is valid;
- `plausible`: the solution is plausible.

## Loss

The loss is computed on scored rows whose covariance is valid. The errors of (log range, vₓ,
v_y) at row k are divided by the row's full-window Cramér–Rao standard deviations, computed from
the truth, giving e. The loss is

L = mean(min(‖e‖², 100)) + 1.0 · mean(min(Σ β-NLL, 100)) + 0.1 · mean(min(‖e_init‖², 100))

where:

- β-NLL = stopgrad(v^β) · (½ log v + e²/2v), with β = 0.5;
- v is the calibrated variance ÷ the bound's variance, per component;
- e_init is the same normalised error of the corrected initial state.

The initial-state head gets no gradient through the converged solve (below), so the auxiliary
term trains it.

## Gradient through the solve

**Training.** The forward pass runs the K iterations without a tape to the solution θ*. One
Newton step with the exact Hessian H = JᵀJ + Σ r ∇²r is then taken from θ* (detached), with the
gradient flowing through r and J. This step's derivative with respect to the inputs is the
implicit-function gradient −H⁻¹ ∂(Jᵀr)/∂inputs at the optimum.

- It was checked against finite differences of the converged solution (research R1).
- Where H is not positive definite, the step falls back to Gauss–Newton.
- Inference has no Newton step.

## Training data

Scenarios are generated on the fly from the training seed 310.

- **Noise draws.** Each scenario gets two noise draws. Draw 0 is the generator's own bearings;
  draw 1 is truth + σ·N(0, 1), seeded by (seed, scenario, draw), with the scenario's own dropout
  pattern.
- **Scored rows.** Each scenario contributes three per epoch: the gate rows zig + 5 and
  zig + 10 min, and one random post-zig row.
- **Batches and optimiser.** Batches hold 64 scenarios. Adam is used with a learning rate of
  1e-3 and gradient-norm clipping.
- **Determinism.** Every random choice is a pure function of (seed, epoch, batch). The
  validation loss is the mean normalised squared error on fixed validation rows. Early stopping
  uses patience 4.

## Export

The whole model exports to one ONNX graph:

- **Inputs:** bearing, valid, ox, oy and t of shape [B, 240], sigma [B], and k [B] as int64.
- **Outputs:** state, cov, cov_ok and plausible.

The K iterations are a single ONNX `Loop`: the eager layer calls a TorchScript-scripted
iteration function while tracing. The graph has about 1,500 nodes and loads in under a second.
CI checks the graph against PyTorch in double in three runtimes, to 1e-5 (measured: 1.5e-9 in
Python, 1.5e-9 in Java, 2.4e-9 in the browser).

## Controls (spec 003 FR-017)

- **(a) Direct head.** The same encoder regresses the corrections and three log-variances at row
  k, with no physics layer. It is never carried.
- **(c) Shuffled labels.** Truths are permuted within each batch. It must score at naive level.
- **(d) Time-late.** An unmasked encoder and a solve over the whole window, reporting row k. It
  must score at least as well as the causal model.
