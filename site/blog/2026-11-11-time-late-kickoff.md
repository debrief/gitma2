---
title: "Kickoff: time-late TMA, the whole track over a given period"
date: 2026-11-11
tags: [kickoff, spec-013, gate-t]
---

Everything this project has scored so far is the real-time question: the best estimate now,
from the bearings so far. The owner has asked for considered steps towards the other mode,
time-late: given a period of bearings, the most consistent solution across the whole period.
Spec 013 defines that solution and its score, gives the classical approach its best shot, and
measures what is left before anything is trained.

<!-- truncate -->

## Where we are

- **Spec 011** closed at tuning ([write-up](/blog/2026/11/11/robust-segmenter)): the classical
  segmenter's largest weakness is missed manoeuvres, about 30% of true changes.
- **Spec 012** ([kickoff](/blog/2026/11/10/scaled-regressor-kickoff)): three seeds of a direct
  regressor are trained. On validation it sits at 1.2 to 1.8 times the bound on held course and
  beats C″ after manoeuvres (0.065 against 0.105 in median relative range error). Its test
  reading is being scored. GPU training is paused by the owner.
- **Carried**: C frozen, C″ the standing classical system, least squares at the bound when the
  manoeuvre times are right.
- **Never done**: scoring a whole track. C″ run to the end of a window already produces one.

## Where this task moves to

- **SRD** §3 (both consumers remain) and §5; a new row, Gate T, proposed for the owner to merge.
  Spec: `specs/013-time-late/`.
- **Owner's decisions** (11 November): a time-late solution is judged on the whole track across
  the period; bearings come every 5 seconds; the analyst does not choose the period.
- **Plan**:
  1. The solution and its score: position, course and speed at every moment, the manoeuvre
     times, and an honest "undetermined" where the data cannot say; a bound at every moment.
  2. Data: 5-second bearings, and periods cut at random from longer engagements, so a period
     may hold several ownship manoeuvres or none.
  3. The classical side, nothing trained: C″ read as a track; a full-period pass that re-tests
     every declared change with all the data and looks for missed ones; least squares told the
     true manoeuvre times as the reference.
  4. The owner's bearing-rate idea: thinning where the rate is steady, as dropped bearings, as
     fixed normal points and as adaptive bins; accuracy, run time, and wild bearings.
  5. Decision record, fresh seeds (329, 330, 331), the panel.
- **Judged by**: the headroom, the best classical system's whole-track range error over the
  reference's. Material above 10% (proposed): the next spec trains a full-period proposer with
  least squares producing the answer. Not material: the classical full-period system is the
  time-late answer.
- **Risks**: independent errors at 5 seconds overstate the information (a correlated condition
  is scored beside); periods with no ownship manoeuvre, where the right answer is that range is
  not determined; a reference that is not a ceiling for systems that do not segment.
- **We stop** if the reference is not near its bound on determined rows: then the scoring is
  wrong, and nothing else means anything.

## How progress will be shown

- **One period's bearings and bearing-rate curve**, with the compression bins drawn on it.
- **Whole-track plots**: truth, C″ read as a track, the full-period system and the reference,
  on periods with and without an ownship manoeuvre.
- **Headroom chart** with intervals, by number of ownship manoeuvres and by position in the
  period.
- **Misses recovered** by the full period, against the causal system's.
- **Compression trade-off**: accuracy against run time for each form of thinning.

## Update, 11 November (evening): the reference was the weak point

The first checkpoint tripped the plan's stop rule. The reference (the physics layer told the
true manoeuvre times) sat at about twice its bound on cut periods and 4.5 times on whole
engagements. The scoring was not at fault: with no target manoeuvre, least squares read as a
track is at the bound. The cause, tested, is that the layer gives each manoeuvre four free
unknowns where a turn at constant speed has one.

The owner chose to add a classical arc-model solve: a manoeuvre is a turn at a constant rate
and a speed change at a constant rate between two times. On 60 tuning periods it reaches 1.2
times the bound told the kind of manoeuvre and 1.4 judging the kind from the data, with the
true times. On C″'s own transitions it is no better than the chord and probably worse: a
stricter model forgives a missed manoeuvre less. So the segmentation remains the larger
factor, about three in median range error, and the full-period re-test is the next step.
Records: `experiments/20261111-tl-diagnosis/`, `experiments/20261111-tl-arc/` (tuning data,
not a gate result).

## Update, 11 November (late): a better search does not help

The full-period re-test was built on the arc model: refine every manoeuvre's times, add a
manoeuvre where the whole-period fit demands one, remove one it does not support. On the same
60 tuning periods it is no better than C″ read as a track (median range error 0.11 to 0.14
against 0.11; the reference told the true times is at 0.035). It fits the bearings exactly as
well as the fit told the truth, with a third of the manoeuvres missed. A missed manoeuvre
costs almost nothing in fit and a factor of five in range.

So the limit is not the search. Structures with different manoeuvres explain the same
bearings, and what separates them is knowledge of how targets manoeuvre, which a test of fit
does not use and a model trained on millions of engagements does. That is the likeliest
reason spec 012's regressor beat C″. Record: `experiments/20261111-tl-retest/` (tuning data).

## Update, 12 November: prior knowledge does not pick the history either

The owner chose to try a classical estimator that uses Annex B's manoeuvre statistics. The
cheap test came first: under those statistics, is the true manoeuvre history more probable
than the wrong one the re-test finds? It is not. Where the re-test is badly wrong, the truth
is clearly ahead in about four periods in ten and the wrong history clearly ahead in about
four in ten. The true history fits slightly better and pays more than that for its extra
manoeuvres. The re-test was already close to the most probable history.

Told only the right history, with every time left free, the fit sits at the bound. So the
problem is neither the solve nor the timing: in about half the difficult periods the bearings
and the statistics together leave two histories standing, and they put the target in different
places. An honest system would say so, with candidate tracks and probabilities. Record:
`experiments/20261112-tl-prior/` (tuning data).
