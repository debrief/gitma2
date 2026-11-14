# Spec 017: panel review, round 1 (2026-11-14)

Five independent reviewers (numbers and provenance; the measure itself; statistics; code;
scope and conclusions) read the spec, the decision record, the tuning, validation and test
records and the code, and recomputed from the per-row errors (results branch
`results/timelate-tl-f-test-43618868241`) and the period files. **All five: approve with
findings. Decided in one round.** Every registered number reproduces, the registration held
and the logic's output, "a proposer study is not recommended", is correctly computed. What
the record *means* is changed in four ways, and the README is corrected.

Figures here that are not in the generated files are the reviewers' recomputations from
the test's per-row errors and period files. They are not registered results.

## Checked and found sound

- E3, E4, E5, the whole gap and the attainable shares recompute to the reported digits
  with independent code; a different bootstrap seed moves limits by 0.01 at most; a 2.5%
  and a 10% trim leave E4 at 20 at 1.43 and 1.40 and E5 at 1.17 and 1.13; sign tests
  p = 4e-7 (E4 at 20) and 0.016 (E5).
- Detectability shares, miss rates by band and the pooled rate above 40 (138 of 782,
  0.176, Wilson [0.15, 0.21]) recompute from `shift.periods.json`.
- All 18 digests in `decision.json` match the files at registration (b8c0455), at the
  test's commit (6c1f3f9) and at HEAD; no file under `src/` or `configs/` changed between
  them; the code digests in every split's summary are the registered ones.
- Order: tuning 14:25; registration committed 16:02:43; validation run 16:02:50, recorded
  17:02:05; one test run, attempt 1, 17:02:11.
- `tables.md` and `supplement.md` regenerate byte for byte; the record's files equal the
  results branch's.
- Spans, the cost's units, one-to-one matching, the true prior's construction, the edited
  references' bearings, the empty-history path: read and found correct. Removing cut
  manoeuvres from the pairing changes no rate.

## Findings that change the reading

**1. The pooled gap is two kinds of period, not a division within periods** (four
reviewers). On the shifted split at threshold 20:

| Periods | n | Control ÷ `ref-d20` |
| --- | --- | --- |
| Some whole manoeuvre under 20 (the reference is denied it) | 336 | 1.16 [1.04, 1.30], median 1.06; attainable share 0.19 [0.05, 0.34] |
| Nothing under 20 (`ref-d20` is `ref-full`) | 115 | 2.65 [2.12, 3.32] |
| The control misses at least one manoeuvre above 20 | 134 | 2.73, median 2.67; 83% of E4's log sum |
| The control finds them all | 317 | 1.09, median 1.00 |

Where a manoeuvre is hidden, the control is close to the reference that is not told it:
there the limit is identifiability. The attainable part sits in under a third of periods,
where the control misses a manoeuvre the bearings show. "0.44 attainable" averages the
two. By how tight the bound is, the share at 20 is 0.70 [0.56, 0.82] in the tight third of
periods, 0.28 in the middle and 0.20 [-0.08, 0.44] in the loose third. For course and
speed the attainable share is larger than for range (0.55 and 0.48; E4 1.75 and 1.50).

**2. The logic's second condition measured the wrong thing, and depends on the matching
tolerance.** It counts manoeuvres; the cost is per period. The control misses a manoeuvre
above 40 in 100 of 451 periods, where E4 is 3.08 [2.36, 4.03] and which carry 69% of E4's
log sum. The pooled miss rate above 40 is 0.30 at 60 s (interval [0.27, 0.34], reaching a
third), 0.18 at the registered 120 s and 0.11 at 240 s. The "no" is the rule's output at
the registered tolerance; **it follows from the rule and not from the evidence**, and with
a tuning value of 0.18 the condition could hardly have fired.

**3. The attainable part looks at least half a prior problem, not a search problem.** Of
the 138 missed manoeuvres above 40, the same search under the targets' own prior finds 66.
E5 is 2.58 [1.89, 3.58] in the 46 periods where it finds more of them and 1.07 elsewhere.
In 85 of 103 periods with such a miss the control declares fewer manoeuvres than the
truth. A proposer feeding the same evidence would mostly be vetoed by it. The next step
this points to is a prior that adapts to the period, classical and on CPU, with the
true-prior search (1.17) as its ceiling.

**4. The detectability measure and its references are not bounds.**
- *Not additive.* On 39 test periods with two or more manoeuvres under 20, omitting them
  together costs 20 or more in 44% and 40 or more in 18% (one period: singles 18, 0.2 and
  2; together 2,481). `ref-d20` is denied sets the bearings show plainly, and those
  periods carry about two thirds of E3. E1's "can barely be seen" and E3 are biased
  upward; **E3 is not "a lower limit on identifiability"**.
- *Flattered and handicapped at once.* Where every manoeuvre is above 20 and the control's
  history is right (about 80 to 100 periods), the control is still 1.6 to 1.7 times
  `ref-full`: that is the held true times and kinds, not detection. And the control beats
  `ref-d20` in 37% of periods and `ref-d40` in 44%. **E4 is not "an upper limit on what a
  perfect detector could gain"**; brought to the level of the matched periods, the gain
  would be nearer 1.10 than 1.43.
- "Not separated from the reference at 40" holds because that reference is forbidden the
  manoeuvres between 20 and 40, of which the control finds 64%.
- The thresholds are priced by Annex B's evidence: the true-prior search misses 0.56
  between 5 and 10 against the control's 0.79, so "undetectable at 20" is partly
  "unaffordable under the wrong prior".
- The references on the shifted splits are fitted under Annex B's prior.

## Corrections to the first record

- **"The tuning seed differed by more than its intervals" was wrong.** The test's values
  (1.43, 1.17) lie inside the tuning intervals ([0.96, 1.59], [0.86, 1.22]); the
  differences are about 1 and 1.3 standard errors. The forecast failed because a point
  estimate from 134 periods was read as fact; scaled to the test's size, E4's lower limit
  was near 1.08, so the first condition was close to even at registration.
- **The filter ratios were on a selected minority of periods.** IMM and EKF have no state
  before the zig; a period over half before it is dropped (264 and 268 of 451 shifted
  periods), and the rest compare an upper quantile with the control's median. On common
  rows the IMM is 3.75 times the control (shifted, 407 periods), 8.8 (Annex B) and 10.5
  (shifted 2); the EKF 4.1, 8.9 and 9.6. "Far behind" stands; 4.8 to 22 does not. The
  plan's EKF is Gate H's re-tune, not MAN2's frozen one.
- **Shifted 2's "mostly attainable (0.91)"** rests on one clipped runaway reference
  (unclipped 1.05 [0.69, 2.96]) and 19 manoeuvres under 20.
- **"The same miss curve" on Annex B** holds below 40 only: above it the control misses
  0.08 against 0.18. Same structure, smaller identifiability part, and no gain from a
  matched prior there.
- The control's half-way point is near 20 (0.55 from 10 to 20, 0.36 from 20 to 40).
- E1 on the scored periods is 0.354 of 1,380, against 0.37 of 1,475 on all.
- E3's median of 1.03 is ties (nothing dropped in a quarter of periods); where something
  is dropped it is 1.85, median 1.47.
- E4 at 20 is 1.20 where the reference is held (101 periods) and 1.51 elsewhere.
- The pooled rate above 40 is arithmetic from `summary.json` by a script written after the
  test (`tl5_supplement.py`), not by bound code.
- Under outliers the detectability table uses unedited bearings (4% of manoeuvres change
  side at 20); the edited references do not use the control's effective sd.

## Not delivered (added to the README's list)

The split under each way of fitting the reference (FR-005); course and speed in the
estimands; a joint detectability; unit tests for `detect.py` and `run5.py`; one leg in the
paired tables; the paired tables' period counts.

## The panel's order for what follows (the owner's choice)

1. **Recommended: a prior that adapts to the period** (a manoeuvre rate estimated from the
   period, or a hierarchical or mixed-rate prior), classical, CPU, registered against
   `ctl` with the true-prior search as the ceiling and false manoeuvres on held course
   reported.
2. Beside it, a hedged track for the periods where the limit is identifiability.
3. Over-reach: a GPU proposer now; calling the gap "mostly identifiability"; reading 1.17
   as the prior's full worth (one seed, median 1.02, more false manoeuvres).
