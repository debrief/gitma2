# Feature Specification: Time-late, one diagnostic of the true prior's gain, and the track written up as a whole

**Feature Branch**: `019-time-late-synthesis` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-15

**Status**: Draft

**Input**: Owner decision, 2026-11-15, after spec 018's panel review: option B. Write up the
time-late track (specs 013 to 018) as a whole with the classical control standing, after
one diagnostic on already-used seeds: a search under the nearest prior, and under the
truth's speed-change and kind ranges. CPU only; no new seed; nothing trained.

**SRD traceability**:
- §1 (the time-late consumer), §5 (references on the same rows, paired statistics) and §9
  (the owner's decision is added as proposed; the owner merges).
- Panel review `experiments/20261115-tl6/review.md`: finding 5 and "The panel's order for
  what follows", items 1 and 2.

**Owner decisions this spec implements**:
- 2026-11-15: option B.

## Background

Spec 018 found that a control choosing among 30 manoeuvre priors by one period's evidence
gains nothing on busier targets, while the same search told the targets' own statistics is
about 1.15 better over three seeds, in a minority of periods. The panel said one thing was
left confounded. The family's members only refitted a shared set of candidate histories,
while the true prior had a search of its own; and the family differed from the truth in
parts never varied (speed-change range, kinds of manoeuvre, turn rates, the smallest
turn). So the study could not say whether the family was the wrong family or the method
could not work.

That is cheap to settle on periods already used, and it changes how the track is written
up: "the right prior helps through one identifiable part" and "it helps only as a whole"
lead to different advice.

Six specs then need one account. Each has its own write-up; none says what the time-late
work as a whole established, what it did not, and what a reader should take from it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Which part of the true prior buys its gain? (Priority: P1)

A researcher sees the search run under a ladder of priors that starts at the broadened
prior and takes on the busier targets' own statistics one part at a time, each with its
own search, on periods already used.

**Why this priority**: it settles the one confound spec 018's panel named, before the
write-up states a conclusion about priors.

**Independent Test**: for each rung the error against the standing control and against
the true-prior search is reported on the same periods, with intervals and period counts.

**Acceptance Scenarios**:

1. **Given** the shifted periods of a used seed, **When** the ladder is run, **Then** each
   rung's ratio to the standing control is stated in range, course and speed, and the
   rung at which most of the true prior's gain appears is named, or it is stated that no
   single rung carries it.
2. **Given** the family member nearest the truth, **When** it is given a search of its
   own, **Then** its error is compared with the same member refitting shared candidates
   (spec 018's record of the same periods).

---

### User Story 2 - The time-late track in one account (Priority: P1)

The owner reads one post that says what specs 013 to 018 established about the time-late
consumer, with the numbers that survived their panels, what was withdrawn or corrected,
what was never tested, and what the standing system is and is not.

**Why this priority**: it is what the owner asked for.

**Independent Test**: every figure in the account is traceable to a committed record and
its panel review; every claim a panel narrowed is stated in its narrowed form.

**Acceptance Scenarios**:

1. **Given** the six specs' records, **When** the account is read, **Then** it states the
   standing system, its measured gains and its known faults, each with its source.
2. **Given** a claim a panel corrected, **When** it appears, **Then** it appears as
   corrected, and the list of forecasts that were wrong is given.
3. **Given** the founding question (can a learned component beat the classical one where
   the constant-velocity model fails), **When** the account ends, **Then** it says what
   the time-late work adds to the answer and what would have to be different to try again.

---

### User Story 3 - What an analyst can be shown (Priority: P2)

A reader sees, in the slides, the standing system's track on example periods beside the
older system and the truth, with the cases where it fails shown as plainly as the cases
where it works.

**Independent Test**: the slides carry track plots chosen by a rule and charts regenerated
from committed records.

### Edge Cases

- A rung whose search finds nothing in a period: counted and reported, not dropped silently.
- The ladder's order matters if the parts interact: the last rung equals the true prior,
  and the single-part rungs (one part alone on the broadened prior) are reported beside.
- A used seed's periods have been seen: nothing here is a registered result, and the
  account says so wherever the diagnostic is quoted.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen**

- **FR-001**: Registered code paths, plans and records of earlier specs MUST NOT change in
  behaviour. The standing control is run as study L registered it.

**The diagnostic**

- **FR-002**: On shifted periods of an already-used seed, the search MUST be run, each
  time as a search of its own, under: the broadened prior; that prior with the truth's
  leg statistics; with the truth's turn sizes as well; with its turn rates; with its
  speed changes; and with its kinds of manoeuvre, which is the true prior.
- **FR-003**: Each part alone on the broadened prior MUST also be run, so that a part's
  effect is seen without the others.
- **FR-004**: The family member nearest the truth MUST be run with its own search and
  compared with spec 018's refit of shared candidates on the same periods.
- **FR-005**: Every comparison MUST be paired per period against the standing control, in
  range, course and speed, with intervals, period counts, the median per-period ratio and
  the share of the gain carried by the ten best periods.
- **FR-006**: The diagnostic MUST be labelled development work on used data wherever it is
  reported. No seed is generated that has not been used.

**The account**

- **FR-007**: One write-up MUST cover specs 013 to 018: what was built, the standing
  system, each result as its panel left it, what was withdrawn, the forecasts that were
  wrong, what was not tested, and what follows.
- **FR-008**: Every figure MUST cite its record; no figure may be quoted in a form its
  panel corrected.
- **FR-009**: The account MUST state what the time-late work adds to the project's
  founding question and under what changed conditions a learned approach would be worth
  trying again.
- **FR-010**: A slides post MUST accompany it, with charts from committed records and
  track plots chosen by a rule; a kickoff post precedes; SRD §9 records the decision
  (proposed; the owner merges).
- **FR-011**: Independent reviewers MUST check the account against the records before the
  PR is ready, and their corrections MUST be applied.

### Key Entities

- **Ladder of priors**: from the broadened prior to the true prior, one part at a time.
- **Single-part rungs**: each part alone on the broadened prior.
- **The account**: the write-up of specs 013 to 018.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The reader can say from one table whether the true prior's gain sits in one
  part, in several, or only in the whole.
- **SC-002**: Search-of-its-own against refit is stated for the nearest member with an
  interval.
- **SC-003**: The account states, for the standing time-late system, its gain over the
  older system and its error against the true-history reference on each kind of target
  and bearing error tested, each with its source.
- **SC-004**: Reviewers find no figure in the account that disagrees with its record.

## Assumptions

- The diagnostic uses the first 150 shifted periods of seed 347 (spec 018's test seed, now
  used), so that spec 018's stored tracks of the same periods can be compared.
- The time-late track ends with this spec unless the diagnostic shows something the owner
  wants pursued; no further identification study is proposed by default.
- GPU: none. About $9 of the owner's $50 is unspent and stays unspent.
