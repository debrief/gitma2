# Spec 031 panel, round 1

Three reviewers each read the test record (`README.md`, `study.json`, `supplement.json`, `raw/`), the
decision record and the scorer. **Verdicts: three approve with findings.** No finding changes a
decided number enough to move a reading.

## Statistics reviewer: approve with findings

The reviewer reproduced D1 0.730 [0.579, 0.917], D2 0.774 [0.632, 0.954] and D3 0.488
[0.386, 0.619] from `raw/` (179 windows, 56 engagements).

1. **Major: (b) has more information than (a) and answers later.**
   - In 176 of 179 decided windows, (b) takes its rows from a 2-hour window that contains an
     ownship turn.
   - That window runs past the end of the 1-hour window by a median of 29 min (quartiles 15
     and 60 min, at most 104 min).
   - D1 and D3 therefore compare different latencies. The result does not hinge on the late
     bearings: D1 is 0.62 [0.45, 0.90] where they run ≤ 30 min past and 0.88 [0.64, 1.18]
     where they run further.
   - D2 uses only earlier bearings, so it is the clean comparison. It still reads worse.
2. **Major: "beats it" needs its spread.**
   - D1: 1-hour `ctl-prior` better in 43% of windows, twice as good in 23%, twice as bad in 35%.
   - D2: 41%, 22% and 37%.
3. **Minor: the readings are robust.**
   - Trimmed 20% at both ends: 0.78, 0.76, 0.51.
   - Leaving one engagement out: D1 0.69–0.75, D2 0.75–0.80, D3 0.46–0.50.
4. **Minor: heterogeneity by length.** D2 is 0.62 [0.45, 0.85] on 6-hour engagements and 0.90
   [0.69, 1.17] on 12-hour ones (not separated). D1's halves both have upper limits just
   above 1.
5. **Minor: the exclusions favour (a).** The four handed-but-undecided windows are (a)'s
   failures to answer. Dropping them and the windows with no hand-over can only flatter (a), so
   the readings are conservative.
6. **Minor: rows differ slightly.** (b) is scored on exactly (a)'s rows in 145 of 179 windows,
   (c) in 166.
7. **Minor: the soundness checks have little power.** S2 is a gross-fault screen. S3 is coverage
   within a band, not a calibration: give the median NEES.
8. **Minor: the forecasts.**
   - D1 and D2's forecasts were wrong in direction, again from about 34 tuning windows.
   - D3 was added on tuning. Its effect is the largest, and it was chosen after the tuning data
     were seen.

## Code reviewer: approve with findings

The reviewer recomputed independently, with their own range-error code: D1 0.7304, D2 0.7743,
D3 0.4881. These match to four digits.
- The `jointheld` chains match `carry2`'s in all 60 engagements.
- The classes are consistent.
- Window settings (3600/900 and 7200/1800) and the carried settings were confirmed from the
  run headers.

1. **Minor: rows offset.** The 1-hour rows and their comparators' rows are offset by 1–5 rows
   (up to 25 s) in some windows (`study30.py:197-199`, `cli/long.py:330`). In 23 held windows
   they share no row. The spans are the same, so the effect on a median is negligible.
2. **Minor: four failures, unnamed.** Engagement/window 41/9, 45/12, 49/12 and 51/2 were handed
   on, but 1-hour `ctl-prior` returned NaN on every row; the comparators answered. Counting them
   as losses strengthens the outcome.
3. **Minor: the supplement's population.** The supplement's 2-hour `ctl-prior` readings use 183
   windows, not D3's 179 (`cmp_supplement.py`).
4. **Minor: missing npz.** `jointheld` writes no `.npz` when there are no held windows, and
   `_load_joint` then crashes. Engagement 1's hand-made empty archive is inert. As written, S1
   cannot tell "no held windows" from "job lost".
5. **Minor: data horizon.** D1 and D3 can use bearings after the 1-hour window ends. D2 has the
   same horizon as (a).
6. **Minor, known limit.** `chain` moves window starts past true manoeuvres, so the joint
   union's start is set on the truth too.
7. **Note.** The plausibility screen reads truth, as a scoring convention applied to every
   system. No system reads truth.

## Interpretation reviewer: approve with findings

1. **Major: D2 is the like-for-like answer to spec 029's panel.** D1 and D3 mostly measure "a
   window long enough to include a turn and later bearings".
2. **Major: the owner's case is absent.** With 1–2 h legs, a 2-hour window is never blind.
   Legs longer than the window, where a carried prior is the only remedy, are not tested.
3. **Major: "adopt `ctl-prior` on 2-hour windows" is not decided here.**
   - D3 compares against 1-hour `ctl-prior` only.
   - The edge over 2-hour `ctl` is supplement only: medians 1.14 held and 1.01 one-turn, and
     validation went the other way (0.076 against 0.065).
   - The registered support is still spec 028's (contact 1, 1.11 [1.006, 1.22]).
4. **Major: cost.** 477 s against 112 s is per window, and the windows advance 90 against
   45 min.
   - Per engagement-hour it is about 318 against 149 s: 2.1× for the whole `carry2` job, which
     also runs `ctl-carry`, the no-guard variant and the reference. No single system's cost is
     known.
   - Latency: (b)'s estimate waits up to about an hour of later bearings, and it updates every
     90 min against 45.
5. **Major: the tuning flip has a likely cause.** On tuning, (a) was copied from spec 029's run
   (EPYC 7763), while (b) and (c) ran on EPYC 9V74. Spec 024's gotcha forbids comparing across
   runs. Together with 34 windows, this explains D1 1.30 and D2 1.28 on tuning.
6. **Minor:** the pooled ratios are averages with wide spread. Give the shares.
7. **Minor:** some range bands are not separated. D2 at 15–25 km is 0.938 [0.66, 1.35].
8. **Minor:** the span reference is not a ceiling for 2-hour `ctl-prior`, which has a carried
   prior and later bearings.
9. **Minor:** S3 covers (a)'s hand-overs only. The 2-hour hand-overs' guard rate and coverage are
   not reported.
10. **Minor:** spec 029 replicated at 1.71 [1.40, 2.14]. Quote it as about 1.7 to 2.4.

**Recommended next step: close the long-engagement track as a simulation study** (the owner's
choice). Alternatives:
- legs longer than the window (2–4 h legs, 2-hour windows) with past-only comparisons;
- reopen with new information (measured realism, an ownship steered by its own track,
  association).

## Narrowings carried into the README and write-up

- D2 is the clean comparison: the same past, no later bearings. It reads "ctl-prior worse".
- D1 and D3 include an ownship turn in 98% of windows and later bearings (a median of 29 min).
- The pooled ratios are averages: (a) is better in about 4 windows in 10 and twice as bad in
  about a third.
- The exclusions favour (a), so the readings are conservative.
- Spec 029's recommendation is withdrawn: a 1-hour window with a carried prior is no substitute
  for a longer window.
- `ctl-prior` on 2-hour windows rests on spec 028's registered result. Here it is supplement only.
- Cost is about 2.1× per engagement-hour for the whole job.
- The limits: legs of 1–2 h, contact 1, one simulator, windows placed past true manoeuvres, and
  spec 028's hand-over defect kept.
