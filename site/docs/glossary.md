---
title: Glossary
---

# Glossary

TMA and ML terms as used in gitma2. Terms carried from gitma keep gitma's meaning.

- **Batch least squares** — the classical reference: a Levenberg–Marquardt fit of a
  constant-velocity target to all bearings so far, from a coarse range–course–speed grid.
- **Bearing** — true direction from ownship to the target, clockwise from north, radians
  internally.
- **Cramér–Rao bound (CRB)** — the lowest variance any unbiased estimator can reach given the
  bearings' Fisher information; batch least squares sits at it on a straight leg.
- **Efficiency** — an estimator's error relative to the CRB for the same scenario and time; a
  flat efficiency across geometry slices is the signature of an approximation floor.
- **Gate** — a pre-registered go/no-go check (P0, Gate 1, Gate D, Gate 2), judged by the agent
  review panel on a fresh test seed.
- **Generator version** — the algorithm that turns (seed, index, ranges) into a scenario;
  gitma2 implements gitma's 0.5.0 and reproduces its files byte for byte.
- **Held leg** — rows where the target's constant-velocity model holds: before any manoeuvre, or
  more than five minutes after the last one ended.
- **Held-out split** — scenarios drawn from parameter ranges outside training (longer initial
  ranges), to measure extrapolation.
- **IMM** — interacting multiple-model tracker (constant velocity plus coordinated turn), tuned
  on validation and frozen; the reference for manoeuvring targets.
- **Instantaneous / time-late** — the causal estimate at each timestep, using bearings up to now,
  versus the estimate using the whole window.
- **Manoeuvre span** — the sample interval of one target course or speed change, from the first
  sample after it starts to the first sample after it ends.
- **Oracle ceiling** — the physics layer fed with the true manoeuvre times and kinds; an upper
  bound for any "segment, then solve" design.
- **Ownship** — the observing platform, whose track is known exactly.
- **Physics layer** — the declared, differentiable piecewise-constant-velocity batch solve that
  produces every gitma2 estimate; with trivial inputs it equals batch least squares.
- **Scenario** — one ownship-versus-target run: metadata, two truth tracks and a bearing series.
- **Seed** — a 64-bit integer that determines a dataset; per-scenario seeds derive from it, so the
  same seed gives the same scenario in gitma and gitma2.
- **Settled row** — a scored row on a held leg (gitma Annex C §C.5's definition).
- **Steady-leg detector** — the first learned component (SRD Annex A): per-timestep manoeuvre
  probability, changepoint weights and manoeuvre kind, feeding the physics layer.
- **Zig** — ownship's deliberate course change that makes range observable; gate times count
  from the first sample after the first turn completes.
