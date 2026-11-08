# Tasks: Gate 2 on MAN2

**Input**: `specs/007-gate2-man2/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: requested by the spec (FR-022, FR-023, SC-002) and by the plan. They are written
before the code they test, wherever marked.

**CI**: tasks marked **(CI)** run on GitHub runners, because container restarts kill local jobs
of more than a few minutes (AGENTS.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[USn]**: user story from spec.md

## Phase 1: Setup (prerequisites from Gate S)

- [x] T001 **(CI)** Record the open-transition hand-over choice from `results/score-c3-val-*`
  (`configs/score/c3-val.json`):
  - choose by the lowest median range error over σ = 1° G5 rows among `C-gap-knot_at_k`,
    `C-gap-start_masked` and `C-gap-start_chord`;
  - report `by_open_at_k`, gap recovered, gross rates, efficiency and the paired `gap_minus`
    between the three;
  - compare with `experiments/20261105-gs-r2-val/c` (C-gap 0.891; S2 +0.632);
  - commit `experiments/20261106-c3-val/` (metrics, report, plan, run, inputs, README with the
    choice and a one-line reason);
  - update spec FR-002's note and research R5. — done: `experiments/20261106-c3-val/` — `knot_at_k` (ties `start_masked` on median range 0.120299; best on the 210 open-at-k rows, 0.695; spec 005's default, parameter digest unchanged). C re-validated: gap recovered 0.891, S2 +0.632
- [x] T002 Raise the physics layer's knot cap to 12 for Gate 2. Construct `PhysicsLayer(knots=12)`
  in the new `tma2.gate2` code and in `tma2-g2`, leaving Gate S's code paths unchanged. Test in
  `tests/unit/test_gate2_knots.py` that 10 knots on a fixture prefix are all active, and that an
  8-knot input gives the same state at caps 8 and 12. — done: `tma2.gate2.KNOTS = 12`; `tests/unit/test_gate2_knots.py` (all ten knots used at cap 12, two dropped at cap 8, equal states with eight)
- [x] T003 **(CI)** Nominator ceiling (research R1):
  - add `--extra-nominations truth` to `tma2-segment` (`src/tma2/cli/segment.py`): extra
    nominations at the true change starts, a diagnostic that refuses any test split;
  - segment validation ordinals 500–1499 on CI with plan `configs/segment/c3-val-truthnom.json`;
  - score it beside C (`configs/score/c3-val-truthnom.json`);
  - record the gain in `experiments/20261106-nominator-ceiling/README.md`. Form (a) is built only
    if the gain is ≥ +0.02 in gap recovered. — done: `experiments/20261106-nominator-ceiling/` — ceiling − C +0.0164 [+0.0071, +0.0277] in range, below the +0.02 rule: form (a) not built

## Phase 2: Foundational

- [x] T004 Add the LinkML types (data-model.md) to `schema/tma.yaml` and regenerate (schema
  0.25.0; update `tests/unit/test_types.py`'s version pin):
  - `EModelConfig` (encoder, `extra_channels`, `weight_bound`, `knots`, `evidence_network`,
    `temperature`, `components`);
  - `ETrainingPlan`;
  - `DecisionTableHeader`;
  - `EPredictionHeader`;
  - `Gate2Decision`;
  - `Gate2Record` and `Gate2Verdict`. — done: schema 0.25.0 (`EComponent`, `EModelConfig`, `DecisionTableHeader`, `EPredictionHeader`, `Gate2Decision`, `Gate2Verdicts`, `Gate2Record`); the training plan stays a plan file with typed `EModelConfig` entries, as Gate S's
- [x] T005 [P] Create the package skeleton `src/tma2/gate2/__init__.py` with module docstrings for
  `model.py`, `inputs.py`, `tables.py`, `loss.py`, `train.py`, `predict.py` and `gate.py` (plan,
  Source Code). — done: `src/tma2/gate2/__init__.py`; modules added as each task implements them
- [x] T006 Implement `src/tma2/gate2/inputs.py`: per-prefix physics inputs from a C segmentation,
  using `segment.inputs.segmentation_inputs` with the chosen `open_handover`. Learned
  log-weights are added to C's hand-over mask. Also C's per-row code channel at prefix k,
  computed causally. — done: `gate2/inputs.py` (`prefix_inputs`, `code_channel`), `tests/unit/test_gate2_inputs.py`

## Phase 3: User Story 1, a classical control that is fixed before learning starts (P1)

**Goal**: C frozen by parameter and code digest; refusals.

**Independent Test**: the gate refuses a segmentation whose `segmenter_sha256` or `code_sha256`
differs from the decision's.

- [x] T007 [US1] Write the test first (`tests/unit/test_gate2_refusals.py`): `tma2.gate2.gate`'s
  input check refuses a segmentation header with another parameter digest, another code digest,
  another dataset digest or `git_dirty: true`. — done: `tests/unit/test_gate2_refusals.py`
- [x] T008 [US1] Implement the input checks in `src/tma2/gate2/gate.py` (as
  `segment/gate.py: check_inputs`, adding `code_sha256` and `weights_sha256` for E). — done: `gate2/gate.py` (`check_segmentation`, `check_prediction`, `RefusedError`)
- [x] T009 [US1] **(CI)** Segment the training stream with C at the frozen code:
  - generate seed 318 (`--count 12500`, MAN2 ranges) at a clean commit;
  - commit its digests to `experiments/<date>-g2-stream/seed318-digests.json`;
  - plan `configs/segment/g2-stream-c.json` (all σ = 1° train-split scenarios, 16 shards,
    `params_from` the Gate 2 plan, the chosen `open_handover`);
  - push `segment/g2-stream-c`.
  - Done at C's final code (2a5cf1c, code `4d2c084f…`): `results/segment-g2-stream-c-42268365081`,
    9,930 scenarios, 39,054 G5 prefixes, clean tree (count 25,000; the stream at 12,500 had too
    few σ = 1° scenarios). Validation at the same code: tuning 0–499
    `results/segment-c3-val-tune-42268374366`, scoring 500–1499 `results/segment-c3-val-42268379557`.
    C's baseline there with 12 knots (`results/score-g2-val-c-42288140230`): gap recovered 0.890
    [0.869, 0.909] (Gate S, 8 knots: 0.891), range/IMM 0.223 [0.200, 0.247], no estimate on 0.6%.

## Phase 4: User Story 2, a learned model trained end to end where C makes its decisions (P1)

**Goal**: E-w, then E-s, untrained equal to C, trained on CI.

**Independent Test**: untrained E reproduces C (SC-002); the causal cut test; finite gradients.

### Tests first

- [x] T010 [P] [US2] `tests/unit/test_gate2_model.py`:
  - untrained E-w on C's segmentation gives the same state as `segment.score.layer_errors`'s
    input path for C, to 1e-12, on 3 fixture scenarios;
  - gradients of the loss to every parameter are finite. — done: `tests/unit/test_gate2_model.py` (untrained E-w equals the physics layer on C's inputs bit for bit; finite gradients; the init head has no gradient under implicit differentiation and is trained by the auxiliary initial-state loss)
- [x] T011 [P] [US2] `tests/unit/test_gate2_causal.py`: E's output at row k is unchanged when the
  scenario is cut to rows 0…k (arrays truncated, not masked), on a fixture scenario with an open
  transition at k. — done: `tests/unit/test_gate2_causal.py` (random heads, a transition open at k: state identical with the arrays cut at k)
- [x] T012 [P] [US2] `tests/unit/test_gate2_tables.py`:
  - for a decision C accepted, the table's "with" error equals the error of C's own segmentation
    at those rows;
  - for a rejected decision, the "without" error equals it;
  - the relaxed loss at evidence 0 and T → 0 equals C's error.
  - Done: also the round trip and the refusals. Only decisions within τ/2 of their threshold get
    rows (the shift cap means no evidence can flip the others; their rows are constants).

### E-w

- [x] T013 [US2] Implement `src/tma2/gate2/model.py` E-w:
  - a `models.gate1` encoder over features plus the C code channel;
  - a weight head (tanh × `weight_bound`) and an initial-state correction head, zero last layers;
  - `PhysicsLayer(knots=12)` with implicit differentiation, on `gate2.inputs`. — done: `gate2/model.py` (`EWeights`: the Gate 1 encoder with C's code channel, weight and init heads, `PhysicsLayer(knots=12)`; the start correction applied as a difference so zero heads are exact)
- [x] T014 [US2] Implement `src/tma2/gate2/loss.py` (research R4):
  - the bound-normalised per-component error against the truth state (known-manoeuvres bound,
    `crb_known_manoeuvres_fast`);
  - each prefix clipped at the cap (100);
  - prefixes excluded whose physics-layer cost exceeds 20 × their valid bearings;
  - the trimmed mean (10% tails) for validation. — done: `gate2/loss.py` (`e_loss`: known-manoeuvres-bound-normalised (log range, vx, vy), cap, failed-fit exclusion at 20 × valid bearings, auxiliary initial-state term; `trimmed_mean`), `tests/unit/test_gate2_loss.py`
- [x] T015 [US2] Implement `src/tma2/gate2/train.py` and `src/tma2/cli/g2train.py` (`tma2-g2train
  train`):
  - examples are each scenario's G5 prefixes plus 2 seeded sampled prefixes per epoch;
  - 4 worker processes at 1 thread each;
  - checkpoints with Adam state and meta (`weights_sha256`, `cpu_model`, `git_dirty`) after every
    epoch; resume; the wall budget;
  - early stopping on the robust loss (patience 3, relative 1e-3);
  - the shuffled control trains on another scenario's truth labels. — done: `gate2/train.py` (prefix tables with C's hand-over, code channel, truth and known-manoeuvres bound; seeded batches; implicit differentiation; robust validation; checkpoints with SHA-256, CPU model and resume; the shuffled control moves another prefix's relative target onto this one), `cli/g2train.py` (`tables`, `train`), `tests/unit/test_gate2_train.py`. Training uses the G5 prefixes only (C segments G5 rows), not 2 extra sampled prefixes
- [x] T016 [US2] Measure the throughput on one runner **(CI)**: one epoch over 1,000 stream
  scenarios with `configs/gate2/throughput.json`. Record seconds per prefix and per epoch in
  research R4.
  - Done: 254 s for 3,905 prefixes with validation (about 65 ms per prefix); a full epoch is
    about 45 min, so g2-a's `max_epochs` is 12.

### E-s

- [x] T017 [US2] Implement `src/tma2/gate2/tables.py` and `src/tma2/cli/dtables.py`
  (`tma2-dtables`, contracts/cli.md):
  - re-run C's confirmation per scenario and record each decision (row a, start, length, source,
    drop Δ, threshold τ′, affected scored rows);
  - record the bound-normalised error with and without the transition, holding C's other
    decisions fixed;
  - write npz with `DecisionTableHeader`;
  - refuse segmentations with other digests.
  - Done: C runs in `tma2-segment`'s chunks (16, padded to the longest), so a shard equal to
    the segmentation run's reproduces it; `c_mismatch_rows` in the header records any difference.
    It also refuses a checkout whose code digest is not the plan's C.
- [x] T018 [US2] **(CI)** Build decision tables for the stream (`segment.yml`-style workflow
  `.github/workflows/dtables.yml`, `dtables/<plan>`) and for validation ordinals 0–499 and
  500–1499.
  - Workflow written (`configs/dtables/<name>.json`: `segmentation` {plan, branch, path},
    `gate2_plan`; shards from the segmentation plan). Runs once C's code and the plan are final.
  - Validation tuning 0–499 (`results/dtables-g2-val-tune-42288137249`): C reproduced exactly
    (0 of 1,971 rows differ); 14,351 decisions, 1,299 within τ/2 (9%), 2,396 decision rows;
    accepting lowers the error on 27% of rows; about 14 s per scenario. Scoring ordinals need no
    tables.
  - Stream (`results/dtables-g2-stream-42295008170`): 9,930 scenarios, 282,429 decisions, 26,352
    within τ/2, 51,003 decision rows; 4 of 39,054 rows differ from the segmentation file (a
    near-threshold flip on another CPU family, as Gate S panel round 2 found). Ceiling: choosing
    each decision's better side lowers the mean decision-row error from 51.0 (C) to 44.4 (median
    39.9 to 25.9); the share of rows where accepting is better is 28%.
- [x] T019 [US2] Implement E-s in `src/tma2/gate2/model.py` and `train.py`:
  - the evidence network as spec 005's (zero head), on features plus the C code channel;
  - the relaxed acceptance p = σ((Δ − τ′ + 2Σe)/T), Σe over the candidate's rows capped at ±τ/2;
  - the loss Σ p·e_with + (1 − p)·e_without;
  - at inference, the hard decision Δ > τ′ − 2Σe, applied through C's confirmation
    (`segment.confirm`'s evidence path).
  - Done (`gate2/es.py`, `tma2-g2train es`). Deviations, with reasons: C's code channel is not an
    input (at a decision it would encode the decision being shifted); validation uses the hard
    loss (what inference does); the shuffled control draws each decision row's error pair from
    the whole training set, re-drawn every epoch. The relaxation holds C's best candidate fixed;
    at inference evidence can also change the best start or length (recorded in `es.py`).
- [x] T020 [US2] Implement `src/tma2/gate2/predict.py` and `src/tma2/cli/g2predict.py`
  (`tma2-g2predict`): E-s's decisions, then E-w's weights; per-row predictions with
  `EPredictionHeader` (`weights_sha256`, `plan_sha256`, `code_sha256`).
  - Done. Plan models carry `kind` (`e`, `ew`, `es`); the CLI refuses missing or extra weights
    and other C digests. Untrained E-w reproduces the scorer's C errors and untrained E-s C's
    segmentation (tests). `weights_sha256` is the SHA-256 of the E-s and E-w digests joined by
    `+` (each also in the header).
- [x] T021 [US2] Create `.github/workflows/g2train.yml` (`g2train/<plan>`):
  - a matrix of models, chained jobs of ≤ 345 min resuming from the checkpoints branch;
  - inputs (stream segmentations, tables) fetched from results branches;
  - results to `results/g2-<plan>-<run id>`;
  - tables and checkpoints in `RUNNER_TEMP`. — done: `.github/workflows/g2train.yml` (tables per shard and validation with digest checks, two chained training jobs per model, results branch)

## Phase 5: User Story 3, Gate 2 judged on a fresh seed with all references on the same rows (P1)

**Goal**: `tma2-g2` and the gate.

**Independent Test**: the gate reproduces its verdict from committed per-row errors, and refuses
mismatches.

- [x] T022 [P] [US3] `tests/unit/test_gate2_gate.py`:
  - G2-a…G2-d logic (pass, fail, inconclusive, no rows → inconclusive);
  - the shuffled rule voids a G2-d pass;
  - the validation rule.
  - Done ("wholly below / above" strict, as the SRD words them).
- [x] T023 [US3] Implement `src/tma2/cli/g2.py` (`tma2-g2`, contracts/cli.md) on `segment.score`'s
  machinery:
  - E enters as prediction files;
  - C, one leg, the oracle, GLR + confirm, IMM, EKF and naive enter as in `tma2-gs`, with
    `PhysicsLayer(knots=12)`;
  - `metrics.json`, `report.md`, `inputs.json` and `errors.npz`;
  - gate mode adds `verdict.json` and `manifest.json` (provenance first), and exits 3 unless all
    pass.
  - Done: `tma2-gs` gained `--predictions NAME=PATH` and `--knots`; `tma2-g2` runs the
    refusals, then `tma2-gs`'s scoring, then the verdicts (`--split validation` writes
    `validation.json` with the validation and shuffled rules; `--split test` the gate). E's rows
    are written in double, so untrained E − C is 0 to 1e-9 end to end (`test_gate2_cli.py`).
- [x] T024 [US3] Add a `g2` plan kind to `.github/workflows/score.yml`: it runs `tma2-g2` with E's
  prediction files fetched from results branches.
  - Done (`kind: "g2"`: `c`, `e`, `knots`, `gate.model`). Also `g2predict.yml`
    (`g2predict/<name>`, shards × models, results merged per model) and `g2train.yml` trains
    E-s (`kind: "es"`, decision tables from `dtables` results); `scripts/ci/regen_split.sh`.
- [x] T025 [US3] Write the SRD amendment record: confirm `docs/SRD.md` §5 and §7 (PR 16) is merged
  by the owner before T026 (FR-034).
- [x] T026 [US3] Write the decision record `experiments/<date>-g2-decision/` (`decision.json` as
  `Gate2Decision`, README; contracts/decision-record.md), with the forecast refined by the T016
  and T001 numbers. Commit it before any E training.
  - Done: PR 16 merged by the owner (2026-11-07); `experiments/20261107-g2-decision/` binds
    plan `6092c364…`.
- [x] T027 [US3] **(CI)** Train E (three seeds plus the shuffled control) and E-w alone (three
  seeds) with plan `configs/gate2/g2-a.json`; push `g2train/g2-a`.
- [x] T028 [US3] **(CI)** Validation:
  - predict on ordinals 500–1499 and score with `tma2-g2` on CI;
  - apply the carried-seed rule (median by gap recovered), the shuffled rule and the validation
    rule;
  - commit `experiments/<date>-g2-val/` and the amendment `carried.json`.
- [x] T029 [US3] **(CI)** If a configuration is carried:
  - generate seed 319 (`--count 100000`) at a clean commit and commit its digests (an amendment);
  - segment and predict the test split on CI;
  - run the gate (`configs/score/g2-gate.json`);
  - commit `experiments/<date>-g2/`.
- [x] T030 [US3] Convene the agent review panel (five specialities, read-only, in rounds until no
  reject and no open blocker or major). Commit `review.md` and set `decided_by` (FR-051).

## Phase 6: User Story 4, an honest record of what was and was not shown (P2)

- [ ] T031 [P] [US4] Site pages:
  - the algorithm note `site/docs/algorithms/gate2-model.md` (E-w, E-s, decision tables);
  - glossary terms (decision table, relaxed acceptance);
  - the Gate 2 write-up `site/blog/<date>-gate-2.md`, with C's figures beside E's, E-w's ablation,
    the open-at-k stratum, and the follow-on with a recommended default.

  Then `(cd site && npm ci && npm run build)`.
- [ ] T032 [P] [US4] Update `AGENTS.md`: spec 007's status, the seeds used (318, 319) and new
  gotchas.

## Phase 7: Polish

- [x] T033 Export E (E-w on C's segmentation as an input, E-s's evidence network) to ONNX, with
  three-runtime conformance to 1e-5 (constitution VI), as spec 005's evidence export.
- [ ] T034 Run `quickstart.md` end to end and fix any drift.

## Handoff (2026-11-08, for the next session)

State: **Gate 2 decided by the panel, round 2: G2-a to G2-d pass** (record
`experiments/20261107-g2/`, `review.md`, `verdict.json` `decided_by`). T027–T030 done in PR 17
(`claude/inspiring-curie-j192v9`). Training run 42352638177; validation
`experiments/20261107-g2-val/` (carried e-s3); test seed 319; E − C +0.025 [+0.018, +0.031].
Panel round 1 raised two majors (E-s ≈ a zig veto; E-w ≈ a fading memory), answered by
pre-registered classical controls (`experiments/20261107-g2-veto/`): C″ (veto + fixed fade,
nothing learned) − C +0.018; E − C″ +0.007 [+0.001, +0.012] on test (validation inconclusive);
E-s adds nothing shown beyond the veto; on test E-w − fade +0.004 [+0.001, +0.007] (descriptive,
validation negative).

Remaining:
1. **T031** write-up `site/blog/2026-11-08-gate-2.md` with the panel's reading (review.md
   "Decision"; the red team's accepted wording in round 2): C's figures beside E's, E-w's
   ablation, the controls table, the open-at-k stratum (+0.139 on 5.8% of rows), gain by range
   band, the shuffled evidence from training logs, the follow-on with a recommended default.
   The algorithm note and glossary exist (`site/docs/algorithms/gate2-model.md`); add a section
   on the controls. Then `(cd site && npm ci && npm run build)`.
2. **T032** AGENTS.md is updated (status, controls, gotchas); add the final verdict line.
3. **T033** done: `segment.evidence_export --plan configs/gate2/g2-a.json` (E-s) and
   `gate2.export` (E-w on C's hand-over, 100 iterations as one Loop, 12 knots), carried weights,
   three legs in `ci.yml` (Python leg: E-s 6e-16, E-w 3.4e-8).
4. **T034** quickstart.
5. Follow-ons for the next plan: time-late variant (G7); score last-epoch shuffled weights (G4);
   coverage assertion in `tma2-g2` and merge-step counts (G10, G11); bind GLR files and E's C file
   (G12); read the shuffled rule from `validation.json` (G9); store C's scored errors (R2-6);
   controls' headers carry their settings (R2-7).

## Dependencies

- **T001 → T009, T026.** The hand-over must be chosen first.
- **T003 → T026.** Form (a) is decided before the decision record.
- **T004 → T006 → T007–T024.**
- **US1 (T007–T009) → US2.** The stream segmentation feeds training and the tables.
- **Within US2:**
  - T010–T012 before T013–T020;
  - T013–T015 before T016;
  - T017 before T018 and T019;
  - T020 and T021 before T027.
- **US3:** T022 → T023 → T024; T025 → T026 → T027 → T028 → T029 → T030.
- **US4:** after T030 (the write-up) or in parallel (the algorithm note).

## Parallel opportunities

- T005 with T004.
- T010, T011 and T012 (different test files).
- T022 with the US2 implementation.
- T031 (algorithm note) and T032 with the gate run.
- The CI tasks T003, T009, T016 and T018 run concurrently within the 20-job runner limit.

## Implementation strategy

1. **MVP:** T001–T016 give E-w trained on C's segmentation, the SRD's end-to-end model. Its
   validation numbers decide whether E-s adds anything worth the tables.
2. **Then:** E-s (T017–T021).
3. **Then:** the decision record, training, validation, test and panel.
