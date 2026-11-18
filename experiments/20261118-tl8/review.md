# Spec 025: panel review, round 1 (2026-11-18)

Five independent reviewers each read the spec, both decision records, the tuning, validation
and test records, and the code at the registered commit, and recomputed from the per-row
errors:

1. numbers and provenance;
2. fairness of the comparison;
3. statistics and the rule;
4. code;
5. scope and conclusions.

**All five approve with findings. The outcome is decided in one round.**

The registered outcome stands: by the rule the joint solve gains on all four splits, with no
harm. No bug changes a decided number. What the outcome means is narrower than the record
first said, and several readings are corrected below.

Figures not in the generated files are the reviewers' own recomputations from
`<split>.errors.npz` and `<split>.periods.json`. They are not registered results.

## Verdict on each registered item

| | As registered | Panel |
|---|---|---|
| Soundness (validation, seed 352) | Passes: 1.13 [0.81, 1.63] over 66 engagements; joint answered 1.00 | Reproduced. **It is a gross-fault screen, not an efficiency check** (see "The soundness check" below) |
| Gain, Annex B | 3.10 [2.22, 4.58] | Reproduced bit for bit with independent code. Robust under BCa, cluster-t, ten bootstrap seeds and 5% trimming at both ends (lower limit 1.98 to 2.26) |
| Gain, busier / wild / held | 1.97 / 2.72 / 12.8; all gains | Reproduced. The lowest lower limit is 1.35 (busier, course); with a Bonferroni correction over all 12 tests it is 1.17. **Wild bearings is the same engagements as Annex B**, and held course shares 69 of 70 layouts with it, so these are not independent replications |
| Harm | None | Cannot fire under any correction |
| What follows | The joint solve is the standing system for several periods of one target | **Narrowed:** see "Outcome, as the panel words it" |

## What was checked and found sound

- **Provenance and order.** The plan `tl-k.json` (`bbba4603…`) has one commit, f9fb4f6, and is
  unchanged since. It differs from `tl-j.json` only in its description and two soundness keys.
  Every shard: seed 353, code `ec046dc0…`, commit f9fb4f6, clean tree. Order: registration
  05:27:50; validation run created 05:28:03; validation record 06:36:27; test run created
  06:36:28. Each was a single attempt, and nothing was scored on seeds 352 or 353 before.
- **Tables.** `tables.md` regenerates byte for byte.
- **Counts.** No engagement is repeated, and the joint solve never fell back.
- **Code.**
  - Tracks, truth and both bounds align row for row. On seed 349, the truth of each period
    equals the matching slice of the span's truth exactly.
  - The masked span hides exactly the gap rows; the period rows and the original
    observations are untouched.
  - `period_bound` reads the masked validity.
  - Gap seconds and declared spans share one time base.
  - The layout stream is independent of the generator's draws. Whether a layout is skipped
    depends on the engagement's length only.
- **Fairness.** The alone side is not handicapped:
  - `ctl` alone ÷ the true history per period is 0.93 (Annex B) and 1.07 (busier), so alone
    is at its own information limit.
  - The ten-manoeuvre budget never binds (the joint solve declares at most 4, or 6 on busier
    targets).
  - Both sides use the same code, settings and priors.
  - Bootstrapping by engagement is the right cluster. Weighting by engagement instead of
    period gives 3.03, against 3.10.

## Corrections and narrowings

1. **The headline mixes two effects (fairness, scope, code; major for the reading).**
   - Rows are chosen by the span's bound. On rows that only the joined data determine,
     `ctl` alone's median relative range error is 0.46 (Annex B), 0.47 (busier) and 0.50
     (held course): about the scoring cut-off, so alone has no estimate there. The ratio
     on those rows is 4.2, 2.5 and 20.5.
   - On rows the period determines alone, the ratio is 2.64 [1.68, 4.70] (Annex B),
     **1.28 [0.95, 1.75] busier (not shown)** and 3.56 held course.
   - On those rows, periods with their own ownship turn read 1.57 [1.16, 2.17] (Annex B),
     **1.06 [0.80, 1.39] busier** and 1.59 wild bearings.
   - The held-course 12.8 is in effect "the span is one leg", which matches the model by
     construction. It is not a measure of reach.
2. **The one by-kind difference that is real everywhere is the ownship turn.** The ratio of
   ratios, periods without their own turn against periods with one, is 2.64 [1.50, 4.76]
   (Annex B), 2.46 [1.83, 3.32] (busier), 2.26 (wild bearings) and 5.48 (held course). The
   gap-length bins are not separated anywhere except one uncorrected, marginal case. "A gap
   that held a manoeuvre gains less" is separated on busier (1.73 [1.13, 2.73]) and wild
   bearings, but **not on Annex B** (1.43 [0.72, 2.59]). The record quoted the Annex B
   difference as a finding.
3. **The soundness check (statistics; major for the check, not the verdict).**
   - Under the record's own one-draw-per-engagement model, a perfectly efficient reference
     has an expected geometric mean of about 0.79, below the band. It passes with
     probability about 0.46 to 0.48, while a reference 1.4 times worse passes with 0.98.
   - It does catch the fault it exists for: a reference that returns its start passes with
     probability at most 0.03.
   - Per-engagement efficiencies run from 0.05 to 510 on validation and up to 773 on test,
     and the geometric mean averages these runaway reference fits away. They should be
     listed.
   - The test-seed figure, 1.09 [0.73, 1.84] over 35 engagements, rules out only gross
     faults.
4. **Splits share engagements (numbers, statistics, fairness).** The record must say that
   wild bearings uses Annex B's engagements, and that held course shares nearly all its
   layouts with Annex B.
5. **Unscored periods (numbers).** On busier targets 48 of 289 periods (17%), including 13
   whole engagements, have no row under the span bound and are dropped for both sides.
6. **What the gaps cost holds only on hard rows (fairness).** Every bearing ÷ joint is 0.61
   on the scored rows, but 0.86 [0.62, 1.18] on rows a period determines alone (not shown).
   The forecast "about a factor of two" is wrong; 0.52 to 0.65 is the range across splits,
   not an interval.
7. **False manoeuvres (fairness, scope).**
   - On held course, the engagement shares 0.17 (joint) and 0.14 (alone) are not like for
     like. Inside periods the joint solve declares fewer (0.09 against 0.14); the excess is
     invented gap manoeuvres (0.15 of held-course engagements, 21% of quiet gaps on Annex B).
   - Those inventions do not cost the ratio, but they are output errors that no ratio
     penalises.
   - 0.17 is 11 of 65 engagements (about [0.09, 0.28]): "not separated from the forecast",
     rather than wrong.
8. **No warning of a failed join (scope).** 12% (Annex B) and 15% (busier) of periods are
   twice as bad joined, and 36% of gap manoeuvres on busier targets are missed. Nothing in
   the output flags a period where joining went wrong, or marks a gap manoeuvre as inferred
   rather than observed.
9. **Weak yardsticks (scope).** Under wild bearings the span reference is fitted to unedited
   bearings (efficiency 2.00; alone ÷ the per-period reference 0.43). So joint ÷ reference
   of 1.10 there is not evidence of near-optimality (spec 016's lesson).
10. **Minor code points, recorded and not repaired; none moves a number.**
    - Tracks pass through float32 (about 1e-2 m in position).
    - The 9-bearing wild-bearing edit window reaches across a gap's edge on the masked span,
      in 1 to 3 engagements a split.
    - `gap_events` counts zero-length true manoeuvres that `run4`'s `true` drops.
    - No unit test covers `run_shard8`'s slicing or its fall-back. The code reviewer's check
      stands in for it.
11. **Not bit-reproducible (statistics).** Reruns differ in the last bits, which moved the
    decided ratio about 8% on tuning. That is immaterial to the verdict (the smallest lower
    limit is 1.63), but the median per-period ratio and the shares carry the same noise.

## Outcome, as the panel words it

By the registered rule, joining gains on all four splits, with no harm. **Within these
simulated conditions, the joint solve (`ctl` over the span with the gaps' bearings marked
missing) is the standing time-late system for two or three periods of one target in a span
of at most two hours.** The conditions:

- periods of 15 to 30 minutes, gaps of 5 to 30 minutes;
- association across the gap certain;
- manoeuvres in the gaps at Annex B's rates;
- the ownship track given.

The gain comes mostly from periods with no ownship turn of their own, which the other
periods' geometry makes answerable (4.35 against 1.65 on Annex B). Where a period is
determined alone, joining gains about 1.6 on Annex B targets and is **not shown** on busier
targets (1.06 with an own turn, 1.28 on own rows). One period in eight is twice as bad
joined, and nothing in the output flags it. Joining is not compared with carrying state
between windows (spec 024), so this is "joining beats ignoring the other periods", not "the
best way to use them".

**The write-up must not claim** any of the following:

- that joining helps where a period already stands alone on busier targets;
- the held-course 12.8 as a general gain;
- validity for long gaps, uncertain association or several targets;
- superiority over carried state;
- near-optimality under wild bearings;
- any learning.

## What the panel wants next (owner's choice), in order

1. Score spec 024's `ctl-carry` on these test engagements once it is merged (the
   registered reading).
2. A per-period consistency flag (alone against joint history and evidence) and markers on
   declared gap manoeuvres. Measure on spent seeds whether the flag picks out the
   twice-as-bad periods.
3. A stated uncertainty for the joined track: coverage by kind of period and by what the
   gap held.
4. A stress split: gaps of 30 to 90 minutes and busier gaps (check the generator's
   manoeuvre table first).
5. Association across a gap (a different contact afterwards): owner's scope; propose, do
   not assume.
6. IMM and EKF as tracks, a test for `run_shard8`'s slicing, and a re-measure of run-to-run
   variation; or record why not.
