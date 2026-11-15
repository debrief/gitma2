# Spec 018: second design on tuning seed 345 (2026-11-15)

CI run 43653896214 (`timelate/tl-g-tune2`, commit f0b14a0, draft plan: `plan.json` here;
the same 530 periods as the first design's run). **Tuning data: nothing here is a
registered result.** Tables in `tables.md`, generated from `summary.json` by
`scripts/research/tl6_tables.py`; the figures below are copied from it. Per-row errors:
results branch `results/timelate-tl-g-tune2-43653896214`.

## The design

A family of 30 manoeuvre priors on the broadened prior: leg mean 600, 900, 1,350, 2,000 or
3,000 s; leg sd 0.35 or 0.6 of the mean; largest turn 60°, 100° or 150°. Two searches
(under the busiest and the quietest member) give one candidate set; every member refits
and scores it. The member with the most evidence in a period is used to declare
(`ada-d1-q0.01`); all members' candidates form the hedged track (`ada-h1`). Each member's
own declared track is kept, so a member can also be chosen by a group of periods.

## What it shows (control = the standing control, declared)

| Control ÷ … (range) | Annex B (89) | Shifted (132) | Shifted 2 (73) | Held course (65) | Outliers (51) | Correlated (51) |
| --- | --- | --- | --- | --- | --- | --- |
| adaptive, declared | 0.90 [0.77, 1.04] | 1.10 [0.96, 1.27] | 1.03 [0.92, 1.18] | 0.91 [0.76, 1.04] | 1.02 [0.82, 1.33] | 0.92 [0.72, 1.18] |
| adaptive, hedged | 0.88 [0.73, 1.05] | 1.16 [1.02, 1.33] | 1.04 [0.93, 1.18] | 0.99 [0.81, 1.17] | 1.03 [0.79, 1.34] | 1.10 [0.88, 1.37] |
| search told the true statistics | 1.03 [0.93, 1.15] | 1.22 [1.02, 1.46] | 1.01 [0.89, 1.16] | – | 0.94 [0.82, 1.03] | 1.09 [0.92, 1.33] |

- **A trade, not yet separated either way.** On busier targets the adaptive control is
  about 10% better in range (16% hedged), about half of what the true statistics give. On
  Annex B targets it is about 10% worse. The median per-period ratio is 1.00 everywhere.
- **Range only.** On shifted targets course and speed are level (0.96 and 0.95). On Annex
  B targets course is worse: 0.83 [0.68, 1.00] declared, 0.74 [0.60, 0.90] hedged.
- **The gain is where spec 017 said it would be.** In the 43 shifted periods where the
  standing control misses a manoeuvre the bearings show, the adaptive control is 1.53
  [1.16, 2.04] better (hedged 1.50 [1.22, 1.85]); in the other 89 it is 0.93 [0.80, 1.08].
- **Why Annex B costs.** The standing control searches under Annex B's own prior as well
  as the broadened one; the family has no member that sharp. The best single member on
  Annex B targets (`L1350-s0.35-a150`) is 0.96 [0.85, 1.08] of the control.
- **Choosing by groups of periods adds nothing.** With every period of a split choosing
  one member together the split's evidence picks a sensible member (leg 900 s on shifted
  targets, 1,350 s on Annex B, 2,000 s on shifted 2, 3,000 s on held course), yet the
  error is no better than choosing per period: shifted 1.10 [0.94, 1.31] at group sizes 5,
  20 and all; Annex B 0.88 to 0.93. No fixed member is better than 1.13 on shifted
  targets. Knowing the rate is worth little; what the true statistics add is elsewhere.
- **Manoeuvres**: on shifted targets the adaptive control misses 0.42 at a 120 s match
  (control 0.47, true statistics 0.35) with false manoeuvres level (0.45 a period against
  0.43). On held course: a manoeuvre given in 0.04 of periods (control 0.08).
  One-manoeuvre Annex B targets called quiet: 0.08 against 0.04 (26 periods).
- **The hedge's spread is too narrow as it comes.** Two mixture sds cover 0.87 of rows on
  Annex B targets and 0.81 on shifted. The error over the sd is heavy-tailed: a factor of
  1.95 on the sd gives 0.95 pooled over the two (`scripts/research/tl6_spread_scale.py`:
  0.97 Annex B, 0.94 shifted, 0.94 shifted 2, 1.00 held course, 0.97 outliers, 0.99
  correlated). Temperatures 2 and 3 widen the spread and cost accuracy (Annex B 0.82 and
  0.81; held course 0.85 and 0.71): temperature 1 is kept.
- **Per-period choice of output** (declared when the first candidate has probability at
  least 0.5 or 0.8): level with the hedge; nothing to add.
- **Cost**: about 45 minutes for ten shifted periods on a CI runner.

## Settled here for the registration

Member weights equal; temperature 1; stated sd = 1.95 × the mixture's; group sizes 5, 20
and all (reported, decide nothing); no further change to the design.
