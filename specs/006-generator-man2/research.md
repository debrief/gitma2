# Research: Generator 0.6.0, the MAN2 simulation model

Phase 0 for [plan.md](plan.md). The kernel is `src/tma2/sim/scenario.py`, a line-for-line port of
gitma's `scenario.ts`; every existing PRNG draw must keep its order (AGENTS.md, Gotchas).
Measurements made 4 November 2026 are marked.

## R1. Random streams: where the new draws come from

**Today.** One xoshiro128** stream per scenario, `create_rng(derive_seed(dataset_seed, index))`,
consumed in `draw_scenario` → `plan_manoeuvres` → `plan_target_manoeuvre` →
`plan_target_manoeuvres` → `observe`. The 0.5.0 manoeuvre *count* already uses a stream of its
own, `create_rng(derive_seed(scenario_seed, 1))`, so that count weights do not disturb the main
stream. That is the pattern to copy.

**Decision.**
- **Stream 2** (`derive_seed(scenario_seed, 2)`): the target leg plan (first-leg phase, each
  leg's length, kind, sign, angle, rate, speed change, acceleration), drawn in that order, one
  leg at a time until the window is full.
- **Stream 3** (`derive_seed(scenario_seed, 3)`): the ownship wander kind, its parameters, and
  its per-row innovations.
- The main stream is untouched. With the leg model present the ranges carry no count weights,
  so `draw_manoeuvre_count` is not called and `plan_target_manoeuvres` returns at once, exactly
  as it does today for ranges without weights. Nothing in the 0.5.0 path moves.

**Consequences.**
- A ranges file without the new fields reproduces 0.5.0 byte for byte (spec FR-001), because no
  existing draw is added to or reordered.
- A MAN2 scenario regenerated with wander disabled is byte-identical except for the ownship
  track (spec SC-003): the leg plan and the bearings' noise draws are unchanged.
- Redraws (minimum range, zig past the window end) re-run `draw_scenario` on the main stream as
  today; the leg plan and wander are re-drawn from their streams on each attempt, keyed by the
  attempt number (`derive_seed(scenario_seed, 2 + 2·attempt)`), so a redraw never reuses a plan.

**Alternative rejected.** Drawing the leg plan from the main stream after `observe`: it would be
order-preserving for 0.5.0 but would make a MAN2 scenario's bearings depend on whether wander is
on. Separate streams are cleaner and already the convention.

## R2. The target leg model in the kernel

**Today.** `plan_target_manoeuvres` places a fixed count of changes with slack after the zig;
`target_manoeuvres` simulates them in order, each an arc at constant speed or a constant
acceleration on a straight course, never overlapping, with `MAX_TM = 4`.

**Decision.**
- **Planning** (new `plan_target_legs`, stream 2): `start = −U·L₁` for the first leg (a uniform
  phase so the first change is not aligned to the window or the zig), then repeatedly draw a leg
  length `L ~ N(mean, sd)` clipped at `min`, a kind from the weights, and the change's sign,
  angle and rate (or speed change and acceleration; both for "both"), until the next change
  would start after the window. Each change is appended to `tm` with `TM_START`, and a speed
  change that would leave the speed range is flipped in sign, as today, or dropped if neither
  sign fits. A leg is measured from the end of the previous transition to the start of the next.
- **Simulation.** `target_manoeuvres` is kept for kinds 0 and 1. Kind 2 ("both") integrates the
  arc with a linearly changing speed in 1-second sub-steps inside the span, then continues
  analytically; its span length is the longer of the turn's and the acceleration's. A new kind
  is a new enum value on `ManoeuvreSpan.kind` (schema bump).
- **MAX_TM = 24** (a 120-minute window with the 5-minute floor cannot hold more). `Batch.spans`
  and `Batch.tm` follow the constant; padding beyond `n_spans` stays −1, so 0.5.0 data is
  unaffected. The known-manoeuvres Cramér–Rao bound reads `tm` through `n_tm`, unchanged.

**Measured (R1 of note 09, 4 November):** at 40–120 min windows the current generator runs at
1,500 scenarios/s end to end with f32pack writing (10,000 in 7.4 s); the kernel alone is far
above the 10,000/s target. The leg model adds a few draws per leg and the "both" sub-stepping
touches only transition rows, so throughput is not at risk.

## R3. Ownship zig planning when the target has already turned

**Today.** `plan_manoeuvres` plans the across-LOS zig from `target_at(P, t)`, the target's
*initial* constant-velocity position at the zig time, which is right because 0.5.0 changes start
at least 2 min after the zig.

**Decision.** With the leg model, the target position at the zig row is taken from the
simulated target track (legs are planned before the zig, so it is available). The zig's across-
LOS geometry is then correct whether or not the target has turned. `zig_on_manoeuvre` is set
when the zig row lies inside a target transition span. The 0.5.0 path keeps `target_at`.

**Pipeline-gate consequence (R6 below).** gitma's `beforeManoeuvre` check fits batch least squares
up to the target's first change. On MAN2 the first change can precede the zig, where range is
unobservable, so the check is restated for MAN2 as **"on the zig leg"**: the steady target leg
that contains the ownship zig's end, from its start to its end; batch least squares on that leg
must recover the noise-free truth at its last row. Scenarios whose zig leg ends within 5 min of
the zig are counted and skipped. This is an adaptation of a check to a new data variant, not a
change to a criterion with a result on it; it is stated in the PR for the owner.

## R4. Ownship wander

**Decision.**
- **Helm wander:** a first-order autoregressive course error, `e[i+1] = ρ e[i] + σ √(1−ρ²) g`,
  `ρ = exp(−dt/τ)` (τ = 60 s, dt = 10 s → ρ = 0.846), σ = 1.5°, clipped at ± 4°.
- **Autopilot oscillation:** `A sin(2π t / T + φ)`, A ~ U(1°, 3°), T ~ U(120, 360) s, φ ~ U(0, 2π).
- **Application:** inside each steady ownship leg (before the first turn, between turns, after
  the last), the recorded course is the planned course plus the error, and positions are
  integrated row by row with the trapezoid of the wandered course, starting from the leg's
  entry point. Turns keep the planned arc from the actual entry point. So the recorded track is
  the true track, navigation stays exact, and every row stays within ± 5° of the leg's course
  (the AR(1) clip is 4° and the oscillation's amplitude at most 3°).
- **Drift:** over a 30-minute leg at 5 kt the lateral displacement from wander is about 30 m
  (random walk with correlation time τ), far below the geometry's scale, so the across-LOS zig
  planned from the analytic track stays valid.
- **Selection:** per scenario from `ownship_wander_weights` (none 0.4, wander 0.3,
  oscillation 0.3, both 0.0 by default), stream 3. The kind and drawn parameters go into the
  scenario header.

**Alternative rejected.** Wander as navigation error (recorded ≠ true): out of scope (SRD).

## R5. Window carry-through at 720 rows

**Measured, 4 November:** the physics layer costs 25.7 ms per solve at 720 rows against 20.8 at
360 (batch 64, 4 threads), +24% not 2×: the batched solve is dominated by per-iteration
overhead, not by row count. Memory and file sizes double (train.f32pack 209 MB for 8,000
scenarios at 720 rows).

**Decision.** `rows_for(ranges)` already drives the model export and batches. The two hard-coded
`R_MAX = 360` constants (`cli/p0.py`, `export/onnx_export.py`) become parameters taken from the
experiment's ranges. The conformance export gains a 720-row artefact beside the 360-row one;
both are checked in CI. Training throughput at 720 rows is measured in spec 005's plan when L is
configured; the physics-layer figure above is recorded now.

## R6. Pipeline gate, references and seeds

- **Pipeline gate** on 0.6.0: the existing `tma2-p0` checks (generator conformance for 0.5.0
  ranges and fixtures; references; physics ≡ least squares; noise-free recovery; efficiency;
  throughput; oracle; IMM at scale; export) run on MAN2 data from seed 316 (noise-free) and 314,
  with the "on the zig leg" restatement of R3 and the tracker NIS check as gitma's phase-4 G0.
  The agent panel decides.
- **IMM and EKF re-tune** on seed 314's validation split with spec 004's grids (`tma2-tune`),
  frozen by name in the experiment record. Slower turns favour a smaller coordinated-turn noise;
  the grid already spans it.
- **GLR + confirm re-run:** `scripts/research/leg_spike.py` stats → confirm → report on seed 314
  with the note 08 protocol (tuning on the first 500 σ = 1° scenarios, scoring on the next
  1,000), giving the MAN2 baseline for spec 005's S2 and the re-measured detectability bands.
- **Seeds:** 314 validation (10,000), 315 test (reserved for Gate S), 316 noise-free; 312 and
  313 recorded as unused.

## R7. Describing a ranges file

`tma2-ranges --describe <ranges.json>` prints the effective model: window, leg-length law and
its 5th/50th/95th percentiles, change-kind weights, turn and acceleration rates with the implied
transition durations for the angle and speed-change ranges, wander settings, and which generator
version's semantics the file selects. With `--sample N --seed S` it generates N scenarios and
prints the measured leg-length and transition-duration quantiles, change counts per engagement,
and the wander kinds drawn, which is how spec SC-002 and SC-003 are checked.

## Summary of decisions

| Item | Decision |
| --- | --- |
| New draws | Streams 2 (leg plan) and 3 (wander) per scenario attempt; main stream untouched |
| Leg plan | Legs laid end to end with a uniform first phase; N(mean, sd) clipped at min; kinds by weight |
| "Both" | Arc with linearly changing speed, 1 s sub-steps inside the span; new span kind |
| MAX_TM | 24 |
| Zig planning | From the simulated target position at the zig row when the leg model is on |
| Pipeline-gate check | `beforeManoeuvre` restated as "on the zig leg" for MAN2 (owner informed) |
| Wander | AR(1) course error and sinusoid, integrated into positions, inside steady legs only |
| 720 rows | `R_MAX` constants parameterised; 720-row conformance artefact added |
| References | IMM/EKF re-tuned and frozen; GLR + confirm and detectability re-measured on seed 314 |
