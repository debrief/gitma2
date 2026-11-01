---

description: "Task list for spec 002: references, physics layer, ONNX harness and gate P0"
---

# Tasks: References, Physics Layer and Gate P0

**Input**: `specs/002-references-physics-p0/` (spec, plan, research, data model, contracts)

**Tests**: required (constitution): conformance against gitma prediction fixtures, golden files,
gradient checks, runtime conformance.

## Phase 1: Setup and schema

- [x] T001 Add `torch` (CPU wheels index), `onnx`, `onnxruntime` to runtime deps; `uv lock`;
  `typings/` stubs only if needed
- [x] T002 Schema 0.17.0: `MetricsRecord` CRB/efficiency slots, `CurvePoint` efficiency,
  `ExperimentManifest.python_version/torch_version`, `GateId.P0`; regenerate types; data
  dictionary picks it up
- [x] T003 [P] Prediction fixtures are committed (`tests/fixtures/gitma/*/predictions/`); add
  `COMMIT` lines describing the commands; `scripts/make_fixtures.sh` extended

## Phase 2: References (US1)

- [x] T004 `references/lsq.py`: numba kernels `cost`, `normal_equations`, `solve4`,
  `levenberg_marquardt`, `grid_start`, `solve_batch` (gitma order preserved)
- [x] T005 `references/classical.py`: `bearing_data`, `row_at`, plausibility, `classical_predict`
  (final, per-timestep with gitma's restart rule); `eval/predictions.py` writer/reader with
  digest binding; `cli/solve.py`
- [x] T006 [P] `references/naive.py` + `cli/naive.py` (fit on train, predict)
- [x] T007 `references/ekf.py`: transition, Q, initialise from batch fit, predict/update (Joseph,
  symmetrise), re-initialisation loop, names; `references/imm.py`: CT/CV motion, FD Jacobians,
  mixing, likelihoods, combine, re-init; `cli/track.py`
- [x] T008 `tests/conformance/test_references.py`: rows vs fixtures (one-ulp rule, flags exact,
  residual counts); noise-free recovery test (G0 check 1 analogue) on a generated noise-free set

## Phase 3: CRB and evaluation (US4)

- [x] T009 `references/crb.py`: Fisher information at truth, delta-method bounds (full-window and
  per-leg), singular detection; `cli/crb.py`; unit test: on a synthetic linear-ish case the bound
  matches Monte-Carlo LS scatter within 10%
- [x] T010 `eval/{errors,slices,stats,metrics,bootstrap,rows}.py` ported from gitma; efficiency
  columns; `cli/eval.py` writing gitma's CSV/JSON (+ new columns); tests: metrics equal gitma's
  `tma-eval` output on the fixtures (fixture produced once with gitma, committed), bootstrap
  intervals reproducible and equal to gitma's on the same inputs

## Phase 4: Physics layer (US2)

- [x] T011 `physics/reference.py`: NumPy implementation of the fused-ridge piecewise-CV solve
  (banded normal equations, block-tridiagonal solve, branchless LM schedule, covariance)
- [x] T012 `physics/layer.py`: the same in torch (batched, masked, fixed K); `physics/segmentation.py`
  (`oracle_inputs`, `trivial_inputs` with the classical grid start)
- [x] T013 `tests/unit/test_physics_layer.py`: reference ≡ layer (1e-6); trivial inputs ≡ ported
  LS to float32 on fixture rows (converged and plausible); hard-knot ≡ piecewise fit; gradient
  checks (`torch.autograd.gradcheck` in float64); masking; `cli/oracle.py` (`tma2-oracle`)
- [x] T014 Oracle ceiling reproduction on the research note's setting: `tma2-oracle` with and
  without the speed prior on a seed-777 count-3000 regeneration, compared with the note's
  numbers (same seed, same IMM): ratios equal to 3 significant figures (the note's run used the
  SciPy script; agreement validates both)

## Phase 5: Export (US3)

- [x] T015 `export/toy_model.py` (2-layer MLP encoder over per-row features → changepoint/speed/
  log-weight heads → physics layer) and `export/onnx_export.py` (export opset 17, golden batch
  `.npy`, Python ORT comparison)
- [x] T016 `conformance/onnx/`: Node project with `onnxruntime-web` + Playwright test loading the
  model in Chromium (WASM EP) and comparing to the golden outputs; Java program + `pom.xml` with
  deferral message; CI job `onnx-conformance`

## Phase 6: Gate P0 (US5)

- [x] T017 `eval/experiment.py` (manifest, checks.csv, verdict) and `cli/p0.py` running: generator
  digests (001 fixtures), reference reproduction, physics ≡ LS, noise-free recovery, oracle ratios
  (when `--oracle-data`), export conformance result file; exit 3 on failure
- [x] T018 CI: `p0` job on `workflow_dispatch` and PR label `p0`: generate seed 301 (cached by
  digest), run IMM/LS/oracle, `tma2-p0`, upload the experiment folder as an artifact
- [x] T019 Run P0, commit `experiments/<date>-p0/`, run the agent panel (5 reviewers, rounds),
  commit `review.md`, set `decided_by` (P0 passed, panel round 3, `experiments/20261101-p0-r4/`)

## Phase 7: Site and docs (US6)

- [x] T020 [P] Algorithm notes: `physics-layer.md` (equations), `least-squares.md`, `ekf-imm.md`,
  `crb.md`; glossary entries; welcome page status
- [x] T021 [P] AGENTS.md: commands and gotchas from this spec; README status

## Phase 8: Polish

- [x] T022 Quickstart run end to end; PR description with decisions and numbers

## Carried to spec 003 (P0 panel rounds 2–3)

Entry conditions, to be met or pre-registered before spec 003's first decision record:

- `cov_ok` also fails when the trajectory passes within 1 m of ownship at any valid sample up to
  k, or a scaled pivot is within a multiple of the ridge; tested at the production iterations.
- The backward pass does not unroll 100 iterations (implicit-function or truncated backward,
  threads pinned); throughput measured against the batch budget (P0: 0.16 s and 72 MB per row
  unrolled).
- A deployable export: the iteration as an ONNX `Loop`, conformance 1e-5 in all three runtimes.
- Training and scoring exclude or down-weight undetermined rows (pre-zig, `cov_ok` false).
- Gate 2's oracle pre-registered: the chord oracle with the speed prior, reported with its
  efficiency against the known-manoeuvres bound.
- SRD Gate 1 efficiency criterion corrected (owner): error/CRB ≤ 1.25 on settled slices.

P0 tooling, before the next P0-style record:

- `check_physics_equals_ls` fails on a non-finite covariance (only range ≤ 1 m counts as
  degenerate), bounds the states of rows where the layer's cost is lower, and has a negative
  test with a crippled layer.
- `--experiment` must sit under `experiments/`; tests for an edit outside the folder and a commit
  during a run.
- The at-scale check asserts gitma's IMM header names the frozen IMM and the gitma pack's
  generator commit.
- The record carries the commands that made `data/p0` and ran the conformance legs.
