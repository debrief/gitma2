# Feature Specification: Time-late, a manoeuvre prior that adapts to the period, and a hedged track

**Feature Branch**: `018-adaptive-prior` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-14

**Status**: Draft

**Input**: Owner decision, 2026-11-14, after spec 017's panel review: option B. A manoeuvre
prior that adapts to the period, and beside it a hedged track for the periods where the
limit is identifiability. Classical, CPU only; nothing trained; no GPU.

**SRD traceability**:
- §1 (the time-late consumer), §5 (references on the same rows, paired statistics, fresh
  seeds, registration before results) and §9, 2026-11-14 (the standing control; this
  decision is added to §9 as proposed, the owner merges).
- Panel review `experiments/20261114-tl5/review.md`: findings 1 to 4 and "The panel's order
  for what follows", items 1 and 2.

**Owner decisions this spec implements**:
- 2026-11-14: option B.

## Background

The standing time-late system is the classical control: wild bearings edited out, an
effective bearing sd, a search over manoeuvre histories scored by evidence under Annex B's
prior pooled with one fixed broadened prior, a manoeuvre declared only at an evidence
margin. On targets that manoeuvre more often and less sharply than Annex B says, it is
2.3 times a fit told the true history.

Spec 017 took that gap apart. In about two thirds of periods the limit is manoeuvres the
bearings barely show: there the control is within 1.2 of a reference that is not told
them. In under a third the control misses manoeuvres the bearings do show, and those
periods carry most of the closable gap. Of those misses about half are found by the same
search when it is given the targets' own manoeuvre statistics, which is 1.17 better
overall, 2.6 times better where it finds more, and pays in false manoeuvres (0.48 a period
against 0.34). In most such periods the control declares fewer manoeuvres than happened:
Annex B's prior tells it the target is quiet.

A real system is not told the target's statistics. Two classical things remain to try. A
prior whose manoeuvre rate is inferred from the period itself, so that a busy target is
recognised as busy; and, where the bearings cannot decide, a track that states the
weighted mean of the candidates and a spread, instead of committing to one history.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A control that recognises a busy target (Priority: P1)

The owner sees a control that is not told which kind of target it faces, infers how busy
the target is from the period's own bearings, and is compared with the standing control
and with the search told the true statistics.

**Why this priority**: it is the lever spec 017 identified, and the cheapest.

**Independent Test**: on periods of busier targets the adaptive control's error is reported
against the standing control's and the true-prior search's, paired per period, with the
manoeuvres each finds and invents.

**Acceptance Scenarios**:

1. **Given** periods of targets busier than Annex B, **When** the adaptive control runs
   untold, **Then** its gain over the standing control is stated with an interval, and the
   share of the true-prior search's gain it obtains.
2. **Given** periods of Annex B targets and of targets that never manoeuvre, **When** it
   runs, **Then** its cost there is stated: range, course and speed error, false manoeuvres
   a period, and one-manoeuvre targets called quiet.
3. **Given** periods with outliers or correlated errors, **When** it runs, **Then** it is
   shown not to mistake error structure for manoeuvring.

---

### User Story 2 - A track that hedges where the bearings cannot decide (Priority: P1)

An analyst receives, beside the declared history, a track that is the probability-weighted
mean of the candidate histories (across the rates considered as well), with a stated
spread, and sees whether that spread can be trusted.

**Why this priority**: in two thirds of busy-target periods no detector can do better; an
honest answer there is a hedge with a spread.

**Independent Test**: the hedged track's range, course and speed errors are reported against
the declared track's on every split, and the stated spread's coverage of the truth.

**Acceptance Scenarios**:

1. **Given** a period whose candidates disagree, **When** the hedged track is produced,
   **Then** it states position, course and speed with a spread at every scored moment.
2. **Given** the test seed, **When** the spread is checked, **Then** the share of rows
   whose true range lies inside the stated interval is reported against its nominal level,
   overall and by how many manoeuvres the period has.

---

### User Story 3 - Which output stands, and when (Priority: P2)

The owner sees one table that says whether the standing output should be the declared
history, the hedged track, or one chosen per period by a rule the system can apply without
the truth, and what each choice costs on each kind of target.

**Independent Test**: the registered rule's output is stated from the test seed, with the
evidence each condition read.

---

### User Story 4 - Where the gain comes from (Priority: P2)

A researcher sees any gain split by the kind of period spec 017 identified (the standing
control misses a detectable manoeuvre, or does not; the bound tight, middle or loose), so
that a pooled figure is not mistaken for a typical one.

**Independent Test**: each paired comparison is reported pooled and by those kinds, with
period counts.

### Edge Cases

- A period too short to say anything about the rate: the adaptive prior falls back to the
  standing control's.
- A period of a quiet target: a high inferred rate would invent manoeuvres.
- Outliers or correlated errors that look like many small manoeuvres.
- Candidates that are mirror images: their mean is a track no target followed.
- A period where every candidate is the same history: the hedge equals the declared track
  and its spread is the fit's own.
- A system with no state on some rows: periods lost from a paired comparison are counted.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen**

- **FR-001**: C, C″, the standing control and the registered code paths, plans and records
  of Gate T and specs 014 to 017 MUST NOT change in behaviour. The standing control is run
  as study L registered it.

**The adaptive prior**

- **FR-002**: A control MUST be built whose manoeuvre prior is not fixed: how often the
  target manoeuvres, and how sharply, is inferred from the period's own bearings by
  classical means. It is not told the split or the generator's settings for it.
- **FR-003**: Its settings MUST be chosen on the tuning seed only and frozen before the
  fresh seeds exist. Nothing is trained.
- **FR-004**: It MUST be compared with the standing control (declared) and with the search
  told the split's own statistics, on: two splits of busier targets, Annex B targets,
  targets that never manoeuvre, outliers, and correlated errors.
- **FR-005**: For each comparison the record MUST state: the paired per-period ratio with
  its interval, the median per-period ratio, the shares of periods over twice as bad on
  each side, and the number of periods in the pair; for range, course and speed.
- **FR-006**: Manoeuvres missed and false MUST be reported at each of three matching
  tolerances; false manoeuvres a period on quiet targets; one-manoeuvre targets called
  quiet.
- **FR-007**: The rate the adaptive prior infers MUST be reported against the true rate of
  each split.

**The hedged track**

- **FR-008**: A hedged track MUST be produced from the candidate histories, weighted by
  their probabilities and pooled across the rates considered, stating position, course and
  speed and a spread at every scored moment.
- **FR-009**: It MUST be scored against the declared track in range, course and speed on
  every split, and its stated spread MUST be checked for coverage of the truth against its
  nominal level, overall and by the number of true manoeuvres.
- **FR-010**: A rule the system can apply without the truth for choosing between declared
  and hedged output per period MAY be proposed from tuning data; if registered it is scored
  as a third output.

**Reading the result**

- **FR-011**: Every pooled comparison on the busier-target splits MUST also be reported by
  kind of period: whether the standing control misses a manoeuvre the bearings show, and
  by how tight the bound is.
- **FR-012**: References told the true times MUST be named as such and not called bounds
  or limits.

**Registration and process**

- **FR-013**: What is decided, the conditions, the sample sizes and what follows MUST be
  fixed in a decision record before the fresh seeds exist. Each condition MUST be shown,
  on tuning data, to be able to come out either way at the planned size, MUST read cost
  and not counts, and MUST state its sensitivity to the matching tolerance where it uses
  one.
- **FR-014**: Seeds: 345 tuning, 346 validation, 347 test. Soundness is read on validation
  and stops the study if it fails. The test is scored once.
- **FR-015**: Every table MUST be generated by a committed script; the new runner and
  study code MUST have unit tests; the record MUST list what was promised and not
  delivered.
- **FR-016**: A five-reviewer panel MUST decide the result; kickoff and slides posts as the
  constitution requires; SRD §9 records the owner's decision (proposed; the owner merges).

### Key Entities

- **Adaptive control**: the standing control with its manoeuvre prior inferred from the
  period.
- **Inferred rate**: what the adaptive prior concludes about how busy the target is.
- **True-prior search**: the search told the split's statistics; the reference for what a
  right prior is worth, not a bound.
- **Hedged track**: the probability-weighted mean of the candidates with a spread.
- **Kind of period**: by whether the standing control misses a detectable manoeuvre, and
  by bound tercile.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On busier targets the adaptive control's gain over the standing control is
  stated with a 95% interval, and as a share of the true-prior search's gain.
- **SC-002**: Its cost on Annex B targets and quiet targets is stated in error, in false
  manoeuvres a period and in one-manoeuvre targets called quiet, and the registered
  no-harm conditions are decided.
- **SC-003**: The hedged track's error against the declared track's is stated on every
  split in range, course and speed, and the coverage of its spread against the nominal
  level.
- **SC-004**: The owner can read from one table which output stands as the time-late
  system after this study and under what conditions.
- **SC-005**: Every paired figure carries its period count, and every pooled figure on the
  busier splits its split by kind of period.

## Assumptions

- The standing control's own settings (editing, effective sd, margin, quiet probability)
  are kept; only the manoeuvre prior and the output form change.
- "Classical" means inference from the period's bearings by likelihood or evidence; no
  parameters are fitted to simulated populations beyond a handful of settings chosen on
  the tuning seed.
- The busier-target splits are spec 017's two (shifted and shifted 2); outliers and
  correlated errors are study L's conditions.
- If the adaptive control gains on busier targets without registered harm, it is proposed
  as the standing system; if it gains with harm, the owner decides; if it does not gain,
  the standing control stays and the result is written up. The hedged track is adopted as
  an output only if its spread is shown to be honest.
- The evidence's recorded faults (prior version 3 at the edges of its support) are not
  repaired here; they apply to both sides of every comparison.
