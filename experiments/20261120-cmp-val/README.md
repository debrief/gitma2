# Spec 030 validation (seed 365): soundness passed

## Run and scoring

- **Engagements:** 10 + 10 held-course engagements, contact 1 (`configs/long/cmp-val.json`).
- **Systems:** (a) 1-hour `carry2`, (b) 2-hour `carry2`, (c) `jointheld`.
- **CI:** run 44651625871, commit 2ead984, AMD EPYC 9V74. 60 jobs took 23.1 runner-hours: (a)
  6.5, (b) 12.5, (c) 4.1.
- **Raw outputs:** in `raw/`.

Scored with:

    uv run tma2-long study30 --raw experiments/20261120-cmp-val/raw \
        --config configs/long/cmp-val.json --out experiments/20261120-cmp-val

## Soundness (registered)

| check | value | |
|---|---|---|
| S1 parts present | (a), (b), (c) for all 20 engagements; 240 of 240 windows ran | pass |
| S2 1-hour ctl ÷ true-history fit (per-engagement geometric mean) | 1.32 [0.96, 2.05] | pass |
| S3 held-window coverage of the carried 95% region | 0.91 (55 hand-overs) | pass |

The test (seed 366) goes ahead.

## Reported, not decided

**Held windows:** 72 in all, 55 handed on, 51 decided.

**The three estimands** (held windows, range; the system named ÷ 1-hour `ctl-prior`):

| estimand | ratio | median | course | speed |
|---|---|---|---|---|
| D1: 2-hour `ctl` | 0.75 [0.49, 1.19] | 0.74 | 0.70 | 0.75 |
| D2: joint solve | 0.84 [0.58, 1.25] | 0.91 | 0.73 | 0.71 |
| D3: 2-hour `ctl-prior` | 0.70 [0.48, 1.12] | 0.89 | 0.72 [0.52, 0.99] | 0.76 |

None is separated. On validation all three lean towards the longer windows. Tuning leant the other
way for D1 (1.30) and D2 (1.28), and the same way for D3 (0.57).

**Median range error on held windows:**

| system | median error |
|---|---|
| 1-hour `ctl` | 0.222 |
| 1-hour `ctl-prior` | 0.115 |
| 2-hour `ctl` | 0.065 |
| 2-hour `ctl-prior` | 0.076 |
| joint solve | 0.074 |
| span reference | 0.028 |

**Other readings:**
- **Spec 029 replicated:** 1-hour ctl ÷ ctl-prior is 1.74 [1.20, 2.49].
- **One-turn windows, D1:** 0.78 [0.59, 1.00].
- **Cost per window:** (a) 98 s, (b) 376 s per 2-hour window, (c) 207 s per held window.

Validation is one seed of 20 engagements. The registered rule is read on the test seed only.
