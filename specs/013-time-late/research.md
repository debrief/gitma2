# Research: spec 013

## R1. Five-second data and periods

- **Decision**: the generator runs MAN2 with `dt_s` 5 (`configs/timelate/tl-ranges.json`,
  otherwise MAN2's ranges; up to 1,440 rows). A period is cut afterwards by `sim/period.py`:
  from the scenario's seed a separate stream draws a start uniform over the engagement and a
  length uniform between 20 minutes and what remains; the period's record holds the slice, its
  offset, the manoeuvres inside it re-indexed, and those that began before it.
- **Rationale**: a transform outside the kernel cannot change existing data; the kernel's
  draws and their order are untouched (the conformance rule). `dt_s` is already a range field.
- **To check first**: the kernel's row buffers and manoeuvre table at 1,440 rows; MAN2's rules
  that are stated in rows.
- **Alternatives**: cutting inside the kernel (touches conformance); scenarios as they are
  (every one has an ownship zig across the line of sight mid-window; kept as a stratum).

## R2. The frozen C at five seconds

- **Decision**: C and C″ are given 10-second normal points: each the mean of two consecutive
  5-second bearings at their mean time, with σ/√2 as the stated σ; a pair with one bearing
  missing keeps the other at σ. C's code, parameters and digests are unchanged.
- **Rationale**: C's parameters are counted in 10-second rows (legs of 30 rows, windows of 36);
  re-tuning them for 5-second rows would unfreeze C. Averaging two bearings 5 seconds apart
  loses nothing measurable unless the bearing curves sharply within 10 seconds (R7 measures
  it), so C sees the same information at the rate it was built for.
- **Alternatives**: re-tune C at 5 seconds (a new C, with its own gate); give C every second
  bearing (throws half the information away).

## R3. A track from the physics layer

- **Decision**: `timelate/track.py` evaluates the layer's model (initial state and velocity
  increments at the knots, `physics/reference.py`) at every row of the period from the solve's
  `theta` and `knots`. Test: at the last row it equals the layer's reported state.
- The solution's own "determined" flag per row comes from the solve's covariance propagated to
  that row (relative range sd below a threshold fixed in the decision record; proposed 0.5).

## R4. The classical full-period system

- **Decision**: start from C″'s segmentation at the period's end, then, with all the data:
  1. **Re-test each declared change**: the rise in the full-period cost when it is removed,
     against the χ² point C uses; a change that fails is dropped.
  2. **Look for missed changes**: nominations from the full-period residuals (C's GLR statistic
     on the residuals of the current fit) and from C's additive search at the final prefix;
     each confirmed by the drop in full-period cost.
  3. Repeat to a fixed point, at most three rounds.
- **Settings** (threshold factor for dropping and for adding; rounds) are chosen on tuning seed
  329 by this rule, declared now: the lowest whole-track median range error on determined rows,
  ties to fewer rounds; the plain C″-to-the-end line is always reported beside.
- **Rationale**: it is C's own test with the one advantage time-late has, bearings after the
  change. It is the control any learned full-period system must beat.
- **Alternatives**: a global dynamic-programming segmentation (spec 005 measured the additive
  search as far weaker than GLR plus confirmation, because legs are coupled through position);
  a fixed-interval smoother over the IMM (R6).

## R5. The bound at every row

- **Decision**: `timelate/bound.py`: the Fisher information of the known-manoeuvres model over
  the whole period (manoeuvre times and kinds known), inverted once per period and propagated
  to the state at each row. Test: at the last row it equals the existing prefix bound.
- A row is **undetermined** for the score when the bound's relative range standard deviation
  exceeds a threshold fixed in the decision record (proposed 0.5); such rows are counted and
  reported apart. Efficiency is reported only on determined rows.

## R6. Systems scored

| System | What it is told | Note |
| --- | --- | --- |
| Reference | the true manoeuvre times | least squares; not a ceiling for systems that do not segment |
| C″ to the end | nothing | the frozen C on normal points, zig veto and fade, read as a track |
| Full-period C″ | nothing | R4; the classical time-late system |
| One leg | nothing | the floor |
| IMM, causal | nothing | each row's own causal estimate; no smoother is built (an IMM fixed-interval smoother is a project of its own), and the line is named for what it is |
| Regressor, causal (reported) | nothing | spec 012's seed 1 on every second bearing (its training rate), each row's causal estimate; not a time-late system, shown to inform the follow-on |

## R7. The compression study (the owner's bearing-rate idea)

- **Forms**: (a) dropping to one bearing in n; (b) fixed normal points of n bearings: the value
  at the bin's mean time of a least-squares line through the bin, variance σ²/n; (c) adaptive
  bins: a bin grows while the bearing's departure from a straight line across it stays below a
  tolerance in units of σ/√n (the "steady bearing rate" condition), up to a maximum length;
  (d) the same with a robust line (Huber) in each bin.
- **Measured** on tuning seed 329: efficiency against the bound on held-course periods;
  whole-track error of the reference on manoeuvring periods; run time of the solve and of C;
  all four again under spec 010's outlier condition.
- **Expectation, stated before the data**: dropping costs about √n; normal points cost under
  2% up to 30 seconds except at short range and in turns; adaptive bins recover that; robust
  bins remove most of the outlier damage. None of this is yet measured.
- **Rule for adoption**: the longest fixed bin whose cost is under 2% with an interval that
  excludes 5%; adaptive bins only if they beat that bin on run time at equal cost.

## R8. Gate T

- **T-a (soundness, validation)**: the reference's efficiency against the bound on determined
  rows within a band fixed from the tuning seed; the adopted compression within its declared
  cost; the track read-out and bound tests pass.
- **T-b (the verdict, test)**: H = the full-period system's whole-track median relative range
  error over the reference's, minus 1; median over determined rows within a period, then over
  periods; scenario-clustered interval at 97.5%. Material if wholly above 10%; not material if
  wholly below; otherwise inconclusive.
- **Reported with it**: course, speed and metres; by number of ownship manoeuvres in the
  period, by position (first leg, interior, last leg) and by range band; manoeuvre counts
  (matched, missed, false) for C″ to the end and the full-period system; the correlated-error
  condition; uncut scenarios.
- **Forecast** (before any data): the full period recovers about half of C″'s misses outside
  the last leg; H lands between 10% and 40%, largest on last legs.

## R9. Known limits, stated before any result

- Independent errors at 5 seconds are the owner's primary assumption; the correlated line shows
  the sensitivity, not what a sensor does.
- The reference is told the manoeuvre times; a system that does not segment (the regressor)
  can beat it at some rows, as on validation in spec 012.
- Periods are cut from engagements built around an ownship zig; periods without one arise only
  by the cut, so their share is whatever the cut gives, and is reported.
- Whole-track medians hide the tails; P90 is reported.
