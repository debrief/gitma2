# Implementation Plan: time-late over several periods of one target

**Spec**: `specs/023-joined-periods/spec.md` · **Date**: 2026-11-17 · CPU only; nothing trained.

## Summary

Lay each engagement out as two or three periods with gaps. Run the standing control `ctl`
three ways on the same bearings: each period alone; the whole span with the gaps' bearings
marked missing (the joint solve, R1); the whole span with every bearing (what the gaps
cost). Score each period on the same rows for both decided systems, chosen by the span's
bound (R2), and compare by paired per-period ratios with an engagement bootstrap.

## Constitution check

- Types once in LinkML: no schema change; `TimeLateShardHeader` already carries the plan
  digest and code digest; `runner: run8` is a plan key.
- Seeded randomness only: seeds 348 tuning, 349 validation, 350 test; the layout from its
  own stream; bootstrap seeds fixed.
- Reported estimate from a declared physics layer: every track is an arc-model fit (`ctl`).
- References on the same rows: C″ and one leg per period, the true history across the span
  and per period (`history-best`), `ctl` with every bearing. IMM and EKF not re-run (FR-007).
- Efficiency per slice: by the span bound's tightness, as spec 016.
- Nothing above OFFICIAL; mock data only. No money, no account, no GPU.

## Structure

```
src/tma2/timelate/layout.py   periods and gaps per engagement (own stream); masked span
src/tma2/timelate/run8.py     runner (plan key `runner: run8`): run4 alone / joint / full
src/tma2/timelate/study8.py   paired ratios, engagement bootstrap, splits by kind of period,
                              gap events, held-course false manoeuvres, verdicts
src/tma2/cli/tlsolve.py       JOIN_FILES digest; runner run8
src/tma2/cli/tlscore.py       runner run8 -> study8
scripts/research/tl8_tables.py, tl8_charts.py
tests/unit/test_timelate8.py
configs/timelate/tl-joined-*.json (ranges), tl-j-draft.json (tuning), tl-j.json (registered),
runs/tl-j-{tune,val,test}.json
```

`run4.py` and everything `ctl` reads are not edited (FR-001).

## Steps

1. Build `layout`, `run8`, `study8`, the CLI wiring and tests; smoke-run two engagements.
2. Tuning on seed 348 (CI, four splits, about 60 engagements each): ratios, variances,
   time; R4's checks (noise alone, a manoeuvre in a gap); the layout's ranges confirmed.
3. Decision record: rule (FR-010), each outcome shown possible on tuning data, sizes from
   tuning variances, forecasts, what follows; plan bound by digest.
4. Validation on seed 349 (soundness, FR-012; stops the study if it fails).
5. Test on seed 350, once. Tables by script.
6. Panel of five; corrections; write-up, slides, AGENTS.md; SRD §9 line (owner merges); PR.
