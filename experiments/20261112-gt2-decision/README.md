# Gate T decision record, second registration (spec 013)

Owner decision 2026-11-12: after the first registration (`../20261112-gt-decision/`) stopped at
validation on seed 330 (`../20261112-gt-val/`: T-a 0.67, because the reference fit started at
the truth), re-register with a sound reference and run again. This record supersedes the
first. `decision.json` is committed before validation seed 332 or test seed 331 is generated.
It binds the plan `configs/timelate/tl-b.json` (`08793d8b…`), the two run configurations, the
ranges files, the time-late code (the digest in `decision.json`, written by `tma2-tlsolve`
into every shard) and the frozen C (`4d2c084f…`). Nothing bound here is edited after this.

**Launch:** the workflow's smoke run on the tuning seed passed at b3b2903 (run 43249491892, four
periods a split: a check that the tools run, not a measurement). Every digest in
`decision.json` was re-checked against the files and is unchanged. Validation seed 332 is
launched from the commit that adds this paragraph.

## What changed from the first registration, and nothing else

| | First | Second |
| --- | --- | --- |
| Reference | true history fitted from the true state | true history's structure only (when, how long, which changes), fitted from four neutral starts on the first bearing, lowest cost kept (`run.history_reference`) |
| T-a reads | that fit, all determined rows | the reference **with its times held** (what the known-history bound assumes), on rows whose bound on relative range is below 0.05 |
| T-e compares the search with | the truth-started fit with the prior | the neutral-start reference fitted with the prior, times free |
| Candidates | Annex B split only | plus **T-d-shift**: the calibration gap on the shifted split |
| Validation seed | 330 (spent) | 332 |

Unchanged: the search and its settings, C″, the splits and their ranges files, the scoring
(rows 30 s apart, bound below 0.5, period medians, 95% period bootstrap), the match rule, the
temperature (3), every threshold, and test seed 331 (never generated).

## Criteria (`decision.json`)

- **T-a** (soundness): range efficiency of the times-held reference within [0.8, 1.3] on rows
  with the bound below 0.05, Annex B split.
- **T-b** (the verdict): C″ ÷ search, interval wholly above 1.10.
- **T-c** (the prior's reach): the same on the shift split, interval wholly above 1.00.
- **T-d** (the candidates): true history among the first three in at least 0.60 of periods,
  and the first candidate's mean stated probability within 0.10 of how often it is the true
  history.
- **T-d-shift**: that gap within 0.10 on the shift split.
- **T-e** (headroom, a reading): search ÷ reference with the prior; material if the interval
  is wholly above 1.10.
- **Validation rule:** T-a on seed 332 stops the gate before seed 331 is generated. The
  others are reported on validation and decided on test.
- **The panel decides.**

## Forecasts

From tuning seed 329 (60 fresh periods, `tma2-tlsolve` at this commit) and, where marked,
from spent seed 330:

| Check | Forecast | Probability |
| --- | --- | --- |
| T-a | 1.10 on tuning; pass | 0.80 |
| T-b | about 2.4 (2.29 tuning, 2.56 on seed 330); pass | 0.92 |
| T-c | about 1.7 (seed 330); pass | 0.85 |
| T-d | in the first three about 0.73; gap about ±0.07; pass | 0.60 |
| T-d-shift | gap about +0.30 (seed 330); **fail** | 0.90 |
| T-e | about 1.5 (tuning: 1.52 [0.96, 2.34] on 56 periods); material | 0.65 |

## What is already known, disclosed

- **Seed 330 has shown T-b, T-c, T-d and the shift calibration.** The thresholds were not
  changed after seeing them, and they are decided on seed 331, which is untouched. T-d-shift
  is registered expecting it to fail: it is there so that the failure is a gate result with a
  stated consequence, not a footnote.
- **The reference, on tuning data.** From neutral starts it reaches the truth-started fit's
  cost within 1 in 46 of 60 periods and is lower in 10: it is not stuck. With its times
  held it is at 1.10 on tightly bounded rows; with times free at 1.43, because the bound
  assumes the times are known and two unknowns a manoeuvre are not free.

## Known weaknesses, stated before the result

- **Rows bounded between 0.05 and 0.2 are not understood.** There the times-held reference
  is at 0.45 from neutral starts (0.27 from the truth). A sub-bound efficiency from a fit
  that was not handed the truth says the neutral start (8 km, 5 m/s) is itself a mild prior
  on weakly determined rows, or the bound is loose there, or both. T-a avoids those rows; the
  headline ratios do not (the owner chose to keep the 0.5 limit). Every system is reported
  by band so the reader can see how much of each figure comes from them.
- **C″ is a weak opponent for this task**; the prior is the simulator's own; the reference
  with the prior is biased; the temperature comes from one seed; "found within 2 minutes" is
  loose; the evidence is Laplace's approximation; no naive estimator; IMM and EKF not
  re-tuned and silent before the ownship's first turn; σ = 1° only. All as in the first
  record.
- **The first registration's failure is part of this gate's history.** A reader should
  weigh a gate whose reference had to be rebuilt once accordingly.
