# Spec 029 test record: agent review panel, round 1

Three reviewers each read the record, the registration and the code on their own:
statistics and registration fidelity, code and design, and interpretation. All three approve
with findings. The reviews are given below, then how each finding is resolved. The
sensitivities are in `supplement.json` (`scripts/research/hold_supplement.py`).

**Decided by the panel:**
- **Outcome:** the rule's output stands: **gain** on windows with no ownship turn, **no harm**
  in either non-empty class.
- **Reproduction:** the scorer re-runs exactly, and the digests hold.
- **What the record may claim** is narrowed, as given in "Resolution".

## Reviewer 1 (statistics and registration fidelity): approve with findings

The rule reproduces exactly:
- the scorer re-run matches `study.json`, except NaN ≠ NaN in the empty "more" class;
- the digests match on all 12 bound files and on code `c39cb031…`;
- the decision commit (7ba9497) precedes validation (defd850) and the test (ec66def).

The rule's output stands: **gain on held windows, no harm in either non-empty class.**

### Findings

1. **(major, wording) The baseline is `ctl` on 1-hour windows, not the standing configuration.**
   - The standing configuration is 2-hour windows overlapping 30 min.
   - 189 of the 219 held windows follow a one-turn window, so `ctl-prior` receives the
     previous turn's information and `ctl` is denied it by the window length.
   - Narrowing: "a turn-free 1-hour window given its predecessor's state beats the same window
     alone". Name 2-hour `ctl` and the joint solve as untested.
2. **(minor) "Roughly halves" mixes classes.** On held windows the geometric mean is 2.41 and
   the median 2.15, and the median error falls from 0.227 to 0.074. One-turn windows: 1.22.
3. **(minor) The 36 held windows with no hand-over do not bias the result.**
   - Their median range is 68 km, against 23 km for held windows that were handed on.
   - 18 of them have zero bearings, and `ctl` answers only 6 of the 36.
   - Counted as ties: held 2.34 [2.01, 2.75], one turn 1.21 [1.06, 1.38].
   - The README must print the class table: 219 / 183 / 176 held windows and 441 / 382 / 354
     one-turn windows (windows / handed on / scored).
4. **(minor) Dependence within engagements.** The registered pooled mean weights engagements by
   their window count. The result holds under other weightings:
   - equal weight per engagement: 2.31;
   - the median engagement: 2.20;
   - engagements above 1: 86%;
   - leaving out one engagement: 2.35–2.48.
5. **(minor) The gain depends on range.**

   | range band | held | one turn |
   |---|---|---|
   | < 15 km | 1.66 [1.34, 2.09] (42 windows) | 1.02 [0.81, 1.33] |
   | 15–25 km | 2.15 [1.52, 3.01] | 1.23 |
   | > 25 km | 3.19 [2.50, 4.07] | 1.27 |

   Report the bands.
6. **(minor) A hand-over through a gap still gains.**
   - After a gap: 1.95 [1.39, 2.78], 44 windows.
   - Contiguous: 2.59.
   - A held window after a held window: 2.31 [0.79, 6.78], 11 windows. Not tested at this
     size.
7. **(minor) The harm rule.** It is conservative under multiplicity. The closest call is
   one-turn speed, 1.15 [0.99, 1.33].
8. **(minor) The tuning README claims something it could not know.** Its sentence "as in
   validation and test, 71% … answered" was written before either existed, and it is false:
   the test gives 0.80. Correct it.
9. **(minor) "Beats the fit told the true history".** Framed correctly, but keep it out of the
   headline.

## Reviewer 2 (code and design correctness): approve with findings

The decided number reproduces exactly: held 2.4136 [2.062, 2.825], outcome "gain". The digests
are unchanged.

**Checks that passed:**
- **Run settings:** all 60 raw headers record 1-hour windows overlapping 15 min, contact 1, the
  registered settings, a clean tree and commit ec66def.
- **Units:** `ownship_turns` and window rows are both sample indices.
- **Hand check:** three held windows, recomputed by hand, equal `load27` to every digit.
- **Coverage:** the scorer uses the widened covariance, wraps the course and uses χ²(4) at 95%
  (9.4877), evaluated at the hand-over row.
- **No double counting by construction:** each hand-over uses only bearings before it, and the
  bearing sets are disjoint.
- **No truth in the carried path.**
- **Widening:** course is widened to about 67° sd. In practice the prior carries position and
  leaves course and speed loose.

### Findings

1. **(minor) The 36 excluded held windows are windows where contact was lost.**
   - Their median is 1 bearing.
   - In 97% of them the previous window was unanswered.
   - Their median range is 68 km.

   The one-turn class shows the same pattern. Changes no number; state it.
2. **(minor, design limit) A hand-over never falls inside a target manoeuvre, by truth.**
   - `timelate.chain` moves each window's start past any true manoeuvre (`in_manoeuvre`), so
     every hand-over is on a target leg.
   - 14 of 176 held windows were shifted: 1.71 shifted, 2.49 not.
   - This is inherited from spec 023. Add it to the limits.
3. **(minor) The held-window gain is confounded with range.** Held ctl ÷ ctl-prior:

   | range | ratio | windows |
   |---|---|---|
   | under 10 km | 1.31 | 17 |
   | 10–20 km | 2.05 | 55 |
   | over 20 km | 2.91 | 104 |

   Report a range split.
4. **(minor) The coverage figure hides a mis-shaped region.**
   - Held coverage is 0.945, but the median NEES is 0.74 against χ²(4)'s median of 3.36.
   - The region is too wide for most hand-overs and too narrow for a few.
   - The ×4 scaling alone gives 0.61.
   - Do not read 0.945 as calibration.
5. **(minor) Held windows after held windows gain most** (2.98, median NEES 0.50, 27 windows).
   This is consistent with a real chain. It is also where the hand-over defect would act. Not
   separable here.
6. **(minor) Row sets.** `plausible` drops `ctl`'s worst rows, so the comparison is
   conservative. Negligible.
7. **(minor) S2's reference is fitted on unedited bearings.** S2 is reported only.
8. **(minor) Thin tests.** The unit test covers `turns_in` only.

## Reviewer 3 (interpretation and claims): approve with findings

The rule's output is a gain, and it is solid:
- held windows: 2.41 [2.06, 2.83], median 2.15, trimmed 2.29;
- 76% of held windows better, 9% twice as bad;
- the same direction on three seeds: tuning 2.10, validation 1.91, test 2.41.

### Findings

1. **(major) The comparator is a window chosen to be blind.**
   - Windows were cut to 1 hour so that turn-free windows exist, so `ctl` on a held window has
     no range information by construction.
   - The gain is "more data beats no data". It does not show that the prior beats the next-best
     way of using the same bearings: a 2-hour window, or a joint solve over consecutive
     windows. Neither was tested.
   - Required wording: "against the same system on the same 1-hour window alone; not compared
     with a longer window or a joint solve over the previous window's bearings."
2. **(major) The mechanism is range observability; "permutations" is not shown.**
   - No manoeuvre-history measure was taken.
   - The gain is largest where the window has no geometry of its own: held 2.4, one turn 1.2.
     It is larger on 12-hour engagements than on 6-hour ones (2.58 against 2.10).
   - Required wording: "knowledge of the previous track usefully constrains this leg's solution
     where the leg alone cannot resolve range: supported in this simulator, for the tended
     contact, on 1-hour windows. Whether it narrows the set of manoeuvre histories was not
     measured."
3. **(moderate) Limited generalisation.**
   - One simulator family, contact 1 only, 1-hour windows.
   - Not tested: the untended contact, 2-hour windows and real data.
   - Held windows are confounded with range and with keeping contact. Both systems answer
     nearly the same share (0.835 and 0.838).
4. **(moderate) The fit told the true history is no reference here.**
   - `ctl-prior` beats it on held windows: fit ÷ ctl-prior 1.83 [1.45, 2.32].
   - Window-alone references are handicapped against any system that carries information. In
     chained designs, read them as soundness only.
   - Future chained studies need a reference told the truth over the whole span.
5. **(moderate) Narrow `ctl-carry`'s adoption.**
   - On one-turn windows, ctl ÷ ctl-carry is 0.89 [0.82, 0.96]: the carried start costs 11%.
   - Spec 026's non-inferiority holds for 2-hour windows with two or more turns only.
   - Do not use `ctl-carry` without the prior.
6. **(minor) The one-turn class is reported, not decided.**
   - Its median is 1.12, and 18% of its windows are twice as bad.
   - The fit told the true history is level with `ctl-prior` there.
   - Required wording: "an average shift with many losses."
7. **(minor) "Realistic" means spec 024's simulated realism.** Give the held figure across seeds
   (1.9–2.4), and note that the test came in above the forecast.
8. **(minor) Name the hand-over defect in the limits.** The 15-minute overlap is a quarter of
   each window, and its information can be counted twice.

### Recommendation

**Default:**
- Adopt `ctl-prior` with its guard as the standing chained time-late system for the tended
  contact, scoped to these conditions.
- Next, one registered comparison on held-course engagements:
  - `ctl-prior` on 1-hour windows;
  - `ctl` on 2-hour windows;
  - a joint solve over two consecutive windows;
  - a reference told the truth over the span.

**Alternatives:**
- (a) Repair the hand-over and rerun on spent seeds.
- (b) The untended contact under held course.
- (c) Close the track and write it up.

## Resolution

**R1. The comparator (reviewers 1 and 3, major).**
- The decided comparison is a turn-free 1-hour window given its predecessor's state, against
  the same 1-hour window alone. The windows were shortened so that turn-free windows exist.
- Not tested:
  - `ctl` on its standing 2-hour windows (spec 023/026);
  - a joint solve over two consecutive windows (spec 025).
- The README and write-up say this in their headline.

**R2. The mechanism (reviewer 3, major).**
- The supported reading: the previous track usefully constrains this leg's solution where the
  leg alone cannot resolve range.
- Whether it narrows the set of manoeuvre histories was not measured.

**R3. Sensitivities** (reviewers 1 and 2; `supplement.json`). None changes the outcome.
- **Ties included:** held 2.34 [2.01, 2.75].
- **Each engagement weighted equally:** held 2.31; median engagement 2.20; 86% of engagements
  above 1.
- **Range bands, held:**
  - under 15 km: 1.66 [1.34, 2.09];
  - 15–25 km: 2.15 [1.52, 3.01];
  - over 25 km: 3.19 [2.50, 4.07].
- **Range bands, one turn:** under 15 km 1.02 [0.81, 1.33], not separated from 1.
- **Hand-over after a gap:** held 1.95 [1.39, 2.78].

**R4. The class table and exclusions (reviewers 1 and 2).**
- The table is added to the README:

  | class | windows | handed on | scored |
  |---|---|---|---|
  | held | 219 | 183 | 176 |
  | one turn | 441 | 382 | 354 |

- The 36 held windows with no hand-over are windows where contact was lost: median range
  68 km, `ctl` answers 6.

**R5. Coverage (reviewer 2).** The 0.945 is a pass of the soundness band, not a calibration.
The median NEES is 0.74 against 3.36, so the region is too wide for most hand-overs.

**R6. Limits added to the README.**
- Hand-overs never fall inside a target manoeuvre, because the windows are moved by truth
  (inherited from spec 023).
- The hand-over defect is kept: held windows after held windows gain most (2.98, 27 windows),
  and this is not separable from the defect.
- One simulator, contact 1 only, 1-hour windows.

**R7. `ctl-carry`'s scope (reviewer 3).**
- On one-turn windows, ctl ÷ ctl-carry is 0.89 [0.82, 0.96].
- Spec 026's adoption of `ctl-carry` as a cost measure is limited to the windows it was tested
  on: 2-hour windows with several turns.
- Recommended: no `ctl-carry` without the prior. Recorded in AGENTS.md.

**R8. The tuning README.** Its sentence "as in validation and test, 71% … answered" was written
before either existed, and it is false: the test answered 0.80. It is corrected there, with a
note.

**R9. Reported classes (reviewer 3).** The one-turn class is "reported, not decided; an
average shift with many losses": median 1.12, with 18% of windows twice as bad.

**R10. Not delivered.**
- Unit tests for `study29`'s exclusions, rule and coverage.
- A reference told the truth over the whole span, which future chained studies need.
