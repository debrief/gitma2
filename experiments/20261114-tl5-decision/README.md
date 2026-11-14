# Spec 017: decision record (2026-11-14)

Written after the tuning run on seed 342 (`experiments/20261114-tl5-tuning/`) and **before
seeds 343 and 344 exist**. `decision.json` binds the plan (`configs/timelate/tl-f.json`,
`0b29a95d…`), the run files, the ranges, the time-late code (`b32247f8…`; the control's
modules are study L's, `e5040f5e…`) and the scoring files by SHA-256. Owner decision:
2026-11-14, option A. SRD §9 lines proposed (the owner merges).

## What is measured

On targets that manoeuvre more often and less sharply than Annex B says, study L's
control is about twice a fit told the true history. This study asks what that gap is made
of.

- **Detectability** of each true manoeuvre: the χ² its omission adds to the fit of the
  true history, the other manoeuvres' times held. Bearings only: no prior, no search.
- **References told only the detectable manoeuvres** (`ref-d10`, `ref-d20`, `ref-d40`),
  built exactly as the full reference (`ref-full`, times held).
- **The control's search given the targets' own statistics** (`true`).
- Beside: the tuned IMM and EKF read as tracks; under outliers, references fitted to the
  edited bearings.

## No decision rule

The plan's rule (the attainable share at threshold 20 against a half) is not registered.
On tuning data that share is 0.32 [-0.08, 0.56], and 0.66 or below zero at thresholds 10
and 40: at the test's size its interval would still reach about a half, and the threshold
would decide it. Spec 015's panel: do not register as a decision a line you forecast as a
coin's toss. Registered instead:

| | Estimand (shifted split; thresholds 10, 20, 40) | Tuning value |
| --- | --- | --- |
| E1 | Share of whole true manoeuvres under the threshold | 0.24 / 0.33 / 0.47 |
| E2 | The control's miss rate by detectability band | 0.97 under 5 to 0.12 above 100; half-way between 20 and 40 |
| E3 | `ref-dT` ÷ `ref-full`: the cost of not being told the undetectable ones | 1.27 / 1.62 / 2.18 |
| E4 | Control ÷ `ref-dT`: what remains for a perfect detector (an upper limit) | 1.59 / 1.25 / 0.93 |
| E5 | Control ÷ the true-prior search | 1.02 |

## The recommendation's logic, fixed now

A proposer study (study L's trained models inside the search) is recommended to the owner
only if, on the test seed's shifted split, **E4 at threshold 20 has a lower limit above
1.10 and the control misses more than a third of the manoeuvres above 40**. Otherwise the
recommendation is to write the time-late track up and name what would add information.
The owner decides either way.

Forecast, restating the tuning run and not an independent prediction: no proposer study.
E4's lower limit at 20 was 0.96 on tuning, and the control missed 0.18 of the manoeuvres
above 40.

## Order

Validation on seed 343 (soundness on Annex B data; a failure stops the study), then the
test on seed 344, once.

## Known limits

In `decision.json`: held times flatter the references (E4 an upper limit, E3 a lower limit
on identifiability); close manoeuvres can hide each other; the thresholds are tied to the
evidence's price under Annex B's prior; the control carries study L's recorded limits.
