# Feature Specification: Time-late, the classical follow-on to Gate T

**Feature Branch**: `014-time-late-classical` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-12

**Status**: Draft

**Input**: Owner decision, 2026-11-12, after Gate T: classical work first. Nothing is trained
and no GPU run is made. Deliver what spec 013 owed and what the Gate T panel asked for, so that
Gate T's upper limit on headroom becomes an attainable figure and a decision on a learned
whole-period model can be made on evidence.

**SRD traceability**:
- §5, Gate T row (re-registered 2026-11-12) and the rules it inherits: references on the same
  rows, efficiency against the bound per slice, paired statistics clustered by period, fresh
  seeds, registration before results.
- §9, 2026-11-12: the owner's follow-on decision.
- Annex B (the manoeuvre model whose statistics the search uses as its prior).
- Spec 013 requirements not delivered: FR-003 (correlated errors beside), FR-011 (manoeuvre
  counts and timing), FR-013 (splits), FR-022 (a classical whole-period reference line),
  FR-030 and FR-031 (bearing-rate thinning).
- Panel review: `experiments/20261112-gt2/review.md` (major findings 1 to 9 and its list of
  what is wanted before any learned model).

**Owner decisions this spec implements**:
- 2026-11-11: test whether thinning bearings where the bearing rate is steady helps.
- 2026-11-12: classical work first; a learned whole-period model is decided after it.
- Standing: 10% is the materiality threshold for headroom (specs 010, 011, 013).

## Background

Gate T (test seed 331) found that a classical search over manoeuvre histories, scored by
evidence under Annex B's statistics, gives a whole-period track with a median range error of
0.039 against 0.088 for the standing classical system C″ read as a track. The panel accepted
the figures and showed that they do not yet say what they were taken to say:

- The search wins where it names the true history (0.032 against 0.081) and where it does not
  (0.057 against 0.093). How much of the gain is the arc model, the prior and the use of the
  whole period, and how much is finding the history, is not measured.
- The headroom (search ÷ reference 1.46; period by period 1.17) is an upper limit: all of it
  sits in periods where the search names the wrong history, and an unknown share of those are
  ambiguous in the bearings themselves.
- The search misses 23% of true manoeuvres (41% under a shifted prior) and, in the 12 periods
  with no manoeuvre, declares one in 7. A target that holds course is the commonest real case
  and was hardly sampled.
- Its candidate probabilities are honest on average only, and carry no meaning when the
  target does not manoeuvre as the prior says; nothing in the output shows which case applies.
- Everything was measured with independent Gaussian bearing errors.

A learned whole-period model would have to beat a classical system given the same knowledge.
This spec builds that comparison's missing parts and says how much there is to win.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Where the search's gain comes from (Priority: P1)

A researcher sees Gate T's gain over C″ split into two parts by two controls scored on the
same periods: C″'s own manoeuvre times refitted over the whole period with the arc model and
the prior (no search), and the search run with an uninformative prior.

**Why this priority**: it decides what a learned model should be asked to do. If refitting
C″'s times gives most of the gain, the open problem is identification only; if not, the search
is doing real work.

**Independent Test**: from one scoring run, the track error of C″, C″ refitted, the flat-prior
search, the search and the reference on the same periods, with paired per-period ratios.

**Acceptance Scenarios**:

1. **Given** the scored periods, **When** the record is read, **Then** it states the share of
   the C″-to-search gain that the refit alone obtains, with an interval.
2. **Given** the flat-prior search, **When** compared with the search, **Then** the record
   states what the manoeuvre statistics add beyond the model and the whole period.

---

### User Story 2 - How often the bearings cannot decide (Priority: P1)

A researcher sees, for every period where the search names a wrong history, whether the true
history was within reach: both histories fitted properly, their evidence compared, and the
period classed as ambiguous, as a failure of the search, or as a failure of the evidence.

**Why this priority**: it turns Gate T's upper limit into an attainable headroom, which is the
figure the owner's decision on a learned model rests on.

**Independent Test**: the three shares with intervals, and the search-to-reference ratio
recomputed with ambiguous periods set aside, from one scoring run.

**Acceptance Scenarios**:

1. **Given** the classes, **When** the attainable headroom is computed by the rule declared
   beforehand, **Then** the record says whether it is material at 10%.
2. **Given** an ambiguous period, **When** its candidates are read, **Then** the record says
   how often the true history is among the first three.

---

### User Story 3 - A target that never manoeuvres (Priority: P1)

An analyst hands over a period in which the target held course throughout. The record says how
often each system declares a manoeuvre that did not happen, and what that costs in track error.

**Why this priority**: it is the commonest real case and the worst false alarm for a system
whose prior expects manoeuvres; Gate T had 12 such periods.

**Independent Test**: on a split of held-course periods, the false-manoeuvre rate and the
track error of the search, C″ and a one-leg fit, with intervals.

**Acceptance Scenarios**:

1. **Given** held-course periods, **When** scored, **Then** the false-manoeuvre rate of the
   search and of C″ is reported, and the search's track error is compared with the one-leg fit,
   which is the right model there.

---

### User Story 4 - Does thinning by bearing rate help? (Priority: P2)

A researcher sees the owner's idea tested on the whole-period search: where the bearing rate is
steady within a tolerance, a run of bearings is replaced by fewer observations. Dropping
bearings, fixed-length normal points and bins set by bearing-rate steadiness are compared with
the full data for accuracy, run time and behaviour when some bearings are wild.

**Why this priority**: the search takes minutes a period; if compression costs little accuracy
it makes every later study cheaper, and a robust bin may remove wild bearings. It does not
change what the other stories conclude.

**Independent Test**: track error and run time with and without each form on the same
periods, clean and with outliers, and the adoption rule's outcome.

**Acceptance Scenarios**:

1. **Given** the adoption rule declared beforehand, **When** the forms are scored, **Then**
   the record says which form, if any, is adopted, and the later stories use it or not
   accordingly.

---

### User Story 5 - Beyond the conditions Gate T measured (Priority: P2)

A researcher sees the same systems scored where Gate T did not look: with correlated and
outlying bearing errors, on whole engagements, by ownship manoeuvre, position in the period and
range band, with manoeuvre counts and timing error as outputs, and beside a smoothed tracking
filter as the conventional whole-period method.

**Why this priority**: it bounds how far the Gate T result may be carried; it does not decide
the follow-on by itself.

**Independent Test**: each table can be recomputed from the committed run.

---

### User Story 6 - A search that knows when its prior is wrong (Priority: P3)

A researcher sees a diagnostic that flags periods whose manoeuvres do not look like the prior's,
and a search with a broadened prior, both measured on the shifted split.

**Why this priority**: under a wrong prior the candidates carry a rank and no probability; a
diagnostic is what would let an analyst know. It is exploratory and reported, not gated.

**Independent Test**: the diagnostic's detection rate on shifted periods at a declared false
alarm rate on Annex B periods; calibration gap of the broadened search on both splits.

### Edge Cases

- A period with no determined rows: counted, kept out of ratios, as in Gate T.
- A manoeuvre that began before the period or ends after it: the track is scored; the change
  is not counted as missed or false.
- A held-course period in which the ownship does not manoeuvre: range is undetermined; the
  false-manoeuvre rate is still scored, the track error is not.
- Two true manoeuvres closer together than the match tolerance.
- A thinning bin that spans a manoeuvre, a dropout or a wild bearing.
- A period where the fit of the true history does not converge from neutral starts: counted
  and reported apart, never replaced by a fit started at the truth.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen and corrected**

- **FR-001**: C, C″, and Gate T's registered code, plans and records MUST NOT change. Gate T's
  search MUST remain runnable exactly as registered, as a system named for that registration.
- **FR-002**: The three recorded errors in the manoeuvre prior MUST be corrected in a version
  with its own code digest, and the effect of the correction on the search's track error,
  manoeuvre counts and candidate calibration reported on the same periods, before any other
  study uses the corrected version.

**Controls and decomposition**

- **FR-003**: A control MUST refit C″'s own manoeuvre times over the whole period with the arc
  model and the prior, with no search over histories.
- **FR-004**: A control MUST run the search with an uninformative prior over manoeuvre
  histories; what "uninformative" means MUST be declared before it is scored.
- **FR-005**: The record MUST state the share of the C″-to-search gain obtained by FR-003,
  with an interval, overall and split by whether the search's first candidate is the true
  history.

**Ambiguity and attainable headroom**

- **FR-006**: For each period where the search's first candidate is not the true history, the
  true history and the search's history MUST both be fitted from starts that do not use the
  true states, and the period classed by a rule declared beforehand as: ambiguous (the
  evidence does not separate them), search failure (the true history has clearly higher
  evidence and was not found), or evidence failure (the wrong history has clearly higher
  evidence).
- **FR-007**: The attainable headroom MUST be defined before results as the search-to-reference
  comparison under a declared treatment of ambiguous periods, reported both as a ratio of
  medians and paired per period, and judged material against 10%.
- **FR-008**: The record MUST report how often the true history is among the first three
  candidates within each class.

**Quiet targets**

- **FR-009**: A split of periods in which the target holds course throughout MUST be scored,
  large enough for the false-manoeuvre rate to have an interval no wider than ±5 points.
- **FR-010**: On that split the false-manoeuvre rate of the search and of C″, and the track
  error of each beside a one-leg fit, MUST be reported; periods where range is undetermined
  are scored for false manoeuvres only.

**Thinning**

- **FR-011**: Dropping, fixed normal points and bearing-rate-adaptive bins MUST be compared
  with the full data on the search: track error, manoeuvre counts and run time, on clean data
  and with outliers.
- **FR-012**: The adoption rule (the accuracy loss tolerated for a given saving in run time)
  MUST be declared before the comparison is scored; the outcome applies to the later runs of
  this spec.

**Scored outputs and conditions**

- **FR-013**: Every scored system that states manoeuvres MUST report matched, missed and false
  manoeuvre counts and timing error, at more than one match tolerance.
- **FR-014**: Every ratio of medians MUST be reported beside the paired per-period ratio, the
  share of periods on which each side is better, and the share where one is more than twice
  as bad.
- **FR-015**: Results MUST be split by number of ownship manoeuvres in the period, position in
  the period (first, middle, last leg), range band and number of true manoeuvres; efficiency
  against the bound MUST be reported per split for systems the bound applies to, and the
  record MUST say for which systems it does not.
- **FR-016**: The systems MUST also be scored under correlated and under outlying bearing
  errors, and on whole engagements, beside the primary condition.
- **FR-017**: A smoothed tracking filter that uses the whole period MUST be scored as a
  conventional reference line.
- **FR-018**: C″ read as a track, one leg, the reference fitted from neutral starts and the
  whole-period bound MUST be on the same rows as every system.

**Prior robustness (reported, not gated)**

- **FR-019**: A diagnostic for prior mismatch MUST be measured as a detection rate on shifted
  periods at a false-alarm rate fixed on Annex B tuning periods.
- **FR-020**: A search with a broadened prior MUST be scored on both splits for track error and
  candidate calibration, beside the corrected search.

**Process**

- **FR-021**: Settings are chosen on the tuning seed only. What is decided on fresh seeds (at
  least FR-005, FR-007 and FR-010), with thresholds and forecasts, MUST be registered in a
  decision record before the validation seed is generated; the test seed is generated only
  after validation shows the references sound.
- **FR-022**: The record MUST list anything in this spec that was not run.
- **FR-023**: Nothing is trained; no paid compute is used.

### Key Entities

- **Period**: a stretch of bearings and ownship track cut from an engagement, with the true
  manoeuvres inside it.
- **History**: the number, times and kinds of the target's manoeuvres over a period.
- **Candidate**: a history with its fitted track and a stated probability.
- **Class of a wrong period**: ambiguous, search failure or evidence failure.
- **Condition**: the bearing-error model and the manoeuvre statistics a split is drawn from.
- **Decision record**: what is decided on fresh seeds, with thresholds and forecasts, written
  before those seeds exist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The record states what share of the search's gain over C″ comes from refitting
  C″'s own manoeuvre times, with a 95% interval, on a fresh test seed.
- **SC-002**: The record states the share of wrong-history periods that are ambiguous, and an
  attainable headroom with a 95% interval judged against 10%.
- **SC-003**: The false-manoeuvre rate on held-course periods is stated for the search and for
  C″ with intervals no wider than ±5 points.
- **SC-004**: The thinning study ends in "adopted" (naming the form) or "not adopted" by a rule
  written beforehand.
- **SC-005**: Every item spec 013 owed is either delivered or listed as not run with a reason.
- **SC-006**: The write-up gives the owner one recommendation on a learned whole-period model
  (pursue, with what it must beat and on which splits; or do not), following from SC-001 to
  SC-003 by a rule stated before the test seed is scored.
- **SC-007**: A review panel can recompute every headline figure from the committed files.

## Assumptions

- Seeds: 333 tuning, 334 validation, 335 test; 324 and 325 stay unused.
- Periods, bearing interval, scoring rows, the "determined" rule and the period bootstrap are
  Gate T's. The shifted split is Gate T's ranges file.
- The primary condition stays independent Gaussian errors at σ = 1°; correlated and outlier
  conditions come from spec 010's declared grid at its primary severities.
- Held-course periods are generated from a ranges file in which the target does not manoeuvre;
  the ownship manoeuvres as in Annex B.
- The corrected prior becomes the search used in this spec once FR-002 has reported its
  effect; Gate T's search stays available under its registered digest.
- Run time limits what can be scored: the search took minutes a period in Gate T. Split sizes
  are set in the plan from measured run time on free runners, and the secondary conditions
  (FR-016) may use fewer periods than the primary ones, stated in the record.
- User Story 6 is exploratory: if time is short it is the first to be cut, and FR-022 records
  that.
- Whether this spec ends in a registered gate with an SRD row or a registered study is settled
  in the plan; either way thresholds and forecasts precede fresh-seed results.
