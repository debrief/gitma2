# Implementation Plan: Steady-leg segmentation and Gate S

**Branch**: `claude/inspiring-curie-j192v9` (feature `005-steady-leg-segmentation`) | **Date**: 2026-11-03 |
**Spec**: [spec.md](spec.md)

## Summary

Segment each prefix of an engagement into steady legs, transitions and unknown intervals, for
ownship (O) and target, and hand the target's transitions to the physics layer as gaps or chords.

**C, the classical target segmenter.** The plan's research changed its design (R1, R2):
- **Measured:** the spec's additive search followed by coupled refinement is well below note 08's
  GLR + confirm (F1 0.65 against 0.79 on the same rows).
- **So C is a coupled nominate-and-confirm segmenter.** GLR alarms, re-tested while raised, and
  the additive search's transitions both nominate. The physics layer confirms each candidate
  transition on its own prefix, choosing its start and length. Accepted boundaries are then
  polished.

**L, the learned segmenter.** It adds per-bearing evidence to the search and, as a capped prior,
to the confirmation threshold. It starts at zero, so untrained it equals C. It is trained by the
semi-Markov likelihood of the truth segmentation (R6).

**Gate S** scores everything on fresh seed 315 (generator 0.6.0, MAN2) against batch least squares, the frozen IMM, the
oracle and GLR + confirm, with the only learning claim being S4.

## Technical Context

- **Language/Version:** Python 3.12 (uv).
- **Primary Dependencies:** PyTorch 2.x CPU (double for the physics layer), NumPy, numba,
  LinkML → Pydantic, onnx and onnxruntime (as spec 003/004).
- **Storage:** validation and test splits as f32pack with pinned digests. Segmentations as
  NDJSON records. Precomputed cost tables for L's training as `.npz` per shard (not committed).
  Experiment records under `experiments/`.
- **Testing:** pytest (unit, golden on fixture scenarios), ruff, mypy --strict.
- **Target Platform:** GitHub-hosted ubuntu-latest, 4 cores.
- **Project Type:** research pipeline of CLIs.
- **Performance Goals:**
  - C at most 10 s per scenario (all scored prefixes) on one 4-core runner. The cost table is
    3.1 s median and 8.3 s at most per scenario (R1).
  - L one epoch over 10⁴ scenarios in under one hour.
- **Requirements source:** SRD Annex B (owner, 4 Nov 2026) wins over the spec where they differ;
  the spec's Clarifications of 2026-11-04 record the amendments.
- **Constraints:**
  - Offline segmentation on each prefix: no bearing after k is used at row k.
  - Double precision for the physics layer.
  - No paid compute.
  - Generator 0.6.0 (MAN2, spec 006) unchanged; 0.5.0 ranges still reproduce 0.5.0.
- **Scale/Scope** (re-planned for MAN2, 2026-11-04):
  - Windows of 40–120 min, up to 720 rows (0.5.0: 360).
  - Validation: seed 314, `data/man2-val` (digests in
    `experiments/20261104-g0-man2/dataset-digests/`). Development tunes on its first 500 σ = 1°
    scenarios and scores on the next 1,000, as note 08 did.
  - Gate S test: seed 315, 10,000 scenarios, generated only after the decision record is
    committed.
  - L training stream: seed 317 (fresh; 316 is the G0-MAN2 noise-free set, 312 and 313 were
    declared for 0.5.0 and are left unused so no reader confuses the generators).

## Constitution Check

| Principle | How this plan meets it |
| --- | --- |
| I. Types once in LinkML | Segmentation, TruthLabels, GateSDecision and GateSRecord are added to `schema/tma.yaml`, then regenerated |
| II. Determinism | The search and confirmation are deterministic. L is seeded, and separate processes are byte-identical (spec 004's test pattern). Seeds 315 and 317 are pinned by digest |
| III. Physics does the numerics | The estimate always comes from the physics layer. Segmenters only set knots and weights |
| IV. Honest measurement | On the same rows: naive, batch least squares, the frozen IMM, the oracle and GLR + confirm. Medians, P90, gross rates and efficiency per slice. Clustered intervals. Three L seeds, carried by a declared rule. A shuffled-label control. The decision record comes before training |
| V. Gates | Gate S is new, with its follow-on fixed in Annex A §A.9. Gate D is untouched. The verdict comes from the panel |
| VI. Portable artefact | L's network exports to ONNX with three-runtime conformance. The decoder stays in host code (FR-045, R8) |

The time-late rule of principle IV does not apply: segmentation is already offline on each
prefix, and no causal variant is carried.

**Result: pass, no violations.** Re-checked after Phase 1: still passes. The design change to C
is recorded in the spec's Clarifications and is within Annex A §A.9's wording ("a joint search …
then a coupled physics-layer refinement").

## Project Structure

### Documentation (this feature)

```text
specs/005-steady-leg-segmentation/
├── spec.md
├── plan.md              # this file
├── research.md          # R1–R8, with measurements
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md           # tma2-segment, tma2-segtrain, tma2-gs
│   └── decision-record.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
schema/tma.yaml                    # + Segmentation, SegmentInterval, TruthLabels, GateSDecision, GateSRecord
src/tma2/segment/
  truth.py                         # truth labels from true tracks (R4)
  ownship.py                       # O: penalised change-point on course and speed (R5)
  search.py                        # additive cost table (numba) + DP nominator (R1; from scripts/research/seg_search.py)
  confirm.py                       # coupled nominate-and-confirm with transition lengths and boundary polish (R2)
  segmenter.py                     # C = nominators + confirmation → Segmentation per prefix; L hook
  inputs.py                        # Segmentation → physics-layer inputs, gap or chord (FR-030)
  crf.py                           # semi-Markov forward recursion, loss (R6)
  evidence.py                      # L's evidence network (torch), export
  metrics.py                       # contamination, coverage, false split, leg count, gap recovered (R7)
src/tma2/detect/confirm.py         # reused (knot_inputs, layer_costs, tau_4dof)
src/tma2/cli/segment.py            # tma2-segment
src/tma2/cli/segtrain.py           # tma2-segtrain (L)
src/tma2/cli/gs.py                 # tma2-gs (Gate S scoring and verdict)
scripts/research/seg_search.py, seg_refine.py   # R1–R2 prototypes (kept as the record)
tests/unit/test_segment_*.py       # truth, O, search, confirm, inputs, CRF gradient, metrics
experiments/20261103-spec005-research/          # R1–R2 summaries
.github/workflows/                 # segment-tables (cost tables for L), train/segL (spec 003 pattern)
```

**Structure Decision**: a new `tma2.segment` package beside `tma2.detect`. The note 08
confirmation primitives are reused, not copied, and the prototypes move from `scripts/research` into
the package with tests.

## Phases after this plan

Generator 0.6.0 (spec 006) is built and its pipeline gate G0-MAN2 passed (panel round 2,
`experiments/20261104-g0-man2-r2/`). Everything below runs on its data. The research measurements
R1–R3 were made on 0.5.0 (seed 304) and are re-measured on seed 314 in phase 1 where they set a
decision-record value: the search penalty, the gap or chord mode, and the cost per prefix. The
cost table is quadratic in rows, so 720-row windows may exceed the 10 s budget; phase 1 measures
it and, if so, the plan's grid or budget is revised before the decision record (a plan goal, not a
gate criterion). The physics layer's knot path at 720 rows (untested by G0-MAN2) gets an
equivalence and export check before C depends on it.

1. **C and its scoring.**
   - Truth labels, O, the search, confirmation with lengths, polish, inputs and metrics.
   - `tma2-segment` and `tma2-gs --validation`.
   - The validation measurements that fix the decision record: the search penalty at ≤ 5% false
     splits, the gap or chord mode, the cost per prefix.
   - Reproduce GLR + confirm's note 08 numbers as a check (SC-002).
2. **Decision record** committed: S1 and S3 limits, the penalty, the mode, the seeds, a forecast.
   S2 is evaluated on validation first. If C does not beat GLR + confirm there, the record says
   so and S4 uses GLR + confirm as the reference.
3. **L:** cost tables for seed 317 on runners, then CRF training with three seeds, the shuffled
   control, and export.
4. **Gate S on seed 315:** the panel, `review.md`, the verdict, and site pages (algorithm note,
   glossary, write-up).

## Complexity Tracking

No constitution violations.
