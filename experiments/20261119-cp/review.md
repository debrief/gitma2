# Spec 027 test record: agent review panel, round 1

Three reviewers each read the record, the registration and the code on their own:
statistics and registration fidelity, code correctness, and interpretation. All three approve
with findings. The reviews are given below, then how each finding is resolved. The resolutions
were checked by `scripts/research/cp_ties.py` (`ties.json`) and `cp_supplement.py`
(`supplement.json`).

**Decided by the panel:**
- **Outcome:** the rule's output stands. Gain is **not shown** at this size, and there is **no
  harm**.
- **Reproduction:** the scorer reproduces `study.json` exactly, and the digests hold.
- **What the record may claim** is narrowed, as given in "Resolution".

## Reviewer 1 (statistics and registration fidelity): approve with findings

The rule was applied as registered and the outcome stands: **not shown, at this size; no
harm**.

**Reproduction and provenance:**
- Re-running `tma2-long study27` on `raw/` reproduces `study.json` exactly, apart from
  `git_commit` and `git_dirty`.
- `cp_digests.py` at HEAD matches `digests.json`: the bound files, code `09a7edae` and the file
  list.
- All 120 shard headers show commit 274154e, a clean tree and the registered settings.
- Commits after registration touched only the trigger `configs/long/run.json` and the records.

**The rule:**
- Gain: the weak split is 1.105 [0.963, 1.273], so its lower limit is not above 1.
- Harm: none of the 12 checks has an upper limit below 1.

### Findings

**1 (minor). The bootstrap unit is the chain, not the engagement.** `study27.ratio` makes one
unit per (engagement, contact) chain, so the weak split has 94 units from 60 engagements.
Contact 1 and contact 2 of one engagement share the ownship, its gaps and its turns, yet the
decision record says "bootstrap over engagements".

Re-clustered by engagement (58 units):

| weak split | estimate and interval |
|---|---|
| range | 1.105 [0.951, 1.279] |
| course | 1.12 [0.94, 1.31] |
| speed | 1.16 [0.94, 1.42] |

The outcome does not change. Contact 1, contact 2 and other have one chain per engagement and
are unaffected. **Required:** record the deviation and give the engagement-clustered interval
beside the registered one.

**2 (minor). The soundness check did not cover the population the rule decides.**
- The coverage check is registered on contact 1 only, yet 156 of the 215 scored weak windows are
  contact 2.
- On validation, contact-2 coverage was 0.76 [0.67, 0.86], which would have failed the
  [0.80, 0.99] band.
- The settings come from a grid recomputed offline; a chain at scale 4 and tail 1,200 s never
  ran on tuning.
- The grid's prediction (0.90) missed the test value (0.953).

**Required:** say that the decided split's prior was overconfident on validation, and that the
registered settings were extrapolated, not tuned.

**3 (major, wording). "Small, broad improvement of about 10%" is too strong.**
- The median window ratio is 1.03 on both weak and other.
- 44–46% of windows are worse.
- Twice better / twice worse: 13% / 11% on weak, 17% / 10% on other.
- The trimmed weak interval is [0.97, 1.17].
- The clearest readings come from many unadjusted beside readings.
- Other range, 1.14 [1.035, 1.27], has some replication: validation gave 1.11 [0.96, 1.27].

**Required wording:** "Beside the rule, not decided: on the tended contact's ordinary windows,
ctl ÷ ctl-prior is about 1.1 in geometric mean (1.03 in the median window) in range and course,
on both validation and test. This is an average shift with many losses, not a gain in most
windows." Drop "broad".

**4 (major, wording). "Mostly a better estimate of the same history; the prior does not narrow
which history is chosen" is not supported.**
- `cp_supplement.py`'s "agree" means equal *counts* of declared manoeuvres, with no timing or
  kind match (`timelate/match.py` exists for that).
- Per window, the gain where the counts differ is as large or larger: other 1.23 [0.88, 1.75]
  against 1.13; contact 2 1.16 against 1.16.
- The agreeing windows carry most of the log gain only because they are 78% of the windows.
- The prior changed the declared count in 98 of 455 windows.

**Required wording:** "The gain is not concentrated where the declared manoeuvre count
changed; per window it is similar either way. Whether the same history was kept was not
tested."

**5 (minor). The prior's own effect is partly `ctl-carry`'s loss.** On contact 1,
ctl ÷ ctl-carry is 0.952 [0.893, 1.021]. Write: "`ctl-carry` is level with `ctl` (0.95,
interval includes 1); the prior adds about 14–22% over `ctl-carry`."

**6 (minor). The weak split is in effect "contact 2 plus near-gap windows".** The contact-1
near-gap part is 0.98 [0.79, 1.25] over 59 windows. Say in the headline that the registered
question is answered for this simulator's untended contact.

**7 (minor). What the record owes.**
- SC-003: no committed script generates the README's tables.
- SC-002: the guard rate has no interval.
- US2 / FR-007: growth of error along the chain is not discussed.
- Wrong carried estimate: no error before and after a fall-back on the chains where one
  occurred (only ctl ÷ noguard 0.54 [0.32, 0.86] on the 8 windows).
- FR-008: coverage after gaps (0.937 [0.88, 0.98]) is missing from the README.
- Edge cases: no rows for windows whose previous window did not answer.
- Share answered: windows are scored only where both systems answer, which is 76% of windows;
  state it.
- FR-012: the tuning joint-solve figure (1.73, 12 pairs) is not cited.

**8 (minor). Forecasts.** The table is fair. Add that two of the five forecasts were wrong:
the other split's sign and the coverage level.

## Reviewer 2 (code correctness): approve with findings

**What was run:**
- The unit tests for the carried prior: 4 passed.
- Experiments on 126 manoeuvre-free 20-minute windows from `configs/long/long.json`:
  - a hand-over at each window's midpoint;
  - the guard on the second half, under a prior drawn consistently around the truth.

**Checked and correct:**
- Frames and times: t_o lands on the previous window's row grid, and the bearing at t_o is
  excluded (`carried.py:381`).
- The prior is applied in sequence: each window's carried estimate is refitted with that
  window's own prior.
- The carried residuals reach the fit and the Laplace Hessian exactly once
  (`carried.py:103, 193`).
- `cp.log_density` shifts every history in a window by the same amount, so the ranking is sound.
- With no carried prior, everything equals the originals (tested).
- Course wrap is handled in the propagation Jacobian, the residual and the NEES.
- The coverage grid's recomputation is exact in τ.

**Edge cases that behave as specified:**
- after a fall-back, the chain resets to `ctl-carry` with no prior;
- an unanswered previous window gives `ctl`;
- a manoeuvre in progress at t_o is truncated;
- the gap widening uses g = t_o − t_last.

**Edge case with a bias:** a manoeuvre starting within `MIN_DURATION` before t_o is dropped
and fitted as straight. The state is biased, and only `tail_s` and the guard cover it.

### Findings

**1 (major). Windows where nothing was carried count as exact ties.** Where `hand_on` returns
None, `ctl-prior` is `ctl`'s own array (`carry2.py:172-178`). `study27.ratio` excludes only
`index == 0`, so these windows enter the rule as log 1 = 0. This repeats spec 026's
constructed-tie lesson.

**2 (major in weak geometry). The carried mean can hold the overlap bearings, and its Gaussian
is overconfident there.**
- `hand_on`'s refit starts from the previous window's full fit, which used the bearings after
  t_o. On a flat valley, Levenberg–Marquardt does not move.
- Example: engagement 9, row 1,320 (one case). The refit stayed 6.9 km from the truth, at a
  cost equal to the truth-started fit's within 1e-11.
- In (x, y, course, speed), a Gaussian cannot represent a curved ridge. On the short
  hand-overs, the raw NEES median was 18.7 against 3.36 for χ²(4). Coverage was 0.40.
- Fix: neutral starts.

**3 (minor). The guard is more lenient than its level.**
- Under a consistent prior, D had mean 2.68 and median 2.10 (χ²(4): 4 and 3.36).
- Widening shrinks D further.
- D compares the same history with and without the prior, so it cannot see a prior that
  changed the declared history.

**4 (minor). The coverage grid assumes the raw covariance is independent of the settings.**
Each raw covariance holds the previous window's carried prior at the tuning run's own scale and
tail, so the effect compounds along a chain.

**5 (minor). The bootstrap units are (engagement, contact) chains, not engagements.**

**6 (minor). `classify` counts only ownship turns starting inside the window.** It misses turns
in progress at the window's start.

**7 (minor, no fix needed). The base prior is counted twice, slightly.** Its state factor and
its stand-in precisions apply in every window and again inside the carried covariance.

## Reviewer 3 (interpretation and claims): approve with findings

The rule's output, "not shown, at this size", with no harm, is read correctly, and the soundness
checks pass. The README needs these wording changes before the write-up.

### Findings

**1 (major). What the owner may conclude about "constrain the permutations".**
The test reframes the hypothesis; it does not support it as stated. The prior did not narrow
which history is chosen:
- Windows where `ctl` and `ctl-prior` declare the same number of manoeuvres carry the gain:
  1.13 on other, 1.12 on weak.
- Where the declared histories differ, the intervals are wide and centred near 1. On weak,
  1.06 [0.79, 1.45], with 19% of windows twice worse.

So the prior acts as a regulariser on the states of the same history, not as a constraint on
the permutations.

Required wording: "a small, broad improvement (geometric mean about 1.1, median window 1.03)
by refining the same manoeuvre history. Whether it narrows the set of histories was not shown.
The registered question was not shown at this size."

Do not write "refuted": a 10% gain on the weak split is inside the interval.

**2 (major). The weak split is a narrow test of the hypothesis.**
- It holds 156 contact-2 windows of 215, plus contact-1 windows near a gap.
- The ownship-turn clause never fires in this simulator.
- The owner's intuition concerns a leg the window's own bearings cannot resolve, and that case
  was not sampled.
- The split mostly tests an untended contact whose carried prior is overconfident (0.76 on
  validation, 0.90 on test).

The record should say: "The case the hypothesis is about, a window with no useful ownship
manoeuvre, does not occur in this simulator; the study cannot speak to it."

**3 (major). The forecasts failed, and that bears on the settings.**
The forecasts were wrong in both directions:
- weak split: 1.52 on tuning, then 1.07 on validation and 1.105 on test;
- other split: 0.92 on tuning, then 1.11 and 1.14.

Twelve tuning engagements, about 40 weak windows, set the direction, and they were noise.

The registered setting (scale 4, tail 1,200 s) was never run as a chain. It was chosen from an
approximate recomputation of coverage, and it happened to give 0.953 contact-1 coverage. The
outcome is therefore partly luck.

The README should say this. It should also say that "about 1.2–1.4" came from a seed whose sign
on the other split was wrong. The panels of specs 018 and 025 made the same point: one small
tuning seed has no forecast value.

**4 (minor). Bootstrap unit.**
`study27.ratio` resamples (engagement, contact) loads, so contact 1 and contact 2 of the same
engagement are separate units. The weak split reports "94 engagements" from 60. The two
contacts share an ownship and simulator draws, so the intervals are somewhat optimistic.

Contact 1's interval is [1.006, 1.22]: its lower limit is within 0.01 of 1. State the bootstrap
unit, report that limit to three decimals, and call the result borderline, not "clearest".

**5 (minor). Position along the chain.**
By position the ratios are 1.17, 0.98, 1.26, 0.99, 1.24, 1.02: they alternate. This shows no
growth along a chain, but the pattern is unexplained. Report it without interpreting it. The
most that can be said is "errors do not accumulate".

**6 (minor). "ctl-carry's start is no help here, and the prior is what helps".**
ctl ÷ ctl-carry is 0.95 [0.89, 1.02]: on this seed the carried start leans to harm. The prior
first recovers that, then adds about 10%. Write instead: "the prior also offsets the carried
start's slight cost on this seed".

**7 (minor). Under-claimed.**
- The guard is worth stating plainly: on its 8 fall-backs, the unguarded answer was 1.85 times
  `ctl`'s error.
- There is no harm on any split, in range, course or speed. That is a real safety result for
  adoption.

**8 (minor). Practical significance.**
- A median window of 1.03 for 24% more search time is a modest trade.
- The reference told the true history is still 0.72–0.86 of `ctl-prior`'s error.
- The joint solve was 1.7 times better on 12 tuning pairs (reported only), at about three times
  one window's time.

Most of what is attainable across windows is therefore not captured by a single-state
hand-over.

### Recommended next step (owner's choice)

**(A), the default.** Adopt `ctl-prior`, guard included, as the standing chained system for
tended contacts up to 12 h, scoped as "a small refinement, no harm shown". Then close the
long-engagement track as a simulation study, as spec 026's panel recommended. Reopen it only
with one of:
- a scenario where a leg genuinely lacks ownship geometry;
- measured realism;
- association.

Alternatives:
- **(B)** A registered joint solve over consecutive windows, using spec 025's machinery on
  chains. It is the only lead with a large effect (1.7×), but it rests on 12 pairs and costs
  about three times as much. Register it against `ctl-prior` on fresh seeds (357 onward), with
  a split where the ownship holds course for a window.
- **(C)** A targeted test of the owner's intuition: a simulator option in which the ownship
  holds course for 1–2 h, with `ctl-prior` scored there. It is cheap and directly answers the
  question this study could not.
- **(D)** Stop without adopting, keeping `ctl`. Not recommended: no harm was found, and the
  guard works.

## Resolution

**R1. Constructed ties (reviewer 2, finding 1).**
- 110 contact-2 windows had nothing handed on: the previous window was unanswered, had too few
  bearings, or its fit failed. Thirteen of them were scored, all as exact ties. No contact-1
  window lacked a hand-over.
- Without them, the weak split is 1.112 [0.964, 1.297]; contact 2 is 1.172 [0.975, 1.414].
- The outcome is unchanged. Reported in `ties.json`.

**R2. Bootstrap unit (reviewers 1, 2 and 3).** The registered computation resamples chains
(engagement and contact), not engagements. Clustered by engagement (58 units), weak is
1.105 [0.951, 1.279]; with handed-on windows only, 1.112 [0.959, 1.315]. Unchanged; recorded
as a deviation from the decision record's wording.

**R3. The carried mean can keep information from the overlap (reviewer 2, finding 2).**
- This is a defect in the registered code: `hand_on`'s refit starts from the full-window fit.
  It is recorded and not repaired, because the code is bound.
- At the study's scale, contact-1 coverage on test was 0.953 [0.930, 0.974] and after gaps 0.937.
  The defect did not show as overconfidence there.
- On validation, contact-2 coverage was 0.76 [0.67, 0.86]. The registered check covered only
  contact 1, yet the weak split is mostly contact 2.
- The registered settings were extrapolated from an approximate grid, not run as a chain on
  tuning. The grid's raw covariances already carried the tuning run's own scale and tail
  (reviewer 2, finding 4).

**R4. Wording (reviewers 1 and 3).** The README now reads:
- **Beside the rule:** "Beside the rule, not decided: about 1.1 in geometric mean (1.03 in the
  median window) on the tended contact's ordinary windows, in range and course, on validation
  and test; an average shift with many losses, not a gain in most windows."
- **Where the gain sits:** the claim "mostly a better estimate of the same history" is
  withdrawn. "Agree" counted manoeuvres only, and per window the gain is similar where the
  count changed (98 of 455 windows). Whether the same history was kept was not tested.
- **The owner's hypothesis:** the case it concerns, a window without useful ownship geometry,
  does not occur in this simulator.

**R5. The guard (reviewer 2, finding 3).** D is smaller than χ²(4) under a consistent prior
(median 2.1 against 3.36), so the effective level is stricter than 0.001. D cannot see a prior
that changed the declared history. Stated in the README.

**R6. What the record owes (reviewer 1, finding 7).**
- **Added to the README:** the guard rate with an interval; the reading by position along the
  chain (no growth); coverage after gaps; the share answered; the tuning joint-solve figure.
- **Not delivered:**
  - a script that generates the README tables;
  - the error before and after each fall-back, chain by chain;
  - a row for windows with an undetermined carried state.

**R7. `classify` misses turns in progress (reviewer 2, finding 6).** No effect: it could only
undercount turns, and the at-most-one-turn clause fired on no window either way.

**R8. Forecasts (reviewers 1 and 3).** Two of five were wrong: the other split's sign, and the
coverage level. The tuning direction came from 40 weak windows on 12 engagements, so it had no
forecast value.
