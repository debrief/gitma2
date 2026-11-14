# Implementation Plan: a manoeuvre prior that adapts to the period, and a hedged track

**Spec**: `specs/018-adaptive-prior/spec.md` · **Date**: 2026-11-14 · CPU only; nothing trained.

## Summary

Run the standing control exactly as registered (`run4`), and on the same bearings: a search
under each member of a small grid of manoeuvre rates, the rate inferred by evidence, a
history declared under the inferred rate, and a hedged track over every rate's candidates
with a spread in range. Beside: the search told the split's own statistics, the
true-history reference and each true manoeuvre's detectability (to class periods).

## Constitution check

- Types once in LinkML: no schema change (shard header fields exist; `runner: run6`).
- Seeded randomness only: seeds 345 tuning, 346 validation, 347 test; bootstrap seeds fixed.
- Reported estimate from a declared physics layer: every track is an arc-model fit or a
  mean of such fits. The hedged mean is not itself a fit and is labelled so.
- References on the same rows: C″ as a track, the standing control, the true-prior search,
  the true-history reference. IMM, EKF and one leg were scored on these splits' kinds in
  spec 017 and are not re-run (stated in the record as not delivered here).
- Efficiency per slice: range, course, speed against the bound in the tables.
- Nothing above OFFICIAL; mock data only. No money, no account, no GPU.

## Structure

```
src/tma2/timelate/adapt.py    rate grid, rate posterior, Laplace sd of range, mixture, hedged spread
src/tma2/timelate/run6.py     runner (plan key `runner: run6`); run4's control unchanged
src/tma2/timelate/study6.py   three-quantity paired ratios, kinds of period, share of ceiling, coverage
src/tma2/cli/tlsolve.py       ADAPT_FILES digest; runner run6 (rate grid from plan `adaptive`)
src/tma2/cli/tlscore.py       runner run6 -> study_split6
scripts/research/tl6_tables.py, tl6_charts.py
tests/unit/test_timelate6.py
configs/timelate/tl-g-draft.json (tuning), tl-g.json (registered), runs/tl-g-{tune,val,test}.json
```

`run4.py`, `run5.py`, `detect.py`, `hedge.py`, `corr.py`, `prior.py` and `search.py` are not
edited (FR-001): their digests are in earlier decision records.

## Steps

1. Build and unit-test (`adapt`, `run6`, `study6`, tables); smoke-run three periods locally.
2. Tuning run on seed 345 (CI): six splits. Read: does the adaptive control gain on the
   shifted split, what does it cost elsewhere, is the spread honest. Choose the grid's
   weights and the per-period rule's threshold here and nowhere else.
3. Decision record: conditions, each shown able to come out either way on tuning data and
   reading cost; sizes from tuning variances; forecasts; what follows. Plan bound by digest.
4. Validation on seed 346 (soundness; stops the study if it fails).
5. Test on seed 347, once. Tables by script.
6. Panel of five; corrections; write-up, slides, AGENTS.md; PR.
