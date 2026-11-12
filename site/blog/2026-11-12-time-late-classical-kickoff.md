---
title: "Kickoff: time-late, the classical follow-on to Gate T"
date: 2026-11-12
tags: [kickoff, spec-014]
---

Gate T showed that a classical search over manoeuvre histories halves the track error of the
standing classical system, and the review panel showed that this does not yet say where the
gain comes from or how much is left to win. The owner has chosen classical work first: spec
014 trains nothing, runs the studies spec 013 owed, and turns Gate T's upper limit on headroom
into a figure a decision on a learned model can rest on.

<!-- truncate -->

## Where we are

- [Gate T](/blog/2026/11/12/gate-t) was decided by the panel in one round: five of six checks
  passed, the sixth failed as forecast. The search is at 0.039 in median period range error
  against 0.088 for C″ read as a track, and 0.022 for the reference.
- Carried: C and C″, frozen; the search as registered for Gate T. Nothing learned is carried
  into the time-late problem.
- Open: the search wins even where it names the wrong history, so the gain may be mostly the
  arc model, the prior and the whole period. The headroom of 1.46 is an upper limit. The
  search misses a quarter of manoeuvres and declares one in 7 of 12 periods that had none. Its
  probabilities mean nothing when the target does not manoeuvre as assumed. The owner's
  bearing-rate thinning idea has not been tested.

## Where this task moves to

- SRD §5 (Gate T row and the rules it inherits) and §9 (owner, 2026-11-12); the spec is
  `specs/014-time-late-classical/`.
- Judged by: a stated share of the gain that refitting C″'s own manoeuvre times obtains; the
  share of wrong-history periods that are ambiguous in the bearings, and an attainable
  headroom judged against 10%; a false-manoeuvre rate on targets that hold course, to within
  5 points; a thinning verdict by a rule written beforehand; and one recommendation on a
  learned whole-period model.
- Plan:
  1. Correct the three small errors in the prior under a new code digest and report the effect.
  2. Build the two controls (C″ refitted with the arc model and prior; the search with an
     uninformative prior) and the classing of wrong-history periods, on tuning seed 333.
  3. Run the thinning study and apply its adoption rule.
  4. Add the scored outputs and conditions Gate T lacked: manoeuvre counts and timing, splits,
     held-course periods, correlated and outlying errors, whole engagements, a smoothed filter.
  5. Register what is decided on fresh seeds, with forecasts; validation seed 334, then test
     seed 335; panel.
  6. If time allows: a prior-mismatch diagnostic and a broadened prior, reported only.
- Risks: the search takes minutes a period, so run time limits split sizes; the classing rule
  may leave most wrong periods "ambiguous" by construction and must be fixed on tuning data;
  a reference fitted from neutral starts may fail to converge on hard periods. We stop, as
  Gate T did, if the references are not sound on validation.

## How progress will be shown

- A bar chart of track error: C″, C″ refitted, flat-prior search, search, reference, with
  paired per-period ratios (test seed 335).
- The classes of wrong-history periods and the attainable headroom beside Gate T's 1.46.
- False-manoeuvre rate on held-course periods for the search and C″, with intervals.
- Accuracy against run time for each thinning form, clean and with outliers (tuning seed 333).
- Track plots of one ambiguous period and one search failure, both candidate tracks drawn.
- All from committed experiment folders; scripts and commits named in the slides post.
