---
title: EKF and IMM
---

# Tracking filters: EKF and IMM

Source: `src/tma2/references/ekf.py`, `imm.py`. Line-for-line ports of gitma's trackers
(`packages/classical/src/ekf.ts`, `imm.ts`), including the finite-difference Jacobians, so that
the frozen phase-4 reference `imm-cv0.01-ct0.03-w0.01-s0.001-p4-r8` gives the same rows in both
repositories (checked on the committed fixtures).

## Common ground

- **Start where classical does**: initialised at `zig_index` from the batch least-squares
  solution on the samples so far, with covariance σ²(JᵀJ)⁻¹ (× `p0_scale`) propagated to that
  time.
- **Run causally**: one update per bearing; one row per sample from `zig_index + 1`, the same
  rows as the classical per-timestep mode.
- **Wrapped innovation** and Joseph-form covariance update; measurement variance = the scenario's
  σ² (floored at 10⁻⁴ rad) × `r_scale`.
- **Divergence**: a state outside the plausibility bounds is reported non-converged and the
  filter re-initialises from the batch solution, at once and then every 6 samples until it
  succeeds.

## EKF (constant velocity)

State (x, y, vₓ, v_y); white-noise-acceleration process noise σ_a: Q = σ_a² [τ⁴/4, τ³/2; τ³/2, τ²] per
axis. Implausible rows keep the state in the row (gitma's choice) but are flagged.

## IMM (constant velocity + coordinated turn)

State (x, y, vₓ, v_y, ω). Two EKFs: CV (ω carried, unused; σ_cv) and CT (closed-form
coordinated-turn motion with small-angle limits; σ_ct and a turn-rate random walk σ_ω). Standard
Blom–Bar-Shalom cycle: mix with switch probability min(0.5, s·τ), predict (Jacobians by central
differences: 10⁻⁴·max(1, |x|) for position and velocity, 10⁻⁷ for ω), update both models,
likelihoods exp(−ν²/2S)/√(2πS) (falling back to the predicted probabilities if their sum is 0 or
non-finite), combine as the mixture mean. Initial μ = (0.9, 0.1), ω prior sd 0.05 rad/s. The
normalised innovation squared (NIS) is recorded for consistency checks.

## In gitma2

The IMM, re-tuned on gitma2's validation split with declared grids before any training, is the
reference for manoeuvring targets at Gate 2 and in the steady-leg detector's downstream checks
(Annex A). The EKF is reported beside it.
