# Spec 016: the classical controls on tuning seed 338 (2026-11-13)

CI run 43467937439 (`timelate/tl-e-tune`, commit 9156bd7, draft plan
`configs/timelate/tl-e-draft.json`). **Tuning data: nothing here is a registered result.**
Every table is in `tables.md`, generated from `summary.json` by
`scripts/research/tl4_tables.py`; the figures below are copied from it. Per-row errors are
on the results branch `results/timelate-tl-e-tune-43467937439`. Ratios are paired per
period (geometric mean, 95% period bootstrap); above 1 means the system named second is
better.

## What the controls do

| Split (scored periods) | Standing search | Combined control `ctl` | Search ÷ `ctl` | Share of the gap to the reference closed | `ctl` ÷ reference |
| --- | --- | --- | --- | --- | --- |
| Annex B (142) | 0.034 | 0.031 | 1.06 [1.00, 1.14] | 0.32 [−0.34, 1.72] | 1.14 [0.94, 1.38] |
| Shifted (90) | 0.083 | 0.071 | 1.04 [0.99, 1.11] | 0.06 [−0.01, 0.15] | 2.05 [1.63, 2.58] |
| Shifted 2 (92) | 0.031 | 0.027 | 1.17 [1.03, 1.35] | 0.36 [0.08, 0.86] | 1.33 [1.03, 1.68] |
| Held course (138) | 0.025 | 0.025 | 1.04 [0.94, 1.14] | 0.09 [−0.19, 0.30] | 1.43 [1.24, 1.67] |
| Correlated, mild (55) | 0.122 | 0.062 | 1.58 [1.25, 2.08] | 0.58 [0.27, 1.06] | 1.38 [0.98, 2.00] |
| Correlated (74) | 0.124 | 0.095 | 1.34 [1.08, 1.67] | 0.53 [0.15, 0.99] | 1.30 [1.00, 1.72] |
| Outliers (74) | 0.067 | 0.034 | 1.57 [1.20, 2.09] | 0.75 [0.34, 1.36] | 1.17 [0.85, 1.59] |
| Outliers, harsh (55) | 0.099 | 0.041 | 2.92 [1.99, 4.27] | 1.24 [0.82, 1.85] | 0.81 [0.57, 1.18] |
| Bias (55) | 0.065 | 0.064 | 1.00 [0.89, 1.13] | 0.00 [−1.14, 1.29] | 1.32 [0.86, 1.87] |

- **Outliers**: editing wild bearings removes the gap (the control is at the reference).
- **Correlated errors**: an effective sd from the estimated correlation closes about half
  the gap; false manoeuvres fall from 1.50 a period to 0.47. The estimate reads a
  correlated share of 0.52 where the truth is 0.5, and 0.00 on every other split; `ctl`
  used it in every correlated period and in 3 to 5% of the others.
- **A shifted prior**: the broadened prior closes almost nothing on the first shifted split
  (0.06) and a third on the second. Half the manoeuvres are still missed on the first
  (0.54), with or without it. **This is the gap no classical control here addresses.**
- **Bias**: nothing addresses it, as intended.
- **Cost on Annex B data**: none (1.06 the right way).
- Soundness as validation will read it: reference efficiency 1.13 on tight rows, every
  reference converged, 0.11 held. Passes.

## Hedging

The hedged track over `ctl`'s candidates, search ÷ hedged:

| Temperature | Annex B | Shifted | Shifted 2 | Held course | Correlated | Outliers |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.08 [0.98, 1.20] | 1.09 [1.02, 1.17] | 1.11 [0.98, 1.27] | 1.03 [0.90, 1.18] | 1.40 [1.14, 1.72] | 1.72 [1.26, 2.39] |
| 3 | 0.94 [0.82, 1.09] | 1.16 [1.03, 1.32] | 1.05 [0.88, 1.24] | 0.99 [0.85, 1.15] | 1.55 [1.23, 1.97] | 1.48 [1.12, 1.98] |
| 5 | 0.86 [0.74, 1.00] | 1.15 [1.01, 1.33] | 0.99 [0.82, 1.18] | 0.95 [0.81, 1.10] | 1.52 [1.21, 1.90] | 1.36 [1.03, 1.78] |

Hedging helps where the history is uncertain (shifted prior, correlated errors) and costs
where it is not, more so at higher temperatures. Temperature 1 is the only one that loses
nowhere.

## Declaration

Held-course periods given a manoeuvre (149), and Annex B targets with one manoeuvre called
quiet (68), for `ctl`:

| Margin | Quiet probability 0 | 0.01 | 0.1 |
| --- | --- | --- | --- |
| 0 | 0.41 / 0.09 | 0.13 / 0.09 | 0.08 / 0.10 |
| 1 | 0.30 / 0.10 | 0.07 / 0.10 | 0.03 / 0.13 |
| 2 | 0.20 / 0.12 | 0.02 / 0.12 | 0.01 / 0.16 |
| 3 | 0.17 / 0.15 | 0.01 / 0.15 | 0.01 / 0.18 |
| 5 | 0.09 / 0.19 | 0.01 / 0.19 | 0.01 / 0.24 |

A stated 1% chance of a quiet target does most of the work; the margin adds a little. On
held course the declared track is 1.4 times better than the search's; on Annex B data it
costs nothing at margins up to 3.

## Settings chosen (by the rules in research R1 and R2; fixed from here)

- **Declaration**: margin 1, quiet probability 0.01: the smallest pair with held-course
  false manoeuvres at most 0.10 (0.07), one-manoeuvre targets called quiet 0.10 against
  0.09 undeclared. System `ctl-d1-q0.01`.
- **Hedged track**: temperature 1: the only temperature whose interval is not wholly below
  1 on any split. System `ctl-h1`.
- **Robust form**: editing (the only one built). **Correlation**: the effective sd, used
  above an estimated share of 0.2. **Priors**: Annex B's and the broadened one, pooled.
- Prior version 4 is not needed for the declaration to reach 0.10 (research R6's
  condition); it stays deferred.

## Weaknesses

- One tuning seed; 55 to 142 scored periods a split: the intervals are wide and the
  settings are chosen on the same data that shows what they do.
- The reference on the correlated and shifted splits is held in 23% to 39% of periods.
- The correlated-error control was built knowing the generator's error family (white plus
  first-order Gauss–Markov). It is not told the parameters, but the family is the truth's.
- The hedged track averages over at most ten candidates of a greedy search, not over a
  posterior.
- Run time: about 20 s a search on clean data and 45 s with 5% outliers before editing;
  `ctl` runs two searches a period.
