# Feature Specification: Time-late, repair and re-registration

**Feature Branch**: `015-time-late-repair` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-13

**Status**: Draft

**Input**: Owner decision, 2026-11-13, after spec 014's panel review: repair and re-register.
Fix the evidence's duration volume, the edge rule in classing and the drifting reference, then
decide the same quantities again on fresh seeds. Nothing is trained and no GPU run is made.

**SRD traceability**:
- §5 (references on the same rows, paired statistics clustered by period, fresh seeds,
  registration before results) and §9, 2026-11-13 (the owner's decision).
- Spec 014's decided quantities D1 to D5 and its decision record
  (`experiments/20261112-tl2-decision/`).
- Panel review `experiments/20261112-tl2/review.md`: major findings 1 to 6, 8, 9 and 11, and
  item 1 of what the panel wants next.

**Owner decisions this spec implements**:
- 2026-11-13: repair and re-register; small and classical.
- Standing: 10% is the materiality threshold for headroom.

## Background

Spec 014 measured where the whole-period search's gain over C″ comes from, how wrong
histories divide, what a better identifier could attain and how often a manoeuvre is declared
on a target that made none. Its figures reproduce. Its panel found that two of them rest on
defects in the registered code and that a third rests on a reference that is not what it is
called:

- The evidence allows a manoeuvre's duration about 600 seconds of room where the prior says
  20 to 120: every small, short manoeuvre is over-credited. Re-ranking stored candidates with
  a corrected volume moved the held-course false rate from 0.76 to between 0.47 and 0.57 and
  changed the first candidate in up to a fifth of Annex B periods.
- The classing counts manoeuvres cut by the period's edge, which the search can hardly
  declare. Without them the first candidate is right in about 60% of periods, not 51%.
- The fit "told the true history" moves its times freely and in 13% of periods ends as a
  different history; on the periods it replaces it is worse than the search in a third.
- Four of 369 refits of C″'s transitions ran away numerically and carry D1's point estimate.

What the decided numbers are with these repaired is not known: the effect on D1 to D3 needs
the search run again.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An evidence whose every density has its volume (Priority: P1)

A researcher can check, parameter by parameter, that the evidence credits a history with the
room its prior allows and no more, and sees what the repair changes on data already spent.

**Why this priority**: every decided quantity is read through the evidence.

**Independent Test**: for each prior factor the bearings may leave open, the density at a
point times the volume the evidence allows there is 1; and on spent periods the false-
manoeuvre rate and first-candidate accuracy are reported before and after.

**Acceptance Scenarios**:

1. **Given** a small speed change the bearings cannot exclude, **When** its evidence is
   computed, **Then** the room allowed for its duration is what the prior allows.
2. **Given** spec 014's registered search, **When** run beside the repaired one, **Then** it
   still reproduces spec 014's fixture.

---

### User Story 2 - One rule for manoeuvres cut by the period (Priority: P1)

A researcher sees every comparison of a found history with the true one (right or wrong, the
classes, the candidates' accuracy, the counts) use the same rule: a manoeuvre the period cuts
is neither required nor counted against a system.

**Independent Test**: a period whose only difference from the search's history is a cut
manoeuvre is "right" in every reading; a manoeuvre that ends on the period's last row but is
complete is not treated as cut.

---

### User Story 3 - A reference that is the history it is named for (Priority: P1)

A researcher sees the fit told the true history's structure stay that history: where its times
drift beyond the match tolerance it is refitted with its times held, flagged, and every reading
that uses it is also given without the flagged periods.

**Independent Test**: no reference used in a composite fails the study's own match rule
against the truth; the share flagged is reported.

---

### User Story 4 - The same questions decided again (Priority: P1)

The owner sees D1 to D4 decided on a fresh test seed with the repairs in, beside the old
figures, with the sensitivities the panel asked for, and a statement of what follows for a
learned model that separates the rule's output from what the evidence supports.

**Independent Test**: one scoring run gives D1 to D4, each at every registered sensitivity
value, and the before-and-after of the repair on the same periods.

**Acceptance Scenarios**:

1. **Given** the registered rule, **When** the test seed is scored, **Then** the record states
   the rule's output and, separately, the headroom on every split with what was and was not
   tried there.
2. **Given** the mixed prior, **When** scored, **Then** the record states how often it calls a
   manoeuvring target quiet, by number of true manoeuvres, beside its false-manoeuvre rate.

### Edge Cases

- A manoeuvre cut at the period's start and another at its end.
- A found manoeuvre that pairs with a cut true one: not false.
- A manoeuvre of the minimum duration the solver allows.
- A refit that diverges: the control falls back by a rule a real system could apply.
- A true-history fit that does not converge even with times held: counted, reported apart.
- A period with no determined rows: classed and counted, kept out of ratios, and the two
  denominators stated wherever both appear.

## Requirements *(mandatory)*

### Functional Requirements

**Frozen**

- **FR-001**: C, C″, Gate T's and spec 014's registered code paths, plans and records MUST
  NOT change in behaviour; both fixtures MUST still pass.

**Repairs**

- **FR-002**: A new prior version MUST give every factor that has no Gaussian residual a
  volume equal to the reciprocal of its density at the fit, including a manoeuvre's duration
  for turns, speed changes and combined manoeuvres. A test MUST check density times volume
  for each such factor.
- **FR-003**: The smaller recorded inconsistencies (the leg's survival and tail under the
  renormalised density; the flat prior's ordered starts) MUST be fixed in the same version.
- **FR-004**: One function MUST decide whether a found history is the true one, ignoring
  true manoeuvres cut by the period and any found manoeuvre paired with one, and MUST be used
  by the classing, the candidates' reading and the counts. A manoeuvre is cut only if the
  engagement's manoeuvre extends beyond the period.
- **FR-005**: The true-history reference MUST be checked against the truth by that function;
  where it fails it MUST be refitted with times held, flagged, and the share reported.
- **FR-006**: The refit control MUST fall back to C″'s own track by a rule that uses no
  truth when its fit diverges; the number of fall-backs MUST be reported.
- **FR-007**: The effect of each repair MUST be reported on spent data (seeds 333 to 335)
  before registration: the old and new search on the same periods.

**The study again**

- **FR-008**: D1 to D4 of spec 014 MUST be decided again on a fresh test seed with the
  repaired evidence, classing and reference, by the same definitions except where a repair
  changes them, each change listed in the decision record.
- **FR-009**: Each decided statistic MUST be reported at every registered sensitivity value
  (class thresholds 1, 3, 5; match tolerances 60, 120, 240 s), as a ratio of medians beside
  the paired figure, and without flagged references.
- **FR-010**: D1 MUST be reported beside the flat-prior search's share and at least two
  other estimands declared beforehand.
- **FR-011**: D4 MUST be reported by period length, and for every prior the share of
  manoeuvring targets declared quiet MUST be reported by number of true manoeuvres.
- **FR-012**: The attainable headroom MUST be reported on every split, with a statement of
  what remedy was tried there (none, unless built).
- **FR-013**: The recommendation on a learned model MUST be stated as the registered rule's
  output and, separately, as what the evidence supports and is silent on.
- **FR-014**: Every table in a record MUST be generated from the summary file.

**Process**

- **FR-015**: Development uses spent seeds only. Forecasts, thresholds and the rule are
  registered before the validation seed exists; validation carries spec 014's soundness stop;
  the test seed is scored once; the panel reviews.
- **FR-016**: Nothing is trained; no paid compute is used.

### Key Entities

- **Prior version**: the density over histories and the volumes the evidence pairs with it.
- **Cut manoeuvre**: a true manoeuvre the period's edge truncates.
- **Flagged reference**: a true-history fit that had to be held to stay that history.
- **Decision record**: what is decided, with forecasts and every changed definition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every prior factor without a Gaussian residual, density times volume is 1
  to within 1% in a test.
- **SC-002**: No reading uses a reference that fails the match rule against the truth.
- **SC-003**: D1 to D4 are stated on a fresh test seed with 95% intervals, beside spec 014's.
- **SC-004**: The record says, for each of D1 to D4, whether the repair changed the reading
  and by how much on the same periods.
- **SC-005**: A review panel can recompute every headline figure, and every table matches
  the summary file exactly.

## Assumptions

- Seeds: 333 to 335 are development data; 336 validation, 337 test; 324 and 325 stay unused.
- Splits and sizes are spec 014's; the smoothed EKF is dropped (no reference on manoeuvring
  targets); spec 014's search runs beside the repaired one on the Annex B and held-course
  splits for the before-and-after.
- The class threshold (3), match tolerance (120 s), materiality (10%) and the rule for a
  learned model are spec 014's, unchanged.
- The mixed prior keeps its half. It is reported, with its cost in missed manoeuvres.
- Not in this spec: a robust likelihood, a correlated-error model, a prior-mismatch
  diagnostic, a hedged track, the thinning idea. They are the next choice.
