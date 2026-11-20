# Spec 032 panel, round 1

Three reviewers read the test record (`README.md`, `study.json`, `raw/`), the decision record and
the scorer. **Verdicts: three approve with findings.** No finding changes the outcome: E1 "ctl-prior
better", E2 "not separated", no harm, soundness passed.

## Code reviewer: approve with findings

**What was checked:**
- **Digests match.** No bound file changed after a9d162c.
- **E1 and E2 recomputed independently** on all 100 engagements, with the reviewer's own error,
  plausibility screen and held test: 1.5374 and 1.1127, equal to `study.json`. A bootstrap with
  another seed gives [1.152, 2.052] and [0.834, 1.444].
- **Chains.** `carry2` and `jointheld` have identical chains in all 100 engagements, and the held
  set (165) equals `jointheld`'s windows.
- **S3** uses the widened covariance actually applied (`carry2.py:277-284`).
- **No system reads truth,** apart from the known placement of windows past true manoeuvres.
- **The README's figures match `study.json`.**

**Findings:**
1. **Minor: offset rows.** In 7 of 165 held windows the joint solve is scored on rows offset by
   5–25 s from `carry2`'s (`cli/long.py:340-343`). The effect is negligible.
2. **Minor: plausibility screen.** Each median is over that system's plausible rows. 4% (`ctl`)
   and 8% (`ctl-prior`) of handed-on held windows are partly implausible, so the two medians can
   cover different row subsets. This is the earlier specs' convention, unstated in the README.
3. **Minor: the exclusion leans conservative.** The decided set requires `ctl` to answer, so a
   window that only `ctl-prior` answers is not counted as its win.
4. **Minor:** `range_km` reads truth every 12 rows while scoring uses every 6. This touches the
   bands only.
5. **Minor:** the unit tests do not exercise `score32` on synthetic raw data.

## Statistics reviewer: approve with findings

The scorer's records were rebuilt from `raw/`: E1 1.537, E2 1.113 and joint ÷ ctl 0.724, all
matching. Clustering is light: of 64 engagements, 46 give one window, 15 give two and 3 give three.

1. **Major: E1 is read on half the held windows.**
   - 85 of 165 are decided. The 62 with no hand-over have a median detected share of 0.003.
   - `ctl` fails on 18 handed-on windows and `ctl-prior` on 17, mostly the same ones.
   - Counting a failure as a 100% error leaves E1 at 1.531 [1.157, 2.027].
   - The joint solve answers 163 of 165 held windows. Its median error is 0.19 where the others
     fail and 0.29 where nothing was handed on.
   - E2 is conditioned on `ctl-prior` answering.
2. **Major: the gain is far-range.**
   - E1 is 2.23 beyond 35 km (44 windows, detected share 0.28) and about 1.03 under 35 km (41
     windows).
   - Range and detected share correlate at −0.85. Within each range class, splitting by detected
     share leaves E1 unchanged on small cells.
3. **Major: the prior almost never comes from a blind window.** In 83 of 85 decided windows the
   window before contains an ownship turn. Chains of blind windows are not tested. Hand-overs from
   each chain's first window carry 2.51, against about 1.3 later.
4. **Minor: sensitivities hold.**
   - Engagements weighted equally: 1.48 [1.08, 2.04].
   - Leave one engagement out: 1.47–1.60.
   - 10% trimmed: 1.50.
   - 6 h 1.55, 12 h 1.53.
   - No exact ties; the guard never fell back.
   - The sd of the log ratio is 1.42.
5. **Major (write-up): seed swings are sampling.**
   - Validation's E1 of 0.87 [0.38, 2.13] rests on 20 windows.
   - Pooled over the three seeds, reported only: E1 1.37 [1.05, 1.80], E2 1.19 [0.95, 1.49], joint ÷
     ctl 0.87 [0.67, 1.11], not separated. "The joint beats the 2-hour window" must stay specific
     to this seed.
6. **Major: S3 is not calibration.** Carried χ²(4) distances against the χ²(4) expectation:

   | statistic | observed | expected |
   |---|---|---|
   | median | 0.94 | 3.36 |
   | share under 1 | 0.51 | 0.09 |
   | share over 20 | 0.059 | 0.0005 |

   The region is too wide in the core and too narrow in the tail. One-turn coverage is 0.79.
7. **Minor: the carried start.** `ctl-carry` equals `ctl` on 33 of 85 windows. "The carried start
   alone does nothing" overstates.
8. **Minor: E2 depends on weighting.** Engagements weighted equally give 1.02 [0.80, 1.31], and
   its band readings change sign. Report only "not separated, at this size".

## Interpretation reviewer: approve with findings

1. **Major: the population.**
   - 48% of held windows are unscored. Their median range is 72 km and contact was lost on them.
   - Answered shares on handed-on held windows: joint 103/103, `ctl-prior` 86/103, `ctl` 85/103.
   - 85 windows came in, against about 120 forecast.
2. **Major: E1 is "more data beats no data" again.** E2 is the fair comparison. It shows the
   summary is not shown to lose to the bearings, not that it beats them.
3. **Major: the gain sits beyond 35 km.**
   - At 15–25 km E1 is 0.82 [0.48, 1.41] and E2 0.53 [0.22, 1.07]. Both lean against `ctl-prior`.
4. **Major: the population moves between seeds.** Median range was 28–30 km on tuning and
   validation and 37 km on test; detected share fell from 0.66 to 0.46.
5. **Minor: consistent with earlier specs.** Spec 031's supplement had joint (2 h) ÷ 2-hour
   `ctl-prior` at 1.56; spec 028 had 1.11 on contact 1.
6. **Minor:** one-turn coverage 0.79 is overconfident across a turn. Do not quote it as an
   uncertainty there.
7. **Minor:** "the carried start does nothing" holds on this seed only. On tuning `ctl-carry` had the
   lowest median error.
8. **Minor:** the cost of `carry2` covers four systems, so it is not `ctl-prior`'s alone.

**Owner's question:** a qualified yes.
- The previous track constrains a blind window at long range far better than nothing.
- It does about as well as solving over the previous bearings, but needs only the state and its
  covariance.

**Adoption:** 2-hour `ctl-prior` with its guard is supported as the standing chained system for the
tended contact up to 12 h, with the limits above. The joint solve stays as the equal alternative
when the bearings are kept.

**Recommended next step:** close the long-engagement track with a synthesis of specs 023–032.
Alternatives:
- an E2 study at ordinary ranges (15–25 km);
- repair the hand-over and the process noise, then check one-turn coverage;
- predict and score through lost-contact windows.

## Narrowings carried into the README and write-up

- **Population:** E1 is read on 85 of 165 held windows (52%), the ones where contact was kept and a
  hand-over made.
  - Answered shares: joint 0.99, `ctl-prior` 0.52 of held windows.
  - Lost-contact windows are outside the claim.
- **Range:** the gain is a far-range effect, about 2.2 beyond 35 km and about 1.0 under. Range and
  contact loss cannot be separated in this design.
- **E1 is "more data beats no data".** E2 against the same past bearings is not separated: the
  compact hand-over is not shown to lose to keeping the bearings.
- **The prior comes from a window with an ownship turn** in 83 of 85. Chains of blind windows are
  not tested.
- **Joint ÷ ctl** is seed-specific. Pooled over three seeds it is 0.87 [0.67, 1.11], not separated.
- **S3** is a gross-fault screen, not calibration. One-turn coverage is 0.79.
- **The cost of `carry2`** covers four systems.
- **Limits:** windows are placed past true manoeuvres; spec 028's hand-over defect is kept; one
  simulator, contact 1.
