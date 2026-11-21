# Spec 032 tuning (spent seed 366, legs 2–4 h): costs and readings, nothing decided

## Run and scoring

- **Engagements:** 6 + 6 held-course engagements with ownship legs of 2–4 h, contact 1
  (`configs/long/legs-tuning.json`). Seed 366 was spec 031's test seed; under this config the
  engagements are different.
- **Systems:** (a) `carry2` and (c) `jointheld`, both at 7200/1800 s.
- **CI:** run 44737336041, commit b00280f, AMD EPYC 9V45. 24 jobs took 12.2 runner-hours: (a) 6.9
  and (c) 5.3.
- **Raw outputs:** in `raw/`.

Scored with:

    uv run tma2-long study32 --raw experiments/20261120-legs-tuning/raw \
        --config configs/long/legs-tuning.json --out experiments/20261120-legs-tuning

## Soundness, run as registered for validation

| check | value | |
|---|---|---|
| S1 parts present | 72 of 72 windows ran | pass |
| S2 ctl ÷ true-history fit, per-engagement geometric mean | 1.47 [1.12, 1.96] | pass |
| S3 coverage of the carried 95% region on decided held hand-overs | 0.857 (14 hand-overs), median NEES 2.08 | pass |

## Windows

- **After each chain's first window:** 60, of which 21 are held and 39 have one turn.
- **Held windows:** 16 handed on, 14 decided, from 9 engagements. Two handed-on held windows had
  no `ctl` or `ctl-prior` answer.
- **Yield:** about 1.2 decided held windows per engagement, more on 12-hour engagements (9 from
  6) than on 6-hour ones (5 from 6).
- **Decided held windows:**
  - median range 27.6 km;
  - median detected share 0.66;
  - the guard never fell back.

## Readings (decide nothing)

| reading | range | median | `ctl-prior` better |
|---|---|---|---|
| E1 `ctl` ÷ `ctl-prior` (held) | 1.32 [0.67, 2.37] | 1.32 | 64% |
| E2 joint ÷ `ctl-prior` (held) | 1.65 [0.86, 3.25] | 1.70 | 79% |
| E1 on one-turn windows (harm) | 1.10 [0.61, 1.89] | 1.36 | 62% |

- **Joint solve ÷ 2-hour `ctl`, held:** 1.25 [0.65, 2.54]. The 3.5-hour joint solve is no better
  than the 2-hour window here.
- **`ctl-carry` ÷ `ctl-prior`, held:** 0.98 [0.39, 2.84].
- **Median range error on held windows:**

  | system | median error |
  |---|---|
  | `ctl` | 0.115 |
  | `ctl-prior` | 0.072 |
  | `ctl-carry` | 0.052 |
  | joint | 0.114 |
  | span reference | 0.025 |

- **By detected share** (under 0.75 against 0.75 and up, 10 and 4 windows): E1 1.78 against 0.63;
  E2 1.34 against 2.79.
- **By length** (6 h against 12 h): E1 0.77 against 1.80; E2 2.43 against 1.34.

Fourteen windows decide nothing. Spec 031 showed that tuning readings on about 34 windows can
point the wrong way.

## Cost

| part | per engagement-hour | other |
|---|---|---|
| (a) `carry2` 2-hour | 228 s | |
| (c) `jointheld` | 177 s | 911 s per held window |

## What changed after tuning (before the decision record)

The test was raised from 30 + 30 to 50 + 50 engagements, because tuning yields only about 1.2
decided held windows per engagement. That is about 120 decided windows on the test, and about 100
runner-hours.
