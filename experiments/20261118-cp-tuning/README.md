# Spec 027 tuning (seed 354): never a result

## What ran

- **CI run:** 44398201010, from commit 88bb937.
- **Engagements:** 6 + 6 realistic engagements of 6 and 12 hours (`configs/long/cp-tuning.json`).
- **Systems:** `ctl`, `ctl-carry` and `ctl-prior` on every window of both contacts. The
  carried prior used scale 2, tail 600 s and α = 0.001.
- **Joint solve:** 12 pairs of consecutive windows, solved jointly as in spec 025, reported only.
- **Collection:**
  - The run's collect job could not push its results branch: the token may not push a branch
    carrying workflow edits.
  - The 36 artifacts were downloaded and unpacked into `raw/` instead.
  - `long.yml` now pushes an orphan branch (ed6d749).

**Scored with:**

    uv run tma2-long study27 --raw experiments/20261118-cp-tuning/raw \
        --config configs/long/cp-tuning.json --out experiments/20261118-cp-tuning

This writes `study.json`.

    uv run python scripts/research/cp_jointpairs.py > experiments/20261118-cp-tuning/jointpairs.json

This writes `jointpairs.json`.

## Readings (tuning; they set the registered settings and the forecasts)

**Soundness:**
- 144 of 144 windows ran.
- ctl ÷ the true-history fit is 1.58 [1.27, 2.01], per-engagement geometric mean, inside
  [0.8, 4].
- Every system answered 74% of windows. The rest have under 60 bearings: contact 2 beyond
  detection, and gaps.

### ctl ÷ ctl-prior per window

Range error, chains' first windows excluded, engagement bootstrap.

| split | windows (engagements) | geometric mean | interval | median | ×2 better / worse |
|---|---|---|---|---|---|
| weak geometry | 42 (20) | 1.52 | [1.006, 2.45] | 1.18 | 14 / 7 |
| other | 47 (12) | 0.92 | [0.78, 1.11] | 1.01 | 2 / 7 |
| contact 1 | 60 (12) | 1.05 | [0.88, 1.24] | 1.04 | 6 / 7 |
| contact 2 | 29 (12) | 1.43 | [0.84, 2.94] | 1.00 | 10 / 7 |
| contact 1 near a gap | 13 (8) | 1.72 | [1.12, 2.48] | | |

**Course and speed on the weak split:**
- Course: 1.87 [1.42, 2.61].
- Speed: 1.55 [0.85, 3.25].

**The prior's own effect, ctl-carry ÷ ctl-prior:**
- weak: 1.31 [0.93, 2.00];
- other: 0.95.

### Joint solve

Over the 12 pairs, ctl-prior ÷ joint is 1.73 and ctl ÷ joint is 2.13, geometric means of
second-window medians. The joint solve took a median of 1,666 s per pair, against 579 s for one
window of the chain.

### Split size (FR-005)

- **Classified:** 73 weak-geometry windows after the first, from 20 engagements.
  - Contact 2: 60 windows.
  - Contact 1 within 30 min of a gap: 13 windows.
  - Contact 1 with at most one ownship turn: **0**. The ownship turns every 20–40 min, so this
    clause never fires.
- **Scored:** 42 of the 73 had answers on both sides.
- **Scaled to the test:** about 180 weak windows (105 answered) from 50 engagements. That is
  above the 100 from 10 engagements the spec requires, so the definition stands unchanged.

### Guard

- It ran on 87 windows and fell back on 2: a 2.3% rate at α = 0.001.
- D's median is 1.7, its 90th percentile 10.2 and its 99th 23.0.
- Rates at other levels: 11% at 0.05, 5.7% at 0.01, 1.1% at 1e-4.

### Coverage of the carried 95% region

At the tuning settings (scale 2, tail 600):

| contact | hand-overs | coverage | interval |
|---|---|---|---|
| 1 | 60 | 0.87 | [0.73, 0.96] |
| 2 | 39 | 0.82 | [0.72, 0.92] |

Contact-1 coverage over the settings grid, recomputed from the raw covariance:

| scale | tail 0 s | tail 600 s | tail 1200 s |
|---|---|---|---|
| 1 | 0.73 | 0.82 | 0.82 |
| 1.5 | 0.80 | 0.85 | 0.85 |
| 2 | 0.82 | 0.87 | 0.87 |
| 3 | 0.85 | 0.87 | 0.88 |
| 4 | 0.85 | 0.88 | **0.90** |

The recomputation is approximate: the chain itself ran at (2, 600).

## Settings chosen by plan.md's rules

- **Scale and tail:** scale 4 and tail 1200 s. This pair's contact-1 coverage, 0.90, is the
  nearest to 0.95. No pair reaches 0.95: the Laplace covariance stays overconfident even at
  4×. Contact 2 is 0.90 at this setting.
- **Guard level:** α stays 0.001, since the fall-back rate is 2.3%, under 20%.
- **Soundness band:** the coverage band for validation is [0.80, 0.99]. The tuning value is
  0.90, not within 0.03 of an edge, so the band is not widened.

## Caveats

- The settings were chosen on these engagements, and the registered settings were never run
  as a chain here.
- A wider prior (4× rather than 2×) pulls less. The weak-split gain seen here at 2× should
  shrink.
