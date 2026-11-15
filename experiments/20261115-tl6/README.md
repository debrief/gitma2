# Spec 018: a prior that adapts to the period, and a hedged track, on test seed 347 (2026-11-15)

CI run 43677426621 (`timelate/tl-g-test`, commit d126456, clean tree, plan
`configs/timelate/tl-g.json` `541aa8b4…` as registered; scored once). 1,250 periods, 1,123
scored. Every table is in `tables.md` (generated from `summary.json` by
`scripts/research/tl6_tables.py`) and `supplement.md` (`tl6_supplement.py`, from the
per-row errors); the figures below are copied from them. Per-row errors: results branch
`results/timelate-tl-g-test-43677426621`. `tracks.npz` (`tl6_tracks.py`) holds the first
20 shifted periods' tracks for the slides.

A registered study. The decision record (`experiments/20261115-tl6-decision/`) fixed the
conditions and what follows before seeds 346 and 347 existed.

## Soundness

The true history with its times held is at 1.13 of the bound on tight rows (band 0.8 to
1.3); 0.99 of Annex B true-history fits converged; 0.09 of Annex B references are held.

## The conditions (standing control ÷ system; above 1: the system is better)

| Split (scored periods) | Adaptive, declared: range | course | speed | Adaptive, hedged: range | course | speed |
| --- | --- | --- | --- | --- | --- | --- |
| Shifted (355) | 1.00 [0.92, 1.08] | 1.00 [0.91, 1.10] | 0.97 [0.88, 1.07] | 1.00 [0.93, 1.08] | **0.91 [0.82, 1.00]** | 0.97 [0.87, 1.07] |
| Shifted 2 (137) | 1.01 [0.92, 1.11] | 1.01 [0.89, 1.14] | 0.96 [0.81, 1.11] | 0.99 [0.89, 1.09] | 0.90 [0.78, 1.03] | 0.89 [0.76, 1.00] |
| Annex B (273) | 0.93 [0.85, 1.01] | 0.94 [0.84, 1.05] | 0.91 [0.82, 1.01] | 0.92 [0.84, 1.01] | 0.92 [0.81, 1.06] | 0.92 [0.82, 1.03] |
| Held course (172) | 1.05 [0.98, 1.13] | 1.07 [0.99, 1.17] | 1.11 [0.98, 1.27] | 1.02 [0.94, 1.12] | 0.91 [0.80, 1.03] | 0.91 [0.81, 1.01] |
| Outliers (93) | 0.95 [0.79, 1.16] | 0.84 [0.68, 1.04] | 0.96 [0.76, 1.23] | 0.94 [0.79, 1.11] | **0.83 [0.70, 0.99]** | 0.96 [0.75, 1.24] |
| Correlated (93) | 0.85 [0.71, 1.00] | 0.89 [0.72, 1.07] | 0.94 [0.76, 1.16] | 0.89 [0.74, 1.06] | 0.84 [0.69, 1.01] | 0.89 [0.71, 1.12] |

- **Gain** (range wholly above 1 on a shifted split): **none**, for either system.
- **Harm** (range, course or speed wholly below 1): none for the declared control; for the
  hedged track, in course on shifted targets and on outliers (bold).
- **Spread** (two stated sds cover 0.90 to 0.99 of rows): Annex B 0.944, **shifted 0.897**:
  not honest by the band, by three parts in a thousand.

**By the registered rule: the standing control stays, for both the declared and the
hedged output.** The median per-period ratio is 1.00 in every cell of the declared
columns.

## Against the forecasts

The decision record forecast a trade for both (a gain on shifted targets, harm on Annex B
targets in course) with "no gain" at about a third. **The forecast was wrong**: the gain
seen on the tuning seed (1.10 declared, 1.16 hedged) is 1.00 and 1.00 here. The validation
seed had already shown it (0.95 and 1.04 on 60 periods). The record said the tuning
figures were from the second design tried on that seed and would flatter it; they did, by
all of the effect.

## What else it shows

- **The true statistics are worth less than spec 017 found.** The search told the split's
  own statistics is 1.10 [0.99, 1.21] of the control on shifted targets (spec 017's seed:
  1.17; the tuning seed: 1.22) and 1.14 [1.02, 1.28] on shifted 2, level elsewhere. The
  ceiling the adaptive control was aiming at is itself about a tenth, and not separated
  from nothing on the main split.
- **Where the gain was expected.** In the 117 shifted periods where the standing control
  misses a manoeuvre the bearings show: adaptive declared 1.08 [0.95, 1.25], hedged 1.11
  [0.98, 1.27], true statistics 1.47 [1.20, 1.81]. In the other 238: 0.96, 0.95 and 0.96.
  The direction is the tuning seed's, at a fifth of its size. By how tight the bound is,
  the declared control is 0.83 [0.73, 0.95] in the tight third of shifted periods and 1.16
  [1.03, 1.32] in the middle third: it loses where the bearings say most.
- **Choosing the prior by groups of periods does not help.** A whole split choosing one
  member: shifted 0.95 [0.89, 1.02], Annex B 0.90 [0.83, 0.97], correlated 0.80 [0.65,
  0.96], held course 1.08 [1.02, 1.14]. Groups of 5 and 20 are the same within their
  intervals. (One shifted period has a runaway evidence under every member; setting it
  aside changes no choice: `supplement.md`.)
- **No fixed member beats the control on shifted targets** (the best is 0.98); on held
  course the quietest members do (1.08 [1.02, 1.14]).
- **Manoeuvres.** Shifted, 120 s match: the adaptive control misses 0.46 (control 0.48,
  true statistics 0.39) with 0.45 false a period (0.38; 0.56). Held course: a manoeuvre
  given in 0.03 of periods against the control's 0.08. One-manoeuvre targets called quiet:
  0.18 against 0.15 on Annex B (103), 0.32 against 0.29 on shifted (38).
- **The inferred rate barely moves**: median inferred leg 1,427 s on shifted targets
  (true mean 900), 1,686 s on Annex B (1,500), 2,056 s on shifted 2 (2,100), 2,633 s on
  held course.
- **The hedge.** Level with the declared control in range on every split (0.97 to 1.05)
  and worse in course. The standing control's own hedge is 0.71 [0.63, 0.80] on held
  course; the adaptive hedge, which uses the quiet probability, is 1.02 there.
- **The spread.** The factor fitted on the tuning seed (1.95) is too small here: this
  seed's own factor for 0.95 pooled would be 2.68. As it comes, two mixture sds cover 0.84
  (Annex B) and 0.75 (shifted). With the registered factor: 0.94, 0.90, 0.97, 1.00, 0.97,
  0.96 across the six splits; 0.89 on shifted periods with two or more manoeuvres.

## Limits

- The standing control contains Annex B's own prior and the family does not: on Annex B
  targets the comparison favours the control by construction.
- This is the second design tried on the tuning seed; a third might do better or worse,
  and nothing here says which.
- The verdict reads period medians of error; the kind-of-period classing reads the truth
  and a 120 s tolerance and is a reading only.
- Outlier and correlated splits are 93 scored periods each: the hedged track's harm in
  course on outliers is 0.83 [0.70, 0.99], close to its boundary.
- The spread is in range only, one factor for every split, fitted on one seed.
- Prior version 3's recorded faults apply to every system.

## Not delivered

- IMM, EKF and one leg on these periods (spec 017 scored them on splits of the same kinds).
- A hedge or spread for course and speed.
- A rule for choosing between declared and hedged output per period that does anything:
  the two registered thresholds are level with the hedge.
- Unit tests of `run6` itself (its parts in `adapt.py` and `study6.py` are tested; the
  runner was exercised by smoke runs and three CI runs only).
- Why the true statistics help: the family varies leg length, its spread and the largest
  turn, and none of the three is it.
