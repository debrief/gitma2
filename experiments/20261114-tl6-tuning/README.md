# Spec 018: first design on tuning seed 345 (2026-11-14)

CI run 43640546592 (`timelate/tl-g-tune`, commit 67af913, first draft plan: `plan.json`
here). **Tuning data: nothing here is a registered result.** Tables in `tables.md`,
generated from `summary.json` by `scripts/research/tl6_tables.py` (the script has since
gained sections this run has no data for). Per-row errors: results branch
`results/timelate-tl-g-tune-43640546592`.

## The first design

A grid of three manoeuvre rates (leg means 600, 1,200 and 2,400 s on the broadened prior),
one search under each, the rate chosen by this period's evidence, the history declared
under it; a hedged track over all three rates' candidates with a spread in range.

## What it showed: no gain, and why

- **No gain on busier targets.** Standing control ÷ adaptive, shifted split, 132 periods:
  range 0.99 [0.88, 1.11], course 0.88 [0.77, 1.00], speed 0.99. The search told the
  targets' own statistics: 1.25 [1.07, 1.49].
- **One period does not identify the rate.** The inferred leg length has a median of 1,366 s
  on shifted targets (true mean 900) against 1,625 s on Annex B targets (true 1,500); the
  busiest rate is chosen in 24% of shifted periods. Held course is recognised (the
  quietest rate in 99% of periods).
- **The rate is not what the true prior buys.** In the 32 shifted periods where the busiest
  rate was chosen the adaptive control is 1.05 of the standing one while the true-prior
  search is 1.36. Summed over the split, the evidence prefers the middle rate by 175 and
  257 over the others: the truth (900 s, sd 300 s) lies between grid points, and its
  sharper leg spread and narrower turns (15° to 75° against 10° to 150°) are not in the grid.
- **Small costs elsewhere**, none separated: Annex B 0.95 [0.80, 1.11], held course 0.91
  [0.75, 1.04], outliers 0.98, correlated 0.97. One-manoeuvre Annex B targets called quiet:
  0.12 against 0.04 (26 periods).
- **The hedged track**: against the declared control, 1.09 [0.98, 1.23] on shifted targets
  (the standing control's own hedge: 1.05 [0.99, 1.12]) and 0.85 [0.67, 1.04] on held
  course (the standing hedge: 0.64 [0.49, 0.80]: it does not use the quiet probability the
  declaration uses). Its two-sd spread covers 0.88 of rows on Annex B, 0.73 on shifted,
  0.99 on held course: too narrow where manoeuvres are missed.
- **Cost**: about 50 minutes for ten shifted periods, twice spec 017's.

## What changes for the second design (still tuning; nothing registered)

1. A family of priors with three dimensions (leg mean, leg spread, largest turn), scored
   by refitting one shared candidate set under each member instead of a search per member.
2. Each member's declared track is kept, so the study can report every fixed member and
   **a member chosen by a group of periods taken to share their statistics**, at several
   group sizes: how many periods of the same kind of target are needed before the prior
   is learnt.
3. The hedge uses the declaration's quiet probability, and is reported at temperatures 1,
   2 and 3 for the coverage of its spread.
