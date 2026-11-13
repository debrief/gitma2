# Gate T (second registration), validation seed 332: T-a passes, the gate proceeds

Run 43252182346 (`timelate/tl-b-val`, commit 21ac02c, clean tree, Intel Xeon Platinum 8573C),
plan `configs/timelate/tl-b.json` (`08793d8b…`), time-late code `88d14eab…`, as bound in
`../20261112-gt2-decision/`. 150 periods a split; 139 (Annex B) and 131 (shift) have determined
rows. Files: `summary.json`, `score.txt`, `*.periods.json`, `plan.json`, `run.json`, `ci.json`;
per-row errors on `results/timelate-tl-b-val-43252182346`.

## The stop rule

**T-a passes: 1.26** against [0.8, 1.3] (forecast 1.10 from tuning; pass at 0.80). The true
history fitted from neutral starts with its times held is at 1.26 times the bound on the
9,120 rows bounded below 0.05, and at 1.16 on the shift split's 5,516. The pass is near the
upper edge of the band. Test seed 331 is launched.

## The other checks, reported on validation only (decided on test)

| Check | Seed 332 | Forecast | Would it pass? |
| --- | --- | --- | --- |
| T-b C″ ÷ search, above 1.10 | 2.41 [1.65, 3.02] | about 2.4 | yes |
| T-c the same under the shifted prior, above 1.00 | **1.26 [0.89, 1.84]** | about 1.7 | **no** |
| T-d true history in the first three (≥ 0.60); calibration gap (≤ 0.10) | 0.62; +0.06 | 0.73; ±0.07 | yes, narrowly |
| T-d-shift calibration gap (≤ 0.10) | +0.32 | +0.30; fail | no, as forecast |
| T-e search ÷ reference with the prior, above 1.10 | 1.41 [1.19, 1.97] | about 1.5 | material |

T-c is the one that moved: 1.70 [1.24, 2.27] on spent seed 330, 1.26 [0.89, 1.84] here. On
150 periods the shifted-prior ratio is not stable enough to call; the test seed has 300.

## Every system (median over periods of the period's median relative range error)

| System | Annex B | Over 10% | Shift | Over 10% |
| --- | --- | --- | --- | --- |
| C″ read as a track | 0.099 | 0.50 | 0.117 | 0.53 |
| **Search (best history)** | **0.041** | 0.27 | **0.093** | 0.47 |
| Search from C″'s transitions | 0.051 | 0.32 | 0.095 | 0.49 |
| Search from nothing | 0.057 | 0.35 | 0.105 | 0.53 |
| One leg | 0.353 | 0.80 | 0.301 | 0.84 |
| IMM, EKF as tracks | no state on over half the rows of the median period | 0.97, 0.96 | likewise | 0.99, 0.98 |
| Reference, times held | 0.024 | 0.17 | 0.031 | 0.19 |
| Reference, times free | 0.029 | 0.22 | 0.037 | 0.19 |
| Reference, times free, with the prior | 0.029 | 0.20 | 0.040 | 0.20 |
| Truth-started fit (reported; not a reference) | 0.019 | 0.13 | 0.010 | 0.05 |

## By how tightly the row is bounded (range efficiency; Annex B split, then shift)

| System | below 0.05 | 0.05 to 0.2 | 0.2 to 0.5 | | below 0.05 | 0.05 to 0.2 | 0.2 to 0.5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rows | 9,120 | 4,182 | 490 | | 5,516 | 6,899 | 702 |
| Reference, times held | 1.26 | 0.96 | 1.64 | | 1.16 | 1.00 | 0.88 |
| Reference, times free | 1.31 | 1.32 | 3.30 | | 1.33 | 1.02 | 0.79 |
| Truth-started fit | 0.89 | 0.65 | 0.57 | | 0.60 | 0.16 | 0.07 |
| Search | 2.10 | 1.58 | 0.90 | | 2.73 | 2.22 | 1.70 |
| C″ | 5.64 | 2.88 | 1.62 | | 4.35 | 3.18 | 2.03 |

- The neutral-start reference is near 1 in the middle band here (0.96, 1.00), where the
  tuning seed showed 0.45. The sub-bound figure the decision record listed as not understood
  did not repeat on 2.5 times the periods; it looks like 60 periods' noise, not a property.
- The truth-started fit is below the bound in every band on both splits, as diagnosed.
- The search is at about twice the bound on tightly bounded rows and near it on loosely
  bounded ones, where its prior does the work the bearings cannot.

## Candidates (temperature 3)

Annex B: first candidate is the true history in 0.45 of periods, stated 0.51; by stated
probability (below 0.4, 0.4 to 0.6, 0.6 to 0.8, above 0.8): stated 0.34 / 0.49 / 0.68 / 0.88,
right 0.33 / 0.34 / 0.69 / 0.88 (49, 58, 35, 8 periods). Shift: right in 0.20, stated 0.52;
by bin right 0.17 / 0.10 / 0.32 / 0.62.

## Cautions before the test seed

- T-a passed with little room; the test seed does not re-apply it, but reports it.
- T-c may well fail on test. Its registered consequence then applies: the search's standing
  is conditional on the manoeuvre statistics being known.
- T-d sits just above its line (0.62 against 0.60).
