# Spec 027 test record (seed 356): the previous window as a prior

## Run and scoring

- **Engagements:** 30 + 30 realistic engagements of 6 and 12 hours, both contacts
  (`configs/long/cp-test.json`).
- **Settings:** the registered ones (scale 4, tail 1,200 s, α = 0.001; decision record
  `experiments/20261119-cp-decision/`, code `09a7edae…`).
- **CI:** run 44448485807, commit 274154e, AMD EPYC 9V45. 120 jobs took 76 runner-hours.
- **Raw outputs:** in `raw/`.

Scored once:

    uv run tma2-long study27 --raw experiments/20261119-cp/raw \
        --config configs/long/cp-test.json --out experiments/20261119-cp

**Provenance:**
- `study.json` records `git_dirty: true` only because the record's folder was untracked when
  it ran. The scoring code is that of the decision record.
- `supplement.json` comes from `scripts/research/cp_supplement.py`.

## Soundness

| check | value | |
|---|---|---|
| S1 windows ran | 720 of 720, no engagement missing | pass |
| S2 ctl ÷ true-history fit (per-engagement geometric mean) | 1.44 [1.30, 1.58] | pass |
| contact-1 coverage of the carried 95% region | 0.953 [0.930, 0.974] (300 hand-overs) | |

## The rule's output: **not shown, at this size** (no harm)

The registered question is answered for this simulator's **untended contact, plus contact-1
windows near a gap**. The "at most one ownship turn" clause fired on no window.

ctl ÷ ctl-prior is a geometric mean over windows of per-window median error. Above 1 favours the
prior. Chains' first windows are excluded.

| split | windows (chains) | range | course | speed |
|---|---|---|---|---|
| **weak geometry (registered)** | 215 (94) | **1.105 [0.963, 1.273]** | 1.12 [0.97, 1.31] | 1.16 [0.95, 1.40] |
| other | 240 (60) | 1.14 [1.035, 1.27] | 1.22 [1.08, 1.38] | 1.07 [0.91, 1.23] |
| contact 1 | 299 (60) | 1.11 [1.006, 1.22] | 1.17 [1.04, 1.31] | 1.04 [0.89, 1.20] |
| contact 2 | 156 (57) | 1.16 [0.988, 1.37] | 1.18 [0.99, 1.39] | 1.26 [1.006, 1.55] |

- **Gain:** the lower limit on the weak split is 0.963, not above 1, so gain is not shown.
- **Harm:** no upper limit is below 1 on any split, in range, course or speed.

**Sensitivities** (panel; `ties.json` from `scripts/research/cp_ties.py`): none changes the
outcome.
- **Bootstrap unit:** the registered computation resamples chains, one per engagement and
  contact. The decision record said "engagements".
  - Clustered by engagement (58 units), weak is 1.105 [0.951, 1.279].
- **Constructed ties:** 13 scored contact-2 windows had nothing handed on, so `ctl-prior` was
  `ctl` there.
  - Without them, weak is 1.112 [0.964, 1.297], and 1.112 [0.959, 1.315] clustered by
    engagement.
- **Registration:** the soundness check covered contact 1 only, and the registered settings
  were extrapolated from an approximate grid, not run as a chain on tuning.
  - The decided split is mostly contact 2, whose carried prior was overconfident on
    validation (coverage 0.76 [0.67, 0.86]); on test it was 0.90 [0.86, 0.94].

## Against the forecasts (decision record)

Two of the five forecasts were wrong: the other split's sign, and the coverage level. The tuning
direction came from about 40 weak windows on 12 engagements, so it had no forecast value.

| forecast | outcome |
|---|---|
| weak split, range: about 1.2–1.4, lower limit above 1 with probability about 0.6 | 1.105 [0.963, 1.273]: smaller, not shown |
| other split, range: about 0.95, harm with probability about 0.3 | 1.14 [1.035, 1.27]: wrong in sign |
| weak split: the course gain larger than the range gain | 1.12 against 1.105: about equal |
| guard falls back on 1–4% | 1.8% (8 of 443) |
| contact-1 coverage 0.88–0.92; contact 2 lower | 0.953; contact 2 0.90: wrong in level |

## Reported beside (decided by nothing)

These readings are not adjusted for how many were taken: 4 splits × 3 quantities, several
ratios, 7 chain positions and 2 durations.

### Size of the shift

On the tended contact's ordinary windows, ctl ÷ ctl-prior is about 1.1 in geometric mean and
1.03 in the median window, in range and course, on validation and test alike. This is an
average shift with many losses, not a gain in most windows. In range:

| split | geometric mean | trimmed 10% at both ends | median | windows better | ×2 better / worse |
|---|---|---|---|---|---|
| other | 1.14 [1.035, 1.27] | 1.10 [1.03, 1.19] | 1.03 | 56% | 17% / 10% |
| weak | 1.105 | 1.07 [0.97, 1.17] | 1.03 | 54% | 13% / 11% |

Validation gave 1.11 [0.96, 1.27] on the other split. Contact 1's lower limit, 1.006, is
borderline.

### The prior's own effect

ctl-carry ÷ ctl-prior shares the carried start, so it isolates the prior:

| split | ctl-carry ÷ ctl-prior |
|---|---|
| weak | 1.14 [1.03, 1.27] |
| other | 1.22 [1.11, 1.34] |
| contact 1 | 1.16 [1.07, 1.26] |
| contact 2 | 1.22 [1.09, 1.36] |

On this seed `ctl-carry` is level with `ctl`: 0.952 [0.893, 1.021] on contact 1, against
spec 026's 1.017. The prior offsets the carried start's slight cost and then adds about 10%.

### Where the gain sits

| split | same declared manoeuvre count | count changed |
|---|---|---|
| other | 1.13 (205 windows) | 1.23 [0.88, 1.75] (35 windows) |
| weak | 1.12 (152 windows) | 1.06 [0.79, 1.45] (63 windows) |

The gain is not concentrated where the declared manoeuvre count changed (98 of 455 windows);
per window it is similar either way. Whether the same history was kept was not tested: "same"
here means the same count, not matched times and kinds.

### By window position along the chain

| position | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| ctl ÷ ctl-prior | 1.17 | 0.98 | 1.26 | 0.99 | 1.24 | 1.02 | 1.25 |

There is no growth along a chain: errors do not accumulate. The alternation is unexplained.

### Guard

- **Rate:** it fell back on 8 of 443 windows, 1.8% [0.9, 3.5] (Wilson interval over windows).
- **Effect:** on those 8, the unguarded answer was 1.85 times `ctl`'s error (ctl ÷ noguard
  0.54 [0.32, 0.86]).
- **Over all windows:** guarded and unguarded are nearly equal (weak 1.105 against 1.099).
- **Limits** (panel):
  - Under a consistent prior, D runs below χ²(4) (median 2.1 against 3.36), so the effective
    level is stricter than 0.001.
  - D compares the same history with and without the prior. It cannot see a prior that changed
    which history was declared.

### Coverage of the carried 95% region

| | hand-overs | coverage |
|---|---|---|
| contact 1 | 300 | 0.953 [0.930, 0.974] |
| contact 1, near a gap | 95 | 0.937 [0.88, 0.98] |
| contact 2 | 190 | 0.90 [0.86, 0.94] |

### Other comparisons

- **Contact-1 windows near a gap** (the contact-1 part of the weak split): 0.98 [0.79, 1.25]
  over 59 windows.
- **References** (÷ ctl-prior): C″ is 2.9–4.9; the fit told the true manoeuvre history is 0.72
  (weak) and 0.86 (other).
- **Spec 025's joint solve** (tuning only, 12 pairs, reported only): ctl-prior ÷ joint 1.73,
  at about three times one window's time.
- **Duration:** 6 h 1.12 [0.97, 1.28]; 12 h 1.13 [1.03, 1.26].
- **Cost:** the prior's two searches took 18.6 of 75.9 runner-hours, about 24% of the run.
- **Answered:** windows are scored where both systems answer, 76% of windows. One window was
  answered by only one of `ctl` and `ctl-prior`.

## Known defects (panel, recorded and not repaired: the code is bound)

- **Overlap information in the hand-over:** `hand_on` refits from the previous window's full
  fit. On a flat valley the refit does not move, so the carried mean can keep information from
  the overlap bearings: they are counted twice.
  - The Gaussian in (x, y, course, speed) also cannot follow a curved ridge.
  - On short test windows the reviewer found coverage 0.40. At this study's scale, contact-1
    coverage was 0.953, so the defect did not show there.
- **Coverage grid:** it assumed the raw covariance does not depend on the settings.
- **Dropped manoeuvres:** a manoeuvre starting within 10 s before the hand-over is dropped.

## What this does and does not support

- **Registered question:** does the prior help where the window's own geometry is weak? Not
  shown, at this size, for this simulator's untended contact and windows near gaps.
- **The owner's hypothesis:** the case it concerns, a window with no useful ownship manoeuvre,
  does not occur in this simulator. The study cannot speak to it.
- **What the test shows, not decided:** carrying the previous window's state and uncertainty
  into the fit gave a small average shift: about 1.1 in geometric mean and 1.03 in the median
  window, with many losses. It was clearest on the tended contact's ordinary windows, in range
  and course, and it did no harm anywhere.
  - Whether it narrows the set of histories was not shown.
- **Not delivered** (see `review.md`):
  - a script that generates these tables;
  - the error before and after each fall-back, chain by chain;
  - a row for windows with an undetermined carried state.

**Panel:** round 1, three reviewers, each approve with findings (`review.md`).
