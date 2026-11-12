# Implementation Plan: Time-late TMA, the whole track over a given period (Gate T)

**Branch**: `013-time-late` (developed on `claude/keen-wozniak-77td7j`) |
**Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-time-late/spec.md`.

## Summary

Nothing is trained and no GPU is used. Periods are cut at random from 5-second MAN2
engagements by a transform outside the generator's kernel, so existing data cannot change
(research R1). A time-late solution is a track: the state at every row, read off the physics
layer's own parameters (R3). Three classical systems produce one: C″ run to the period's end,
a full-period re-test of its segmentation (R4), and least squares on the true manoeuvre times,
which is the reference. The frozen C runs unchanged because it is given 10-second normal
points, each the mean of two 5-second bearings (R2); that is also the first test of the
owner's thinning idea, which a separate study takes further (R7). A bound for the state at
every row given the whole period separates determined from undetermined moments (R5). Gate T
(R8) measures the headroom between the best classical system and the reference on fresh seeds.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: NumPy, numba, PyTorch 2.x (physics layer, double); nothing new.

**Storage**: f32pack periods; track NDJSON (one record per period: per-row states, manoeuvre
intervals, determined flags); `errors.npz`; results branches.

**Testing**: `pytest` (existing data byte-identical; a period's rows equal the engagement's
slice; the track at the last row equals the layer's state; the bound at the last row equals the
existing prefix bound; C's digests unchanged; normal points of noise-free bearings on a held
course solve to the truth), `ruff`, `mypy --strict`.

**Target Platform**: CI runners (`timelate/**`); the session for seconds-long steps only.

**Project Type**: research library and CLIs.

**Performance Goals**: the full-period system within 3 times C″'s run time per period; the test
seed scored in one CI run under 6 hours in shards.

**Constraints**: C's code and parameter digests unchanged; no system reads the truth except the
reference (manoeuvre times only); comparisons within one scoring run; one long CI run at a
time; no GPU.

**Scale/Scope**: tuning seed 329 (150 periods), validation 330 (500), test 331 (1,500);
periods of 20 minutes or more cut from 40 to 120 minute engagements at 5 seconds (up to 1,440
rows, 720 normal points).

## Constitution Check

- **I. Types once (LinkML)**: `PeriodCut`, `TrackSolution`, `TrackRow`, `GateTCriteria`,
  `GateTDecision` in `schema/tma.yaml`. Pass.
- **II. Determinism**: the cut draws from its own stream derived from the scenario seed;
  nothing else is random. Pass.
- **III. Physics does the numerics**: every track is the declared piecewise-constant-velocity
  solve read at every row. Pass.
- **IV. Honest measurement**: one leg, the IMM, C″, the reference and the bound on the same
  periods; settings from the tuning seed by rules declared first; three seeds do not apply
  (nothing trained). Pass.
- **V. Fail fast through gates**: Gate T pre-registered (SRD row, owner merges; decision record
  before seeds 330 and 331 exist), soundness on validation, the panel. Pass.
- **VI. Portable artefact**: no model. Not applicable.
- **Classification**: simulated data only; the 5-second interval and the error model are the
  owner's stated assumptions, not a sensor's figures. Pass.

## Project Structure

```
specs/013-time-late/            spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
schema/tma.yaml                 PeriodCut, TrackSolution, TrackRow, GateTCriteria, GateTDecision
configs/timelate/               tl-ranges.json (MAN2 at 5 s), tl-heldout.json, plans, gt-a.json
src/tma2/sim/period.py          cut a period from an engagement; tma2-period
src/tma2/timelate/points.py     normal points: fixed, adaptive by bearing-rate steadiness, dropping
src/tma2/timelate/track.py      state at every row from the layer's parameters
src/tma2/timelate/systems.py    C″ to the end, the full-period re-test, the reference, one leg, IMM
src/tma2/timelate/bound.py      Cramér–Rao bound for the state at every row, whole period
src/tma2/timelate/score.py      whole-track errors, strata, manoeuvre measures, headroom
src/tma2/timelate/gate.py       T-a, T-b
src/tma2/cli/tlsolve.py, tlscore.py     tma2-tlsolve, tma2-tlscore
scripts/research/tl_compress.py the compression study
.github/workflows/timelate.yml  generate → cut → solve (shards) → score
experiments/                    tuning, compression study, decision, validation, test
```

## Phases

1. **Data and the solution format**: 5-second ranges, the period cut, normal points, the track
   read-out, the whole-period bound; tests.
2. **Systems on the tuning seed** (329): C″ to the end, the reference, one leg, IMM; whole-track
   scoring; the first headroom figure and the manoeuvre counts. Stop here if the reference is
   not near its bound on determined rows.
3. **The full-period re-test**: build, choose its settings on the tuning seed by the declared
   rule; how many of C″'s misses it recovers.
4. **The compression study** (R7), on the tuning seed.
5. **Gate T**: SRD row (owner merges), plan, decision record; validation 330; test 331 once;
   panel; write-up; slides post.

## Complexity Tracking

None: no constitution deviation.
