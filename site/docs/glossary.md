---
title: Glossary
---

# Glossary

TMA and ML terms as used in gitma2. Terms carried from gitma keep gitma's meaning.
- **Autopilot oscillation** — generator 0.6.0's second kind of ownship wander: a sinusoid of
  1–3° amplitude and 2–6 min period on the course of every steady ownship leg.
- **Batch least squares** — the classical reference: a Levenberg–Marquardt fit of a
  constant-velocity target to all bearings so far, from a coarse range–course–speed grid.
- **Bearing** — true direction from ownship to the target, clockwise from north, radians
  internally.
- **Changepoint weight** — the physics layer's input c ∈ [0, 1] per row: how free the target's
  velocity is to change there. The M largest become candidate knots; 0 everywhere is one leg.
- **Control (model)** — a variant trained only to test the pipeline, never carried: direct regression head, shuffled labels (must score no better than the design without learning: naive for a regressor, batch least squares for a physics-layer model), time-late (must score at least as well as the causal model).
- **Cramér–Rao bound (CRB)** — the lowest variance any unbiased estimator can reach given the
  bearings' Fisher information; batch least squares sits at it on a straight leg. Three models:
  full window, known manoeuvres, per leg (see [CRB](algorithms/crb.md)).
- **CUSUM** — cumulative-sum change detector: S(k) = max(0, S(k − 1) + ν(k)² − 1 − δ) on normalised innovations, an alarm while S exceeds a tuned threshold; a Gate D control (see [detector](algorithms/detector.md)).
- **Efficiency** — the median over a slice's rows of error ÷ that row's CRB, divided by 0.6745,
  so an unbiased estimator at the bound scores 1; a flat efficiency across geometry slices is the
  signature of an approximation floor.
- **Fisher information** — the curvature of the bearings' log-likelihood in the target state; its
  inverse is the Cramér–Rao bound. See [CRB](algorithms/crb.md).
- **G5 rows** — σ = 1° scenarios scored at zig + 5, 10, 15 and 20 min where the window reaches
  them (gitma Annex C); one scenario contributes several rows, so bootstraps resample scenarios.
- **Gate** — a pre-registered go/no-go check (P0, Gate 1, Gate D, Gate 2), judged by the agent
  review panel on a fresh test seed.
- **Gate D** — the steady-leg detector's gate (SRD Annex A §A.5): detection delay and misses against CUSUM and GLR at matched false-alarm rates, held-leg false alarms, and the physics layer's error fed by the detector's knots against the IMM and batch least squares.
- **Generator version** — the algorithm that turns (seed, index, ranges) into a scenario;
  gitma2 implements gitma's 0.5.0 and reproduces its files byte for byte. Generator 0.6.0 adds the
  MAN2 model behind new ranges fields, so 0.5.0 ranges still give 0.5.0's bytes.
- **GLR** — generalised likelihood ratio test for a velocity change inside a sliding window, the window's one-leg fit projected out; a Gate D control.
- **Grid start** — gitma's coarse initialisation for batch least squares: the lowest-cost candidate of 12 ranges × 8 courses × 3 speeds along the first valid bearing; the Gate 1 model corrects it before the solve.
- **Helm wander** — generator 0.6.0's first kind of ownship wander: a first-order
  autoregressive course error (σ 1.5°, τ 60 s) clipped at ± 4°, on steady ownship rows only.
- **Held leg** — rows where the target's constant-velocity model holds: before any manoeuvre, or
  more than five minutes after the last one ended.
- **Held-out split** — scenarios drawn from parameter ranges outside training (longer initial
  ranges), to measure extrapolation.
- **IMM** — interacting multiple-model tracker (constant velocity plus coordinated turn), tuned
  on validation and frozen; the reference for manoeuvring targets.
- **Implicit gradient** — the derivative of a converged solve's solution with respect to its inputs, from the optimality condition instead of unrolling the iterations; the Gate 1 model takes one exact-Hessian Newton step from the detached optimum to get it ([Gate 1 model](algorithms/gate1-model.md)).
- **Instantaneous / time-late** — the causal estimate at each timestep, using bearings up to now,
  versus the estimate using the whole window.
- **MAN2** — the problem generator 0.6.0 simulates (SRD Annex B): target legs of N(25, 9.1) min
  with a 5-min floor (5% at or under 10 min), ended by a course (80%), speed (10%) or combined
  (10%) change of about a minute or more, in 40–120 min windows (up to 720 rows), with ownship
  helm wander or autopilot oscillation.
- **Manoeuvre span** — the sample interval of one target course or speed change, from the first
  sample after it starts to the first sample after it ends.
- **Oracle ceiling** — the physics layer fed with the true manoeuvre times and kinds (knots at
  each manoeuvre's start and end, the chord of a turn, ridge τ_r = 3 m/s): the reference for any
  "segment, then solve" design. It is not a strict upper bound: on noise-free data most of its
  error after a turn is the chord approximation; with noise, giving the in-turn bearings zero
  weight does not help, and at σ = 1° it is 1.2–1.3 × the known-manoeuvres Cramér–Rao bound, the
  information limit.
- **Ownship** — the observing platform, whose track is known exactly.
- **Physics layer** — see [the algorithm note](algorithms/physics-layer.md); the declared, differentiable piecewise-constant-velocity batch solve that
  produces every gitma2 estimate; with trivial inputs it equals batch least squares.
- **Ridge prior** — the physics layer's prior that a new leg's velocity stays near the old one
  (√c · Δv / 3 m/s per knot), which keeps a leg a few samples old finite.
- **Scenario** — one ownship-versus-target run: metadata, two truth tracks and a bearing series.
- **Seed** — a 64-bit integer that determines a dataset; per-scenario seeds derive from it, so the
  same seed gives the same scenario in gitma and gitma2.
- **Settled row** — a scored row on a held leg (gitma Annex C §C.5's definition).
- **Speed-continuity prior** — the physics layer's prior that speed carries through a course
  change (‖v_after‖ − ‖v_before‖)/1 m/s, skipping the chord leg inside the turn.
- **Steady-leg detector** — the first learned component (SRD Annex A): per-timestep manoeuvre
  probability, changepoint weights and manoeuvre kind, feeding the physics layer.
- **Transition** — the interval of a target change between two steady legs, from its first
  changed row to the row where the new course and speed hold (a manoeuvre span).
- **Zig** — ownship's deliberate course change that makes range observable; gate times count
  from the first sample after the first turn completes.
- **Zig leg** — the steady target leg that contains the ownship zig. On MAN2 data the target can
  change before the zig, so the noise-free and efficiency checks fit this leg alone (spec 006
  research R3, the restatement of gitma's "before the manoeuvre").
