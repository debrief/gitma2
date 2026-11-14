# Spec 017: the shifted-prior gap on test seed 344 (2026-11-14)

CI run 43618868241 (`timelate/tl-f-test`, commit 6c1f3f9, clean tree, plan
`configs/timelate/tl-f.json` `0b29a95d…` as registered; scored once). 1,150 periods, 1,044
scored. Every table is in `tables.md` (generated from `summary.json` by
`scripts/research/tl5_tables.py`) and `supplement.md` (`tl5_supplement.py`); the figures
below are copied from them. Per-row errors: results branch
`results/timelate-tl-f-test-43618868241`. `tracks.npz` (`tl5_tracks.py`) holds the first
20 shifted periods' tracks for the slides.

**Decided by the panel, round 1 (`review.md`): five approve with findings.** Every number
below reproduces and the logic's output stands, but the panel changed what it means; read
"After the panel" at the end before quoting anything from the sections above it. Sentences
the panel found wrong are struck through there, not silently edited here.

A registered study, not a gate: no pass or fail. The decision record
(`experiments/20261114-tl5-decision/`) fixed five estimands and the logic of the
recommendation before seeds 343 and 344 existed.

## Soundness

The true history with its times held is at 1.11 of the bound on tight rows (band 0.8 to
1.3); every Annex B true-history fit converged; 0.09 of Annex B references are held (limit
0.25; 0.22 on the shifted split).

## The estimands, shifted split (500 periods, 451 scored, 1,475 whole true manoeuvres)

| | Estimand | Threshold 10 | Threshold 20 | Threshold 40 | Tuning seed 342 |
| --- | --- | --- | --- | --- | --- |
| E1 | Share of true manoeuvres under the threshold | 0.28 [0.26, 0.31] | 0.37 [0.34, 0.39] | 0.47 [0.44, 0.50] | 0.24 / 0.33 / 0.47 |
| E3 | `ref-dT` ÷ `ref-full` | 1.34 [1.24, 1.45] | 1.58 [1.45, 1.73] | 2.02 [1.81, 2.24] | 1.27 / 1.62 / 2.18 |
| E4 | Control ÷ `ref-dT` | 1.70 [1.52, 1.90] | 1.43 [1.28, 1.61] | 1.12 [0.99, 1.27] | 1.59 / 1.25 / 0.93 |
| | Attainable share of the control's gap | 0.65 [0.55, 0.74] | 0.44 [0.33, 0.54] | 0.14 [-0.01, 0.27] | 0.66 / 0.32 / -0.11 |

- **E2**, the control's miss rate by detectability band: 0.96 under 5, 0.79 from 5 to 10,
  0.55 from 10 to 20, 0.36 from 20 to 40, 0.30 from 40 to 100, 0.13 above 100 (tuning:
  0.97, 0.86, 0.65, 0.48, 0.31, 0.12). Its half-way point is between 10 and 40.
- **E5**, control ÷ the search under the targets' own prior: **1.17 [1.06, 1.29]**
  (tuning: 1.02 [0.86, 1.22]). The tuning reading "knowing the true statistics does not
  improve the track" does not hold on the test seed. The median per-period ratio is 1.02:
  the gain is in a minority of periods (the control over twice as bad in 0.21, the
  true-prior search in 0.13).
- The whole gap, control ÷ `ref-full`: 2.27 [2.04, 2.55], median per-period ratio 2.18.

## What it shows

**More than a third of the shifted targets' manoeuvres can barely be seen.** 0.37 add
less than 20 to the χ² of the true history's fit when left out (Annex B: 0.16; shifted 2:
0.08). The control misses 0.83 of those and 0.18 of the ones above 40.

**The gap is part identifiability and part attainable, and the division depends on where
"detectable" is drawn.** At threshold 20, not being told the undetectable manoeuvres costs
a factor 1.58, and the control is a further 1.43 [1.28, 1.61] from that reference:
attainable share 0.44 [0.33, 0.54]. At 10 the share is 0.65; at 40 it is 0.14 and the
control is not separated from the reference (1.12 [0.99, 1.27]). The plan's rule reads
"mixed" on the shifted split, on Annex B (0.50 [0.29, 0.68]) and under outliers with
edited references (0.68 [0.46, 0.86]); "mostly attainable" on shifted 2 (0.91).

**The tuning forecast was wrong in two places.** E4 at 20 is separated from 1 (the tuning
interval reached 0.96), and E5 is 1.17, not 1.02. Both say more is attainable than the
tuning seed's 134 periods suggested: a prior that matched the targets would close about a
fifth of the control's gap to the full reference (log 1.17 over log 2.27 = 0.19), and
would miss 0.12 of the manoeuvres above 40 against the control's 0.18, at the price of
more false ones (0.48 a period against 0.34).

**The control's gap on Annex B data is of the same kind.** Control ÷ `ref-full` is 1.58
[1.36, 1.85] there, with 0.16 of manoeuvres under 20 and the same miss curve by band.

**The filters are far behind as tracks.** IMM ÷ control 4.8 (shifted) to 16 (shifted 2);
EKF 5.6 to 22. Read as whole-period tracks they are causal filters, not smoothers.

## The recommendation, by the logic fixed in the decision record

A proposer study is recommended only if E4 at threshold 20 has a lower limit above 1.10
**and** the control misses more than a third of the manoeuvres above 40.

- E4 at 20: 1.43 [1.28, 1.61]. Lower limit above 1.10: **yes** (forecast: no).
- The control misses 0.18 of the 782 manoeuvres above 40. More than a third: **no**.

**Outcome of the logic: a proposer study is not recommended.** The recommendation is to
write the time-late track up and name what would add information. The first condition
held against the forecast, so this is "no" on one condition of two, not on both; the
owner decides.

## Limits

- Times held flatter every reference: E4 is an upper limit on what a perfect detector
  could gain, E3 a lower limit on identifiability. 0.22 of shifted references drift when
  their times are free.
- Detectability is computed with the other manoeuvres' times held; close manoeuvres can
  hide each other, and the measure is not additive.
- Thresholds 10, 20 and 40 bracket the evidence's price for a manoeuvre under Annex B's
  prior (about 22); under the targets' own prior the price is lower, and the true-prior
  search finds 0.44 of manoeuvres between 5 and 10.
- Under outliers the references fitted to unedited bearings are no yardstick (control ÷
  `ref-full` 1.06; ÷ `ref-full-edit` 1.69): read the edited rows only. Only 0.04 of
  outlier-split true-history fits converged on the unedited bearings.
- Period medians of relative range error; course and speed are in `tables.md`
  (efficiency) and not in the estimands.
- One test seed; the tuning seed differed from it by more than its intervals on E4 and E5.

## Not delivered

- A proposer, a prior-mismatch diagnostic, a prior fitted to the period: named, not built.
- Detectability with times free, or jointly over pairs of manoeuvres.
- A smoothed IMM (the filters are scored as they are).
- Unit tests for `run4`/`study4` beyond those added in this spec's `test_timelate5.py`.

## After the panel (round 1, 2026-11-14)

Corrections to this record; the evidence is in `review.md`.

- **"Part identifiability and part attainable" is two kinds of period.** Where a manoeuvre
  is under 20 (336 periods) the control is 1.16 [1.04, 1.30] times the reference not told
  it; where none is (115 periods) it is 2.65 times the full reference. The attainable part
  is the under-a-third of periods where the control misses a manoeuvre the bearings show
  (E4 2.73 there, 1.09 elsewhere). The share at 20 is 0.70 in the tight third of periods
  by bound and 0.20 in the loose third.
- **E4 is not an upper limit and E3 is not a lower limit.** The references are flattered
  by held true times (the control is 1.6 to 1.7 times `ref-full` even with the right
  history) and handicapped by hard omission (the control beats `ref-d20` in 37% of
  periods); detectability is not additive (jointly omitted "undetectable" manoeuvres cost
  20 or more in 44% of 39 periods checked).
- **The recommendation is the rule's output, not the evidence's.** The second condition
  counts manoeuvres at a 120 s match (0.18; 0.30 at 60 s, 0.11 at 240 s), while the cost
  sits in the 100 periods with a miss above 40 (E4 3.08, 69% of the log sum).
- **Wrong as written:** "the tuning seed differed from it by more than its intervals" (the
  test's values lie inside the tuning intervals; about 1 standard error); "IMM ÷ control
  4.8 to 16; EKF 5.6 to 22" (on 40% of periods; on common rows 3.75 to 10.5 and 4.1 to
  9.6); "the same miss curve by band" on Annex B (below 40 only); "half-way point between
  10 and 40" (near 20); shifted 2 "mostly attainable" (one clipped reference, 19
  manoeuvres).
- **Added:** of the 138 missed manoeuvres above 40 the true-prior search finds 66; E5 is
  2.58 where it finds more and 1.07 elsewhere. The attainable part looks at least half a
  prior problem.
- **Not delivered, added:** the split under each way of fitting the reference; course and
  speed in the estimands (attainable share 0.55 and 0.48 by the panel's recomputation);
  a joint detectability; unit tests for `detect.py` and `run5.py`; period counts in the
  paired tables.
