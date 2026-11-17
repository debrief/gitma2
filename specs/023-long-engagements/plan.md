# Implementation Plan: Longer engagements (6 to 48 hours)

**Spec**: `specs/023-long-engagements/spec.md` · **Issue**: #42 · **Date**: 2026-11-17

## Summary

Simulate one engagement each of 6, 12, 24 and 48 hours (seed 348), run the standing real-time
systems (E, C″, one leg, IMM) every 10 minutes on a sliding 2-hour window and the standing
time-late control `ctl` on a chain of 2-hour windows, measure run time and error against time,
time `ctl` on single periods of growing length, and show the engagements on the viewer and
time-late pages. Long runs go to CI (`long/**` is not used: the workflow triggers on pushes to
this task's branch that change `configs/long/run.json`, and on `workflow_dispatch`).

## Constitution check (v1.3.0)

- Types once in LinkML: the long engagement's meta is an in-memory dict for an investigation and
  is not written as a dataset record; nothing enters `schema/tma.yaml`. **Pass** (no new record
  type is published).
- Seeded randomness only: `derive_seed(348, index)`. **Pass**.
- The reported estimate comes from a declared physics layer: every system is a standing one,
  unchanged except C″'s veto at every turn (declared in the spec). **Pass**.
- No result without the references on the same rows: this is not a result; one leg and the IMM
  run beside, the time-late true-history fit is shown as a reference. Efficiency against the bound
  is not computed (the bound over 48 hours is the open problem the note describes). **Recorded
  departure**: an investigation, labelled as one.
- Three seeds per carried configuration: nothing is carried. **N/A**.
- Mock data only, nothing above OFFICIAL. **Pass**.

## Structure

```
configs/long/long.json            simulator settings (seed 348, durations, ownship policy)
src/tma2/long/sim.py              the simulator
src/tma2/long/windows.py          windows, thinning, the veto at every turn
src/tma2/long/realtime.py         E, C″, one leg, IMM on a sliding window
src/tma2/long/timelate.py         ctl on a chain of windows; stitching; scaling
src/tma2/cli/long.py              tma2-long {realtime,timelate,scaling}
.github/workflows/long.yml        one job per (part, engagement); results uploaded as artefacts
                                  and committed to results/long-<run id>
scripts/research/long_report.py   summary.json and tables.md of experiments/20261117-long/
scripts/research/long_viewer_data.py   site/static/long-data/
site/src/components/LongEngagements.js and the two pages
docs/research/12-long-engagements.md
tests/unit/test_long.py
```

## Risks

- `ctl` on 2-hour windows of a busy target takes several minutes a window; 48 hours is about 32
  windows. Mitigation: one CI job per engagement and part, 6-hour job limit.
- A container restart kills local runs: nothing over a few minutes runs in the session.
