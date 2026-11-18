# Implementation Plan: carrying state across gaps, against joining through them

**Spec**: `specs/026-carry-across-gaps/spec.md` · **Date**: 2026-11-18 · CPU only; nothing trained.

## Summary

Spec 025's runner (`run8`, unchanged) and, per engagement, the carry: each period in order
solved by a copy of `ctl`'s search whose start from nothing is replaced by the previous
period's declared state at its last row, run forward at constant velocity through the gap.
Compared with the joint solve and with `ctl` alone over periods after the first.

## Constitution check

- Types once in LinkML: no schema change (`runner: run9` is a plan key).
- Seeded randomness only: tuning on spent seed 353, validation 360, test 361; bootstrap seed 23.
- Reported estimate from a declared physics layer: every track is an arc-model fit.
- References on the same rows: spec 025's (C″, one leg, the true history across the span and
  per period). IMM/EKF not re-run (spec 025 FR-007).
- Nothing above OFFICIAL; mock data; no money, no GPU.

## Structure

```
src/tma2/timelate/carry.py    Carried, carried_theta, solve_ctl (ctl with an optional carried start)
src/tma2/timelate/run9.py     runner: run8 per engagement, then the carry chain
src/tma2/timelate/study9.py   carry ÷ joint, alone ÷ carry over later periods; verdict9
src/tma2/cli/tlsolve.py       CARRY_FILES digest, runner run9; tlscore: run9 → study9
tests/unit/test_timelate9.py
configs/timelate/tl-m-draft.json (tuning), tl-m.json (registered), runs/tl-m-{tune,val,test}.json
```

## Steps

1. Build; check locally that `solve_ctl(carried=None)` reproduces `run4`'s `ctl-d1-q0.01`
   (FR-001); every run also records the first period's carry against `run8`'s alone.
2. Tuning on spent seed 353 (CI): ratios, variances, time.
3. Decision record (rule FR-003, sizes, forecasts, soundness band, what follows).
4. Validation seed 360 (soundness); test seed 361 once.
5. Panel of five; write-up, slides; AGENTS.md; SRD §9 line; PR.
