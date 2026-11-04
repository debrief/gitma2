# Implementation Plan: Generator 0.6.0, the MAN2 simulation model

**Branch**: `claude/inspiring-curie-j192v9` (feature `006-generator-man2`) | **Date**: 2026-11-04 |
**Spec**: [spec.md](spec.md)

## Summary

Add the owner's manoeuvre model to the generator behind new ranges fields: target legs of
10–40 min (normal, mean 25 min, sd 9.1 min, floor 5 min) laid end to end, each ending in a course
change, a speed change or both, with slower turns so transitions last about a minute; target
changes allowed during ownship turns; helm wander or autopilot oscillation on ownship inside the
± 5° band; 40–120 min windows (720 rows). All new draws come from streams of their own, so a
ranges file without the fields reproduces 0.5.0 byte for byte (R1). Then regenerate the fixed
splits (seeds 314, 315, 316), re-run the pipeline gate with the panel, re-tune and freeze the IMM
and EKF, and re-measure note 08's GLR + confirm baseline, so spec 005's decision record has
everything it needs (R6).

## Technical Context

- **Language/Version:** Python 3.12 (uv); numba kernel; LinkML → Pydantic.
- **Primary Dependencies:** as the repository: NumPy, numba, PyTorch (physics layer for the
  gate), onnx/onnxruntime for the 720-row conformance artefact.
- **Storage:** f32pack splits with pinned digests; `configs/man2-ranges.json` and its noise-free
  twin; experiment records under `experiments/`.
- **Testing:** pytest (golden files for 0.5.0 and the new MAN2 fixtures; gitma conformance
  fixtures unchanged; unit tests for the leg planner, wander, the "both" kind and the zig
  planner), ruff, mypy --strict.
- **Target Platform:** GitHub-hosted ubuntu-latest, 4 cores.
- **Project Type:** generator library and CLIs.
- **Performance Goals:** kernel ≥ 10,000 scenarios/s at 720 rows (measured 1,500/s end to end
  with file writing on the current kernel; the kernel itself is far above); physics layer
  25.7 ms per solve at 720 rows (measured).
- **Constraints:** every existing PRNG draw keeps its order; float32 rounding and JavaScript
  semantics as today; new behaviour only behind new ranges fields; no paid compute.
- **Scale/Scope:** 10,000-scenario splits; MAX_TM 24; 720 rows.

## Constitution Check

| Principle | How this plan meets it |
| --- | --- |
| I. Types once in LinkML | New ranges fields, header fields and the span kind are added to `schema/tma.yaml` (0.21.0 → 0.22.0) and regenerated; CI's `--check` guards it |
| II. Determinism | Seeded streams only; new draws on streams 2 and 3; 0.5.0 byte-identity proved by the golden and gitma-conformance tests; new MAN2 golden fixtures; `tma2-generate` refuses a dirty tree |
| III. Physics does the numerics | No change: the generator feeds the same physics layer and references |
| IV. Honest measurement | References re-tuned on the new validation split with declared grids and frozen; GLR + confirm re-measured on the same rows; the pipeline gate's efficiency check stays |
| V. Gates | The pipeline gate re-runs on 0.6.0 with the panel before any training on MAN2 data; the `beforeManoeuvre` check is restated for the new variant (R3) and the owner is told |
| VI. Portable artefact | A 720-row conformance export is added beside the 360-row one, three runtimes to 1e-5 |

**Result: pass.** Re-checked after Phase 1: pass.

## Project Structure

### Documentation (this feature)

```text
specs/006-generator-man2/
├── spec.md
├── plan.md              # this file
├── research.md          # R1–R7
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md           # tma2-generate fields, tma2-ranges, tma2-p0 on MAN2
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
schema/tma.yaml                      # 0.22.0: ranges fields, OwnshipWander header, zig_on_manoeuvre, span kind "both"
src/tma2/sim/
  ranges.py                          # R_* layout: leg model, kind weights, wander; validation messages; MAN2 defaults
  scenario.py                        # streams 2 and 3; plan_target_legs; kind 2 simulation; wander on the ownship track; zig from the simulated target; MAX_TM 24
  version.py, ../data/versions.py    # 0.6.0 readable and produced
  generate.py                        # header fields
src/tma2/features/batch.py           # MAX_TM-sized tables (no behaviour change)
src/tma2/cli/
  ranges.py                          # tma2-ranges --describe [--sample]
  p0.py                              # R_MAX from the experiment's ranges; "on the zig leg" check for MAN2
src/tma2/export/onnx_export.py       # window rows as a parameter; 720-row artefact
configs/man2-ranges.json, man2-noise-free.json
tests/unit/test_leg_plan.py, test_wander.py, test_both_kind.py, test_zig_plan_man2.py
tests/golden/                        # MAN2 golden fixtures (new); existing ones unchanged
tests/fixtures/man2-seed316/         # small noise-free fixture for the gate's unit checks
experiments/<date>-g0-man2/          # pipeline gate, panel review.md
experiments/<date>-man2-tune/        # IMM/EKF grids and the frozen names
experiments/<date>-man2-refs/        # GLR + confirm re-run, detectability quantiles
.github/workflows/ci.yml             # 720-row conformance job; p0 on MAN2
```

**Structure Decision**: changes stay inside `tma2.sim` and the CLIs that read its constants. No
new package.

## Phases after this plan

1. **Kernel and schema** (R1, R2, R4): streams, leg planner, "both", wander, MAX_TM, header
   fields; golden tests for 0.5.0 unchanged and new MAN2 goldens; `tma2-ranges --describe`.
2. **Zig planning and 720 rows** (R3, R5): simulated target position at the zig; `R_MAX`
   parameterised; 720-row conformance export in CI.
3. **Data and gate** (R6): seeds 314/315/316 from a clean tree; the pipeline gate on MAN2 with
   the panel; `review.md`.
4. **References** (R6): IMM/EKF re-tune and freeze; GLR + confirm and detectability re-run;
   records committed. Spec 005's decision record can then be written.

## Complexity Tracking

No constitution violations.
