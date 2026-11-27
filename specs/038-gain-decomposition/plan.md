# Implementation Plan: where the regressor's gain comes from

**Branch**: `claude/lucid-wright-y1xstj` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

## Summary

Nothing is trained. Around the frozen C two hardened controls are built (a raised confirmation
threshold; wild bearings edited out and an effective bearing sd in front of C), each followed
by Gate H's robust final solve. Spec 012's ownship-only regressor is scored alone and as the
prior of spec 037's hybrid solve. Everything is scored beside spec 037's fine-tuned regressors
on three kinds of split (in-distribution, busier targets, far initial ranges), clean and under
the primary mismatch condition. Settings are chosen on spent seeds 321 and 370, the estimands
are registered, and fresh seed 372 is scored once on CI. Decisions: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: existing `tma2.headroom`, `tma2.segment.robust`, `tma2.regress`
(`hybrid`, `mread`), `tma2.timelate.thin`/`corr` (wild-bearing editing, effective sd)
**Storage**: results branches `results/headroom-gd-*`; committed records under `experiments/`
**Testing**: pytest (unit: editing in front of C leaves C's digests and the final solve's
bearings unchanged; the ownship-only model's dependence on bearings; plan writer; readings)
**Target Platform**: GitHub runners (CPU only)
**Constraints**: no GPU, no spending. About 25 minutes per job of 50 engagements with C in it;
16 jobs at a time. The test is sized at 500 engagements per split and condition (research R6).
**Scale/Scope**: test: 7 split-conditions × 500 engagements × about 9 runs with C

## Constitution Check

- Types once in LinkML: new plan keys and header fields (`edit`, the splits' ranges) go in
  `schema/tma.yaml` (0.42.0). Pass.
- Seeded randomness only: no new draw; the new ranges file is read by the existing generator.
  Pass.
- Reported estimate from a declared physics layer: the regressors are controls and named so;
  the hardened controls and the hybrids report from the layer. Pass.
- References on the same rows: naive, one leg, C″, C″-robust, the robust solve told the true
  manoeuvre times, IMM, EKF, the known-manoeuvre bound, in one scoring run per split and
  condition. Pass.
- Efficiency per slice (by thirds of the bound); three seeds where a system has three; mock data
  only. Pass.
- Owner-only: none touched. No money, no SRD change, nothing carried.

Post-design re-check: unchanged. C's frozen code (`physics/layer.py`, `segment/`) is not
edited; editing happens to the data C is given, in `cli/hpredict.py`.

## Structure

```
src/tma2/headroom/edit.py       edited(d): BearingData without wild bearings, with an effective sd (R2)
src/tma2/cli/hpredict.py        --segmentation c2e (C″ on edited data), c2r kept; --edit settings
src/tma2/regress/decomp.py      the readings of this spec: gap shares, split differences, owed slices (R5)
src/tma2/cli/rdecomp.py         tma2-rdecomp: one scoring run's errors.npz -> decomp.json
.github/workflows/headroom.yml  plan keys `ranges`, `heldout` (override the Gate H plan's); `decomp` step
scripts/rmis_regressors.sh      unchanged (the ownship-only checkpoint is one more entry)
scripts/research/gd_plan.py     writes configs/headroom/gd-*.json from configs/gd/protocol.json
scripts/research/gd_tables.py   tables.md of a record from its decomp.json files
scripts/research/gd_charts.py   figures
configs/gd/                     protocol.json, shift-ranges.json, conditions (reuses configs/rmis)
tests/unit/test_headroom_edit.py, test_regress_decomp.py, test_gd_plan.py, test_ownship_only.py
```

## Steps

1. Code and unit tests (edit control, plan keys, readings); ranges file checked locally (R4).
2. Development run A on spent seed 321 (300 engagements; clean and primary): the threshold grid
   and the edit variants, the ownship-only model alone, the own-prior hybrid's weight grid.
3. Development run B on spent seed 370 (300 engagements): the chosen settings beside the grid's
   neighbours, the three splits, every reading run end to end. The stop rule is read here.
4. Decision record: protocol bound by digest, estimands, thresholds, forecasts, code digest.
5. Test: seed 372, generated in its run, scored once.
6. Three reviewers; write-up; slides; AGENTS.md; PR.

## Complexity Tracking

None.
