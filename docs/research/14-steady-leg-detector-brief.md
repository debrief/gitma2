# The target steady-leg detector: problem brief

Status: a brief for an outside investigation (owner request, 28 November 2026). It states the
problem, what the arctan relationship gives us, what has been tried in this repository and how
well it did, and what a better algorithm would have to deliver. It is written to be read without
the rest of the repository. Every figure is from simulation and is quoted with its source; none
is from real data.

Updated 28 November 2026 with the first findings of that investigation (section 11, and notes
marked "Investigation:" elsewhere). Those findings come from a stand-alone re-implementation of
section 4, not from this repository, and are hypotheses until re-run here.

## 1. The problem in one paragraph

A submarine (ownship) listens to a surface or sub-surface contact (the target) with passive
sonar. All it measures is the bearing to the target, every few seconds, with an error of about
one degree. From those bearings and its own track it must estimate the target's range, course
and speed: target motion analysis (TMA). The classical solve assumes the target holds a constant
course and speed. Real targets do not: they hold a steady leg for ten to forty minutes, then
turn or change speed over a minute or more, then hold another leg. If the solve is told where
the legs are, it does well. If it is not, it is wrong, often by a large factor and without
knowing it. **The steady-leg detector's job is to find, from the bearings alone, the intervals
in which the target held course and speed, and the transitions between them.**

## 2. Why it matters: the size of the prize

On our simulator (section 4), median relative range error at the scored moments:

| Estimator | Clean bearings | With realistic bearing errors |
|---|---|---|
| One leg assumed throughout | fails on about a quarter of rows | fails |
| Our standing classical system (segmenter C″, robust solve) | 0.104 | 0.263 |
| The same solve told the true manoeuvre times | 0.065 | 0.122 |
| A learned regressor (no physics, knows the simulator) | 0.068 | 0.106 |

Source: `experiments/20261128-gd/` (500 engagements, fresh seed). The same solve with perfect
knowledge of the leg structure is 1.6 times better on clean data and about twice as good under
bearing errors. That gap is the detector's to close. A learned model reaches the told-truth
figure in range, which shows the information is in the bearings (together with some prior
knowledge of how targets move), but it is worse in course and speed and it is not a physics
solve.

## 3. Geometry and observability

- Positions are in a flat local frame, x east and y north. Bearing is measured clockwise from
  north: b = atan2(x_T − x_O, y_T − y_O).
- With both vessels on steady legs the bearings determine the target's motion only up to an
  unknown range scale. Range becomes observable only when ownship manoeuvres (a "zig"), and then
  only weakly at first.
- A target manoeuvre changes the bearing history only through the change in relative velocity
  divided by range. A small turn at long range, or a change mostly along the line of sight,
  moves the bearings by less than the noise for many minutes.
- Consequence: detection is delayed, some manoeuvres are undetectable in principle, and several
  different leg structures can fit one bearing history equally well. In our time-late studies
  the fit told the true manoeuvre times and the best wrong structure often had the same cost
  (`experiments/20261111-tl-retest/`): a pure goodness-of-fit test cannot reach the reference.

## 4. The data we simulate

Simulated only; mock data, nothing above OFFICIAL. The manoeuvre model is the owner's
(`docs/SRD-annex-B.md`), generator 0.6.0, ranges file `configs/man2-ranges.json`:

| Quantity | Value |
|---|---|
| Bearing interval | 10 s for real-time work (5 s in the time-late studies) |
| Bearing error | Gaussian, sd 1° stated (0.5° to 2° exist); see mismatch below |
| Window | 40 to 120 minutes, at most 720 rows |
| Initial range | 2 to 20 km |
| Target speed | 3 to 20 knots |
| Ownship speed | 5 to 15 knots; one or two deliberate zigs; small helm wander or autopilot oscillation |
| Target leg length | bell shaped, mean 25 min, sd 9 min, minimum 5 min |
| Target change | course 80%, speed 10%, both 10% |
| Course change | 30° to 120°, at 0.25 to 1 degree per second |
| Speed change | 2 to 6 knots, at 0.01 to 0.05 m/s² |

A typical engagement has two to four target changes. Truth labels (steady, transition) come from
the true kinematics, row by row.

**Bearing-error mismatch** (`src/tma2/sim/mismatch.py`). Real bearings are not white Gaussian.
Our "primary" stress condition adds, at once: a correlated component (half the variance, 60 s
correlation time), a slowly wandering bias (0.5° sd, 30 min), a true sd up to 1.5 times the
stated one, and 2% wild bearings (ten times the sd). Further kinds: sinusoidal error, bursts
with a common offset. The owner has also said bearings are lost during ownship's turns and for
about two minutes after each.

## 5. The arctan relationship

### 5.1 The law

While target and ownship both hold course and speed, the relative position is linear in time:

    Δx(t) = Δx₀ + u t,   Δy(t) = Δy₀ + w t

with (u, w) the relative velocity. So

    tan b(t) = (Δx₀ + u t) / (Δy₀ + w t)

Dividing through by the range at t = 0 removes the unobservable scale and leaves three
parameters:

    b(t) = atan2(sin b₀ + a t, cos b₀ + c t)

- b₀ is the bearing at t = 0;
- a = u / R₀ and c = w / R₀ are the relative velocity components divided by the initial range.

Three numbers describe every bearing history a steady target can produce against a steady
ownship. A target manoeuvre breaks the law; nothing else does, apart from noise and dropouts.

### 5.2 Useful properties

- **Pseudo-linear form.** The law is equivalent to
  sin b · (C + D t) − cos b · (A + B t) = 0, which is linear in (A, B, C, D) up to scale. A
  linear least-squares start is cheap, but it is biased when the bearings are noisy; we polish
  with Levenberg–Marquardt on the angle residual.
- **Bearing rate.** ḃ = (a cos b − c sin b) / ((sin b₀ + a t)² + (cos b₀ + c t)²) in these
  units: the cross-range relative speed over range. It is largest at the closest point of
  approach, which is where a manoeuvre is easiest to see.
- **Shape.** Along a steady leg the bearing is a monotone arctangent sweep of at most 180°. A
  bearing rate that changes sign, or a sweep that does not fit one arctangent, means a manoeuvre
  by someone.
- **What a change looks like.** A target manoeuvre is a change in (a, c) with the bearing
  continuous. The fitted (a, c) on either side differ by the change in target velocity divided
  by the range at the manoeuvre. A split test therefore has power proportional to that ratio
  and to the length of data either side.
- **What it cannot see.** The three parameters do not contain range. Two slices fitted
  independently have six free parameters and nothing ties them together, although the target's
  position must be continuous across the manoeuvre. That freedom matters (5.5).
  Investigation: within one steady ownship leg, position continuity is exactly bearing
  continuity at the knot (b₀′ = b(t_k)), one constraint, leaving five parameters of the six.
  The rest of the joined model's benefit comes from sharing one range scale across ownship's
  turns (section 11).

### 5.3 The general form through ownship's turns

Ownship's track is known, so it can be subtracted:

    b(τ) = atan2(x + vₓ τ − o_x(τ), y + v_y τ − o_y(τ))

with (x, y, vₓ, v_y) the target's state. This is the constant-velocity target fit, four
parameters, valid through ownship's own turns. Within a steady ownship leg it reduces to the
three-parameter law. An ownship turn inside the window is what makes range observable and is
where a split test has most power (`docs/research/07-steady-leg-preprocessor.md`).

### 5.4 Debrief's 2015 arctan slicing

The zig detector of the Debrief analysis tool, as we have re-implemented it
(`site/static/demo-data/js/arctan.js`):

1. Take one steady ownship leg.
2. Fit the three-parameter law to the whole leg; record the sum of squared residuals.
3. For every candidate split time, drop a fixed buffer of bearings around it (two minutes), fit
   the law to each side separately, and add the two sums.
4. Accept the best split if its score is under the whole-leg score times a ratio ("ZigRatio";
   we use 0.6, our choice).

Its limits, from the owner's review (`docs/SRD-annex-B.md`) and our measurements:

- One split per ownship leg. With two real manoeuvres the best single split lands between them.
- The buffer is fixed, not estimated, though a turn takes from half a minute to several minutes.
- The acceptance ratio is not tied to the bearing noise, so its false-alarm rate is unknown.
- It works only inside a steady ownship leg, so a target manoeuvre during ownship's turn is
  invisible to it.

### 5.5 What we learned extending it (spec 036, the interactive demonstrator)

Three splitters built on the law, compared on hand-built scenarios at 1° noise, five noise
draws each (`experiments/20261121-demo-splitters/`; anecdotes, not statistics):

| Splitter | Two target turns inside ownship legs: median range error | A target turn during ownship's turn |
|---|---|---|
| True manoeuvre times | 2.0% | — |
| **Arctan law, joined legs** | **2.6%** (9 of 10 turns found) | 3.1% (knot placed late) |
| Classical segmenter C | 8.2% (false transitions at ownship's turns) | — |
| Debrief 2015 slicing | 14.5% | 31.9% (blind) |
| Independent slices, recursive | 37.8% (splits between the turns) | 1.4% |
| One leg | 27% | — |

- **Independent slices are too flexible.** Each slice has its own free range, so a slice without
  an ownship turn absorbs a misplaced break, and the cost is flat over a quarter of an hour of
  candidate break times.
- **Joined legs fix that.** One model for the whole window: position continuous, velocity
  stepping at each knot, ownship's motion subtracted. Knots are added by forward selection and
  then re-placed; a knot is accepted when the cost drops by more than 25 σ² units (40 for the
  independent variant), a threshold tied to the bearing variance. At most four knots.
- No splitter won everywhere, and none produced a false split on a held-course target in these
  scenarios. This variant has not been scored on the simulator at scale. That is an obvious
  first experiment.

### 5.6 Two tests from the investigation

- **Cross-ratio invariant.** For any four bearings on a steady leg against a steady ownship,
  sin(b₁−b₂) sin(b₃−b₄) / (sin(b₁−b₃) sin(b₂−b₄)) = (t₁−t₂)(t₃−t₄) / ((t₁−t₃)(t₂−t₄)).
  No parameters and no fit, but noisy on single bearings and valid only inside a steady
  ownship leg. A screening tool.
- **Linearised likelihood-ratio scan.** Linearise the four-parameter fit; a knot at time k adds
  two columns, the hinge max(t − k, 0) times (cos b, −sin b)/R. The statistic is the residual
  energy in those columns after projecting out the fit: χ² with 2 degrees of freedom under
  white noise, a known quadratic form under any stated error covariance. A full scan of a
  window costs milliseconds, so the maximum over k can be calibrated per geometry.

## 6. What has been tried, and what happened

| Attempt | What it was | Outcome | Source |
|---|---|---|---|
| Learned change detector (Gate D) | A network giving P(change) per bearing | Raised no useful alarm; it learned "time since ownship's zig" | `experiments/20261102-gd-a-val/` |
| Sliding-window split test | The arctan law's general form in a 6-minute window, a likelihood-ratio statistic per row | Detects 64% of manoeuvres at a 5% false-alarm rate; alarms used directly as knots are worse than no knots (57% false, true ones a median 235 s late) | research note 07 |
| **C: nominate, then confirm** | Candidates from a GLR test and a leg search; each confirmed by the drop in the full physics solve's cost on the history so far | **Standing system.** Recovers 0.90 of the gap between one leg and perfect knowledge on clean data, 0.66 under bearing errors | Gate S, `experiments/20261105-gs-r2/`; `experiments/20261110-gh-c2/` |
| L: learned evidence added to C | Per-bearing evidence in C's search | Not shown to beat C | Gate S |
| C″: C with a veto at ownship's zig and a fading memory | Two classical rules | +0.018 over C; the learned version added +0.007 more | Gate 2, `experiments/20261107-g2/` |
| Huber costs in C's tests | A robust confirmation | Removed 28% of false transitions; so did doubling the threshold | `experiments/20261111-gr-choice/` |
| Wild-bearing editing before C | Drop bearings over 4 sd from a running median of nine | Closes about a fifth of the gap under bearing errors, no cost on clean data | `experiments/20261128-gd/` |
| Raising C's threshold × 4 | Fewer false transitions | Helps under bearing errors, costs about 18% on clean data | same |
| Evidence search (time-late only) | Whole-period search over manoeuvre histories with a prior on how targets manoeuvre | Twice as good as C″ read as a track; needs the whole period; misses 23% of manoeuvres and invents some on held course | specs 013 to 018 |

What we know about C's failures:

- **Misses are the larger part.** About 30% of true changes are never declared, with or without
  bearing errors (`experiments/20261111-gr-choice/`).
- **Bearing errors add false transitions.** 248 on clean data against 1,126 under the primary
  condition on the same engagements; wild bearings first, then correlated error; bias and a
  mis-stated sd do nothing (`experiments/20261110-gr-diagnosis/`).
- **Having the right list of transitions is not having the right solve.** Where C″'s declared
  transitions match the truth at the first scored moment, its error is still 1.5 times the
  told-truth solve's later on (`experiments/20261128-gd/review.md`). Timing, transition length
  and what happens after matter as much as the count.
- By a strict match (every true change found within two minutes, nothing extra) C″ has the
  structure right in 43% of clean engagements and 12% under bearing errors.
- C is slow: its leg search takes tens of seconds per engagement, and minutes in a browser.

## 7. The algorithm we are hoping for

### 7.1 Inputs

- Time-stamped bearings with a validity flag and a stated error sd (which may be wrong).
- Ownship's track (position, course, speed at each bearing time), taken as exact.
- Nothing else: no truth, no error model, no knowledge of which stress condition applies.
  Statistics of how targets manoeuvre (section 4) may be used as a prior, and must then be
  declared, because a system that knows the simulator's statistics has to be compared with
  controls that know them too.

### 7.2 Outputs

For each bearing time, and causally (using only bearings up to that time):

- the segmentation so far: steady legs and transitions, each with start and end, and "unknown"
  where the data cannot say;
- ideally a confidence or a short list of alternative structures with probabilities, since some
  histories are ambiguous in principle.

The leg boundaries are handed to a physics solve (legs joined by position continuity,
transitions excluded or modelled as a constant-rate turn or speed change). The estimate must
come from that solve. A network may supply judgement about where legs are; it may not supply
the answer.

### 7.3 Properties wanted, in priority order

1. **Fewer missed manoeuvres** than C at the same false rate. This is the larger loss.
2. **A false-alarm rate tied to the noise**, stated and holding on held-course targets,
   including under correlated error and wild bearings. Debrief's ratio and C's threshold both
   lack this.
3. **Transition length estimated**, not fixed: half a minute to about eight minutes.
4. **Works through ownship's turns**, where range becomes observable, and when bearings are
   missing during and after them.
5. **Several manoeuvres per window**, including two inside one ownship leg, without the "split
   between them" failure.
6. **Honest about ambiguity**: reports unknown, or alternatives, instead of forcing a choice.
7. **Causal and cheap**: seconds per update on one CPU core, with earlier decisions revised only
   by a stated rule. A whole-window (time-late) version is also useful and easier.
8. **Classical first.** A learned component is welcome only against the classical rule it might
   be reproducing; twice our learned parts turned out to be a simple rule in disguise.

Investigation: the stand-alone evidence (section 11) suggests priority 1 has little headroom,
because most of C's misses may be undetectable, and that priorities 2 and 3 are where the gap
is. The order above is left as the owner set it until the cross-tabulation in section 11 has
been run in this repository.

### 7.4 Directions we think are promising

- **The joined-leg arctan model at scale** (5.5): never scored on the simulator, and the best of
  the splitters where we tried it.
- **A split statistic with a known null distribution**: a generalised likelihood ratio on the
  joined model, calibrated under correlated error by an effective sample size, so that the
  threshold means a false-alarm rate.
- **A prior on structure.** Leg lengths, turn sizes and rates are far from uniform (section 4).
  In the time-late work a prior on histories was what separated structures the bearings could
  not. A causal version (a changepoint model with a leg-length hazard, or a small bank of
  hypotheses pruned by evidence) is untested.
- **Robust residuals inside the test**, not only in the final solve: wild-bearing editing was
  the one cheap gain.
- **Detectability first.** For each true manoeuvre, compute how much the bearings could
  possibly show (the cost of omitting it, with times held). In one study 37% of manoeuvres on
  busy targets were below a sensible threshold (`experiments/20261114-tl5/`). An algorithm
  should be judged on the detectable ones, and should know which is which.

## 8. How a candidate will be judged

Segmentation is judged by what it does to the estimate, not only by where the boundaries are.

| Measure | Meaning |
|---|---|
| Gap recovered | (error with one leg − error with the candidate) ÷ (error with one leg − error told the truth) |
| Ratio to the told-truth solve | per engagement, paired, with a bootstrap interval over engagements |
| Missed changes, false transitions | matched one to one within two minutes, by kind |
| False-split rate on held course | engagements with no target change that are split |
| Contamination and coverage | transition time labelled steady; steady time labelled steady |
| Detection delay | from the end of a true change to its declaration |
| Cost | seconds per update |

Rules of evidence we hold ourselves to, and would hold a new algorithm to:

- Settings are chosen on development seeds; the claim is made on a fresh seed, scored once,
  with the comparison written down beforehand.
- The same rows for every system, with the references beside: one leg, C″, the solve told the
  true manoeuvre times, a tuned IMM, and the error bound for known manoeuvre times.
- Paired per-engagement ratios, with medians and the shares twice as good and twice as bad
  beside any mean: several of our averages turned out to be tails.
- Clean data and the mismatch conditions both, because a gain bought on one is often paid for
  on the other.
- Read results by how tightly the bearings determine the answer; a win only where the bound is
  loose is prior knowledge, not detection.

**Numbers to beat** (section 2's table): close the gap between 0.104 and 0.065 on clean
bearings, and between 0.263 and 0.122 under the primary mismatch, without losing on held-course
targets.

## 9. Open questions for the investigation

1. Is there a closed-form or cheap test for "these bearings left the arctan family" whose null
   distribution is known under correlated bearing error?
2. How should position continuity across a manoeuvre be used when range is unobservable within
   an ownship leg? The joined-leg model uses it through the four-parameter form; is there an
   equivalent constraint on consecutive (b₀, a, c) triples?
3. What is the best achievable detection delay for a given change in relative velocity over
   range, and how far is C from it?
4. Can transition start, end and kind (turn or speed change) be estimated jointly with the
   split, at acceptable cost?
5. Which manoeuvres are undetectable in principle in a given geometry, and can the algorithm
   say so in real time?
6. Does a prior on leg length and turn size help a causal detector, as it helped the
   whole-period search, without inventing manoeuvres on quiet targets?

Investigation, status of each question (detail in section 11):

1. Partly answered: the cross-ratio invariant and the linearised scan (5.6). The null is known
   if the error covariance is known; estimating it online is only a partial fix.
2. Answered, negatively: bearing continuity is the whole constraint within an ownship leg.
3. Answered as a floor: delay ≈ (3 λ* σ² Δt / Δḃ²)^(1/3), with Δḃ the change in cross-range
   speed over range and λ* the threshold. C appears to be near it.
4. Negative so far: freeing transition start and end inside a crude stand-alone solve did not
   recover a two-minute timing error and made the estimate worse. Not a proof.
5. Answered in outline: the omission cost is computable for a hypothesised manoeuvre in the
   current geometry, which gives a real-time "would not be visible" statement.
6. Answered in outline: as a detection aid the leg-length prior moves the threshold by about
   −5 to +2 σ² units, which is small. Prior knowledge pays in the estimate, through bounds on
   speed and range.

## 10. Where things are in the repository

| What | Where |
|---|---|
| The owner's requirements for steady-leg segmentation | `docs/SRD-annex-B.md`, `docs/SRD-annex-A.md` |
| The arctan pre-processor study | `docs/research/07-steady-leg-preprocessor.md`, `08-leg-detection-spike.md` |
| Arctan law, Debrief slicing, joined legs (JavaScript) | `site/static/demo-data/js/arctan.js`, `splitters.js` |
| Interactive demonstrator (drag tracks, pick a splitter) | the site's `/demo` page; spec `specs/036-leg-splitters/` |
| Classical segmenter C | `src/tma2/segment/` (frozen; controls are built around it) |
| Sliding-window channels | `src/tma2/detect/steady_leg.py` |
| Physics solve | `src/tma2/physics/layer.py`; arc model `src/tma2/timelate/arc.py` |
| Generator and manoeuvre model | `src/tma2/sim/`, `configs/man2-ranges.json` |
| Bearing-error conditions | `src/tma2/sim/mismatch.py`, `configs/gateh/conditions.json` |
| Scoring a segmentation through the solve | `tma2-hpredict`, `tma2-gh`, workflow `headroom.yml` |
| Latest record of the gap | `experiments/20261128-gd/` (README, `review.md`) |

Generate a data set to work on (a spent seed; fresh seeds are kept for registered tests):

```bash
uv run tma2-generate --seed 321 --count 900 --ranges configs/man2-ranges.json \
  --heldout-ranges configs/man2-heldout.json --format f32pack --out data/brief-321
```

## 11. Investigation findings so far (stand-alone, 28 November 2026)

Source: `docs/research/15-steady-leg-theory-note.md` and its scripts
(`experiments/20261128-standalone/`). The
simulator is a re-implementation of section 4 (ownship zigs assumed 60° to 120° at 1°/s; no
helm wander, no dropouts). None of this has been run against generator 0.6.0, segmenter C or
the physics solve.

| Finding | Figure | What it bears on |
|---|---|---|
| Manoeuvres costing under 25 σ² to omit, times told, whole window | 28% (speed changes 67%, course changes 23%) | C's 30% misses may be mostly undetectable |
| Same, at a threshold honest under the primary condition (about 170) | 56% | Under bearing errors about half of manoeuvres are beyond a goodness-of-fit test |
| Scan maximum on held course, 95th percentile: white / correlated only / primary | 10.6 / 58 / 171 | 25 σ² is conservative on white noise and far too low under mismatch |
| Held-course windows split at 25 σ² under the primary condition | 90% (84% after wild-bearing editing) | Explains the false transitions in section 6 |
| Wild-bearing editing, wild bearings only | false splits 21% to 2% | Agrees with the one cheap gain in section 6 |
| Online noise correction, primary condition, threshold set on white | false splits 98% to 25–35% | Partial; not a stated rate |
| Same correction against a higher fixed threshold, matched false rate | flags 69–78% of manoeuvring windows against 89% | The correction costs power; a higher threshold does as well |
| Bias wander inflation of the null: whole window / 20 min / 12 min | ×4.8 / ×1.2 / ×1.0 | Why bias does nothing to C; a time-late test needs a short window or a bias term |
| Expected detection delay from the end of a change, 25 σ² | median 209 s | C's 235 s is near the bound |
| Joined-model Jacobian rank, ownship steady / with a zig | 5 of 6 / 6 of 6 | Open question 2 |
| Told-truth solve with bounds on speed and initial range, against without (stand-alone solve, paired) | clean 0.109 against 0.166; primary 0.251 against 0.455 | Told-truth may not be the ceiling; may explain the learned regressor |
| Solve given only manoeuvres over 25 σ², against told-truth | clean 0.152 against 0.166; primary 0.365 against 0.455 | Undetectable manoeuvres need not be found |
| True structure declared 120 s late, against told-truth | 3.5 times the error, equal to one leg | Timing may be the main lever |
| Instantaneous knot against constant-rate arc, no noise | 6% median range error against zero | Transitions should be modelled as arcs |
| Position error of a mid-point knot after a turn | median 92 m, 90th percentile 386 m | Same |

The stand-alone solve behind the last five rows is cruder than `src/tma2/physics/layer.py`
(its clean told-truth error is 0.166 against 0.065 in section 2), so only the paired
comparisons carry over, and they need repeating here.

Question for the owner: does the told-truth solve bound target speed and initial range to the
simulator's limits? The answer changes what the numbers to beat in section 8 mean.
Answered from the code (`specs/040-steady-leg-headroom/e0.md`): no. The solve is unbounded; its
range and speed limits only set a flag on a finished solve. It fits a chord between knots at a
change's start and end and does not exclude or arc-model the bearings inside.

Cautions:

- The undetectable shares are expected noise-free costs with true transition rows excluded, so
  they are on the optimistic side.
- "Manoeuvring windows flagged" counts a window as found if any one of its changes is seen.
- The agreement between 28% and C's 30% could be a coincidence of the stand-in ownship model.

First experiments proposed for this repository, in order:

1. On seed 321, compute the omission cost of every true manoeuvre through the physics solve and
   cross-tabulate it against C″'s hit, miss and delay. This decides whether priority 1 has
   headroom.
2. Measure the null of the linearised scan on held-course engagements under each condition in
   `configs/gateh/conditions.json`, by window length.
3. Timing sensitivity of the physics solve: true structure with times shifted by 60, 120 and
   240 s, and a "told detectable" reference given only manoeuvres above the threshold.
4. Then the joined-leg model at scale (5.5), scored on detectable manoeuvres separately.
