# Implementation Plan: the scaled regressor under bearing-error mismatch

**Branch**: `claude/lucid-wright-y1xstj` | **Date**: 2026-11-22 | **Spec**: [spec.md](spec.md)

## Summary

Three steps. Step 1 scores spec 012's three regressors unchanged under Gate H's sixteen
conditions on spent seed 321, beside C″, C″ with the robust final solve, the robust solve on the
true segmentation, the IMM, the EKF and one leg, on CI and at no GPU cost; a rule written
beforehand says whether step 2 goes ahead. Step 2 fine-tunes the three checkpoints on a stream
of scenarios with bearing errors drawn per scenario, registers its readings first, and scores
once on a fresh seed, including an error family training never saw. The model's existing
variance head supplies the stated intervals. Step 3 starts and constrains C″'s final solve with
the regressor's estimate. Decisions and alternatives: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: NumPy/numba (generator, overlay), PyTorch (regressor), existing
`tma2.regress`, `tma2.headroom`, `tma2.sim.mismatch`; Modal for the GPU runs
**Storage**: results branches (`results/rmis-*`, `results/gputrain-*`); committed records under
`experiments/`
**Testing**: pytest (unit; byte-identity of existing conditions; a toy fine-tune on CPU)
**Target Platform**: GitHub runners (CPU), one Modal T4 per run
**Project Type**: research code and CLI
**Performance Goals**: the fine-tuning stream at 500 scenarios a second or better on a T4
container (spec 012 measured 570 to 670 without the overlay)
**Constraints**: GPU dollars by the ledger. The ledger reads $40.57 used; `gputrain.yml`
refuses past $49 (owner, 2026-11-22; was $45), under the owner's $50 total (research R4).
**Scale/Scope**: step 1: 16 conditions × 300 engagements; step 2: about 7.5 million scenarios a
seed; test: 2,000 engagements × 4 conditions

## Constitution Check

- Types once in LinkML: new condition fields, plan and header fields go in `schema/tma.yaml`
  (schema 0.40.0). Pass.
- Seeded randomness only: the per-scenario training condition and the new error kinds draw from
  their own SplitMix64 streams; no existing draw moves. Pass.
- Reported estimate from a declared physics layer: the regressor is a control, named so in
  every header; the hybrid reports from the layer. Pass.
- References on the same rows: naive, one leg, C″, C″-robust, the robust solve on the true
  segmentation, IMM, EKF, the known-manoeuvre bound, in one scoring run. Pass.
- Efficiency per slice; three seeds; mock data only. Pass.
- Owner-only: money. Inside the existing guard; the question of raising it is put to the
  owner and nothing depends on the answer except the fine-tune's length.

Post-design re-check: unchanged. C's frozen code (`physics/layer.py`, `segment/`) is not edited;
the hybrid subclasses the layer as `headroom/gls.py` does.

## Structure

```
src/tma2/sim/mismatch.py       two new kinds from a second stream (R2); existing output unchanged
src/tma2/features/batch.py     generate_indices(..., mismatch=[n, M]) applies the overlay per scenario
src/tma2/regress/
  mixture.py                   the training mix: a condition per scenario index (R3)
  data.py, train.py            the mix in the stream; start from a checkpoint (`init_from`)
  intervals.py                 95% intervals from the variance head: range, speed, course arc (R1)
  predict.py                   rows carry the intervals
  hybrid.py                    C″'s final solve with the regressor as start and prior (R7)
  mread.py                     paired ratios, shares, coverage, the readings M1–M5, Y1, Y2 (R6)
src/tma2/cli/                  rpredict (--scale), hpredict (--prior-from), rmread (new)
.github/workflows/rmis.yml     `rmis/**`: conditions × (classical shards, regressors, scorer, readings)
configs/rmis/                  dev-321.json (step 1), val-370.json, test-371.json, smoke.json
configs/regress/               ft-mix.json, ft-pilot.json, ft-s1..s3.json
configs/gateh/conditions.json  unchanged; configs/rmis/heldout-conditions.json (R2)
scripts/research/              rmis_tables.py, rmis_charts.py
tests/unit/                    test_mismatch_kinds.py, test_regress_mixture.py, test_intervals.py,
                               test_hybrid.py, test_mread.py
```

## Phases

1. **Step 1** (CPU): `rmis.yml`, `mread.py`, intervals from the existing head, the rule
   (R5) committed before the run; smoke run; the run on seed 321; record
   `experiments/<date>-rmis-dev/`. Checkpoint: the rule's output decides step 2.
2. **Overlay and mix**: the two new kinds with byte-identity tests; the training mix; start
   from a checkpoint; toy fine-tune on CPU.
3. **Pilot** (GPU, at most a quarter of what is left): throughput with the overlay, one
   learning rate, the validation curve on seed 370's monitor. Stop if nothing moves in the
   first hour.
4. **Decision record** `experiments/<date>-rmis-decision/`: plans by digest, code digest,
   readings and thresholds, forecasts, seeds. Then the three fine-tunes, a minute apart.
5. **Validation** (seed 370): the interval scale, the hybrid's settings, early stopping;
   addendum binding them. **Test** (seed 371), scored once.
6. **Hybrid** code and its readings in the same test scoring run.
7. Panel review, write-up, slides post, PR.
