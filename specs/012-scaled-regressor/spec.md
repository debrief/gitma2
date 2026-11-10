# Feature Specification: The scaled end-to-end regressor control

**Feature Branch**: `012-scaled-regressor` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: research note 04 option B and note 10 §6 decision 2. gitma's learned
estimators sat at about 3 × the Cramér–Rao bound, but they were small models trained on 80,000
scenarios with about 300 CPU-hours, and its capacity scan could not separate "capacity is flat"
from "nothing here is trained to convergence". Train one large sequence model that regresses
the target state directly from the bearings and the ownship track, with far more data and a GPU,
and score it with the existing scorer. The question: was the floor compute and data, or
architecture?

**SRD traceability**:
- §5 (references on the same rows, efficiency per slice, paired clustered statistics, fresh
  seeds); §7 (the plan's controls). No gate row: this is a control experiment with a
  pre-registered reading, not a gate on a carried estimator.
- `docs/research/04-proposal.md` (option B), `docs/research/10-reflection-headroom.md`
  §5, §6, §9; `docs/research/03` (GPU options and prices).

**Owner decisions this spec implements**:
- 2026-11-09: the scaled regressor follows the headroom gate, on Modal's free credit.
- 2026-11-10: start now, in parallel with spec 011.
- 2026-11-10: the GPU budget is one month of Modal's free credit, about 50 T4-hours, as a hard
  cap.

- 2026-11-10 (later, superseding the cap above): the budget is **$50 in total** for this spike
  ($30 of free credit and up to $20 charged), "useful to understand our hardware limits". The
  cap is in dollars; hours follow from the measured cost per hour.

**Standing of the model**: constitution principle III requires the reported estimate to come
from a declared physics layer. This model has none. It is a **control**: it is never carried,
exported, or reported as the project's estimator, whatever it scores.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An answer to "was it compute?" (Priority: P1)

A reader sees the regressor's efficiency (error over the Cramér–Rao bound) on rows where the
target has held its course, beside batch least squares on the same rows, with intervals, by
geometry band, for three training seeds. The reading was fixed before any GPU run: the
regressor **reaches the bound**, or it sits at a **flat floor**, or it lands between and the
result is stated as partial.

**Why this priority**: it is the question gitma left open and the only reason a different
paradigm would be worth a fresh start.

**Independent Test**: from the committed record alone, the three efficiencies, their intervals
and the pre-registered reading can be reproduced by the scorer.

**Acceptance Scenarios**:

1. **Given** the registered reading, **When** the test seed is scored, **Then** the record
   states one of reaches, floor or partial, for each seed and for the three together.
2. **Given** the efficiency by geometry band, **When** the classical error falls with better
   geometry, **Then** the record says whether the regressor's falls with it or stays flat.

---

### User Story 2 - The regressor after manoeuvres (Priority: P1)

The same model on rows after target manoeuvres, against the standing classical system C″, the
tuned IMM and EKF, one leg and the oracle. gitma's networks beat its IMM there by 25–40%; C″
did not exist then.

**Why this priority**: straight legs can at best tie least squares. After manoeuvres is the
only place the regressor could win, and the comparison that matters is with C″.

**Independent Test**: the paired difference in median range error between the regressor and
C″ on manoeuvring rows, with a scenario-clustered interval, from one scoring run.

**Acceptance Scenarios**:

1. **Given** the test seed, **When** scored, **Then** the record gives regressor − C″ and
   regressor − IMM with intervals, by range quartile and in operational units.

---

### User Story 3 - Spending stays inside the cap (Priority: P1)

The owner can see, before any GPU run, the cap in GPU-hours, how it is split between a pilot
and the three seeds, and what stops a run. Afterwards the record shows the hours used.

**Why this priority**: spending is the owner's; the cap is their decision.

**Independent Test**: the sum of recorded GPU-hours is at most the cap, and every run names its
own limit.

**Acceptance Scenarios**:

1. **Given** a run that reaches its time limit, **When** it stops, **Then** its last checkpoint
   and metrics are kept and the hours are recorded.
2. **Given** the cap is spent, **When** another run is requested, **Then** it is refused.

---

### User Story 4 - Everything ready before the account exists (Priority: P2)

The training code, the data stream and the workflow are built and tested at toy size on CPU
before the owner has created the account, so the first GPU run starts as soon as the secrets
are in place.

**Independent Test**: a CPU run of a few minutes trains the toy configuration, writes a
checkpoint and metrics in the final format, and the scorer reads its predictions.

### Edge Cases

- A run is cut off mid-epoch: it resumes from its last checkpoint; the hours of both parts count.
- The GPU type differs between seeds: recorded; a seed on other hardware is flagged.
- Rows before the ownship zig, where no estimator can know range: scored as the scorer already
  treats them, never trained to match an undetermined truth as if it were determined.
- The model answers every row, the classical systems do not: comparisons are reported on all
  rows and on rows every system answers.
- The pilot shows the planned model cannot be trained inside the cap: the configuration is
  reduced and the reduction recorded before the three seeds, never after.

## Requirements *(mandatory)*

### Functional Requirements

**The model and its data**

- **FR-001**: The model MUST map bearings, their times and the ownship track of a prefix to the
  target's state at the prefix's end directly, with no physics layer or iterative solve in the
  estimate, and MUST be causal.
- **FR-002**: Training data MUST be generated on the fly from a seed stream by the existing
  generator (0.6.0, MAN2, no mismatch), about 10⁷ scenarios, never stored as a dataset; the
  stream's seed and the count consumed are recorded.
- **FR-003**: The architecture family, its size, the loss, the data budget and the training
  schedule MUST be fixed in a decision record before any GPU run; the pilot may reduce them
  once, before the three seeds, and the reduction is recorded.
- **FR-004**: The carried configuration MUST be trained with three seeds.

**Budget**

- **FR-010**: Total spend MUST NOT exceed the owner's cap ($50, all charges: GPU, CPU, memory
  and storage), converted to GPU-hours at the cost per hour the pilot measures; the decision record splits it (pilot; three seeds) and each run
  enforces its own limit.
- **FR-011**: Every run MUST record GPU type, hours, library versions, seed and code commit.
  GPU training is not bit-reproducible; the record says so and relies on three seeds.
- **FR-012**: No GPU run may start until the owner has created the account, a spending limit and
  the two repository secrets; secrets MUST reach only this repository's own workflows.

**Measurement**

- **FR-020**: Scoring MUST use the existing scorer on CPU, on fresh seeds (training stream 326,
  validation 327, test 328), on the same rows as naive, batch least squares, one leg, C″, the
  tuned IMM and EKF, the oracle and the bound.
- **FR-021**: **Held-course reading**, registered before any GPU run, on settled rows where the
  target has held course since the start, efficiency against the full-window bound with a
  scenario-clustered interval: **reaches the bound** if the interval lies wholly below 1.25;
  **flat floor** if it lies wholly above 2.0 and efficiency does not fall from the worst to the
  best geometry band; otherwise **partial**. Batch least squares on the same rows is the check
  that the rows and the bound are sound (expected 0.95–1.01).
- **FR-022**: **Manoeuvring reading**: paired differences in median range error, regressor − C″
  and regressor − IMM, on rows after a target change, with intervals; also course and speed, by
  range quartile, in operational units, on all rows and on rows every system answers.
- **FR-023**: The validation seed is used for the pilot's choices and early stopping only; the
  test seed is scored once per trained seed.
- **FR-024**: Registered controls for the regressor's own claims: a model given the ownship
  track only (what the prior alone yields), and the same model at a tenth of the data (does
  data still help at the end of the budget?). Both inside the cap.

**Reading and reporting**

- **FR-030**: The write-up MUST state which reading holds and what it implies: reaches → the
  physics layer is not needed for precision and the design question reopens with evidence;
  floor → gitma's result was architecture and the hybrid design stands; partial → what moved
  and what did not. The panel reviews the write-up; there is no pass or fail.
- **FR-031**: A kickoff post now and a slides post before the PR that carries the results:
  efficiency by geometry band against batch least squares; error against data seen; the
  manoeuvring comparison; track plots on a representative engagement.
- **FR-032**: The model is named a control wherever it appears and is not exported.

### Key Entities

- **Regressor**: the direct sequence-to-state model; a control.
- **Training stream**: scenarios drawn on the fly from seed 326.
- **Decision record**: configuration, budget split, readings, forecasts; precedes any GPU run.
- **Run record**: per run, the seed, GPU type, hours, versions, commit, metrics, checkpoint digest.
- **Readings**: reaches the bound, flat floor, partial (held course); the paired differences
  (manoeuvring).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The record states one held-course reading for each of three seeds, with intervals.
- **SC-002**: The record gives regressor − C″ and regressor − IMM on manoeuvring rows with
  intervals.
- **SC-003**: Recorded GPU time is at most the cap.
- **SC-004**: The decision record predates the first GPU run, and the test seed is scored once
  per trained seed.
- **SC-005**: A reader can tell from the write-up alone whether a large direct model changes
  the case for the hybrid design.
- **SC-006**: Everything up to the first GPU run works on CPU at toy size before the account
  exists.

## Assumptions

- One month of free credit is about $30 and a T4 about $0.59 an hour (note 03, re-checked
  2026-11-10 from public pricing); the owner confirms at sign-up. If the cap must be expressed
  in money, it is the free credit.
- The thresholds in FR-021 (1.25 and 2.0) are proposals with no result behind them: gitma's
  networks were near 3, least squares is near 1. They are the owner's to change until the
  decision record.
- Seeds 323–325 are spec 011's; this spec takes 326 (training stream), 327 (validation) and 328
  (test); the next fresh seed is then 329.
- The generator's kernel is fast enough (about 20,000 scenarios a second on CPU) that data are
  not the bottleneck; whether the GPU container's CPUs keep up is for the plan to measure.
- Out of scope: bearing-error mismatch (a later question if the regressor reaches the bound);
  any hybrid of the regressor and the physics layer; export; uncertainty calibration of the
  regressor beyond what the loss needs.
