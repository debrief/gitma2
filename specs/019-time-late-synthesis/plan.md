# Implementation Plan: one diagnostic of the true prior's gain, and the time-late track as a whole

**Spec**: `specs/019-time-late-synthesis/spec.md` · **Date**: 2026-11-15 · CPU only; nothing
trained; no new seed.

## Summary

1. A diagnostic runner (`run7`): the standing control unchanged, and a search of its own
   under each rung of a ladder from the broadened prior to the shifted targets' own
   statistics (legs, turn sizes, turn rates, speed changes, kinds), each part alone, and
   the family member nearest the truth. 150 shifted periods of used seed 347.
2. The account of specs 013 to 018 from their committed records and panel reviews, checked
   by independent reviewers against those records.

## Constitution check

- Types once in LinkML: no schema change. Seeded randomness only: seed 347, already used;
  nothing new generated beyond regenerating that seed's shifted split in the CI run.
- No result: the diagnostic is development work and is labelled so everywhere. The account
  quotes registered results from their records only.
- Reported estimates come from the arc-model fit. References on the same rows: the
  standing control and the true-prior search; the account cites each spec's own references.
- Mock data only; nothing above OFFICIAL; no money, no GPU.

## Structure

```
src/tma2/timelate/run7.py     ladder of priors, each with its own search (plan key `runner: run7`)
src/tma2/timelate/study7.py   each rung against the control and the true prior; concentration
src/tma2/cli/tlsolve.py, tlscore.py   runner run7
configs/timelate/tl-h-dev.json, runs/tl-h-dev.json
scripts/research/tl7_tables.py     the diagnostic's tables from its summary
scripts/research/tl_synthesis.py   the account's table and charts from the committed test records
tests/unit/test_timelate7.py
site/blog/2026-11-15-time-late-synthesis.md, -slides.md; deck; figures
docs/SRD.md §9 (proposed)
```

No earlier runner, plan or record is edited.

## Steps

1. Build and test `run7`/`study7`; smoke one period; run on CI (15 shards of 10 periods).
2. While it runs: collect from each spec's committed `summary.json` the figures the account
   needs (`tl_synthesis.py`), so that no number is typed by hand.
3. Record the diagnostic (`experiments/20261115-tl7-dev/`), with tables by script.
4. Write the account and the slides; three independent reviewers check them against the
   records; apply corrections.
5. AGENTS.md, tasks, PR (the owner merges: SRD §9).
