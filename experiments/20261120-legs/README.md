# Spec 032 test (seed 368): E1 "ctl-prior better", E2 not separated, no harm

Test record for spec 032 (`specs/032-long-legs/`). It was scored once, under the decision record
`experiments/20261120-legs-decision/`.

## Run and scoring

- **Engagements:** 50 + 50 held-course engagements with ownship legs of 2–4 h, contact 1
  (`configs/long/legs-test.json`).
- **Systems:** (a) `carry2` and (c) `jointheld`, both at 7200/1800 s.
- **CI:** run 44780652481, commit f93dfab, AMD EPYC 7763. 200 jobs took 80.4 runner-hours: (a)
  48.1 and (c) 32.3.
- **Raw outputs:** in `raw/`. Every part wrote its files, so none was made by hand.

Scored with:

    uv run tma2-long study32 --raw experiments/20261120-legs/raw \
        --config configs/long/legs-test.json --out experiments/20261120-legs

`study.json` records `git_dirty: true` only because this folder was untracked when it was scored.
The tracked tree was at f93dfab.

## Soundness (registered)

| check | value | |
|---|---|---|
| S1 parts present | all 100 engagements; 600 of 600 windows ran | pass |
| S2 ctl ÷ true-history fit, per-engagement geometric mean | 1.46 [1.27, 1.69] | pass |
| S3 coverage of the carried 95% region on decided held hand-overs | 0.906 (85 hand-overs), median NEES 0.94 | pass |

## The registered rule

**Counts:**
- **After each chain's first window:** 500, of which 165 are held and 335 have one turn.
- **Held windows:** 103 handed on.
  - 85 are decided, from 64 engagements.
  - 18 of the handed-on held windows had no `ctl` or `ctl-prior` answer.
  - 62 held windows had no hand-over (contact lost).
- **Decided held windows:**
  - median range 37.0 km;
  - median detected share 0.46;
  - the guard never fell back.

**Readings** (geometric mean [95% interval over engagements]):

| estimand | range | median | `ctl-prior` better | twice as good / twice as bad | course | speed | reading |
|---|---|---|---|---|---|---|---|
| E1 `ctl` ÷ `ctl-prior` (held) | 1.537 [1.156, 2.029] | 1.25 | 59% | 38% / 18% | 1.05 | 1.35 | **ctl-prior better** |
| E2 joint ÷ `ctl-prior` (held) | 1.113 [0.840, 1.445] | 1.24 | 61% | 24% / 19% | 0.94 | 1.03 | **not separated** |
| harm: E1 on one-turn windows | 1.259 [1.056, 1.500] | 1.21 | 60% | 31% / 16% | 1.19 | 1.37 | **no harm** |

The 10% trimmed means are 1.505, 1.158 and 1.283.

**Against the forecasts** (in the decision README):
- **E1:** forecast 1.1–1.5, "better" with probability 0.45. "Better" came out, at 1.54, at the top
  of the range.
- **E2:** forecast 1.0–1.6, "not separated" with probability 0.5. "Not separated" came out.
- **Harm:** forecast "no harm" with probability 0.95. "No harm" came out.

**What this says.** On the standing 2-hour windows, where the ownship holds course through the
whole window, carrying the previous window's state as a prior reduces range error against `ctl`
on the same window: 1.54, median 1.25. The joint solve over the past 3.5 hours does not beat
it, and is not shown to lose to it either.

## Reported, not decided

**Median range error on decided held windows:**

| system | median error |
|---|---|
| `ctl` | 0.167 |
| `ctl-carry` | 0.166 |
| joint | 0.128 |
| `ctl-prior` | 0.104 |
| span reference (told the true history) | 0.033 |

**Other readings on held windows:**
- **`ctl-carry` ÷ `ctl-prior`:** 1.52 [1.13, 1.99]. The carried start alone does nothing; the
  prior does the work.
- **Joint ÷ `ctl`:** 0.724 [0.548, 0.963]. On this seed the joint solve beats the 2-hour window.
  It did not on tuning (1.25) or validation (1.46).
- **E1 by range band:**

  | band | windows | ratio |
  |---|---|---|
  | under 15 km | 3 | 0.54 |
  | 15–25 km | 15 | 0.82 [0.48, 1.41] |
  | 25–35 km | 23 | 1.31 [0.68, 2.41] |
  | over 35 km | 44 | **2.23 [1.53, 3.23]** |

- **E2 by range band:**

  | band | ratio |
  |---|---|
  | under 15 km | 0.31 |
  | 15–25 km | 0.53 [0.22, 1.07] |
  | 25–35 km | 1.58 [1.08, 2.18] |
  | over 35 km | 1.30 [0.95, 1.77] |

- **By detected share:**
  - E1: 1.60 under 0.75 (71 windows) against 1.27 at 0.75 and up (14).
  - E2: 1.16 against 0.90.
- **By length:**
  - E1: 1.55 on 6-hour engagements against 1.53 on 12-hour ones.
  - E2: 0.88 against 1.29.
- **Guard:** fell back on none of the held windows and 0.6% of one-turn windows. One-turn coverage
  is 0.79.

**Cost per engagement-hour:**

| part | cost | other |
|---|---|---|
| (a) `carry2` | 192 s | |
| (c) `jointheld` | 129 s | 705 s per held window |

## What the panel narrowed (round 1; `review.md`)

The panel had three reviewers, each approving with findings. Every decided number was reproduced
independently, and no finding moves a reading.

- **The population is half the held windows.**
  - E1 and E2 are read on 85 of 165 held windows (52%): those where contact was kept and a
    hand-over made.
  - The other 80 are windows with contact lost, at a median of 72 km. There a 2-hour system has
    nothing to fit, and the joint solve extrapolates with a median error of 0.19–0.29.
  - Answered shares of held windows: joint 0.99, `ctl-prior` 0.52, `ctl` 0.52.
  - Counting failures as 100% errors leaves E1 at 1.53.
- **The gain is far-range.**
  - E1 is about 2.2 beyond 35 km (44 windows) and about 1.0 under 35 km (41 windows; 0.82 at
    15–25 km).
  - Range and detected share correlate at −0.85, so they cannot be separated here.
- **E1 is "more data beats no data".**
  - `ctl` sees only the blind window.
  - E2 is the like-for-like comparison against the same past bearings. It is not separated, and
    weighting engagements equally gives 1.02. The compact hand-over is not shown to lose to
    keeping the bearings, and not shown to beat them.
- **The prior comes from an observable window.** In 83 of 85 decided windows the window before
  contains an ownship turn. Chains of blind windows are not tested.
- **Seeds.**
  - E1 was 1.32, 0.87 and 1.54 across the three seeds. Pooled, reported only: 1.37 [1.05, 1.80].
  - Joint ÷ `ctl` was 1.25, 1.46 and 0.72. Pooled it is 0.87 [0.67, 1.11]: the line above, "on this
    seed the joint solve beats the 2-hour window", holds on this seed only.
- **S3 is a gross-fault screen, not calibration.**
  - Carried distances have a median of 0.94 against 3.36 expected, and 6% of them are over 20.
  - One-turn coverage is 0.79: do not quote the carried region as an uncertainty across a turn.
- **"The carried start alone does nothing"** holds on this seed. `ctl-carry` equals `ctl` on 33 of
  85 windows, and on tuning it had the lowest median error.
- **The cost of (a)** covers four systems run together, so it is not `ctl-prior`'s alone.
- **Rows.** Medians are over each system's plausible rows. The joint solve's rows are offset by
  5–25 s from (a)'s in 7 of 165 held windows.
- **Limits:**
  - windows are placed past true manoeuvres;
  - spec 028's hand-over defect is kept;
  - one simulator, contact 1, one realism setting.
