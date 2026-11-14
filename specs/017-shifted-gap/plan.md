# Implementation Plan: the standing control and the shifted-prior gap

**Branch**: `claude/keen-wozniak-77td7j` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

## Summary

Run study L's control unchanged and, beside it, readings that split its gap to the true
history into what no detector could find and what a better one could: per-manoeuvre
detectability, references told only the detectable manoeuvres, and the search given the
true prior. Register a rule on the attainable share, decide it on a fresh seed, and make
good what study L's record owes. Nothing trained; CPU only. Decisions:
[research.md](research.md).

## Constitution Check

- Seeded randomness only; fresh seeds 342 to 344. Pass.
- References on the same rows: C″, one leg, the tuned IMM and EKF as tracks, the search,
  the true-history references. Pass (study L omitted the filters; restored here).
- Reported estimates come from the declared arc model. Pass. Nothing is carried.
- Owner-only: no money. SRD §9 line proposed; the owner merges.

## Structure

```
src/tma2/timelate/detect.py   detectability, detectable-only references (R1, R2)
src/tma2/timelate/run5.py     run4's control + references, true-prior search, IMM/EKF (plan key runner: run5)
src/tma2/timelate/study5.py   detectability tables, the gap split, the verdict
src/tma2/cli/tlsolve.py, tlscore.py   runner run5 wiring (run2 to run4 paths unchanged)
configs/timelate/tl-f-draft.json, tl-f.json, runs/tl-f-{tune,val,test}.json
.github/workflows/headers.yml   shard headers of a finished run to a results branch (R4)
scripts/research/tl5_tables.py, tl5_charts.py
tests/unit/test_timelate5.py
```

## Phases

1. Code and local check. 2. Tuning on seed 342; read what the thresholds mean and the
rule's power. 3. Owed items (headers workflow, export check, tests). 4. Decision record.
5. Validation 343 (soundness), test 344 once. 6. Panel, write-up, slides.
