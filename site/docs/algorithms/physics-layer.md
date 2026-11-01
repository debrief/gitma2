---
title: Physics layer
---

# The physics layer

Source: `src/tma2/physics/reference.py` (NumPy, the documentation of record) and
`src/tma2/physics/layer.py` (PyTorch, batched and exportable). Requirements: SRD §4, constitution
principle III, spec 002.

Every gitma2 estimate comes from this layer. It is a piecewise-constant-velocity bearings-only
batch solve whose *inputs* a learned component may supply (when the target manoeuvred, how much
to trust each bearing, where to start) and whose *estimate* is produced by physics.

## Model

For one scenario at row k, with times t_i, ownship o_i, bearings z_i (valid v_i), noise σ, and M
candidate knot rows r_1 … r_M (the M rows with the largest changepoint weight c among rows ≤ k;
inert when c = 0):

- Parameters θ = (p₀, u₀, d₁ … d_M): position at window start, velocity on the first leg, and a
  velocity increment at each knot.
- Position at row i: p_i = p₀ + u₀ t_i + Σ_m c_m d_m (t_i − t(r_m))⁺; velocity at row i:
  u_i = u₀ + Σ_m c_m d_m [t(r_m) ≤ t_i]. With every c_m = 0 this is gitma's constant-velocity
  model θ = (x₀, y₀, vₓ, v_y) exactly.
- Residuals, all σ-normalised:
  - bearings: r_i = √w_i · wrap(z_i − atan2(dx_i, dy_i)) / σ with w_i = v_i exp(ℓ_i) (ℓ the
    per-bearing log-weight);
  - ridge on each increment: √c_m · d_m / τ_r (τ_r = 3 m/s), the prior that a new leg's velocity
    is near the old one;
  - speed continuity at knot m: √(c_m s_m) · (‖u_after,m‖ − ‖u_ref,m‖) / τ_s (τ_s = 1 m/s), where
    u_ref,m is the velocity before knot m with the previous active knot's increment removed in
    proportion to the skip weight k_m. A course change modelled as a start knot and an end knot
    (the chord of the turn) puts s = 1 and k = 1 on the end knot, tying the speed after the
    manoeuvre to the speed before it.
- Solve: K = 100 fixed Gauss-Newton iterations with Levenberg damping (JᵀJ)ᵢᵢ(1 + λ). Each
  iteration may try T damping values λ, 10λ, …, 10^(T−1)λ side by side and take the first that
  does not increase the cost (gitma's inner retry; T = 1 by default); λ ← max(λ_used/10, 10⁻¹²)
  on accept, min(10^T λ, 10¹²) when no trial is accepted (gitma's constants; λ₀ = 10⁻³). P0
  panel round 1 measured the settings on every fixture row against the solver from the same
  start: 40 × 1 stopped short on 159 rows, 40 × 4 on 8, 100 × 1 and 60 × 2 on none, and 100 × 1
  was the fastest. The linear system is Jacobi-scaled and
  solved by Gauss-Jordan elimination without pivoting (static operations only). Start: the
  classical grid start for (p₀, u₀), increments zero.
- Output: state (p_k, u_k), covariance G (JᵀJ)⁻¹ Gᵀ with G = ∂(p_k, u_k)/∂θ (residuals are
  σ-normalised, so this is in m² and m²/s²), the final cost, and gitma's plausibility flag
  (speed ≤ 25 m/s, range ≤ 100 km).

## Properties (tested)

- **Trivial inputs reproduce batch least squares.** With c ≡ 0, uniform weights and the grid
  start, on every scored row of the fixtures the plausibility flags agree with the ported solver
  from the same start, and the layer's cost never exceeds the solver's by more than 10⁻⁹
  relative. Where the costs agree the states agree to 3.3 × 10⁻⁴ standard deviations; in relative
  terms to about 10⁻⁵ where a quantity is determined, while on a row whose speed is undetermined
  (sd several times the speed) the solver's own stopping point is 1.3 × 10⁻⁴ from the optimum the
  layer reaches (P0 run r2). Where the solver stops without converging, the layer's flag and cost
  are reported.
- **Oracle ceiling.** With knots at the true manoeuvre starts and ends it reproduces the ratios
  of `docs/research/05` against the frozen IMM. It is a reference, not a strict ceiling: the
  chord of a long turn misfits the in-turn bearings, and the masked-turn diagnostic (in-turn
  bearings at zero weight) is better (P0 panel round 1).
- **Differentiable** in the selected knots' changepoint and speed weights, the bearing
  log-weights and the initial state (central differences agree with autograd). A candidate that
  TopK does not select has zero gradient, as in any sparse selection, and a saturated weight (0 or
  1) has none either, so knot placement needs its own supervised loss. Every gradient is finite:
  square roots of masked zeros are taken branch-safe (an earlier version gave NaN on invalid and
  beyond-k rows, which poisoned a whole model's gradients; P0 panel round 1). With 40 or more
  iterations the unrolled gradient equals the implicit one at the optimum.
- **Exact under masking**: rows beyond k and invalid rows contribute nothing; batched and single
  results agree to the last bits that BLAS reduction order allows (≈10⁻⁷ relative after 40
  damped iterations).
- **Exportable** (the conformance export unrolls 8 iterations; the production 100 need an ONNX
  `Loop`, spec 003): the graph holds only standard operators (TopK, Gather, Where, MatMul,
  elementwise maths, Atan on a float32 seed refined by Newton steps in double); the Python,
  browser (WASM) and Java runtimes agree with PyTorch to 10⁻⁵ in double on the golden batch.

## Why not a full per-row velocity model

A velocity per row with a fused ridge would be the most general segmentation, but every bearing
depends on all earlier velocities, so the normal matrix is dense in 2R + 2 ≈ 720 unknowns: too
slow on CPU for training and for the 10⁵-scenario oracle check. M candidate knots (M = 8 covers
every manoeuvre plan the generator draws, with two knots per turn) keep the solve at 4 + 2M = 20
unknowns and the selection a standard TopK operator.
