# Spec 029 validation (seed 363): soundness passed

## Run and scoring

- **Engagements:** 10 + 10 engagements with the ownship holding course 1–2 h
  (`configs/long/hold-val.json`).
- **Systems:** contact 1, 1-hour windows overlapping 15 min, at the registered settings.
- **CI:** run 44557882869, commit defd850, AMD EPYC 7763. 20 jobs took 7.3 runner-hours.
- **Raw outputs:** in `raw/`.

Scored with:

    uv run tma2-long study29 --raw experiments/20261119-hold-val/raw \
        --config configs/long/hold-val.json --out experiments/20261119-hold-val

## Soundness (registered)

| check | value | band | |
|---|---|---|---|
| S1 windows ran | 240 of 240, no engagement missing | ≥ 95% | pass |
| S2 ctl ÷ true-history fit (per-engagement geometric mean) | 1.58 [1.26, 2.02] | [0.8, 4] | pass |
| S3 held-window coverage of the carried 95% region | 0.95 [0.90, 1.00] (60 hand-overs) | [0.80, 0.99] | pass |

The test (seed 364) goes ahead.

## Reported, not decided

### Classes

| class | windows | handed on | scored |
|---|---|---|---|
| held | 69 | 60 | 59 |
| one turn | 151 | 134 | 124 |

The "more" class is empty.

### ctl ÷ ctl-prior

| class | range | course | speed |
|---|---|---|---|
| held | 1.91 [1.34, 2.80], median 1.33 | 1.65 [1.17, 2.40] | 1.90 [1.31, 2.90] |
| one turn | 1.21 [0.96, 1.54], median 1.07 | 1.08 [0.79, 1.51] | 1.23 [0.88, 1.65] |

### Median range error per window

| | ctl | ctl-carry | ctl-prior | true-history fit | C″ |
|---|---|---|---|---|---|
| held | 0.153 | 0.160 | **0.066** | 0.092 | 0.882 |
| one turn | 0.113 | 0.100 | 0.091 | 0.058 | 0.240 |

### Other readings

- **The prior's own effect** (ctl-carry ÷ ctl-prior): held 1.69 [1.23, 2.46]; one turn 1.14.
- **Guard:** it fell back on 2 of 184 windows.
- **Answered:** 0.86.
- **Coverage on one-turn windows:** 0.90.

Validation is one seed of 20 engagements. The registered rule is read on the test seed only.
