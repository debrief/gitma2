# Spec 029 tuning (seed 362): never a result

## Run and scoring

- **Engagements:** 6 + 6 realistic engagements with the ownship holding each leg for 1–2 h
  (`configs/long/hold-tuning.json`).
- **What ran:** contact 1, 1-hour windows overlapping 15 min. `ctl`, `ctl-carry` and
  `ctl-prior` ran at spec 028's registered settings (scale 4, tail 1,200 s, α 0.001).
- **CI:** run 44534116364, commit c33ca1e, AMD EPYC 9V45. 12 jobs took 4.1 runner-hours.
- **Raw outputs:** in `raw/`, from the run's orphan results branch.

Scored with:

    uv run tma2-long study29 --raw experiments/20261119-hold-tuning/raw \
        --config configs/long/hold-tuning.json --out experiments/20261119-hold-tuning

## Readings (tuning; they set the forecasts and confirm the settings)

**Soundness:**
- 144 of 144 windows ran.
- ctl ÷ the true-history fit is 1.35 [1.10, 1.74].
- Held-window coverage is 0.89.

**Classes** (chains' first windows excluded):

| class | windows | handed on | scored (both answered) | engagements |
|---|---|---|---|---|
| held (no ownship turn) | 40 | 28 | 26 | 12 |
| one turn | 92 | 70 | 66 | 12 |
| more | 0 | | | |

The "more" class is empty: with 1-hour windows and legs of at least an hour, a window holds at
most one turn. The harm check on "more" is therefore vacuous. Here 71% of windows are answered by both systems.

*Corrected after the panel:* this sentence first said "as in validation and test". That could
not have been known when it was written, and it was false: the test answered 0.80.

**ctl ÷ ctl-prior** (geometric mean, engagement interval, median, share better):

| class | range | course | speed |
|---|---|---|---|
| held | 2.10 [1.17, 3.77], median 1.43, 65% better | 1.71 [1.02, 2.96] | 1.98 [1.15, 3.51] |
| one turn | 1.54 [1.16, 1.97], median 1.19, 59% better | 1.62 [1.25, 2.14] | 1.33 [0.88, 1.91] |

**Median range error per window:**

| | ctl | ctl-carry | ctl-prior | true-history fit | C″ |
|---|---|---|---|---|---|
| held | 0.358 | 0.282 | **0.108** | 0.117 | 0.999 |
| one turn | 0.093 | 0.083 | 0.057 | 0.059 | 0.196 |

**Other readings:**
- **The prior's own effect** (ctl-carry ÷ ctl-prior): held 2.04 [1.22, 3.63]. ctl ÷ ctl-carry
  is 1.03 on held windows, so the carried start alone does nothing.
- **Guard:** it fell back on 1 of 92 windows.
- **Coverage of the carried 95% region:** held 0.89 [0.71, 1.00] over 28 hand-overs; one turn
  0.83.

## Settings (plan's rule)

Held-window coverage of 0.89 lies within [0.85, 0.99], so spec 028's settings stay unchanged
(`configs/long/carry2.json`).

## Caveats

- Twelve engagements gave 26 scored held windows.
- Spec 028's tuning direction did not replicate: tuning gave 1.52, the test 1.105.
- Here the effect is large against its interval, and it matches the mechanism: a window with no
  ownship turn leaves range open, and the prior closes it.
