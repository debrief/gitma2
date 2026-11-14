# Implementation Plan: time-late, classical controls and a learned whole-period model

**Branch**: `claude/keen-wozniak-77td7j` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

## Summary

Two tracks. Track 1 builds classical controls on the repaired search (hedged track,
declaration margin, robust and correlated-error likelihoods, a broadened prior with a
diagnostic, prior version 4) and tunes them on seed 338. Track 2 trains a bidirectional
sequence model on a declared mix of simulated periods (three seeds, about $22 of T4 time)
under a plan bound before the first job. The model is scored once, on test seed 341,
against the best classical control per split, after the controls' validation record
exists. Decisions and alternatives: [research.md](research.md).

## Technical Context

Python 3.12, NumPy/numba, PyTorch (model), existing `tma2.timelate`, `tma2.regress`,
`tma2.headroom`. CPU work on GitHub runners through `timelate.yml`; GPU through
`gputrain.yml` and `scripts/modal_train.py` with the ledger. Schema bump for new header
fields. Tests: unit (pytest), fixtures pinned loosely across CPU families.

## Constitution Check

- Types once in LinkML: new shard header and plan fields go in `schema/tma.yaml`. Pass.
- Seeded randomness only: stream seed 339, mix draws from per-engagement sub-streams. Pass.
- Reported estimate from a declared physics layer: `learned-arc` (R8). Pass.
- References on the same rows: C″ as a track, one leg, IMM/EKF tracks, the plain search,
  the true-history reference under three conventions. Pass.
- Efficiency per slice, three seeds per carried configuration, mock data only. Pass.
- Owner-only: money. Within the pre-approved $50 total (R10); nothing beyond without the
  owner. SRD §5 row and §9 line proposed; owner merges.

## Structure

```
src/tma2/timelate/
  prior.py        version 4 (R6), kinds broad, mix2 (R5)
  hedge.py        hedged track, declaration margin (R1, R2)
  robust.py       Huber fits and evidence; uses thin.edit_wild (R3)
  corr.py         AR(1)+white estimate, whitened fit and evidence (R4)
  run4.py         runner: plain v3 and v4 searches, each control, hedged tracks, stored tracks
  study4.py       paired comparisons per split, gap closed, counts, criteria L-a to L-d
  learned.py      model's track at scored rows; logit runs to spans; arc read-out (R8)
src/tma2/regress/
  period_data.py  the mixed stream of periods (R9), features and targets per 5-s row
  model.py        `causal: bool`, manoeuvre logit head (R7); spec 012's behaviour unchanged
  train.py        loss with the logit term when configured
src/tma2/cli/     tlsolve (runner run4), tlscore (study4, --learned, --controls-record),
                  tlpredict (model → shard of learned tracks), rtrain (period stream)
configs/timelate/ tl-e-draft.json, tl-e.json, runs/, tl-shift2-ranges.json, tl-broad.json
configs/regress/  tlm-pilot.json, tlm-s1..s3.json
scripts/research/ tl4_tables.py, tl4_charts.py, tl4_readme_check.py
tests/unit/       test_timelate4.py, test_period_model.py
```

## Phases

1. **Controls, code** (CPU): prior v4 with edge tests; hedge; robust; corr; broad prior;
   run4 and study4; fixture.
2. **Controls, tuning** on seed 338 (CI): choose T, M, q, robust form, correlated form;
   record `experiments/<date>-tl4-tuning/`.
3. **Model, code** (CPU): period stream, non-causal model with logit head, export check,
   read-out; toy training test; pilot plan.
4. **Pilot** on a T4 (at most 1 h): throughput and a loss curve; then bind the training
   plans.
5. **Registration**: SRD §5 row and §9 line; decision record binding the controls' plan,
   the model's plans, the comparison and the power table. Before any training job beyond
   the pilot and before seeds 340 and 341 exist.
6. **Training**: three seeds (GPU, about 30 h in all), launched a minute apart.
7. **Controls' validation** on seed 340 (CI); L-a; record committed.
8. **Test** on seed 341: controls and learned tracks solved, scored once.
9. **Panel**, corrections, write-up, slides.

Phases 2 and 3 to 4 run in parallel; 6 runs while 7 is prepared.

## Risks

- Run time: five searches a period at 30 to 50 s each is about 4 minutes a period; 2,300
  test periods is about 150 runner-hours. Shards of 10 periods, runs queued one at a time.
- The budget buys about 23 million periods a seed if throughput holds; if the pilot shows
  under half that, two seeds are trained and the third is reported as not run (the criteria
  then need both).
- A sixth evidence error: v4 is tested at edges; the plain v3 search is kept beside it.
- The model's logit read-out proposes spans the arc fit cannot use: `learned` (direct) is
  reported beside it either way.
