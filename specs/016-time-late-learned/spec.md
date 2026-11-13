# Feature Specification: Time-late, classical controls and a learned whole-period model

**Feature Branch**: `016-time-late-learned` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-13

**Status**: Draft

**Input**: Owner decision, 2026-11-13, after spec 015's panel review: option B. Build the
classical controls on CPU and, in parallel, train a learned whole-period model on GPU under a
plan registered before any result; the learned model is scored only once the controls exist.

**SRD traceability**:
- §1 (time-late consumer), §3 (the reported estimate comes from a declared physics layer),
  §5 (references on the same rows, paired statistics, fresh seeds, registration before
  results; a new row proposed by this spec, owner to merge) and §9, 2026-11-13.
- Panel reviews `experiments/20261113-tl3/review.md` ("What the panel wants next", 2 to 5;
  the table of what a learned model may be compared with) and
  `experiments/20261112-tl2/review.md`.

**Owner decisions this spec implements**:
- 2026-11-13: option B.
- 2026-11-12: GPU may be used in support of time-late learning, within the $50 total;
  runs are registered before their results.
- 2026-11-11: spending within $50 is pre-approved (about $24 unspent).

## Background

Three time-late studies (Gate T, specs 014 and 015) leave this position. A classical search
over manoeuvre histories, scored by a Laplace evidence under Annex B's statistics, halves the
track error of C″ read as a track. Where the simulator's assumptions hold, an oracle is 10%
to 20% ahead of it and 400 periods cannot decide a 10% line. Where they fail the gaps are
large: against an oracle the search is 1.7 times worse under a shifted manoeuvre prior, 1.4
under correlated bearing errors and 1.5 with outliers, and on quiet targets it invents a
manoeuvre in half the periods. No classical remedy has been tried for any of these. A learned
model that won there today could not be told from a missing robust cost, a broader prior or
simple hedging; this project has drawn that wrong conclusion three times and had it corrected
by a control.

The owner has chosen to build those controls and to train the learned model at the same
time, so that GPU time is not idle while the controls are built, with one safeguard: the
model's plan, comparison and criteria are fixed first, and it is not scored on fresh data
until the controls' own validation results are recorded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A hedged track and a cautious declaration (Priority: P1)

A researcher gets, from the search's own candidates and with no new fitting, a track that
averages over the plausible histories instead of committing to one, and a history in which a
manoeuvre is declared only when the evidence for it is clear.

**Why this priority**: it is the control for hedging, the cheapest one, and the one both
earlier studies were silent on. A learned model minimising error will hedge.

**Independent Test**: on periods already solved, the hedged track's error and the declared
history's false and missed manoeuvres are reported beside the search's first candidate, with
no solve repeated.

**Acceptance Scenarios**:

1. **Given** a period whose candidates disagree, **When** the hedged track is formed, **Then**
   it lies between them, weighted by their stated probabilities.
2. **Given** a quiet target, **When** the declaration margin is applied, **Then** the false-
   manoeuvre rate and the rate at which one-manoeuvre targets are called quiet are both
   reported over a range of margins.

---

### User Story 2 - A search that tolerates bearing errors it was not told about (Priority: P1)

A researcher runs the search with a likelihood that does not assume independent Gaussian
errors: wild bearings carry bounded weight, and correlated errors are modelled.

**Why this priority**: outliers and correlated errors are two of the three large gaps.

**Independent Test**: on data with outliers and with correlated errors, at two severities
each, the robust search's track error and false manoeuvres are reported beside the plain
search's; on clean data its cost is reported.

**Acceptance Scenarios**:

1. **Given** 2% wild bearings, **When** the robust search runs, **Then** its false manoeuvres
   per period and track error are reported against the plain search and against the same
   search on the clean data.
2. **Given** clean data, **When** the robust search runs, **Then** what it loses is reported.

---

### User Story 3 - A prior that can be wrong, and says so (Priority: P1)

A researcher runs the search with a broader prior on how targets manoeuvre and a stated small
chance of a quiet target, and gets a diagnostic that reports when the period's best history
is improbable under Annex B's statistics.

**Why this priority**: the shifted prior is the largest gap; candidates there carry no
usable probability.

**Independent Test**: on the shifted split and on Annex B data, the broadened search's error,
manoeuvre counts and candidate calibration are reported beside the Annex B search's; the
diagnostic's rate of firing is reported on both.

---

### User Story 4 - A learned whole-period model, registered before it is trained (Priority: P1)

The owner sees a sequence model that reads a whole period and gives the whole track, trained
on simulated periods of mixed kinds, with its architecture, training mix, budget, comparison
and criteria fixed in a decision record before any training result exists.

**Why this priority**: it is the question the project exists to answer for the time-late
consumer, and the owner has asked for it now.

**Independent Test**: the decision record and plan digests predate the first training job;
three seeds train within the budget; the spending ledger accounts for every GPU hour.

**Acceptance Scenarios**:

1. **Given** the registered plan, **When** a training job starts, **Then** it refuses to run
   if the plan's digest differs or the ledger would exceed its cap.
2. **Given** a trained model, **When** it is exported, **Then** the reported track comes from
   the declared read-out and the model also runs without a GPU.

---

### User Story 5 - A comparison the controls make interpretable (Priority: P1)

The owner sees the learned model scored once, on a fresh test seed, against the best
classical control on each kind of period, after the controls' validation results are on
record; and sees plainly whether it beats them, where, and by how much per period.

**Independent Test**: the scoring run refuses to read validation or test data for the
learned model unless the controls' validation record exists; the record reports paired
per-period ratios with intervals, the share of periods lost, efficiency by slice and the
result on each split.

**Acceptance Scenarios**:

1. **Given** the learned model beats the search's first candidate but not the hedged track,
   **When** the result is written, **Then** it is recorded as hedging, not as learning.
2. **Given** a split whose conditions were in the training mix and one whose were not,
   **When** scored, **Then** the two are reported apart.

### Edge Cases

- A period with a single candidate: the hedged track is that candidate.
- Candidates whose tracks are mirror solutions: the hedged track may lie between them and be
  far from both; reported, and its error counted as it falls.
- A training job refused by the GPU provider's rate limit: re-run from the same plan.
- A model that diverges for one seed: counted, reported, not replaced.
- A condition severity the classical control was tuned on and the model was not trained on,
  or the reverse: stated per split.
- A period shorter or longer than the model's window.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen**

- **FR-001**: C, C″ and the registered code paths, plans and records of Gate T and specs 014
  and 015 MUST NOT change in behaviour; their fixtures MUST still pass.

**Classical controls (nothing trained)**

- **FR-002**: A hedged track MUST be formed from the search's candidates as their
  probability-weighted mean track, at the registered temperature and at others, without
  refitting.
- **FR-003**: A declaration rule MUST accept a manoeuvre only when the evidence margin over
  the history without it exceeds a threshold, combined with a small stated probability of a
  quiet target; both are tuned on the tuning seed only and their false and missed rates
  reported as a curve.
- **FR-004**: The search MUST be runnable with a robust likelihood (bounded weight for wild
  bearings) in its fits and its evidence.
- **FR-005**: The search MUST be runnable with a correlated-error likelihood in its fits and
  its evidence, with the correlation estimated from the data or stated, and each reported.
- **FR-006**: The search MUST be runnable with a broadened manoeuvre prior (alone and as a
  mixture with Annex B's), and a diagnostic MUST report when the best history is improbable
  under Annex B's statistics.
- **FR-007**: Each control's settings MUST be chosen on the tuning seed and fixed in the
  decision record before validation.
- **FR-008**: Known evidence faults at the edges of the prior's support MAY be repaired in a
  new prior version where a control needs it; any repair MUST be tested at the edges and at
  solver bounds.

**Learned model**

- **FR-009**: A learned model MUST read a whole period (bearings at 5-second intervals,
  ownship motion, the stated bearing error) and output the target's track at every scored
  moment, with manoeuvre times as a secondary output.
- **FR-010**: The reported track MUST come from a declared read-out (the arc model or the
  physics layer fitted from the model's output), and the model's direct output MUST be
  reported beside it.
- **FR-011**: Training data MUST be generated on the fly from a seeded stream that mixes
  Annex B periods, shifted and broadened manoeuvre statistics, quiet targets, correlated
  errors and outliers, in declared proportions; conditions held out of training MUST be
  declared.
- **FR-012**: Three seeds MUST be trained under one plan bound by digest in a decision record
  committed before the first training job; the record MUST fix the comparison, the splits,
  the statistics, what each outcome will be called and what follows from it.
- **FR-013**: GPU spending MUST stay within the owner's budget by a ledger that refuses a job
  that would exceed it; the record MUST state the dollars spent.
- **FR-014**: The learned model MUST NOT be scored on the validation or test seed until the
  classical controls' validation record is committed; the scoring tool MUST enforce this.
- **FR-015**: The model MUST export to a form that runs without a GPU, and the exported
  model's output MUST agree with the trained one's.

**The comparison**

- **FR-016**: On each split (Annex B, shifted prior, correlated errors and outliers at two
  severities each, held course, and at least one condition absent from training) the learned
  model MUST be compared with the best classical control for that split as chosen on
  validation, and with the hedged track, the plain search, C″ as a track and the true-history
  reference, on the same periods.
- **FR-017**: Every comparison MUST report the paired per-period ratio with a period-
  bootstrap interval, the ratio of medians, the share of periods each side loses, efficiency
  against the bound by slice for range, course and speed, and manoeuvre counts (missed,
  false) at 60, 120 and 240 s.
- **FR-018**: The true-history reference MUST be reported under each convention (times free,
  held where drifted, held everywhere) wherever a headroom is quoted.
- **FR-019**: No criterion MUST be registered whose outcome at the planned sample size is
  forecast as near even; the decision record MUST state the power of each criterion from
  tuning data.
- **FR-020**: A win of the learned model MUST be attributed only after the registered
  controls: against the hedged track (hedging), against the robust and correlated-error
  searches (the likelihood), against the broadened prior (the prior). What remains is
  recorded as learning; what does not is recorded under the control's name.
- **FR-021**: The record MUST list what the spec promised and did not deliver, and every
  table MUST be generated from the summary by a committed script, with the README's figures
  checked by a committed test.

**Process**

- **FR-022**: Seeds: 338 tuning, 339 the training stream, 340 validation, 341 test. Test is
  scored once.
- **FR-023**: A five-reviewer panel MUST decide the result; kickoff and slides posts as the
  constitution requires.

### Key Entities

- **Candidate set**: a period's histories with evidence, probabilities and tracks.
- **Hedged track**: the probability-weighted mean of the candidates' tracks.
- **Control**: a classical variant of the search (robust, correlated-error, broadened prior,
  declaration margin) with settings fixed on tuning data.
- **Learned model**: weights for one seed, its plan digest, its export.
- **Training mix**: the declared proportions of period kinds and error conditions.
- **Ledger**: GPU hours and dollars by job against the cap.
- **Split**: a set of periods of one kind and severity, marked as inside or outside the
  training mix.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each of the three large gaps (shifted prior, correlated errors, outliers)
  the record states how much of the gap between the plain search and the true-history
  reference the best classical control closes, with an interval.
- **SC-002**: On held course, a declaration rule is shown whose false-manoeuvre rate is
  under 0.10 with the rate of one-manoeuvre targets called quiet stated beside it.
- **SC-003**: The hedged track's error is reported against the first candidate's on every
  split, paired per period.
- **SC-004**: Three seeds of the learned model are trained within the budget, and the
  decision record's digests predate the first job.
- **SC-005**: The learned model is scored exactly once on the test seed, after the controls'
  validation record, and on every split the record states whether it beats the best classical
  control, by what paired ratio, in what share of periods, and under which control's name any
  win falls.
- **SC-006**: The owner can read from one table, per split, what is classical, what is
  hedging and what, if anything, is learning.

## Assumptions

- The learned model is a control-and-candidate in one: if it beats every classical control
  on the mismatch splits it becomes the candidate time-late system for a later gate; nothing
  is carried from this spec alone.
- "Best classical control" is chosen per split on the validation seed by median period range
  error, before the learned model is scored.
- Budget: the unspent part of the owner's $50 (about $24). Modal's new monthly credit is not
  assumed; using it beyond the $50 total needs the owner's word.
- Periods are cut as in Gate T (random periods from 5-second MAN2 engagements); the model's
  window covers the longest period.
- The severities for correlated errors and outliers are spec 010's central condition and one
  step either side where the generator allows.
- The registered form is a study with criteria the sample can decide, proposed as an SRD §5
  row; the owner merges the amendment.
- If the controls close the gaps (the best control within 10% of the reference on every
  mismatch split), the learned model is still scored once as registered.
