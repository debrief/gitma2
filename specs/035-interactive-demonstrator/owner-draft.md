# gitma2 Spec 005 — Interactive TMA Demonstrator

Nov 21, 2026 · Draft from owner interview

## Summary

A browser page on the gitma2 Docusaurus site where stakeholders drag a blue (ownship) and red (target) track, add steady turns, narrow the analysis window, and see a time-late TMA solution recomputed with a full performance dashboard.

Purpose: give non-specialists a feel for solver performance — where it is good, where geometry or target manoeuvres break it — without reading gate reports.

Status: draft for owner review. Depends on a browser-runnable solver (see Open decisions).

## Decisions from interview

| # | Topic | Decision |
| --- | --- | --- |
| 1 | Solvers | Pluggable; user picks from a dropdown |
| 2 | Bearings | Truth + Gaussian noise; σ slider and Reseed button |
| 3 | Turns | Waypoints joined by steady-rate arcs; rate (°/s) editable per waypoint |
| 4 | Kinematics | Per-leg drag handle sets course **and** speed |
| 5 | Feedback | Full dashboard |
| 6 | Recompute | On drag release (not continuous) |
| 7 | Hosting | React component on the Docusaurus site, reusing repo types and solvers |
| 8 | Ownship | Fully free, including unobservable (no-zig) geometry, which the demo flags |
| 9 | Scenarios | Presets, URL sharing, LinkML-typed JSON import/export |
| 10 | Handle | Rotating a leg rotates/moves all downstream waypoints with it |
| 11 | Time | Time-late only. Range slider starts at full period; analyst drags ends in to solve over a sub-window |
| 12 | Frame | Flat X/Y in nautical miles, pan and zoom |

## Scope

**In scope:** one ownship, one target; constant-speed legs joined by constant-rate turns; Gaussian bearing noise with known σ; batch (time-late) solutions over a user-chosen window.

**Out of scope:** real data; multiple contacts; real-time / causal TMA; Monte Carlo clouds (possible later); speed changes within a leg; lat/long charts.

## Functional requirements

**Track editing**

- **FR-001** Each vessel is a start point plus an ordered list of legs (course, speed, duration). Waypoints sit at leg joins.
- **FR-002** Drag a waypoint to move it; adjacent legs' course, speed and duration are recomputed. Downstream waypoints stay put.
- **FR-003** Each leg has a velocity handle at its midpoint. Dragging changes course and speed; all downstream waypoints translate/rotate rigidly with it (decision 10). Show the speed (kt) and course (°) while dragging.
- **FR-004** Click a leg to insert a waypoint; delete via context action or key.
- **FR-005** Each waypoint carries a turn rate (default 1°/s, range proposed 0.25–3°/s). The join is drawn as an arc of radius v/ω. If the arc does not fit the adjoining legs, clamp and mark the waypoint amber.
- **FR-006** Ownship editing is unconstrained (decision 8). No minimum zig is enforced.
- **FR-007** Undo/redo for all edits.

**Bearing generation**

- **FR-010** Bearings sampled at a fixed interval (default 10 s, editable) over the whole scenario from the truth tracks, including during turns.
- **FR-011** Noise: zero-mean Gaussian, σ slider (proposed 0–5°, default 1°). Seeded PRNG; Reseed draws a new seed. Same seed + scenario ⇒ identical bearings.

**Window and solve**

- **FR-020** A range slider under the plot spans the scenario period; both ends draggable. Initial state: full period.
- **FR-021** Only bearings inside the window go to the solver. Bearings outside are shown greyed.
- **FR-022** Recompute fires on release of any drag (track, handle, slider, σ) and on Reseed or solver change.
- **FR-023** Solvers run in a Web Worker so the UI never blocks; a stale result is discarded if a newer request was issued.
- **FR-024** Solver plug-in contract: `solve(problem: TmaProblem): TmaSolution`, both types generated from LinkML. A solver declares name, version, model assumptions (e.g. "single constant-velocity leg") and whether it accepts gap knots.
- **FR-025** Initial solver set: batch least squares (single CV leg). Later: Spec 004 D2-segmented LS, learned models via ONNX Runtime Web.

**Dashboard (decision 5)**

- **FR-030** Plot: truth tracks, bearing lines (thinned), estimated red track over the window with its position at window end; optional 1σ/2σ ellipse from the solution covariance.
- **FR-031** Error panel at the reference time (window end): range, bearing, course, speed errors; also as % of range.
- **FR-032** Error-vs-time chart: position error of the estimated track against truth across the window.
- **FR-033** Bearing plot: measured bearings and the solution's predicted bearings against time; residuals below, scaled by σ.
- **FR-034** Solver status: converged / failed, iterations, runtime (ms), normalised RMS residual (≈1 is a consistent fit).
- **FR-035** Observability indicator: condition number of the solution's information matrix (or CRB on range), green/amber/red. Shown, never blocking (decision 8).
- **FR-036** Model-mismatch flag: if truth contains a target turn inside the window and the chosen solver assumes a single leg, say so beside the error panel.

**Scenarios**

- **FR-040** LinkML `DemoScenario` type: both vessels' legs and turn rates, σ, sample interval, seed, window, selected solver.
- **FR-041** Presets (proposed): good-geometry ownship zig; no ownship zig (unobservable); target turn mid-window; near-endfire geometry; short window after zig.
- **FR-042** Current scenario encoded in the URL fragment (compressed JSON); opening the URL restores it exactly.
- **FR-043** JSON import/export, validated against the LinkML schema; invalid files rejected with the validation message.

## Non-functional

- **NFR-1** Batch LS solve ≤ 200 ms at 360 bearings on a mid-range laptop.
- **NFR-2** Deterministic: same URL ⇒ same bearings, same solution.
- **NFR-3** Static only — runs from gh-pages, no backend, works offline once loaded.
- **NFR-4** Usable at 1366×768; keyboard access for slider ends and waypoint deletion.
- **NFR-5** All presets and defaults unclassified and generic (public repo).

## Acceptance criteria

1. Every preset loads, solves, and shows all dashboard panels.
2. Zero-noise good-geometry preset: LS errors below a set tolerance (proposed range error < 0.1%).
3. No-zig preset: observability indicator red; solution still displayed.
4. Target-turn preset: model-mismatch flag shown; narrowing the window to one target leg clears it and reduces error.
5. URL and JSON round-trips reproduce identical solutions.
6. Docusaurus build and PR preview (/pr/N/) work.

## Critical analysis and risks

- **Solver availability in the browser is the main risk.** Spec 004 exports networks to ONNX, implying the physics layer and learned models may not be in TS. The demo needs either a TS physics layer or ONNX Runtime Web plus a TS LS. A second implementation of LS risks drift from the reference — mitigate with shared golden test vectors.
- **Single-noise-draw misreading.** One realisation can look much better or worse than typical. Reseed helps but relies on users pressing it; consider showing the CRB alongside the actual error so luck is visible.
- **Decision 10 is powerful but surprising.** Rotating one leg swings the whole downstream track, possibly off-screen. Waypoint drag (FR-002) is the local alternative; both need clear affordances or users will fight the tool.
- **Free ownship invites garbage solutions.** That is a valid teaching point, but a stakeholder may screenshot a wild failure out of context. The observability indicator and residual panel must be prominent.
- **On-release recompute loses some "feel".** Users won't see the solution respond during a drag. Acceptable for LS speed; revisit if stakeholders ask, since a worker-based throttle (FR-023) makes continuous mode a small change.
- **Model mismatch is the interesting case.** A single-leg LS over a window containing a target turn is biased by design; the demo should make this the headline lesson, and it is where a Spec 004 segmented solver earns its place in the dropdown.

## Open owner decisions

- [ ] How solvers reach the browser: TS port, ONNX Runtime Web, or both.
- [ ] Reference time for errors: window end (proposed) or user-selectable.
- [ ] Default σ, sample interval and turn-rate range.
- [ ] Which learned models are exposed to stakeholders, and only after passing which gate.
- [ ] Whether covariance ellipses are shown by default (risk of over-trust).
