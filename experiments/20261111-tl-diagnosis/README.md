# Spec 013, first checkpoint: the reference is not near its bound, and why

Tuning seed 329 (never a result). 5-second MAN2 engagements (`configs/timelate/tl-ranges.json`,
count 400; σ = 1° ordinals) and the held-course variant (`tl-held-ranges.json`, count 300),
generated in the session; periods cut by `timelate/periods.py`. Scripts:
`scripts/research/tl_reference_strata.py`, `tl_reference_variants.py`, `tl_kinematic_fit.py`
(kept as run). Efficiency is median(|error| / bound) / 0.6745 over determined rows (bound on
relative range below 0.5), pooled over rows; rows within a period are correlated, so these are
indications from 24 to 60 periods, not estimates with intervals.

The plan's rule (tasks T013): stop if the reference is not near its bound on determined rows.
It is not. The scoring is sound; the reference's manoeuvre model is the cause.

## 1. The scoring is sound

| Data | Periods | Efficiency: range, course, speed |
| --- | --- | --- |
| Held course, whole engagements | 60 | 1.02, 0.88, 1.08 |
| Held course, cut periods | 60 | 1.10, 1.21, 1.26 |

With no target manoeuvre, least squares read as a track sits at the whole-period bound. The
track read-out, the time axis, the 10-second pairing and the bound agree. Unit tests: the bound
at the last row equals the existing prefix bound; the track at the last point equals the
layer's state.

## 2. With manoeuvres the reference is at about twice the bound, everywhere

Reference = the physics layer with knots at the true manoeuvre starts and ends (MAN2, cut
periods, 60 periods, 31,537 determined rows):

| Rows | Range | Course | Speed |
| --- | --- | --- | --- |
| All | 1.87 | 2.27 | 1.95 |
| First leg | 1.87 | 1.98 | 1.83 |
| Interior | 1.81 | 2.41 | 1.93 |
| Last leg | 2.20 | 1.97 | 2.13 |
| Within a minute of a turn | 1.84 | 6.08 | 3.10 |
| Away from turns | 1.88 | 2.15 | 1.83 |

Not the cause (same 60 periods; baseline 1.87, 2.27, 1.95):

| Variant | Range | Course | Speed |
| --- | --- | --- | --- |
| No speed-continuity prior | 1.97 | 2.47 | 2.24 |
| Bearings inside turns masked | 1.87 | 2.08 | 1.91 |
| Ridge prior ten times weaker | 2.60 | 2.51 | 2.39 |
| 5-second rows, no pairing | 1.76 | 2.23 | 1.80 |

The priors help rather than hurt; in-turn bearings and the pairing are not it.

## 3. The cause: the layer's manoeuvre model is freer than the bound's

The bound assumes each manoeuvre is what the generator makes: a turn at constant speed along
an arc (or a speed change on a constant course), with its start and duration known, and one
unknown, its size. The layer gives each manoeuvre two free velocity increments (four
unknowns) joined by a chord. Tested directly on 24 **whole** MAN2 engagements (22,533 rows):

| Fit | Range | Course | Speed | Median relative range error |
| --- | --- | --- | --- | --- |
| The layer, knots at the true times (the reference) | 4.55 | 4.54 | 4.73 | 0.0643 |
| The bound's own model fitted by least squares | 1.25 | 0.98 | 1.27 | 0.0147 |

A fit of the bound's own model reaches the bound; the reference is four times worse in range
on whole engagements. The explanation is tested, with these limits:

- The kinematic fit was started at the truth (a local test of efficiency, not a usable
  estimator) and is told each manoeuvre's kind, start and duration, which no real system has.
- 24 engagements; the factor (4.5 whole, 1.9 on cut periods) grows with the number of legs.
- At 10 seconds and at the scorer's real-time rows, Gate H measured about 1.25; the gap is
  larger here because 5-second data over a long period leaves model error as the larger part.

## Consequence (for the owner; nothing decided here)

The largest known loss in the time-late problem is not the segmentation but the physics
layer's manoeuvre model. A solve that models a manoeuvre as a turn at constant speed (or a
speed change on a constant course) between two times, with its size unknown, is classical,
is what Annex B describes, and would be a better reference and probably a better final solve.
How much of the factor it keeps when it must also estimate the kind and the duration is not
measured. Spec 012's regressor matching the reference after manoeuvres now reads differently:
the reference it matched is far from what the data allow.
