# Research: Gate 1, a learned model on constant-velocity data

Measurements were taken in this container (4 shared cores, Intel Xeon 2.1 GHz), PyTorch 2.15 CPU,
double precision, batches of 256 rows from the iteration-4 (CV) fixtures, 240-row windows.

## R1. Backward pass: implicit differentiation at the solution

**Decision**: the physics layer gains an `implicit` mode. It runs its K iterations without a
gradient tape, then takes one Newton step from the detached solution θ* with the true Hessian of
the cost held constant: θ = θ* − H⁻¹ Jᵀr, H = JᵀJ + Σ rᵢ∇²rᵢ (the curvature term from autograd
over the layer's own analytic Jacobian, P backward passes). The step is ~0 at the optimum, so the
value is unchanged (measured 3.9e-6 m on positions), and its derivative with respect to every
learned input is the exact implicit-function gradient −H⁻¹ ∂(Jᵀr)/∂w. Where H is not positive
definite on a row (a saddle or flat direction) that row uses the Gauss–Newton Hessian.

**Rationale**: unrolled backward costs 0.16 s and 72 MB per row (P0). A first version used the
Gauss–Newton Hessian JᵀJ only: on six fixture rows its gradient was up to 25% off the exact
implicit gradient (e.g. 0.144 against 0.190), because the bearing residuals' curvature matters on
flat rows. With the true Hessian the implicit gradient equals the exact one (0.19045, −0.010536,
3.0424e-4, −1.0085e-3), which in turn matches central differences of the converged solve at a step
of 1e-3 (0.19047, −0.010536, 3.0424e-4, −1.0082e-3); differences at 1e-5 are noise from the
solver's stopping rule. Test: implicit gradient against central differences at 1e-3 on fixture
rows, 1e-3 relative where the row is determined.

**Consequence**: the initial state receives no gradient (the solution does not depend on where
the solve starts, within a basin). Its head is trained by an auxiliary loss (R3).

**Alternatives**: unrolled backward (cost); truncated backward through the last few iterations
(biased, still costly); Gauss–Newton implicit step (cheap but 25% off on flat rows).

## R2. Export: the iteration as an ONNX Loop

**Decision**: export the iteration as a TorchScript-scripted function called from the traced
model. The TorchScript exporter turns the scripted `for` loop into one ONNX `Loop` node. The
iteration body is refactored into a function of tensors only (no dataclasses, no Python control
flow on values), shared by the layer's forward pass so the eager and exported paths are the same
code.

**Rationale**: P0 found that unrolling 100 iterations gives a 45 MB graph that onnxruntime could not
load in 12 minutes. A prototype (a damped Gauss–Newton fit, 100 iterations) exported as one Loop
node and ran in onnxruntime Python (max difference 0.0 from PyTorch) and onnxruntime-web in
Node (the same values in double). Java's onnxruntime uses the same CPU kernels.

**Alternatives**: unrolled export at the production count (infeasible); export only the
iteration body and loop in host code (not one graph, against constitution VI); `torch.export`
with a while-loop operator (less mature for ONNX in 2.15).

## R3. The model

**Decision**:

- Features per timestep: sin and cos of the bearing (0 where invalid), the valid flag, ownship
  position relative to its start ÷ 10 km, time ÷ 1 h, σ ÷ 2°. Fixed scales, no statistics from
  data (constitution IV).
- Encoder: linear embedding to width 64, two pre-norm transformer layers (4 heads, feed-forward
  128, no dropout), causal mask; the time-late control uses no mask. The PyTorch fast path is
  disabled so the graph uses standard operators.
- Heads: per-bearing log-weight ℓᵢ = 2 tanh(·) from token i (shared by every row ≥ i); at the
  scored row k, an initial-state correction (Δ log range, Δ course, Δ log speed) applied to the
  classical grid start's state at k, and a covariance log-scale 2 tanh(·). The last linear layer of
  every head starts at zero, so the untrained model is exactly batch least squares (FR-009).
- Physics layer: no knots, K = 100, implicit mode in training; double precision throughout.
- Loss on each scored row: squared errors of log range, vx and vy, each divided by its
  Cramér–Rao standard deviation (full window, computed from the truth); β-NLL (β = 0.5) of the
  same errors under the calibrated covariance; an auxiliary term on the initial state's errors,
  also CRB-normalised, weight 0.1. Per-row loss capped at 100 so gross errors do not dominate.
- Control (a): the same encoder and features with a direct head (log range, course, speed at k)
  and the same loss.

**Rationale**: the per-token weight is causal and costs one encoder pass per scenario for all
its rows. A correction to the grid start keeps the least-squares guarantee at initialisation and
lets the model learn to move the start into the right basin, which is where batch least squares
loses (its gross errors).

## R4. Throughput

**Decision**: about four scored rows per scenario per epoch, two noise draws per truth, batches of
64 scenarios, four threads.

**Measurements** (per row, batch of 256):

| Physics layer | Forward | Backward |
| --- | --- | --- |
| 8 knots, unrolled tape | 67 ms | (P0: 0.16 s) |
| 8 knots, implicit | 10.7 ms | 0.22 ms |
| 0 knots, implicit | 4.0 ms | 0.03 ms |
| 0 knots, no grad, K = 100 | 5.5 ms | – |

With zero knots (identical results to eight inert knots: state and covariance differences 0.0)
and the implicit step, four rows per scenario cost about 16 ms, so 10⁵ scenarios take about
1,600 s of solving. The encoder and the data pipeline are measured in the first task and the
budget re-checked before the decision record.

## R5. Data on the fly and re-noising

**Decision**: training scenarios come from `generate_batch` (≈ 20k scenarios/s) on the training
seed stream (seed 310, indices 0 … 10⁵·epochs). Extra noise draws re-draw each valid bearing as
truth + σ·N(0, 1) from `numpy.random.default_rng([seed, index, draw])`, wrapped and
float32-rounded; draw 0 is the generator's own bearings. The grid start and the Cramér–Rao bound
are computed per scored row on the fly (the bound for all rows of a scenario from one cumulative
sum of per-bearing information).

## R6. Re-tuned EKF and IMM

**Decision**: tune on the CV validation split (seed 302) before training, as gitma's phase-4
research did, and freeze: IMM over σ_cv ∈ {0.003, 0.01, 0.03}, σ_ct ∈ {0.01, 0.03, 0.1},
ω ∈ {0.001, 0.01}, switch ∈ {0.001, 0.01}, p0 scale ∈ {4}, r scale ∈ {1, 2, 8}; EKF over
σ_a ∈ {0.001, 0.003, 0.01, 0.03, 0.1}, p0 scale ∈ {4}, r scale ∈ {1, 2, 8}. Criterion: median range
error at zig + 5 min on σ = 1° validation rows; ties to the smaller grid index. `tma2-tune` writes
the grid's table and the frozen choice.

## R7. Training on GitHub Actions

**Decision**: gitma's train workflow, ported. Pushing `train/<id>` runs every model of the plan in
`configs/` in a matrix, each in up to three chained jobs of at most 345 minutes. A job resumes from
the checkpoint branch `checkpoints/<plan>/<model>` (weights, optimiser and RNG state, epoch, best
validation loss), checkpoints after every epoch, and records its duration and CPU model. When all
models are complete an evaluation job predicts on validation and pushes `results/<plan>-<run>`.
Nothing merges automatically.

## R8. Carried weights and Gate 1 rows

**Decision**: the carried model is the training seed whose validation median range error at
zig + 5 min (σ = 1°) is the median of the three: not the best, so the choice is not a selection on
noise. Gate rows: σ = 1° test scenarios at zig + 5 min for range and course and zig + 10 min for
speed; settled slices for efficiency are the same rows (CV has no manoeuvres, so every post-zig
row is on a held leg). Ratios are model ÷ batch least squares medians with a scenario-clustered
paired bootstrap at 95%, 2,000 resamples, gitma's seed; gross-error rates compared as a clustered
difference.
