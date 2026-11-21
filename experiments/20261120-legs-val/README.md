# Spec 032 validation (seed 367): soundness passed

## Run and scoring

- **Engagements:** 10 + 10 held-course engagements with ownship legs of 2–4 h, contact 1
  (`configs/long/legs-val.json`).
- **Systems:** (a) `carry2` and (c) `jointheld`, both at 7200/1800 s.
- **CI:** run 44751557791, commit c105162, AMD EPYC 7763. 40 jobs took 19.4 runner-hours: (a)
  10.9 and (c) 8.5. The jobs waited about 30 minutes for runners.
- **Raw outputs:** in `raw/`.

Scored with:

    uv run tma2-long study32 --raw experiments/20261120-legs-val/raw \
        --config configs/long/legs-val.json --out experiments/20261120-legs-val

## Soundness (registered)

| check | value | |
|---|---|---|
| S1 parts present | all 20 engagements; 120 of 120 windows ran | pass |
| S2 ctl ÷ true-history fit, per-engagement geometric mean | 1.73 [1.33, 2.27] | pass |
| S3 coverage of the carried 95% region on decided held hand-overs | 0.95 (20 hand-overs), median NEES 0.84 | pass |

The test (seed 368, 50 + 50 engagements) goes ahead.

## Reported, not decided

**Windows:**
- **After each chain's first window:** 100, of which 30 are held and 70 have one turn.
- **Held windows:** 23 handed on, 20 decided, from 14 engagements. Three handed-on held windows
  had no `ctl` or `ctl-prior` answer.
- **Decided held windows:**
  - median range 29.7 km;
  - detected share 0.66;
  - the guard never fell back.

**Readings:**

| reading | range | median | `ctl-prior` better |
|---|---|---|---|
| E1 `ctl` ÷ `ctl-prior` (held) | 0.87 [0.37, 2.09] | 0.92 | 50% |
| E2 joint ÷ `ctl-prior` (held) | 1.27 [0.73, 2.24] | 1.51 | 60% |
| E1 on one-turn windows (harm) | 1.79 [1.11, 2.87] | 1.70 | 64% |

- **E1 has turned round from tuning,** 1.32 then 0.87. E2 leans to the prior on both seeds.
- **On one-turn windows the prior helps clearly.** That is the harm check, which is far from
  harm.
- **Joint ÷ `ctl`, held:** 1.46 [0.74, 2.62]. As on tuning, the 3.5-hour joint solve is no
  better than the 2-hour window.
- **Median range error on held windows:**

  | system | median error |
  |---|---|
  | `ctl` | 0.083 |
  | `ctl-prior` | 0.063 |
  | `ctl-carry` | 0.088 |
  | joint | 0.083 |
  | span reference | 0.018 |

**Cost per engagement-hour:**

| part | cost | other |
|---|---|---|
| (a) | 219 s | |
| (c) | 170 s | 1,018 s per held window |

Validation is one seed of 20 engagements. The registered rule is read on the test seed only.
