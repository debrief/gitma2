# Tasks: Generator 0.6.0, the MAN2 simulation model

**Input**: `specs/006-generator-man2/` (spec, plan, research R1–R7, data-model, contracts, quickstart)

**When**: implementation starts after PR 12 (documents only: Annex B, the MAN2 decisions, specs 005
and 006) is merged by the owner, on `claude/inspiring-curie-j192v9` restarted from `main`.

**Tests**: the spec's success criteria are byte-identity, distributional checks and a gate, so
test tasks are included. Golden files for 0.5.0 are never regenerated; new MAN2 goldens are added.

**Format**: `[ID] [P?] [Story] Description with file path`. `[P]` = parallelisable (different
files, no dependency on an unfinished task).

## Phase 1: Setup

- [ ] T001 Restart the branch from `origin/main` after PR 12 merges; set `.specify/feature.json` to `specs/006-generator-man2`
- [ ] T002 [P] Add `configs/man2-ranges.json` (phase-4 ranges with `window_s` 2400–7200, `target_turn_rate_rad_s` 0.25–1°/s, `target_speed_change_rate_mps2` 0.01–0.05, `target_leg_length_s` {mean 1500, sd 546, min 300}, `target_change_kind_weights` {course 0.8, speed 0.1, both 0.1}, `ownship_wander` {sd 1.5°, tau 60 s, clip 4°}, `ownship_oscillation` {amp 1–3°, period 120–360 s}, `ownship_wander_weights` {none 0.4, wander 0.3, oscillation 0.3, both 0}; no count weights, spacing, after-zig or margin), `configs/man2-heldout.json` (range 20–30 km) and `configs/man2-noise-free.json` (σ = 0, no dropouts)

## Phase 2: Foundational (schema and layout)

- [ ] T003 Add to `schema/tma.yaml` (version 0.22.0): `ParameterRanges.target_leg_length_s` {mean, sd, min; all > 0}, `target_change_kind_weights` {course, speed, both; ≥ 0}, `ownship_wander` {sd_rad, tau_s, clip_rad}, `ownship_oscillation` {amp_rad {min, max}, period_s {min, max}}, `ownship_wander_weights` {none, wander, oscillation, both}; a new `OwnshipWander` class (kind enum none|wander|oscillation|both; sd_rad, tau_s, clip_rad, amp_rad, period_s, phase_rad optional); scenario header fields `ownship_wander: OwnshipWander?` and `zig_on_manoeuvre: bool`; `ManoeuvreSpan.kind` enum gains `both`
- [ ] T004 Regenerate types with `uv run python scripts/gen_types.py` and the data dictionary with `scripts/data_dictionary.py`; commit `src/tma2/types/generated/` and `site/docs/data-dictionary.md`
- [ ] T005 Extend the flat layout in `src/tma2/sim/ranges.py`: new `R_*` slots after `R_TM_SPACING` (leg mean/sd/min; three kind weights; wander sd/tau/clip; oscillation amp min/max, period min/max; four wander weights), `R_LEN` updated, `flatten_ranges` fills them (NaN when absent); `validate_ranges` raises `RangesError` with the three messages of `contracts/cli.md`
- [ ] T006 Set `MAX_TM = 24` in `src/tma2/sim/scenario.py`, `MAX_COUNT_WEIGHTS` unchanged; confirm `src/tma2/features/batch.py` and `src/tma2/sim/generate.py` size their tables from `sc.MAX_TM` and that `Batch.tm`/`spans` docstrings say 24
- [ ] T007 Bump `GENERATOR_VERSION` to "0.6.0" in `src/tma2/sim/version.py` and add it to `READABLE_GENERATOR_VERSIONS` in `src/tma2/data/versions.py`; run `uv run pytest -q tests/golden tests/conformance` and confirm every 0.5.0 golden and gitma fixture still passes (header version is excluded from digests as before; if any golden embeds the version string, update only that string and say so in the commit)

## Phase 3: User Story 1, nothing already generated changes (P1)

**Goal**: 0.5.0 (and earlier) ranges reproduce byte for byte under 0.6.0.

**Independent test**: golden and gitma-conformance suites pass; seed 304's validation split regenerates with the committed digest.

- [ ] T008 [US1] Add `tests/golden/test_generator_060_identity.py`: generate 200 scenarios of `tests/fixtures/gitma/phase4-seed777/ranges.json` and of the iteration-1 and 0.3.0 fixture ranges with seeds 777 and 304, assert arrays equal to the pre-0.6.0 generator's committed outputs (reuse the existing golden fixtures' arrays), and assert `TI`/`spans` padding beyond `n_spans` is −1 with `MAX_TM = 24`
- [ ] T009 [US1] Add to `tests/unit/test_ranges.py`: the three new validation errors fire; a ranges file without new fields flattens to NaN in the new slots; `rows_for` gives 720 for `configs/man2-ranges.json`
- [ ] T010 [US1] Regenerate seed 304 with `tma2-generate` on the phase-4 fixture ranges into a scratch directory and compare `digests.json` with `data/gd-val`'s committed digests; record the command and result in `experiments/<date>-g0-man2/README.md` (created in T030)

## Phase 4: User Story 2, target legs follow the owner's model (P1)

**Goal**: the leg model, kinds, slower transitions and changes during ownship turns.

**Independent test**: `tma2-ranges --describe configs/man2-ranges.json --sample 10000 --seed 314` reports leg quantiles ≈ 10/25/40 min, 4–6% ≤ 10 min, median transition 60–180 s, ≥ 60% of engagements with ≥ 2 changes.

- [ ] T011 [US2] In `src/tma2/sim/scenario.py` add `plan_target_legs(seed, attempt, R, P, tm, rmax) -> int` on stream `create_rng(derive_seed(scenario_seed, 2 + 2*attempt))`: first start = −U·L₁; loop: L ~ N(mean, sd) clipped at min (Box–Muller via `gaussian`), kind by weights, then sign, |angle| (0.5.0 range), turn rate; or sign, Δv, acceleration (flip sign if out of speed range, drop if neither fits); or both; append to `tm` (TM_KIND 0/1/2, TM_START = f32(start·dt rounded to a row)) until the next start ≥ window end or `MAX_TM` reached; return n_plan; set `P[P_N_TM]`
- [ ] T012 [US2] Wire it in `generate_into`/`draw_scenario`: when `R[R_LEG_MEAN]` is not NaN, skip `draw_manoeuvre_count` and `plan_target_manoeuvres` (they already no-op with no weights) and call `plan_target_legs` after the main-stream draws of `draw_scenario`, per attempt; keep the 0.5.0 path byte-identical (no new call when the field is absent)
- [ ] T013 [US2] Extend `target_manoeuvres` for kind 2: inside the span integrate position with 1 s sub-steps along an arc of rate `rate` while speed changes linearly at `acc` (both drawn into `tm` via two extra columns `TM_CHANGE2`, `TM_RATE2`; table width 6), span length = max(turn duration, acceleration duration); after the span continue analytically from the integrated end state; kinds 0 and 1 unchanged
- [ ] T014 [US2] Record spans with kind 2 in `spans` and in the header's `manoeuvres` (kind "both"); `src/tma2/sim/generate.py` maps kind codes 0/1/2 to course/speed/both
- [ ] T015 [US2] Zig planning (research R3): when the leg model is on, in `plan_manoeuvres` take the target position at the zig row from a target-only simulation of the planned legs (new `simulate_target_only`), not from `target_at`; set `zig_on_manoeuvre` when the zig row falls inside a span; 0.5.0 path unchanged
- [ ] T016 [P] [US2] Unit tests `tests/unit/test_leg_plan.py`: on 10,000 planned scenarios the complete-leg lengths pass a KS test against N(1500, 546) truncated at 300 (p > 0.01); 4–6% ≤ 600 s; kind shares within ±2 pp of 0.8/0.1/0.1; a speed change never leaves the speed range; the first change's phase is uniform (KS p > 0.01); the plan is identical across two calls with the same seed and differs with `attempt`
- [ ] T017 [P] [US2] Unit test `tests/unit/test_both_kind.py`: a kind-2 span's end position, course and speed match the 1 s integration to 1e-6 relative, and with acceleration 0 equal the kind-0 analytic arc to 1e-9
- [ ] T018 [P] [US2] Unit test `tests/unit/test_zig_plan_man2.py`: with a target change before the zig, the across-LOS zig computed from the simulated target position satisfies the LOS-offset relation at the zig row; `zig_on_manoeuvre` is set exactly when the zig row is inside a span
- [ ] T019 [US2] Add `src/tma2/cli/ranges.py` (`tma2-ranges --describe <ranges> [--sample n --seed s]`) per `contracts/cli.md`, registered in `pyproject.toml`; unit test `tests/unit/test_ranges_cli.py` on `configs/man2-ranges.json` with `--sample 2000`
- [ ] T020 [US2] New golden `tests/golden/test_man2_golden.py` with fixture `tests/fixtures/man2-seed316/` (50 noise-free scenarios, f32pack + digests) generated once from a clean tree; the test regenerates and compares byte for byte

## Phase 5: User Story 3, ownship wanders inside the band (P2)

**Goal**: helm wander and autopilot oscillation on the recorded ownship track, separable from everything else.

**Independent test**: every wander row within 5° of the leg course; a scenario regenerated with weights {none: 1} differs only in the ownship arrays.

- [ ] T021 [US3] In `src/tma2/sim/scenario.py` add `draw_wander(seed, attempt, R) -> (kind, params)` on stream `derive_seed(scenario_seed, 3 + 2*attempt)` and `apply_wander(P, kind, params, own_x, own_y, own_c, TI, s_w)`: per steady leg (rows before `TI_TURN_START`, between `TI_ZIG` and the second turn, after it), course error = AR(1) (ρ = exp(−dt/τ), innovations from the wander stream, clipped) and/or sinusoid; positions re-integrated with the trapezoid of the wandered course from the leg's entry point; turns keep the planned arc from the actual entry point; called from `simulate_truth` only when kind ≠ none
- [ ] T022 [US3] Header: write `ownship_wander` (kind and drawn parameters) per scenario in `src/tma2/sim/generate.py`; `zig_on_manoeuvre` from T015
- [ ] T023 [P] [US3] Unit test `tests/unit/test_wander.py`: 500 MAN2 scenarios: for every wander row |recorded − planned course| ≤ 5°; positions equal the trapezoid integral of the recorded course to 1e-6 m; regenerating with `ownship_wander_weights` {none: 1} leaves `tgt`, `bearing`, `valid`, `spans` and the header's manoeuvres identical and changes only `own`; wander kinds drawn within ±3 pp of 0.4/0.3/0.3
- [ ] T024 [US3] Confirm `ownship_legs` in `src/tma2/detect/steady_leg.py` still finds the planned turns on wander tracks with a tolerance argument (document: spec 005's O replaces it for wander data); add a test case in `tests/unit/test_steady_leg.py`

## Phase 6: User Story 4, the pipeline still passes and references are re-frozen (P2)

**Goal**: 720 rows carried through; seeds generated; the gate passed by panel; references frozen.

**Independent test**: `tma2-p0` on MAN2 exits 0 with a panel-approved `review.md`; `experiments/<date>-man2-tune/` names the frozen IMM and EKF; `experiments/<date>-man2-refs/spike.json` exists.

- [ ] T025 Parameterise `R_MAX` in `src/tma2/cli/p0.py` from the experiment's ranges (`rows_for`) and in `src/tma2/export/onnx_export.py` via `--rows` (default 360); the Gate 1 model export already uses `rows_for(ranges)`
- [ ] T026 [P] Add the 720-row conformance artefact: `onnx_export --rows 720` in `.github/workflows/ci.yml` beside the 360-row one; both run through `conformance/onnx/wasm_leg.mjs` and `java_leg.py`; record timing in the job summary
- [ ] T027 [US4] Restate the before-manoeuvre check in `src/tma2/cli/p0.py` for ranges with `target_leg_length_s`: "on the zig leg" (research R3): find the steady target leg containing the ownship zig's end row; fit batch least squares on that leg's rows; require noise-free recovery at its last row; skip and count legs ending within 30 rows of the zig; report `zig_leg_skipped` in `checks.json`
- [ ] T028 [US4] Generate from a clean tree: seed 314 (10,000) with `configs/man2-ranges.json` → `data/man2-val`; seed 316 (10,000) with `configs/man2-noise-free.json` → `data/man2-g0`; seed 315 (10,000) → `data/man2-test` (reserved, digests only committed); commit `digests.json` files under `experiments/<date>-g0-man2/data/` with the generating commit; record that 312/313 are unused
- [ ] T029 [US4] Measure and record kernel throughput at 720 rows (`tma2-generate` on 10,000 scenarios, f32pack) and physics-layer cost per solve at 360 vs 720 rows (batch 64, 4 threads) in `experiments/<date>-g0-man2/throughput.json`
- [ ] T030 [US4] Run `tma2-p0 --experiment experiments/<date>-g0-man2 --oracle-data data/man2-val` on MAN2 (generator conformance, references, physics ≡ LS, noise-free recovery incl. the zig-leg check, efficiency, throughput, oracle, IMM at scale, export at 720 rows); fix what fails; write `README.md`
- [ ] T031 [US4] Agent review panel on the gate (≥ 5 reviewers: TMA geometry, estimation and numerics, evaluation statistics, reproducibility, red team); respond; repeat until no blocker or major is open; commit `review.md`; set `decided_by`
- [ ] T032 [P] [US4] Re-tune the IMM and EKF on `data/man2-val/validation.f32pack` with spec 004's grids via `tma2-tune`; freeze by name; commit `experiments/<date>-man2-tune/` (grids, results, frozen names, git commit)
- [ ] T033 [P] [US4] Re-run note 08's reference on seed 314: `scripts/research/leg_spike.py stats|confirm|report` with `--configs glr:0.2:13.8` (tuning on the first 500 σ = 1°, scoring on the next 1,000), using the frozen MAN2 IMM from T032; commit `experiments/<date>-man2-refs/spike.json`, the detectability quantiles and a README with the baseline ratios spec 005's S2 will cite

## Phase 7: Polish

- [ ] T034 [P] Update `AGENTS.md` (generator 0.6.0, MAN2 ranges, seeds 314/315/316, the zig-leg check, the two gotchas: streams 2/3 per attempt, kind-2 sub-stepping) and `docs/SRD.md` §2's MAN2 row if any value changed
- [ ] T035 [P] Site: glossary entries (steady leg, transition, MAN2, helm wander, autopilot oscillation), data dictionary regenerated, and a short blog write-up `site/blog/<date>-generator-060.md` with the measured leg and transition distributions
- [ ] T036 Run `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q` and `(cd site && npm run build)`; open the PR with the colleague decisions listed (leg reading, kind weights, rates, wander parameters, zig-leg check) for the owner to overrule

## Dependencies

- Phase 2 (T003–T007) blocks everything after it.
- US1 (T008–T010) needs T007; it is the byte-identity guard and should pass before US2 lands.
- US2: T011 → T012 → T013 → T014 → T015; T016–T018 after T015; T019 after T012; T020 after T015 and T021 (goldens include wander).
- US3: T021 after T012 (shares `simulate_truth`); T022 after T021; T023 after T022; T024 any time after T021.
- US4: T025–T026 independent of US2/US3; T027 after T015; T028 after T020 and T023 (clean tree, final kernel); T029 after T028; T030 after T027–T029; T031 after T030; T032–T033 after T028 (T033 also after T032 for the frozen IMM).
- Polish after US4.

## Parallel opportunities

- T002 with T003–T007.
- T016, T017, T018 together once T015 is in.
- T023 with T016–T018.
- T025 and T026 with all of US2/US3.
- T032 and T033 with T030/T031 (T033 waits only for the frozen IMM).
- T034 and T035 together.

## Implementation strategy

- **MVP** is US1 + US2 without wander: the leg model behind its field, byte-identity proved, and
  `tma2-ranges --describe` showing the owner the distribution they asked for. That alone lets
  the owner confirm or correct the normal reading before any data is frozen.
- Then US3 (wander), then US4 (data, gate, references), which is where the clock time goes: the
  gate's panel rounds and the IMM re-tune.
- Spec 005's decision record waits for T032 and T033.
