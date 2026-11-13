# Implementation Plan: Time-late, repair and re-registration

**Branch**: `015-time-late-repair` (developed on `claude/keen-wozniak-77td7j`) |
**Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

## Summary

Prior version 3 pairs every factor that has no Gaussian residual with a volume equal to the
reciprocal of its density at the fit (research R1), which repairs the duration's volume and
is tested factor by factor. One function decides whether a found history is the true one,
ignoring manoeuvres the period cuts (R2); the classing, the candidates and the counts use it.
The true-history reference is checked by that function and held to the true times where it
drifts (R3). The refit control falls back to C″'s track when its fit is not one a system
would accept (R4). Spec 014's runner, search and scorer keep working as registered: the
repairs live in new functions and a new runner selected by the plan (R5). The effect of each
repair is measured on the spent seeds (R6), then the study is registered and run again on
seeds 336 and 337 (R7).

## Technical Context

**Language/Version**: Python 3.12. **Dependencies**: NumPy, numba, PyTorch (C″ only); none new.

**Storage**: as spec 014; per-row errors committed this time as float16 where that keeps the
record under 10 MB, otherwise left on the results branch and said so.

**Testing**: `pytest`: density × volume = 1 for each open factor of prior version 3; both
earlier fixtures unchanged; the edge rule on constructed histories; a drifting reference is
caught and held; the refit's fall-back; tables in a record equal the summary. `ruff`, `mypy`.

**Target Platform**: CI (`timelate/**`). **Constraints**: C, C″, Gate T and spec 014
behaviour unchanged; no truth to any system; one long run at a time; no paid compute.

**Scale/Scope**: development on seeds 333 to 335 (spent); validation 336 (150 Annex B, 150
held course); test 337 (400 Annex B, 300 shifted, 400 held course, 100 correlated, 100
outliers, 60 whole).

## Constitution Check

- **I. Types once**: `TimeLateStudyCriteria` reused; shard header gains nothing (the prior
  kinds string names version 3). Schema unchanged unless a field is needed. Pass.
- **II. Determinism**: no new randomness. Pass.
- **III. Physics does the numerics**: unchanged. Pass.
- **IV. Honest measurement**: the same references on the same rows; before-and-after on the
  same periods; every statistic at its registered sensitivities. Pass.
- **V. Fail fast**: registered study with a soundness stop, as spec 014 (its justification
  stands); the panel reviews. Pass with that deviation.
- **VI. Portable artefact**: none. **Classification**: simulated data only. Pass.

## Project Structure

```
specs/015-time-late-repair/      spec, plan, research, tasks, checklists
src/tma2/timelate/prior.py       version 3 (volume = 1 / density for open factors)
src/tma2/timelate/match.py       same_history(): the one rule, edge-aware
src/tma2/timelate/run3.py        runner: search3 family, held reference, refit fall-back
src/tma2/timelate/study3.py      readings with the edge rule, sensitivities, tables
src/tma2/cli/tlsolve.py, tlscore.py   runner "run3"
tests/unit/test_timelate3.py
configs/timelate/tl-d*.json, runs/tl-d-*.json
scripts/research/tl3_tables.py   every record table from summary.json
experiments/                     development, decision, validation, test
```

## Phases

1. Prior version 3 and its tests; `match.same_history` and its tests.
2. `run3` (held reference, fall-back, version 3 searches, spec 014's search beside) and
   `study3`; local smoke on spent data.
3. Development run on seed 335 (spent): before and after, on CI.
4. Register; validation 336; test 337; panel; write-up and slides.

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected because |
| --- | --- | --- |
| A registered study, not a gate | As spec 014: decomposition and a rule's output | A new gate row would change what D5 is called after results exist on it |
