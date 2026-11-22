# Feature Specification: The scaled regressor under bearing-error mismatch, with an uncertainty and a hybrid

**Feature Branch**: `037-regressor-mismatch` (developed on `claude/lucid-wright-y1xstj`)

**Created**: 2026-11-22

**Status**: Draft

**Input**: User description: owner 2026-11-22, option A of four ("specify 037 as experiments
1 → 2 → 3, staying within the remaining $9"). Three steps in order: score the existing spec 012
regressors unchanged under spec 010's bearing-error mismatch; fine-tune them under mismatch with
heads that state an uncertainty, one error family held out of training; a hybrid in which the
regressor's estimate and uncertainty start and constrain C″'s final physics-layer solve.

**SRD traceability**:
- §5 (references on the same rows, efficiency per slice, paired clustered statistics, fresh
  seeds), §7 (the plan's controls), §9 (owner decisions). No gate row: a registered study with
  readings fixed beforehand, not a gate on a carried estimator.
- Spec 010 (Gate H: the mismatch overlay, the robust control, "the mismatch's cost is in the
  segmentation"), spec 011 (a robust classical segmenter did not close it), spec 012 (the
  regressor beats C″ after manoeuvres on clean data; the margin's source is open), specs 008
  and 009 (no usable uncertainty from E).

**Owner decisions this spec implements**:
- 2026-11-10: GPU spending is **$50 in total**, in dollars. About $41 is spent (spec 012 about
  $26, spec 016 about $14). This spec may use what the ledger shows is left, about $9, and no more.
- 2026-11-11: spending within the $50 is pre-approved.
- 2026-11-22: option A (this spec).

**Standing of the models**: constitution principle III requires the reported estimate to come
from a declared physics layer. The regressor has none and stays a **control**: never carried or
exported as the project's estimator, whatever it scores. The hybrid (step 3) does report from
the physics layer; whether it is carried is the owner's choice after the panel, not this spec's.

**Why this, and why now**: under the primary mismatch condition C″'s median range error goes
from 0.102 to 0.280, and the cost is in the segmentation; the classical remedy failed. The
regressor has no segmenter. It is also the one learned model that beat C″ after manoeuvres. If
it degrades little, or can be made to with a few GPU-hours, that is the largest gain on the
table; if it cannot, the record says so at almost no cost.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The unchanged regressor under mismatch (Priority: P1)

A reader sees, for each of the sixteen declared conditions, the three existing regressors'
errors beside C″, C″ with the robust final solve, the robust solve on the true segmentation, the
tuned IMM and EKF and one leg, on the same rows of a spent seed. It costs no GPU time and
decides whether step 2 is worth its spend.

**Why this priority**: it is free, and each outcome is informative: a regressor that holds up
needs no fine-tune for robustness; one that degrades as C″ does shows the segmenter was not the
whole story.

**Independent Test**: from the committed record alone, each system's median range error and
course and speed efficiency per condition can be regenerated, and the step-2 decision follows
from a rule written before the scoring.

**Acceptance Scenarios**:

1. **Given** the spent validation seed of Gate H and its sixteen conditions, **When** the
   existing regressors are scored unchanged, **Then** the record gives, per condition, each
   system's median range error, course and speed efficiency, and the paired per-scenario ratio
   C″-robust ÷ regressor with its interval and the shares twice as good and twice as bad.
2. **Given** the rule fixed beforehand, **When** the reading is "holds up" (see FR-012), **Then**
   no GPU run starts and the owner is asked whether the uncertainty alone is worth the spend.

---

### User Story 2 - Fine-tuned under mismatch, with a stated uncertainty (Priority: P1)

The three regressors are fine-tuned on scenarios with bearing errors drawn across the declared
kinds and severities, and gain heads that state an interval for range, course and speed. They
are scored once on a fresh test seed: on clean data, on the primary condition, and on an error
family that training never saw.

**Why this priority**: it is the only spend, and it tests two open questions together:
robustness where the classical system loses a factor of 2.7, and an uncertainty that Gates 3
and 4 did not deliver.

**Independent Test**: one scoring run on the test seed gives every registered reading with its
interval; the decision record, with plan digests, predates the first GPU run.

**Acceptance Scenarios**:

1. **Given** the registered readings, **When** the test seed is scored, **Then** the record
   states for each of: robustness in training conditions, robustness on the held-out family,
   the fine-tune's own effect, its cost on clean data, and the uncertainty, one of the outcomes
   fixed beforehand, per training seed and for the three together.
2. **Given** the held-out family, **When** the record is read, **Then** it is plain which
   conditions lay inside the training ranges and which did not, and no in-range condition is
   called a mismatch for the model.
3. **Given** the stated intervals, **When** scored, **Then** coverage is given with a
   scenario-bootstrap interval, beside a normalised-error median, by range band and by time
   since the last target change, and beside the per-slice temperature control.

---

### User Story 3 - A hybrid that reports from the physics layer (Priority: P2)

C″'s final solve is started from the regressor's estimate and constrained by its stated
uncertainty as a prior, so the reported state comes from the declared layer. A reader sees it
beside C″, C″ with the robust solve, the regressor alone and C″ with a classical range prior.

**Why this priority**: on clean data the regressor was better in range and C″ better in course
efficiency (3.19 against 3.40). A hybrid could keep both and would be eligible to be carried;
but it depends on step 2's uncertainty, and spec 012's simple-prior control already failed.

**Independent Test**: on the validation seed, then once on the test seed, paired ratios of the
hybrid against each comparator in range, course and speed.

**Acceptance Scenarios**:

1. **Given** the fine-tuned regressors and their intervals, **When** the hybrid is scored,
   **Then** the record gives hybrid against C″-robust and against the regressor alone in range,
   course and speed, clean and under the primary and held-out conditions.
2. **Given** a row where the regressor states no usable uncertainty, **When** the hybrid runs,
   **Then** it returns C″'s own solve and the row is counted as a constructed tie.

---

### User Story 4 - Spending stays inside what is left (Priority: P1)

Before any GPU run the owner can see the dollars left, the split between a pilot and the three
fine-tunes, and what stops a run; afterwards, the dollars used.

**Independent Test**: the ledger's total after this spec is at most $50; each plan names its own
limit and is refused if it would pass the cap.

**Acceptance Scenarios**:

1. **Given** the ledger's total, **When** a plan's limit would take it past the cap, **Then**
   the run is refused before any container starts.
2. **Given** a run cut off at its limit, **When** it stops, **Then** its last checkpoint and
   metrics are kept and its cost is recorded.

### Edge Cases

- The unchanged regressor already holds up under mismatch: no fine-tune for robustness; ask.
- The pilot's first fine-tuning hour moves nothing on validation: stop, record, ask; do not spend
  the rest to confirm it.
- The fine-tune buys robustness by losing clean-data accuracy: both are registered readings;
  neither is hidden by pooling.
- The model answers every row, the classical systems do not: every comparison is given on all
  rows and on rows every system answers, with the scenario count beside each paired ratio.
- A stated course interval wider than a half circle says nothing: reported as "undetermined",
  counted, and excluded from coverage rather than counted as a hit.
- The held-out family turns out to be harmless to every system: reported as such; it is then no
  test, and the record says so.
- The mismatch overlay is extended for the held-out family: with mismatch off, and under every
  existing condition, generated data must be unchanged byte for byte.
- Two fewer seeds than planned finish inside the money: the record reports what finished and
  reads "three together" as not available.

## Requirements *(mandatory)*

### Functional Requirements

**Step 1: the unchanged regressors (CPU, development data)**

- **FR-010**: The three spec 012 regressors MUST be scored unchanged, their weights' digests
  recorded, on Gate H's spent validation seed under all sixteen declared conditions, on the same
  rows as naive, one leg, C″, C″ with the robust final solve, the robust solve on the true
  segmentation, the tuned IMM and EKF, and the bound. All systems are compared within one
  scoring run.
- **FR-011**: The step is development work on a spent seed and is never quoted as a result
  beyond "tuning".
- **FR-012**: A rule written before the scoring decides what follows, on the primary condition
  and the three seeds together: **holds up** (regressor's error under mismatch within 10% of
  its clean error, and C″-robust ÷ regressor wholly above 1) → no fine-tune for robustness, the
  owner is asked about the uncertainty alone; otherwise → step 2 proceeds. The rule's inputs are
  recorded either way.

**Step 2: fine-tune with an uncertainty (GPU)**

- **FR-020**: Fine-tuning MUST start from the three spec 012 checkpoints and draw scenarios on
  the fly from a fresh seed stream, with bearing errors drawn per scenario across the declared
  kinds and a stated share of clean scenarios; the ranges are recorded in the plan.
- **FR-021**: One bearing-error family MUST be absent from training and tuning entirely and used
  only at validation and test: by default heavy-tailed white error (not a Gaussian with
  outliers) and a bearing-error level that changes within the engagement. The record lists which
  scored conditions lie inside the training ranges.
- **FR-022**: The fine-tuned models MUST state, for range, course and speed, a central estimate
  and a 95% interval (course as an arc, "undetermined" allowed), trained on the errors the
  scorer scores. The central estimate is the one scored for accuracy.
- **FR-023**: Total GPU spend across the project MUST stay at or under $50 by the ledger; this
  spec's plans split what is left between one pilot (at most a quarter) and three fine-tunes,
  each plan with its own limit. Launches are spaced at least a minute apart.
- **FR-024**: A decision record MUST exist before the first GPU run of the three seeds: plans
  bound by digest, code digest, the readings of FR-030 with their thresholds, forecasts, the
  controls, the seeds. The pilot may change the configuration once, before that record.
- **FR-025**: Controls registered in that record, all scored in the test's scoring run: the
  unchanged regressor; C″; C″ with the robust final solve; the robust solve on the true
  segmentation (named for what it is told, not a ceiling); IMM, EKF, one leg; for the
  uncertainty, a per-slice temperature on a fixed-width baseline, fitted on validation only.

**Step 2's registered readings (test seed, scored once)**

- **FR-030**: Each reading is a paired per-scenario ratio of median range error with a
  scenario-bootstrap interval, three seeds pooled and each alone, decided "better" (interval
  wholly above 1), "worse" (wholly below) or "not separated", three decimals when a limit is
  within 0.02 of 1:
  - **M1 robustness, in range**: C″-robust ÷ fine-tuned regressor on the primary condition.
  - **M2 robustness, held out**: the same on the held-out family.
  - **M3 the fine-tune's effect**: unchanged ÷ fine-tuned regressor on the primary and the
    held-out conditions.
  - **M4 cost on clean data**: unchanged ÷ fine-tuned regressor with mismatch off; "no cost" if
    the lower limit is at least 0.95.
  - **M5 uncertainty**: coverage of the stated 95% intervals for range, course and speed, each
    "honest" if its bootstrap interval lies within 0.90 to 0.99 on clean, primary and held-out
    data separately; and interval score against the temperature control, "better" if wholly
    below.
- **FR-031**: Beside every reading the record MUST give: course and speed efficiency against
  the known-manoeuvre bound; the median per-scenario ratio and the shares better, twice as good
  and twice as bad; the reading by range band and by time since the last target change; all
  rows and rows every system answers, with counts.
- **FR-032**: Validation uses one fresh seed for early stopping, the temperature and the
  hybrid's settings; the test seed is generated only in its run and scored once.

**Step 3: the hybrid (CPU)**

- **FR-040**: The hybrid MUST be C″'s segmentation with a final physics-layer solve started from
  the regressor's estimate and carrying it as a prior with the regressor's stated uncertainty;
  the reported estimate is the layer's. C and C″ stay frozen; the layer's registered code is not
  edited.
- **FR-041**: Comparators in one scoring run: C″, C″-robust, the regressor alone, and C″ with a
  classical range prior of the same form (spec 012's control). Rows where the hybrid falls back
  to C″ are constructed ties, excluded from the decided ratio and counted.
- **FR-042**: Registered readings, same form as FR-030: **Y1** C″-robust ÷ hybrid and **Y2**
  regressor ÷ hybrid, in range, on clean and primary conditions; course and speed reported as
  FR-031. Harm: any of range, course or speed wholly below 1 against C″-robust on clean data.
- **FR-043**: The hybrid's settings (prior weight, when to fall back) are chosen on validation
  and bound by an addendum before the test scoring; if step 2's M5 reads "not honest", the
  hybrid uses a fixed prior width chosen on validation and says so.

**Reading and reporting**

- **FR-050**: The write-up MUST say, in the panel's terms, what is shown and what is not: a win
  inside the training ranges is "robust to this simulated error family", not to real sonar; the
  regressor knows the simulator's manoeuvre prior and C″ does not; nothing is carried by this
  spec.
- **FR-051**: The agent review panel reviews the test record. There is no pass or fail; a
  follow-on (carrying the hybrid, more budget) is proposed with a recommendation and is the
  owner's.
- **FR-052**: A kickoff post now; a slides post before the PR that carries the results: error by
  condition for every system; the paired-ratio distributions; coverage by slice; track plots of
  one engagement clean and under mismatch.
- **FR-053**: What the spec promised and did not run is listed in the record.

### Key Entities

- **Unchanged regressor**: a spec 012 checkpoint, as trained on clean data; a control.
- **Fine-tuned regressor**: the same, trained further under mismatch, with interval heads; a
  control.
- **Mismatch conditions**: spec 010's sixteen, plus the held-out family that training never sees.
- **Hybrid**: C″'s segmentation and layer, with the regressor as start and prior.
- **Decision record**: plans, digests, readings, forecasts, seeds; precedes the three GPU runs.
- **Ledger**: the dollars spent on every GPU run of the project; the cap is $50.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Step 1's record gives all systems on all sixteen conditions and the step-2
  decision by the rule written before it.
- **SC-002**: The decision record predates the three GPU runs, and the test seed is scored once.
- **SC-003**: The ledger's total is at most $50.
- **SC-004**: The test record states M1 to M5, Y1 and Y2, each with its interval and outcome, for
  three seeds together and each alone.
- **SC-005**: A reader can tell from the write-up alone whether a direct learned model keeps its
  accuracy under bearing errors the classical system does not survive, whether its stated
  intervals can be shown, and whether a physics-layer hybrid keeps the gain.
- **SC-006**: With mismatch off and under each existing condition, generated data are unchanged
  byte for byte after the overlay is extended.

## Assumptions

- Seeds: 369 fine-tuning stream, 370 validation, 371 test; step 1 on spent seed 321. The next
  fresh seed after this spec is 372.
- About $9 buys about 13 T4-hours at the measured $0.66 an hour: roughly 3 for the pilot and 3
  for each seed. If the ledger shows less, the plans shrink; none is launched past the cap.
- The existing checkpoints are retrievable from spec 012's results branches with their digests.
- The regressor is real-time (causal) and this spec is about real-time estimates; the time-late
  track and its standing systems are untouched.
- A December free credit, or any budget beyond $50, is the owner's decision and is not assumed.
- Scoring, the hybrid and step 1 run on CI on CPU, not in a session.

## Out of Scope

- Training from scratch, a larger model, or training through a physics layer.
- A learned segmenter or proposer; any change to C, C″ or the time-late controls.
- Real data. Carrying or exporting any model from this spec.
