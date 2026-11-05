# Tasks: Steady-leg segmentation and Gate S

**Input**: `specs/005-steady-leg-segmentation/` (spec, plan, research R1–R8, data-model, contracts,
quickstart), re-planned for generator 0.6.0 (MAN2) on 2026-11-04.

**Data**: everything runs on MAN2 data with 720-row windows.
- **Validation:** seed 314, `data/man2-val`, with digests in
  `experiments/20261104-g0-man2/dataset-digests/`. Tune on its first 500 σ = 1° scenarios and
  score on the next 1,000, as note 08 did.
- **Gate S test:** seed 315, 10,000 scenarios. It is generated only after the decision record is
  committed.
- **L training stream:** seed 317.
- **Reserved:** seed 305 is never touched. Seeds 312 and 313 stay unused.

**Prerequisites from spec 006**:
- **T032:** the frozen MAN2 IMM and EKF.
- **T033:** the GLR + confirm reference on seed 314 (`experiments/<date>-man2-refs/`). It is S2's
  baseline and the record SC-002 must reproduce.

**Tests**: the success criteria are equalities (untrained L equals C, the oracle's gap recovered
is 1) and gradient checks, so test tasks are included.

**Format**: `[ID] [P?] [Story] Description with file path`. `[P]` means the task can run in
parallel: it touches different files and depends on no unfinished task.

**Story order**: the spec's priorities are US1 C, US2 scoring, US3 L and US4 O. US4 is
implemented before the decision record, because S1 needs O and its limit is fixed there, and
before US3, because L uses O's labels as input (FR-043).

## Phase 1: Setup

- [x] T001 Point `.specify/feature.json` at `specs/005-steady-leg-segmentation`. Re-plan for MAN2 in `plan.md`, `research.md` R6–R7, `quickstart.md` and `contracts/`: seeds 314, 315 and 317, and 720-row windows
- [x] T002 Bring the spec's stale 0.5.0 values in line with Annex B and MAN2, recorded under a "Session 2026-11-04 (MAN2 re-plan)" clarification in `specs/005-steady-leg-segmentation/spec.md` and in `data-model.md`'s SegmentParameters:
  - SegmentParameters: `course_tol_deg` 5.0, `speed_tol_kt` 0.5, `course_change_deg` (D) 10.0, `speed_change_kt` (D_S) 1.0, `l_min_rows` 30 (5 min), `t_min_rows` 6 (1 min); `t_lengths_rows` initially [6, 9, 12, 18, 24, 36], final value set by T010;
  - FR-062's frozen IMM becomes spec 006 T032's MAN2 IMM;
  - US2 scenario 3 and SC-002 reproduce the MAN2 reference record (spec 006 T033), not note 08's seed-304 figures;
  - FR-024 and SC-004 apply to prefixes of up to 720 bearings, with the 10 s budget re-confirmed or revised by T010 before the decision record;
  - the edge case "a target change while ownship is turning" now occurs in the data (13% of engagements), not only on constructed tracks.
- [ ] T003 [P] Create the package `src/tma2/segment/__init__.py`. Add the entry points `tma2-segment`, `tma2-segtrain` and `tma2-gs` to `pyproject.toml`, initially pointing at stubs that exit 2

## Phase 2: Foundational (blocking)

- [x] T004 Add the following classes to `schema/tma.yaml` and bump its minor version:
  - `SegmentInterval`: kind enum `steady|transition|unknown`, `start_index` ≥ 0, `end_index` ≥ `start_index` (inclusive), `open` bool;
  - `Segmentation`: `scenario_index`, vessel enum `ownship|target`, `prefix_row`, `intervals`, `cost`, `margin` (optional; null for O), `segmenter`, `segmenter_sha256`;
  - `SegmentParameters`: every field of data-model.md with its T002 defaults, and mode enum `gap|chord`;
  - `TruthLabels`, `GateSDecision` (the fields of `contracts/decision-record.md`) and `GateSRecord`.

  Then regenerate the types (`uv run python scripts/gen_types.py`) and the data dictionary (`scripts/data_dictionary.py`).
- [x] T005 Add a validator `tma2.segment.validate(seg, k)` in `src/tma2/segment/__init__.py`. It checks that the intervals tile [0, k] exactly, in order, without overlap; that steady intervals are ≥ `l_min_rows` and transitions ≥ `t_min_rows`, unless the interval is unknown or open; and that only the last interval may be open. Test it in `tests/unit/test_segment_validate.py`
- [x] T006 Check the physics layer's knot path at 720 rows; G0-MAN2 left it untested. Both checks use 50 seed-314 σ = 1° scenarios with ≥ 600 rows and every truth knot:
  - **Equivalence.** In `tests/unit/test_physics_knots_720.py`, compare `physics/layer.py` with `physics/reference.py` on `oracle_inputs` in both chord and masked-turn modes (relative range ≤ 1e-4, flags exact), and the gradients for finiteness.
  - **Export.** Add `--man2 --knots` to `src/tma2/export/onnx_export.py`: a golden batch with knots at 720 rows (k ≥ 480), conformance across Python, WASM and Java to 1e-5, and `inputs_sha256` bound. Add the CI step to `.github/workflows/ci.yml`.

  If either fails, fix the layer before T013 depends on it.
- [x] T007 [P] Implement truth labels in `src/tma2/segment/truth.py` (research R4):
  - **Target:** steady and transition from the generator's spans and the true track, at Annex B's tolerances.
  - **Ownship:** labels from the true course and speed, with wander inside ± C kept steady.
  - **Unknown:** rows before the first ownship zig ends.

  Add `tests/unit/test_segment_truth.py`, where labels match the span rows exactly on 20 seed-316 noise-free scenarios. Add a golden on the 0.5.0 fixture `tests/fixtures/gitma/phase4-seed777`.
- [x] T008 [P] Implement the metrics in `src/tma2/segment/metrics.py` (FR-060, FR-061, R7): contamination, coverage, false split, leg-count accuracy on detectable changes, boundary error at ± 60 s and ± 3 min, gap recovered (range and velocity, raw medians), and the live metrics (delay, false transitions per hour, boundary moves after acceptance). Add `tests/unit/test_segment_metrics.py`: the oracle gives contamination 0, coverage 1 and gap 1; one leg gives gap 0
- [x] T009 [P] Implement `Segmentation → LayerInputs` in `src/tma2/segment/inputs.py` (FR-030):
  - **gap:** knots at both ends, transition bearings masked;
  - **chord:** knots at both ends, bearings kept, the speed prior across course-only transitions.

  It reuses `detect/confirm.knot_inputs` and `physics/segmentation.oracle_inputs`. Add `tests/unit/test_segment_inputs.py`: the truth segmentation gives the same inputs as `oracle_inputs`.
- [x] T010 Re-measure research R1 on seed 314 and add an "R1 on MAN2" addendum to `research.md`: — done: research.md addendum "R1 and R3 on MAN2" (grid step 6, budget met at the margin)
  - **Cost table timing** at 720 rows: median and maximum per scenario, with nothing else running.
  - **Grid step** (3 or 6 rows) and `t_lengths_rows` from MAN2's transition-duration distribution (median 116 s).
  - **The verdict on the 10 s budget.** If the budget is exceeded, the grid or budget is revised here, before the decision record.

## Phase 3: User Story 1, classical segmenter C (P1)

**Goal**: C finds legs and transitions on each prefix, coupled-confirmed by the physics layer.

**Independent test**: on noise-free seed 316, transitions lie within ± 60 s on detectable changes and there is no false split (SC-001). Prefix invariance holds.

- [x] T011 [P] [US1] Move the search from `scripts/research/seg_search.py` into `src/tma2/segment/search.py`: the numba cost table, the DP over the lattice (steady ≥ `l_min_rows`, transitions in `t_lengths_rows`), and the per-leg penalty. Leave the script as a thin wrapper. Add `tests/unit/test_segment_search.py`: a constructed three-leg track is recovered, and the result matches the script's output on 20 seed-304 scenarios
- [x] T012 [US1] Implement the coupled nominate-and-confirm in `src/tma2/segment/confirm.py` (research R2):
  - **Nominations:** GLR alarm episodes (re-tested every `retest_rows` while raised) and the search's transitions.
  - **Confirmation:** each nomination is tested on its own prefix with `layer_costs`, searching the transition's start and length. A candidate is accepted when its drop exceeds `tau_4dof(tau)`.
  - **Polish:** accepted boundaries are then polished under the coupled cost.

  The machinery comes from `src/tma2/detect/confirm.py`, reused rather than copied.
- [x] T013 [US1] Implement C in `src/tma2/segment/segmenter.py`. Per prefix it runs the nominators and the confirmation, then builds the Segmentation. It labels as unknown any interval where the best and runner-up segmentations differ by less than the margin (FR-023), and it records cost and margin. Add an `evidence` hook that defaults to zero (for L)
- [ ] T014 [US1] Add `tests/unit/test_segment_c.py`, covering US1's acceptance scenarios on constructed noise-free engagements:
  - two target zigs inside one ownship leg give 3 legs and 2 transitions within ± 60 s;
  - no manoeuvre gives one leg;
  - a near-tie gives unknown;
  - prefix invariance: segmenting [0, k] with the later bearings deleted gives a byte-identical result;
  - before the zig, C never invents a transition;
  - a target change during an ownship turn is accepted with legs spanning it.
- [x] T015 [US1] Implement `tma2-segment` in `src/tma2/cli/segment.py` (`contracts/cli.md`):
  - options `--segmenter C|L`, `--params`, `--rows g5|all|<list>`, `--vessel`, `--workers` and `--work`;
  - a header record with provenance, parameters and `segmenter_sha256`;
  - one Segmentation per scenario, vessel and prefix row;
  - a cost-table cache keyed by commit and data digest, reused only from a clean tree;
  - exit 2 on refusals.
- [ ] T016 [US1] Run SC-001 on seed 316 noise-free (regenerate with `configs/man2-noise-free.json`, 1,000 scenarios). Record the timing per prefix on 720-row windows (SC-004). Write both to `experiments/<date>-gs-dev/sc001.md`

## Phase 4: User Story 2, scoring by downstream effect (P1)

**Goal**: every segmenter scored on the same rows against batch least squares, the frozen MAN2 IMM, the oracle and GLR + confirm.

**Independent test**: the oracle's gap recovered is 1 and one leg's is 0. GLR + confirm reproduces spec 006 T033's record to the printed precision (SC-002).

- [x] T017 [P] [US2] Add the reference segmentations in `src/tma2/segment/references.py`: oracle (from spans), one-leg, and GLR + confirm. GLR + confirm calls `scripts/research/leg_spike.py`'s confirm path through `detect/confirm.py`, at the configuration `glr:0.2:13.8` and the frozen MAN2 IMM recorded in T033
- [ ] T018 [US2] Implement `tma2-gs` in `src/tma2/cli/gs.py` (diagnostic mode):
  - **Scoring:** the same σ = 1° G5 rows and settled rows for every segmenter, with batch least squares and the frozen MAN2 IMM on those rows; downstream medians, P90, gross rates and known-manoeuvres efficiency.
  - **Intervals:** scenario-clustered paired bootstraps at 97.5% (2,000 resamples).
  - **Strata (FR-063):** detectability band, kind and size, transition duration, range band, change count, overlap with an ownship turn, and speed-only changes.
  - **Output:** `metrics.json` and `report.md`.
- [ ] T019 [US2] Add `tests/unit/test_gs.py`, using a 20-scenario fixture:
  - the oracle's gap recovered is 1 and one leg's is 0;
  - the strata partition the rows;
  - the bootstrap is deterministic for a fixed seed.
- [x] T020 [US2] Run SC-002 on seed 314's 1,000 scoring scenarios: GLR + confirm's ratios reproduce `experiments/<date>-man2-refs/spike.json` to the printed precision. Write the result to `experiments/<date>-gs-dev/sc002.md` — done: `experiments/20261104-gs-val/sc002.md` (ratios and intervals identical; all-row medians differ only by the median convention)
- [x] T021 [US2] Run the phase-1 validation measurements on seed 314 (tune on 500, score on 1,000). Write them to `experiments/<date>-gs-val/` (`metrics.json`, `README.md`): — done: `experiments/20261104-gs-val/` (penalty 30, mode gap, margin 0, S2 +0.632 [0.558, 0.734])
  - **Search penalty** at ≤ 5% false splits on the tuning scenarios (R1).
  - **Gap or chord**, the lower median range error over G5 rows, with ties going to the chord (R3, FR-031).
  - **Margin** (FR-023).
  - **S2 on validation:** C − GLR + confirm, gap recovered with its interval, and the S4 reference this implies.

## Phase 5: User Story 4, ownship legs O (P3; needed for S1 and as L's input)

**Goal**: ownship steady legs and turns from the recorded track, robust to wander and oscillation.

**Independent test**: O against the ownship truth labels on seed 314, with no transition called on wander or oscillation.

- [x] T022 [P] [US4] Implement O in `src/tma2/segment/ownship.py`, the two-pass detector of Annex B (FR-010–FR-013):
  - **Coarse pass:** 1-min moving averages, compared against D for course (wrap at 360°) and D_S for speed.
  - **Fine pass:** a walk to the sign change of the turn rate, or to the ± C band, with a delayed end.
  - **Turn test:** the signed-change test (net ≥ 90% of the total absolute change).
  - **Legs:** the ± C and ± S band, L_min and T_min, and 30 s trimmed from each end.

  It supersedes the penalised change-point search in research R5.
- [x] T023 [US4] Add `tests/unit/test_segment_ownship.py`, covering the constructed tracks of FR-014 and US4's scenarios. Extend `tests/unit/test_steady_leg.py`'s wander cases:
  - helm wander and autopilot oscillation inside ± C call no transition;
  - turns of 10–15° and 30° have their boundaries found;
  - one zig gives two legs and one transition within ± 30 s before trimming;
  - a course across 0°/360° calls no transition;
  - O agrees with `ownship_legs` on 0.5.0 fixture data.
- [x] T024 [US4] Run O on seed 314's ownship tracks: contamination (median, P90) on ownship legs per turn-size band (10–15°, 15–30°, ≥ 30°) and per wander kind. Write it to `experiments/<date>-gs-val/ownship.md`. This proposes the S1 limit (spec: 0.02) — done: `experiments/20261104-gs-val/ownship.json` (contamination 0; small-turn strata empty on MAN2)

## Phase 6: Pre-registration (blocks all L training and the test data)

- [x] T025 Confirm that SRD Annex A §A.9 (Gate S) is on `main`, merged by the owner (spec Assumptions). If it is not, stop and ask the owner one multiple-choice question — done: §A.9 is on main
- [x] T026 Write the plan `configs/segment/gs-plan.json`: — done: `configs/segment/gs-plan.json`
  - validation 314 with its digest;
  - L stream 317: `count` and `generator_git_commit`, with the shard digests recorded when the tables are made;
  - test seed 315: `--count 100000`, whose test split holds the 10,000 scenarios (80/10/10 by index; `--count 10000` would give 1,000), its digest filled at generation;
  - the evidence-network configuration and the loss weights (CRF 1.0, auxiliary 0.1).
- [x] T027 Commit the decision record `experiments/<date>-gs-decision/decision.json` (type `GateSDecision`) with a `README.md`: — done: `experiments/20261104-gs-decision/`
  - SegmentParameters, final (from T010, T021 and T024);
  - mode, gap normalisation `raw`, S1 and S3 limits, and the S2 validation outcome with the implied S4 reference;
  - the carried rule (median of three seeds by validation gap recovered in range) and the shuffled rule;
  - the seeds, a forecast for S1–S4, and the follow-on copied from Annex A §A.9.

  This must be committed before T029–T035.
- [x] T028 Generate seed 315 (`tma2-generate --seed 315 --count 100000 --ranges configs/man2-ranges.json --heldout-ranges configs/man2-heldout.json --format f32pack`) at a clean commit after T027. Commit its digests to `experiments/<date>-gs-decision/seed315-digests.json`. Do not open or score it until T038 — done: generated at a38f61b; digests in `experiments/20261104-gs-decision/seed315-digests.json`

## Phase 7: User Story 3, learned segmenter L (P2)

**Goal**: L adds per-bearing evidence to C. Untrained, it equals C; trained, it is credited only if it recovers more of the gap than the reference.

**Independent test**: untrained L equals C byte for byte (SC-003). The first step's gradient is non-zero. The shuffled control is not better than C.

- [x] T029 [P] [US3] Implement the semi-Markov forward recursion in `src/tma2/segment/crf.py` (log-sum-exp, the R6 lattice). It covers the truth path's score, the negative log-likelihood, and the auxiliary per-bearing term at 0.1. Add `tests/unit/test_segment_crf.py`: the gradient at zero evidence matches finite differences and is non-zero, and the normaliser equals brute-force enumeration on a 30-row toy
- [x] T030 [P] [US3] Implement the evidence network in `src/tma2/segment/evidence.py`:
  - **Inputs (FR-043):** the per-bearing features, O's labels and C's residuals, normalised from inputs only.
  - **Architecture:** a small causal 1-D convolution, or the Gate 1 encoder, with no GELU and attention written out (export rules). The head is zero-initialised, with no dying ReLU before it.
- [x] T031 [US3] Wire L into `segment/segmenter.py`:
  - **Search:** the evidence is added to the search costs.
  - **Confirmation:** the threshold shifts by twice the evidence summed over the candidate's rows, capped at ± τ/2.

  Add `tests/unit/test_segment_l.py`: an untrained L's segmentations equal C's byte for byte on 50 seed-314 prefixes (SC-003). Also run the full validation check with `tma2-segment --segmenter L`.
- [x] T032 [US3] Add a cost-table workflow, `.github/workflows/segment-tables.yml`. It generates seed 317 at the plan's commit, writes per-shard `.npz` tables (not committed) as workflow artefacts or a `tables/` results branch, and records shard digests in the plan — done as `.github/workflows/segtrain.yml` (tables jobs: seed 317 in eight shards plus validation tables; per-shard digests in each results branch)
- [x] T033 [US3] Implement `tma2-segtrain` in `src/tma2/cli/segtrain.py`: — done: `tma2-segtrain`; tests in `tests/unit/test_segtrain.py`; throughput about 18 min per epoch over 10,000 scenarios on one runner thread (`experiments/20261105-segL-val/README.md`)
  - per-epoch checkpoints with Adam state, in the spec 003/004 layout;
  - weights bound by SHA-256;
  - early stopping with a relative minimum improvement;
  - `--shuffled`;
  - `git_dirty` in the job record.

  Add `tests/unit/test_segtrain.py`: separate processes give byte-identical results, resume equals uninterrupted, and the head stays alive after a small run. Measure the throughput: one epoch over 10⁴ scenarios in under an hour on four cores.
- [x] T034 [US3] Add the training workflow `.github/workflows/train-segL.yml` on `train/segL` branches, following the spec 003 pattern. It runs three seeds and the shuffled control, pushing to `results/segL-<run id>`. Push the branch and fetch the results — done as `segtrain.yml` on `segtrain/**` (`train/**` belongs to train.yml): run 41923847724, `results/segL-41923847724`
- [x] T035 [US3] Export L's evidence network to ONNX (fixed 720-row window, dynamic batch) in `src/tma2/segment/evidence.py`. Check conformance across Python, WASM and Java to 1e-5, with `inputs_sha256`. Add the CI step — done: `segment/evidence_export.py` (convolutions as MatMul: onnxruntime has no double Conv); Python and WASM legs 1.3e-15 locally, WASM 91 ms for four windows; Java leg in CI. The carried weights are exported with `--weights` after T036
- [x] T036 [US3] Run validation diagnostics for the three seeds and the control (`tma2-gs`, no decision) in `experiments/<date>-segL-val/`. Apply the carried rule, then freeze the carried weights by digest — done: `experiments/20261105-segL-val/`; carried segL-s3 (`carried.json` beside the decision); shuffled rule passes; no seed beats C on validation

## Phase 8: Gate S

- [x] T037 Add gate mode to `tma2-gs` (`--decision --plan --split test`): — done (f8e7709): `segment/gate.py`, `tma2-gs --decision --plan --split`; smoke on 4 validation scenarios ran end to end (exit 3, manifest clean, amendments listed). L carried weights come from `carried.json` beside the decision (T036)
  - **Refusals:** a decision whose seed, plan, data digest or weights digest does not match the inputs.
  - **Outputs:** `verdict.json` with S1–S4, and `manifest.json` with every digest, the amendments and `git_dirty`.
  - **Exit code:** 3 unless every criterion passes.

  Add `tests/unit/test_gs_gate.py`, covering the refusals and the pass, fail and inconclusive logic of FR-071.
- [x] T038 Score Gate S on seed 315 at a clean commit: C, L (carried), GLR + confirm, the oracle, one leg, batch least squares and the frozen MAN2 IMM, all on the same rows. Write the results to `experiments/<date>-gs/` — done: `experiments/20261105-gs/` at e648f8b; S1–S3 pass, S4 inconclusive, reference C
- [ ] T039 Convene the agent review panel: five or more read-only reviewers (geometry, numerics, statistics, reproducibility, red team), in rounds until no reviewer rejects and no blocker or major finding is open. Commit `experiments/<date>-gs/review.md` and set `decided_by`. Then apply the follow-on of FR-072

## Phase 9: Polish

- [x] T040 [P] Write the site pages:
  - an algorithm note on C, L and the gap or chord handover in `site/docs/`;
  - glossary terms (contamination, coverage, gap recovered, nomination, confirmation, semi-Markov likelihood) in `site/docs/glossary.md`;
  - the Gate S write-up in `site/blog/`.

  Then run `(cd site && npm ci && npm run build)`.
- [x] T041 [P] Update `AGENTS.md`: the status of spec 005 and Gate S, the seeds used, and new gotchas
- [x] T042 Run `quickstart.md` end to end and fix any drift — done: rewritten to the commands as built (test files, `--params` from the plan, `tma2-segtrain tables`/`train`, `tma2-gs` inputs, CI and gate sections); each local step run on 2–3 scenarios; `tables` now creates its output folder

## Dependencies

- **Phase 1 → Phase 2 → US1 → US2.** T017 and T020–T021 need spec 006 T032/T033.
- **US4** depends only on Phase 2 and runs alongside US1 and US2.
- **Phase 6** needs T010, T021 and T024.
- **US3** needs Phase 6. T028 needs T027.
- **Gate S** needs US3 and T028.

## Parallel examples

- **Phase 2:** T007, T008 and T009 run together once T004 is in.
- **US1 and US4:** T011 and T022 run together.
- **US3:** T029 and T030 run together; T032 runs on CI while T033 is written.

## Implementation strategy

- **MVP: US1 and US2.** C scored against GLR + confirm on validation is a deliverable on its own (owner: "C alone is an acceptable deliverable"). It also answers S2 before any learning.
- **Then** O, the decision record and L.
- **Gate S last**, with the test seed generated only after the record.
