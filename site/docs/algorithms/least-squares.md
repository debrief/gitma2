---
title: Batch least squares
---

# Batch least-squares bearings-only solver

Source: `src/tma2/references/lsq.py`, `classical.py`. A line-for-line port of gitma's solver
(`packages/classical/src/lsq.ts`, `estimate.ts`); its prediction files equal gitma's on the
committed fixtures (flags identical, converged rows within 10⁻⁴ relative, 10⁻⁷ typical).

## Model and cost

Target state θ = (x₀, y₀, vₓ, v_y) at window start, constant velocity. Predicted bearing at
sample i: h_i(θ) = atan2(x₀ + vₓt_i − p_x(t_i), y₀ + v_y t_i − p_y(t_i)); cost C(θ) = Σ wrap(z_i − h_i)²
over valid bearings. Jacobian rows (dy/ρ², −dx/ρ², t·dy/ρ², −t·dx/ρ²).

## Levenberg–Marquardt

Solve (JᵀJ + λ·diag(JᵀJ)) δ = Jᵀr by 4 × 4 Gaussian elimination with partial pivoting; accept
θ + δ if the cost does not increase (then λ ÷ 10, floored at 10⁻¹²), otherwise λ × 10 and retry
up to 10¹². Converged when an accepted step changes the cost by ≤ 10⁻¹² relative (or the cost is
below 10⁻²⁴), or when no damping reduces it (a stationary point). At most 50 iterations; reaching
it is `converged = false`.

## Start

12 log-spaced ranges 1–40 km along the first valid bearing × 8 courses × 3 speeds (2, 5, 9 m/s);
the lowest-cost grid point seeds LM.

## Modes

- **final**: all bearings, one row at the last sample.
- **per-timestep**: rows from `zig_index + 1`; each row uses bearings up to and including that
  sample, warm-started from the previous row; a fresh grid start is also tried at the first row,
  every 6th row, and whenever the warm solution is missing, non-converged or implausible; the
  better solution (plausible first, then lower cost) is kept.

## Plausibility

A solution with speed above 25 m/s or range above 100 km is reported with `converged = false`,
so it scores as a gross error rather than a silent answer, and the next row restarts from the
grid. This catches the unobservable "range → ∞" valley.

## In gitma2

Batch least squares is a reference (never a result on its own), the trivial-input case of the
[physics layer](physics-layer.md), and the settled-row yardstick of Gate 1 and Gate 2.
