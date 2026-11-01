# Implementation Plan: References, Physics Layer and Gate P0 (foundations, part 2)

**Branch**: `002-references-physics-p0` (pushed on the session branch) | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

Port gitma's reference estimators (naive, batch least squares, EKF, IMM) and its evaluation
(errors, slices, metrics, clustered bootstrap, settled and G5 rows) to Python, checked against
prediction files gitma produced on the spec-001 fixtures; add the per-scenario Cramér–Rao bound
and the efficiency metric; build the physics layer (a differentiable piecewise-constant-velocity
batch solve with fixed, branchless Levenberg–Marquardt iterations) in PyTorch with a NumPy
reference, prove it equals batch least squares with trivial inputs and reproduces the oracle
ceiling with truth segmentation; export it with a toy encoder to ONNX and run a three-runtime
conformance test; run and record gate P0 with the agent review panel; add algorithm notes.

## Technical Context

**Language/Version**: Python 3.12 (as 001)

**Primary Dependencies**: numpy, numba (reference estimators: per-scenario scalar kernels),
**torch (CPU)** for the physics layer, **onnx + onnxruntime** for export and the Python leg,
`onnxruntime-web` under Playwright (Node) for the browser leg, ORT Java via Maven (JDK from
`actions/setup-java`) for the Java leg; pydantic/linkml as 001

**Storage**: prediction NDJSON files (gitma's format), metrics CSV/JSON, `experiments/<id>/`

**Testing**: pytest; conformance against gitma prediction fixtures; golden files; gradient checks;
a 10^5-scenario oracle check (CI, cached by digest)

**Target Platform**: Linux 4-core CI; no GPU

**Project Type**: library + CLIs + CI jobs

**Performance Goals**: per-timestep batch LS on the frozen IMM's scale (a 10^5 validation split:
~2–3 × 10^7 LM solves) in under 30 min on 4 cores; IMM on the same split in under 15 min;
physics layer forward+backward for a batch of 256 × 360 rows in under 1 s on CPU

**Constraints**: equality with gitma under the one-ulp float32 rule; physics layer has no
data-dependent control flow (fixed K, branchless damping) so it exports; oracle ratios inside
the research note's intervals

**Scale/Scope**: ~4,000 lines of Python; one schema minor bump

## Constitution Check

| Principle | Check | Status |
| --- | --- | --- |
| I Types | Prediction, metrics, manifest and verdict types from the schema; `efficiency` and CRB fields added to `MetricsRecord` by a minor schema bump (0.17.0) and regenerated | pass |
| II Determinism | Estimators are pure functions; bootstrap seeded (20261011) with gitma's PRNG; experiment manifest records commit, digests, seeds, versions; weights: none yet | pass |
| III Physics layer | Declared, differentiable, standard ops, equations in an algorithm note, NumPy reference, equals batch LS with trivial inputs, oracle ceiling with truth inputs | pass (this spec builds it) |
| IV Measurement | gitma's metrics plus efficiency per slice; references reproduced; clustered bootstrap | pass |
| V Gates | P0 defined, run by `tma2-p0`, decided by the panel; no training in this spec | pass |
| VI Portable artefact | ONNX export + three-runtime conformance before any model | pass |
| Constraints | CPU only; frame and units as gitma; public repo, mock data | pass |
| Workflow | PR, CI, algorithm notes and glossary | pass |

**Post-design re-check**: unchanged. One point of care: the physics layer's LM uses branchless
accept/reject (`where`) rather than loops, which is a numerical choice, not control flow; the
NumPy reference mirrors it exactly.

## Project Structure

### Documentation (this feature)

```text
specs/002-references-physics-p0/
├── plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/
    ├── cli-estimators.md      # tma2-naive, tma2-solve, tma2-track, tma2-eval, tma2-p0
    ├── prediction-format.md   # gitma's prediction NDJSON (shared format)
    ├── physics-layer.md       # tensor interface, equations summary, invariants
    └── eval-outputs.md        # metrics.csv/json, curves.csv, bootstrap.json, experiments/<id>/
```

### Source Code

```text
src/tma2/
├── references/
│   ├── lsq.py          # cost, normal equations, LM, grid start (numba scalar kernels)
│   ├── classical.py    # per-timestep driver, plausibility, rows (gitma estimate.ts)
│   ├── naive.py        # training-set means, rows
│   ├── ekf.py          # EKF + initialisation from the batch fit
│   ├── imm.py          # IMM (CV + CT), mixing, likelihoods, re-initialisation
│   └── crb.py          # Fisher information per row, delta-method bounds
├── physics/
│   ├── layer.py        # torch: piecewise-CV LM solve, fixed K, branchless damping, covariance
│   ├── reference.py    # NumPy mirror of layer.py (documentation of record, golden tests)
│   └── segmentation.py # truth spans → changepoint/speed weights (oracle inputs); CUSUM later
├── eval/
│   ├── errors.py, slices.py, stats.py, metrics.py, bootstrap.py, rows.py (settled, G5)
│   ├── predictions.py  # prediction file reader/writer, digest binding
│   └── experiment.py   # manifest, verdict, folder layout
├── export/
│   ├── toy_model.py    # toy encoder + physics layer module
│   └── onnx_export.py  # export, golden batch, runtime comparison
└── cli/ (naive, solve, track, eval, p0)
tests/
├── conformance/test_references.py   # vs tests/fixtures/gitma/*/predictions/*.ndjson
├── unit/ (lsq, ekf, imm, crb, physics_layer, eval, bootstrap, export)
├── golden/ (physics-layer reference outputs, metrics on fixtures)
└── fixtures/gitma/<name>/predictions/{test,validation}-{lsq,ekf,imm}.ndjson
conformance/onnx/   # Playwright + Java harness (package.json, pom.xml or Gradle-free jar run)
experiments/<date>-p0/
site/docs/algorithms/{physics-layer,least-squares,ekf-imm,crb}.md
```

**Structure Decision**: references and physics live in separate sub-packages so that the physics
layer never imports the references (it must stand alone for export); equality is tested, not
shared code. `features/` (001) feeds both.

## Complexity Tracking

None.
