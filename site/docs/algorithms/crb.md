---
title: Cramér–Rao bound and efficiency
---

# Cramér–Rao bound and efficiency

Source: `src/tma2/references/crb.py`; used by `tma2-crb` and `tma2-eval`. Requirements: SRD §5
(efficiency), constitution IV.

## Fisher information

For the constant-velocity parameters θ = (x₀, y₀, vₓ, v_y) anchored at a reference time and
independent Gaussian bearing noise σ, the Fisher information from the valid bearings up to row k,
evaluated on the **true** trajectory, is

I = Σ_i g_i g_iᵀ / σ², g_i = (dy_i/ρ_i², −dx_i/ρ_i², τ_i dy_i/ρ_i², −τ_i dx_i/ρ_i²),

with (dx, dy) the true target offset from ownship, ρ its length and τ_i the time since the
anchor. Any unbiased estimator's covariance is at least I⁻¹.

## Bounds on the reported quantities

By the delta method, var(f(θ)) ≥ ∇fᵀ I⁻¹ ∇f for range r = ‖p(t_k) − o_k‖, course c = atan2(vₓ, v_y)
and speed s = ‖v‖. gitma2 reports the standard deviations in the metric units: relative range
(σ_r / r), course in degrees, speed in knots. Before the zig (one leg) and in degenerate
geometry I is singular (condition number above 10¹²): the bound is undefined and the row is
counted in `crb_singular_rate`, never as 0 or ∞.

## Two anchors

- **Full window**: all bearings up to k, anchored at window start: the right bound when the
  target holds course throughout (Gate 1's data).
- **Per leg** (`--per-leg`): only bearings since the last completed manoeuvre, anchored there:
  the bound for an estimator that knows the manoeuvre times (the oracle's regime) on manoeuvring
  data. During a manoeuvre the leg has no information yet.

## Efficiency

For a slice, `efficiency_<metric>` = median over rows with a regular bound of |e_i| / σ_i,
divided by 0.6745 (the median of a standard normal's absolute value). Each error is normalised
by its own row's bound before the median, so slices that mix σ = 1° and 2° rows, or near and
far rows, are not biased; dividing a median error by a median bound would be (it drifts from
0.67 to below 0.6 as the bounds spread). An unbiased estimator at the bound with Gaussian errors
scores 1; batch least squares scores close to 1 on held-course rows at σ = 1° (P0 checks speed).

Caveats:

- The bound holds for unbiased estimators. Estimators with priors (the physics layer's ridge
  and speed-continuity priors) or with plausibility clipping can legitimately score below 1.
- Range and course bounds come from the delta method, which is poor when the bound is large
  relative to the value (σ_r / r or σ_c large: young legs, weak geometry); read efficiency on
  those slices with care. Course errors wrap at 180°.
- On manoeuvring data the full-window bound assumes a model the target does not follow; use the
  per-leg bound there.

A learned estimator whose efficiency is *flat* across range and bearing-rate
bands while classical's tracks the geometry has hit an approximation floor rather than an
information floor: this is the diagnostic gitma's record lacked (`docs/research/01`).
