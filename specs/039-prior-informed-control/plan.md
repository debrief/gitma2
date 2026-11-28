# Implementation Plan: a classical control given the generator's priors

**Branch**: `claude/lucid-wright-y1xstj` | **Date**: 2026-11-28 | **Spec**: [spec.md](spec.md)

## Summary

A read-out (`headroom/profile.py`) profiles the robust solve's cost over the target's range at
the scored row, weights the profile by the generator's distribution of ln range and its support
for speed, and reports the posterior median. On the true manoeuvre times it is a reference; on
C″'s segmentation a causal control. Development on spent seed 370, registration, fresh test
seed 373 on CI. Decisions: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: `tma2.headroom` (robust solve, whitened layer), `regress.hybrid`
(a prior row on the state at the row; here it holds the range), `regress.decomp`
**Testing**: pytest (weighted median, prior table, tempering, one scenario through the layer)
**Target Platform**: GitHub runners (CPU only)
**Constraints**: no GPU, no spending. A profile is about 29 constrained solves, 4.5 s per row.
**Scale/Scope**: development 300 engagements × 2 conditions; test 500 × 6

## Constitution Check

- Types once in LinkML: the header's `kind` gains "profile" (a description change; schema stays 0.41.0). Pass.
- Seeded randomness only: none new; the prior table is built from a spent seed. Pass.
- Reported estimate from a declared physics layer: every profile point is a layer solve; the
  read-out interpolates between two of them, which is stated in the header and the record. The
  regressors are controls. Pass with that statement.
- References on the same rows; efficiency per slice; mock data only. Pass.
- Owner-only: none touched.

`physics/layer.py` and `segment/` are not edited.

## Structure

```
src/tma2/headroom/profile.py      the read-out; Prior, ProfileSettings
src/tma2/cli/hpredict.py          --kind profile --profile <json>
src/tma2/cli/rdecomp.py           names["pairs"]: control ÷ system overall and by bound third
scripts/research/pic_prior.py     the prior table from a spent seed
scripts/research/pic_plan.py      plans from configs/pic/protocol.json
configs/pic/                      protocol.json, prior-man2.json
tests/unit/test_headroom_profile.py
```

## Steps

1. Read-out, tests, plans (done before the first run).
2. Development run on seed 370: tempered and untempered, a flat-prior variant (median against
   mode with no prior), on the true segmentation, on C″'s, and on C with edited bearings.
3. The cut evidence search on a development subset (part 3): accuracy and seconds.
4. Decision record; test on seed 373; three reviewers; write-up; slides; AGENTS.md; PR.
