# Feature Specification: Steady-leg segmentation and Gate S

**Feature Branch**: `005-steady-leg-segmentation` (developed on `claude/inspiring-curie-j192v9`)

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: the owner's draft "gitma2 Spec 004 — Steady-Leg Detector (Gate D)"
(3 November 2026), with the review changes the owner accepted ("go ahead, write it as spec 005"):
segment each engagement into steady legs, transitions and unknown intervals, for ownship and
target; a classical target segmenter as the reference and a learned one that must beat it; legs
handed to the physics layer as gaps or chords; contamination as the primary error; a new gate
whose only learning claim is recovering more of the gap to the oracle than the classical
segmenter.

**SRD traceability**: SRD Annex A as amended by §A.9 (this spec's companion amendment, merged by
the owner); SRD §4 (physics layer inputs), §5 (references, metrics, statistics; Gate 2's "half the
gap to the oracle"); constitution 1.2.0 III (physics does the numerics, learning the judgement),
IV (honest measurement), V (gates). Evidence: `docs/research/05` (oracle segmentation), `06`
(design rethink), `07` (steady-leg pilot), `08` (leg-detection spike, §6 turn windows);
`experiments/20261101-p0-r4/review.md` (masked turns against the chord, with noise).

**Relation to spec 004**: spec 004 and Gate D stand as recorded. Gate D stopped at validation, and
its criteria and verdict are unchanged. Test seed 305 stays reserved. This spec defines a new
gate, **Gate S**, and does not re-score Gate D.

**Naming**: the owner's draft called the components D1, D2 and D3. Annex A already uses D1–D4 for
its defaults, so this spec calls them **O** (ownship steady-leg detector, the draft's D1), **C**
(classical target leg segmenter, D2) and **L** (learned target segmenter, D3).

## Why the existing detectors fall short

Every prior detector flags turn edges instead of finding legs, and none estimates how long a
transition lasts.

| Detector | Shortfall |
| --- | --- |
| Debrief ArcTan slicing (2015) | One split per ownship leg; fixed buffer; ZigRatio not tied to bearing noise |
| Multi-leg slicing (2017 note) | With two real zigs the best single split lands between them; splits must be searched jointly |
| Ownship single-pass and twin-pass | Heading only; timing depends on the window; averaging blunts turns |
| gitma phase 3b | Learned P(turned) flagged ~30% of held rows; trained on a mixture, it hedges |
| Gate D detector (spec 004) | Never raised an alarm: its `p_change` reads only time since the zig |
| GLR + confirm (note 08) | Best so far (range 0.81 × the IMM), but point knots, one test per alarm episode; half the misses of detectable manoeuvres are turns inside an already-raised episode |

## Definitions

Each bearing time is labelled, per vessel, steady, transition or unknown. Truth labels apply the
same definitions to the true tracks.

| Term | Definition | Adopted default (owner, 3 Nov 2026) |
| --- | --- | --- |
| Steady leg | Course within ± C of the leg mean and speed within ± S, for at least L_min | C = 2°, S = 0.5 kt, L_min = 2 min |
| Transition | Interval between two steady legs; no motion model assumed | Length ≥ T_min = 30 s; estimated, not fixed |
| Unknown | Interval the data cannot classify (too short, or too little bearing information) | Reported, never forced into a leg |
| Gap | A transition handed to the physics layer: its bearings excluded and a knot at each end | — |
| Chord | A transition handed to the physics layer: a knot at each end, the bearings kept, the speed prior across it | — |
| Contamination | Fraction of time labelled steady that is truly transition | Primary error measure |
| Coverage | Fraction of truly steady time labelled steady | Secondary measure |
| Detectable change | A target change whose detectability (note 08 §2: the oracle cost drop, χ² with 4 dof) is at least 13.3 | — |

Reasons for the defaults:
- **L_min is 2 min, not 5.** On validation seed 304, 64% of the gaps between consecutive target
  manoeuvres are under 5 min (median 4.2 min; the generator spaces them at least 3 min apart).
  With L_min = 5 most real legs between turns would be unknown by definition.
- **T_min is 30 s.** Simulated turns last 20 s at the 10th percentile and 50 s at the median.
- **The 3-minute figure of the 2017 note** is a search-window size, not a turn duration. It is
  not a default here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A classical segmenter that finds legs, not edges (Priority: P1)

An analyst runs segmenter C on an engagement's bearing history up to now and gets back the
target's steady legs, the transitions between them with their estimated lengths, the intervals it
cannot classify, and how much better its answer is than the runner-up. Two zigs inside one ownship
leg are found as two transitions, not one split between them.

**Why this priority**: C is the reference every learned result is judged against, and on its own
it may already be the Gate 2 segmenter. Owner decision: C alone is an acceptable deliverable.

**Independent Test**: Run C on validation engagements with known truth and compare its legs with
the truth labels and with note 08's GLR + confirm on the same rows.

**Acceptance Scenarios**:

1. **Given** a noise-free engagement with two target zigs inside one ownship leg, **When** C
   segments it, **Then** it reports three target legs and two transitions, each transition within
   ± 60 s of truth.
2. **Given** an engagement with no target manoeuvre, **When** C segments it, **Then** it reports
   one target leg in at least the share of such engagements the decision record declares (the
   false-split limit).
3. **Given** two segmentations whose costs differ by less than the declared margin over some
   interval, **When** C reports, **Then** that interval is labelled unknown, not forced into a
   leg.
4. **Given** a scored row k, **When** C segments, **Then** it uses bearings at rows ≤ k only, and
   segmenting [0, k] gives the same answer whether or not later bearings exist.

---

### User Story 2 - Segmentation measured by what it does to the estimate (Priority: P1)

A reviewer reads, for each segmenter on the same rows:
- contamination, coverage and false splits;
- leg-count accuracy on detectable changes;
- the share of the gap from batch least squares to the oracle that it recovers in range and
  velocity;
- downstream error against batch least squares, the frozen IMM, the oracle and GLR + confirm.

Everything is stratified by detectability, so a miss of an invisible turn is not counted as a
failure.

**Why this priority**: Gate D measured detection, and note 08 showed that detection metrics and
downstream error can disagree. A segmenter is only as good as the estimate it feeds.

**Independent Test**: Score the oracle segmentation, the trivial segmentation (one leg) and GLR +
confirm, and check the ordering: oracle best, one leg worst, GLR + confirm reproducing note 08's
figures on the same rows.

**Acceptance Scenarios**:

1. **Given** the oracle segmentation, **When** it is scored, **Then** contamination is 0,
   coverage 1 and the gap recovered is 1 by construction.
2. **Given** the one-leg segmentation, **When** it is scored, **Then** the gap recovered is 0 by
   construction.
3. **Given** GLR + confirm's knots from note 08, **When** they are scored on the same rows,
   **Then** its downstream ratios reproduce `experiments/20261103-leg-detection-spike/spike.json`
   (range 0.81 × the IMM) to the printed precision.

---

### User Story 3 - A learned segmenter that starts at the reference (Priority: P2)

A researcher trains segmenter L, which adds per-bearing evidence to C's search. Before training
it returns C's segmentation exactly. Training moves it only if the evidence helps, and Gate S
credits learning only if L recovers more of the gap than C.

**Why this priority**: it is the learning claim. Gate 1's heads died, and Gate D's detector never
alarmed. L is built so that neither failure can pass silently.

**Independent Test**: Check that an untrained L equals C on validation, byte for byte in its
segmentation. Check that its evidence head receives a non-zero gradient from the first training
step. Check that a shuffled-label L scores no better than C.

**Acceptance Scenarios**:

1. **Given** an untrained L, **When** it segments the validation split, **Then** every
   segmentation equals C's.
2. **Given** the training loss at the zero-initialised evidence head, **When** one step runs,
   **Then** the evidence head's gradient is non-zero and finite.
3. **Given** a model trained on shuffled labels, **When** it is scored, **Then** its gap recovered
   is not better than C's (clustered interval on the difference includes or lies below zero).

---

### User Story 4 - Ownship legs (Priority: P3)

The pipeline knows ownship's steady legs and turns from navigation data, so target statistics
that assume constant relative velocity are computed inside steady ownship legs, and L can use
ownship state as an input.

**Why this priority**: ownship navigation is exact in this scope, so O is a sanity check and an
input, not a research question.

**Independent Test**: Run O on validation ownship tracks and compare with the ownship truth
labels.

**Acceptance Scenarios**:

1. **Given** an ownship track with one zig, **When** O segments it, **Then** it reports two legs
   and one transition within ± 30 s of truth, before trimming.
2. **Given** a heading crossing 0°/360° on a steady leg, **When** O segments it, **Then** no
   transition is reported.

### Edge Cases

- **A target change while ownship is turning.** Generator 0.5.0 starts target manoeuvres at least
  2 min after the zig, so this does not occur in the data. C and L must still accept it (legs may
  span ownship transitions), and it is tested on a constructed engagement.
- **Too little history.** Before the ownship zig the target's range is undetermined. C reports the
  whole prefix as one leg or unknown; it never invents a transition there.
- **Two changes closer than L_min.** The interval between them is a transition or unknown, never a
  leg shorter than L_min.
- **A change below the detectability floor.** It counts against contamination, but leg-count
  accuracy and the gate's detection measures exclude it, and its stratum is reported.
- **Dropouts inside a transition.** A transition may begin or end on a missing bearing; the
  boundaries are times, not indices of valid bearings.
- **Speed-only changes.** 81% fall below the detectability floor (note 08). They are reported in
  their own stratum.

## Requirements *(mandatory)*

### Functional Requirements

**Segmentation output**

- **FR-001**: Every segmenter MUST return, for a vessel and a prefix [0, k], a list of steady
  legs, transitions and unknown intervals that tiles [0, k], with the cost of the chosen
  segmentation and the margin to the runner-up (C and L).
- **FR-002**: Segmentation of the target MUST be offline on each prefix: at a scored row k it
  uses bearings and ownship state at rows ≤ k only. A causal, real-time variant is out of scope
  (owner decision).
- **FR-003**: The segmentation MUST be a persisted record type defined once in the schema
  (constitution I): vessel, prefix row, legs, transitions, unknown intervals, cost, margin and
  the producing segmenter's identity and digest.

**O — ownship steady-leg detector**

- **FR-010**: O MUST segment ownship navigation into steady legs, transitions and unknown, using
  course and speed jointly, by a penalised change-point search with course wrap at 360°.
- **FR-011**: O MUST accept a leg only if every sample lies within ± C and ± S of its mean, and
  MUST enforce L_min and T_min, trimming 30 s from each leg end.

**C — classical target leg segmenter**

- **FR-020**: C MUST model the target as constant-velocity legs in absolute coordinates, separated
  by transitions of at least T_min. Legs may span ownship transitions.
- **FR-021**: C MUST search the number of legs, their boundaries and the transition lengths
  jointly, not one split at a time.
- **FR-022**: C MUST run in two stages:
  - **Search.** Segments are scored by additive costs: each candidate leg's own constant-velocity
    fit residual. Each extra leg is charged a penalty derived from the known bearing noise σ
    (BIC-style), replacing ZigRatio.
  - **Coupled refinement.** The best few segmentations from the search (k declared in the plan)
    are re-scored by the whole-history physics-layer solve, in which legs share the target's
    position. The best is kept.

  Reason: the additive search needs independent leg costs, but within one ownship leg the range
  comes only from coupling the legs, so the final choice must be made coupled.
- **FR-023**: C MUST label as unknown any interval on which the best and runner-up segmentations
  differ and whose cost margin is below the declared value.
- **FR-024**: C MUST segment one prefix of 300 bearings in at most 10 s on one 4-core runner
  (search and refinement together), measured and reported.
- **FR-025**: C MUST run standalone and write its segmentations to file, so Gate 2 can report it
  beside any learned pipeline.

**Handing segmentation to the physics layer**

- **FR-030**: A segmentation MUST be convertible to physics-layer inputs in two declared modes:
  - **gap:** knots at both ends of each transition, its bearings excluded;
  - **chord:** knots at both ends, bearings kept, the speed prior across course-only
    transitions.

  The estimate always comes from the physics layer (constitution III).
- **FR-031**: Which mode is carried MUST be chosen on validation and declared in the decision
  record before any test scoring. P0 found the gap mode no better than the chord with noise:
  0.539 [0.519, 0.561] against 0.531 [0.510, 0.554] on all G5 rows.

**L — learned target segmenter**

- **FR-040**: L MUST emit per-bearing evidence (a log-likelihood ratio of steady against
  transition) that is added to C's search costs. C's search and refinement run unchanged.
- **FR-041**: L's evidence head MUST start at zero, so an untrained L returns C's segmentation
  exactly.
- **FR-042**: L MUST be trained with a loss that gives the evidence head a gradient at zero: the
  log-likelihood of the truth segmentation under a semi-Markov model whose segment scores are C's
  costs plus the evidence (computed by the differentiable forward recursion over segmentations).
  A hard decoder alone gives no gradient.
- **FR-043**: L's inputs MUST be the existing per-bearing features, O's ownship labels and C's
  per-bearing residuals. Normalisation statistics come from inputs only.
- **FR-044**: L MUST be trained with three seeds; the carried seed is the median on validation
  gap recovered; a shuffled-label control is trained and judged against C.
- **FR-045**: L's network MUST export to ONNX with cross-runtime conformance as spec 003's models
  do. The search and refinement may run in host code beside it.

**Data and truth**

- **FR-050**: The data MUST come from generator 0.5.0 unchanged. It already has turn rates of
  0.5–3°/s, rate-limited speed changes, 0–3 target changes and 180 s spacing. A new generator
  version (ownship wander, target changes during ownship turns) is out of scope.
- **FR-051**: Truth labels (steady, transition, unknown per vessel per row) MUST be derived from
  the stored true tracks with the Definitions, by a deterministic function under test, and stored
  or recomputed with the data's provenance.
- **FR-052**: Development MAY use validation seed 304. Gate S MUST be scored on a fresh test seed
  from 312 onward. Training data for L MUST come from a fresh seed. The seeds are pinned in the
  plan by digest. Seed 305 stays reserved for Gate D, and 311 was spec 004's training stream.

**Metrics**

- **FR-060**: Each segmenter MUST be scored on σ = 1° engagements for:
  - contamination (median, P90);
  - coverage;
  - false-split rate on engagements with no target change;
  - leg-count accuracy on detectable changes only;
  - boundary error at ± 60 s and ± 3 min (diagnostic);
  - gap recovered.
- **FR-061**: Gap recovered MUST be measured on σ = 1° G5 rows, in range and in velocity:
  (median error with one leg − median error with the segmentation) ÷ (median error with one
  leg − median error with the oracle). The decision record fixes whether errors are normalised by
  the known-manoeuvres Cramér–Rao bound, before any result exists.
- **FR-062**: Downstream median range, course and speed error MUST be reported for every
  segmenter against the following, on the same rows, all G5 rows and settled rows, with
  scenario-clustered paired bootstraps at 97.5%:
  - batch least squares;
  - the frozen IMM (`imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16`);
  - the chord oracle;
  - GLR + confirm (note 08's configuration).
- **FR-063**: Everything MUST be stratified by:
  - detectability band (0–13, 13–50, 50–200, ≥ 200);
  - change kind and size;
  - transition duration;
  - range band;
  - number of changes.

  Efficiency against the known-manoeuvres bound and gross-error rates MUST be reported per slice
  (constitution IV).

**Gate S**

- **FR-070**: A decision record MUST be committed before any L training. It fixes:
  - the limits for S1 and S3;
  - the margin and k of FR-022 and FR-023;
  - the physics-layer mode of FR-031;
  - the gap normalisation of FR-061;
  - the seeds;
  - the carried-seed rule;
  - a forecast.
- **FR-071**: Gate S MUST apply these criteria, each with the whole interval and the point on the
  passing side:
  - **S1 (sanity):** O's contamination P90 on ownship legs is at or below the declared limit.
  - **S2 (classical):** C recovers more of the gap than GLR + confirm (interval on the difference
    above zero). If it does not, the record says C adds nothing classical, and the better of the
    two is the reference for S4.
  - **S3:** L's contamination and false-split rate are no worse than the reference's, with the
    whole interval inside the declared limits.
  - **S4 (the only learning claim):** L recovers more of the gap than the reference, interval on
    the difference above zero.
- **FR-072**: The follow-on MUST be fixed in advance:
  - If S4 passes, L is the Gate 2 segmenter and its control.
  - If S4 fails, the reference (C or GLR + confirm) carries into Gate 2 and learning is recorded
    as not shown.

  Gate 2's "half the gap to the oracle" MUST also be reported for the carried classical
  segmenter, so a Gate 2 gain is attributed correctly.
- **FR-073**: The Gate S verdict MUST come from the agent review panel, with `review.md`
  committed.

### Key Entities

- **Segmentation**: vessel, prefix row, ordered intervals (leg, transition, unknown) with
  start and end times, cost, margin to the runner-up, and the segmenter's identity and digest.
- **Truth labels**: per vessel per row, steady, transition or unknown, from the true track and the
  Definitions; with the definitions' parameters.
- **Decision record (Gate S)**: the fixed values of FR-070, the seeds and digests, and the
  forecast.
- **Gate S record**: per segmenter and stratum, the metrics of FR-060 to FR-063 with intervals,
  and the S1–S4 verdicts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On noise-free validation engagements, C's transitions all lie within ± 60 s of
  truth on detectable changes, and it reports no false split on any engagement without a change.
- **SC-002**: On validation, the oracle, one-leg and GLR + confirm segmentations reproduce their
  known values: gap recovered 1 and 0, and note 08's ratios to the printed precision.
- **SC-003**: An untrained L returns C's segmentation on 100% of validation prefixes, and its
  evidence head receives a non-zero gradient on the first training step.
- **SC-004**: C segments a 300-bearing prefix in at most 10 s on one 4-core runner. A full
  validation scoring run (1,000 engagements, four scored rows each) finishes within one 6-hour job.
- **SC-005**: Gate S is decided by the panel, on a fresh test seed, against criteria committed
  before any L training. Every segmenter is reported beside batch least squares, the IMM, the
  oracle and GLR + confirm on the same rows.
- **SC-006**: Every reported metric is available per detectability band. A reader can see what
  share of each error comes from changes below the detectability floor.

## Assumptions

- Gaussian bearing noise with known σ, exact ownship navigation, one contact (SRD scope).
- The physics layer already accepts per-bearing log-weights low enough to exclude a bearing (the
  oracle's masked-turn mode), so FR-030's gap mode needs no new physics.
- The note 08 machinery (window fits, confirmation, the scorer) is reused, not rewritten.
- No paid compute (owner decision): C is classical and runs on free runners; L is small enough
  to train on them.
- The Annex A amendment §A.9 that introduces Gate S is merged by the owner before the Gate S
  decision record is committed.

## Out of Scope

- Real sensor data, navigation error, non-Gaussian noise, several contacts.
- Causal, real-time segmentation (owner decision: offline on each prefix only).
- Generator changes: ownship wander, autopilot oscillation, target changes during ownship turns.
- Re-scoring or amending Gate D.

## Risks

- **Weak observability.** 41% of target changes fall below the detectability floor (note 08), so C
  may recover little more than GLR + confirm. That is still a usable Gate 2 segmenter, and S2
  records it.
- **C's compute.** The search may exceed 10 s at 600 bearings. Mitigation: cap candidate
  boundaries and warm-start segment fits; the coupled stage runs on k segmentations only.
- **Tolerances drive results.** C, S, L_min and T_min shape every metric. They are fixed here and
  in the decision record before training.
- **L may add nothing.** If C already recovers most of the gap, S4 fails, and C carries.
- **Export.** The search may not fit in an ONNX graph; it runs in host code beside the exported
  network (FR-045).
