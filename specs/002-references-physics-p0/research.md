# Research: References, Physics Layer and Gate P0

Sources: gitma `d0aec60`: `packages/classical/src/{lsq,estimate,naive,ekf,imm,predictions}.ts`,
`packages/eval/src/{errors,slices,stats,evaluate,bootstrap,gate-g5,csv,prediction-file}.ts`,
schema `tma.yaml`; `docs/research/05-oracle-segmentation.md` and its script. Prediction fixtures
were produced from the local gitma checkout on the spec-001 fixtures (research R6).

## R1 Batch least squares, exactly as gitma

- **Cost and Jacobian.** θ = (x0, y0, vx, vy) at t = 0; residual r = wrap(z − atan2(dx, dy)) with
  `angleDiff` = atan2(sin, cos); Jacobian rows (dy/ρ², −dx/ρ², t·dy/ρ², −t·dx/ρ²).
- **LM.** λ0 = 1e-3, λmax = 1e12; damped system (JᵀJ)ᵢᵢ(1 + λ); 4 × 4 Gaussian elimination with
  partial pivoting (`solve4`, null if a pivot < 1e-300 or non-finite); accept if cost does not
  increase, then λ ← max(λ/10, 1e-12); converged when the accepted step changes cost by
  ≤ 1e-12 relative or cost < 1e-24; "no damping reduces the cost" → converged at a stationary
  point; max 50 iterations → `converged = false`.
- **Grid start.** 12 log-spaced ranges 1–40 km (`1000·40^(i/11)`) along the first valid
  bearing from ownship at that sample × 8 courses × speeds (2, 5, 9); θ back-propagated to t = 0.
- **Per-timestep driver.** Rows from `zig_index + 1`; warm start from the previous solution's θ;
  a fresh grid solve at the first row, every 6th row, and when the warm solution is missing,
  non-converged or implausible; keep the better (plausible first, then lower cost); emit the row
  with `converged = false` if implausible (speed > 25 m/s or range > 100 km); `prev` is null after
  an implausible row. Empty row (all zeros, converged false, iterations 0) when no valid bearings.
- **Rows.** float32 range, course (`f32Angle(bearingOf(vx, vy))`), speed, x, y; `iterations`.

**Decision**: port as numba scalar kernels (`lsq.py`), operation order preserved, including
`solve4`'s elimination order (float results must agree to float32 after up to 50 iterations, so
the arithmetic order matters). The driver is Python over the kernel per row. Conformance is to
gitma's prediction fixtures (R6).

## R2 EKF and IMM, exactly as gitma

- **Common.** Initialisation at `zig_index` from the batch solution on samples [0, i] propagated
  to t_i; P0 = F·(σ²(JᵀJ)⁻¹·p0Scale)·Fᵀ (σ floored at 1e-4 rad); null if no solution, implausible
  or singular. Measurement variance r² = max(σ, 1e-4)²·rScale. Re-initialisation: on an
  implausible state the row is non-converged, the filter is dropped and re-initialisation is tried
  at once and then every 6 samples. The EKF's implausible row still carries the state (`stateRow`,
  converged false); the IMM's implausible row is all zeros.
- **EKF.** CV transition; Q from white-noise acceleration (τ⁴/4, τ³/2, τ²); wrapped innovation;
  Joseph form; `symmetrise` after every covariance product.
- **IMM.** State (x, y, vx, vy, ω), two models (CV with ω carried; CT with `ctMotion` closed
  form and small-angle limits at |ωτ| < 1e-9), Jacobians by **central differences** (step
  1e-4·max(1,|s|) for position/velocity, 1e-7 for ω), process noise with σ_ω²τ on ω; mixing with
  switch probability min(0.5, switchPerS·τ); initial μ (0.9, 0.1) and ω prior 0.05 rad/s; model
  likelihoods `exp(−ν²/2S)/√(2πS)`, fallback to the predicted probabilities when the total is 0 or
  non-finite; combined estimate = mixture mean; NIS recorded.
- **Names.** `ekf-sa<σa>[-p<k>][-r<k>]`, `imm-cv…-ct…-w…-s…[-p…][-r…]`, numbers formatted as
  JavaScript (`String(0.01)` → `0.01`; `js_number` from 001 applies).

**Decision**: port both as numba scalar kernels over per-scenario arrays, mirroring every
numerical choice (finite-difference Jacobian included; an analytic Jacobian would change the
numbers). Validate against gitma's EKF and IMM prediction fixtures, including scenarios where
re-initialisation fires (the phase-4 test split has non-converged rows).

## R3 Evaluation, exactly as gitma

- **Row errors**: non-converged → all +∞ and gross; range_rel = |r̂ − r|/r; course in degrees via
  `angleDiff`; speed in knots; position; gross = !(range_rel ≤ 0.5).
- **Slices**: `overall`, `range_band=` (mean range, km bands 0–2, 2–5, 5–10, 10–20, 20–30, 30+),
  `zig_band=` with the 90°/180°/30° rounding guards, `sigma=<deg>` rounded to 2 dp,
  `dropout_band=`, `manoeuvre=` (`held`, `Nturn[s][+speed]`, or 0.4.0 angle bands).
- **Statistics**: nearest-rank percentiles (rank max(1, ⌈p·n⌉)); NaN sorts as +∞; medians of
  ascending arrays.
- **Metrics record**: per label × point (`final`, `zig+<s>s`) × slice; non-finite values dropped
  from the record; `excluded` counts scenarios without a row at the point; curves per 60 s step.
- **Bootstrap**: gitma's PRNG (`createRng(20261011)`, `uniformInt`), 2,000 resamples, nearest-rank
  quantiles by selection; paired (same draw for both estimators); clustered variants draw
  clusters (scenarios) with replacement; interval `percentile(sorted, tail)`/`(1 − tail)`.
- **Settled rows and G5 rows**: as `gate-g5.ts` (σ = 1° only; rows at zig + 5/10/15/20 min where
  reached; settled = no span covers k and the last ended ≥ 300 s before).

**Decision**: port all of it; the bootstrap reuses `tma2.sim.prng` so intervals equal gitma's on
the same inputs (tested against gitma's `bootstrap.json` fixtures where available, else against a
one-off gitma run recorded as a fixture). Add **efficiency**: for each slice/point, median error
÷ median CRB-derived bound over the same rows (and reported per row for curves), plus the CRB
itself in the record. Schema bump 0.17.0: `MetricsRecord` gains `crb_range_rel_median`,
`crb_course_deg_median`, `crb_speed_kt_median`, `efficiency_range`, `efficiency_course`,
`efficiency_speed` (all optional).

## R4 The Cramér–Rao bound

For the constant-velocity parameterisation θ = (x0, y0, vx, vy) with independent bearing noise
σ, the Fisher information from valid bearings up to row k is I = Σ gᵢgᵢᵀ/σ² with gᵢ the Jacobian
row of R1 evaluated at the **true** trajectory. Bounds on derived quantities at row k by the delta
method: range r(θ) = ‖p(t_k) − o_k‖, course c(θ) = atan2(vx, vy), speed s(θ) = ‖v‖; var(f) ≥
∇fᵀ I⁻¹ ∇f. Reported as standard deviations in the metric units: range relative (σ_r / r),
course in degrees, speed in knots. Before the zig and in degenerate geometry I is singular
(condition number > 1e12): report `singular = true` and no bound. For manoeuvring targets the
bound is computed on the **current leg's** CV model using bearings since the last manoeuvre
ended plus a note that it is a lower bound for an estimator that knows the manoeuvre times (the
oracle's regime); the full-window CV bound is also reported for settled rows. **Decision**: both
variants, with the per-leg one used for efficiency on manoeuvring data and the full-window one on
CV data; documented in the algorithm note.

## R5 The physics layer

**Problem.** Bearings z_i (valid v_i), ownship o_i, times t_i, i ≤ k; segments defined by knots
(timesteps j with changepoint weight c_j); parameters x0, y0 and velocities u_0 … u_S. Position at
t: p(t) = x0 + Σ_s u_s · A_s(t) with A the time spent in segment s up to t (as the oracle script).

**Soft segmentation without control flow.** Rather than a variable number of segments, use one
velocity per **row** with a ridge between consecutive rows whose strength is (1 − c_j)/τ_ridge²:
a weight of 0 pins u_j = u_{j−1} (no knot), a weight of 1 frees it fully (hard knot), and
intermediate values give a soft knot. This makes the parameter count fixed (2 + 2R) and the
Hessian banded; it is the standard fused-ridge formulation and it reduces exactly to the
piecewise model at the extremes. Cost = Σ w_i r_i²/σ² + Σ_j (1 − c_j)/τ² ‖u_j − u_{j−1}‖² +
Σ_j s_j (‖u_j‖ − ‖u_{j−1}‖)²/τ_s², with s_j the speed-continuity weight (active only at knots).

**Solver.** K fixed Gauss-Newton iterations with Levenberg damping: at each iteration form the
banded normal equations (dense 2R+2 ≤ 722 is fine on CPU for batches of 256 with a block
structure; use dense `torch.linalg.solve` with the damping on the diagonal), try the step; accept
it where the cost decreases (`where`), and update λ branchlessly (λ ← λ/10 on accept, ×10 on
reject, clamped to [1e-12, 1e12]). Covariance at the end: σ²·(JᵀJ)⁻¹ on the current row's state
via the delta propagation to (x, y, vx, vy) at t_k. Output: state at t_k, covariance, cost, and a
plausibility flag with gitma's bounds.

**Equality with batch LS (FR-007).** With c_j = 0 everywhere, w_i = 1, the ridge pins all
velocities equal, so the problem is gitma's 4-parameter LS in disguise; with the same grid start
and enough iterations (K = 30) both converge to the same optimum; agreement to float32 (≤ 1 ulp)
is expected except where gitma stopped early (non-converged after 50 iterations, or a stationary
point of the damping loop). The test compares rows where gitma's `converged` is true and the
solution is plausible, and reports the rest.

**Gradients (FR-009).** Autograd through the K unrolled iterations; `torch.linalg.solve` is
differentiable; costs ~K× the forward. Implicit differentiation (solve the final normal equations
once for the backward) is the fallback if memory or time bites; both export the same forward
graph.

**ONNX.** Ops used: matmul, elementwise, atan2 (opset ≥ 17 via `Atan` + quadrant logic or the
`Atan2` contrib? standard ONNX has no `Atan2`: implement `atan2` from `Atan` with `Where` on
signs), `Where`, linear solve: ONNX has no `Solve`; export the solve as an explicit Cholesky-free
method: use `torch.linalg.inv`? also not in ONNX. **Decision**: implement the banded solve as a
fixed-size **block tridiagonal Thomas algorithm** in tensor ops (2 × 2 blocks with explicit
inverses), which is both cheaper and ONNX-exportable; the dense solve stays as a test oracle.

## R6 Prediction fixtures and their digests

`tma-solve --per-timestep`, `tma-track --filter ekf --sigma-a 0.03 --p0-scale 4 --r-scale 8` and
`tma-track --filter imm --sigma-cv 0.01 --sigma-ct 0.03 --sigma-omega 0.01 --switch 0.001
--p0-scale 4 --r-scale 8` were run on the test and validation `.f32pack` of the two seed-777
fixtures at gitma `d0aec60`; the 12 files are committed under `tests/fixtures/gitma/<name>/
predictions/`. Their `dataset_digest` equals the fixture file's SHA-256, which also pins the
binding rule.

## R7 The oracle-ceiling check at P0

Seed 301, `tma2-generate --count 100000` with phase-4 ranges, validation split (10,000
scenarios), `.f32pack` only; frozen IMM and batch LS run with gitma2's ports (minutes with numba;
the IMM is ~1 ms/scenario-row); the physics layer with truth segmentation (knots at span starts
and ends; speed weights 1 across course-only spans in the "speed prior" variant); G5 rows; paired
clustered bootstrap of median range ratio, 97.5%. Pass if the point estimates fall inside the
research note's intervals ([0.486, 0.574] all rows and [0.450, 0.557] settled with the prior;
[0.595, 0.687] and [0.508, 0.628] without). CI runs it on `workflow_dispatch` and on the P0 PR
(about 20–40 min), with the dataset cached by digest.

## R8 ONNX runtimes on CI

Python: `onnxruntime` wheel. Browser: `onnxruntime-web` + Playwright (Chromium is installed via
`npx playwright install chromium`); WASM EP. Java: `actions/setup-java` (Temurin 21) and the
`com.microsoft.onnxruntime:onnxruntime` jar fetched with a tiny Maven `pom.xml`; a 40-line Java
program loads the model and the golden batch (NPY written as raw little-endian floats) and prints
outputs; compared in Python. If the jar cannot be fetched (network policy), the job prints
"Java leg deferred: <reason>" and passes, and the P0 record states it.

## R9 Experiment record and panel

`experiments/<date>-p0/`: `manifest.json` (`ExperimentManifest`: id, created, git commit/dirty,
schema and generator versions, datasets with digests, estimators with settings, command lines;
`node_version` left absent, `python_version` added by schema bump), `metrics.json`/`.csv`,
`verdict.json` (`GateVerdict`, gate `P0`: new `GateId` value), `review.md`. The panel: five
reviewer agents (TMA geometry, estimation/numerics, statistics, reproducibility, red team) run as
subagents with the record and the quickstart, returning verdict and findings; rounds until no
reject and no open blocker/major; `decided_by: "panel round N"`.
