# Spec 017: validation on seed 343 (2026-11-14)

CI run 43613435875 (`timelate/tl-f-val`, commit b8c0455, plan `configs/timelate/tl-f.json`
`0b29a95d…` as registered). **Soundness only: nothing here decides the study.** Tables in
`tables.md`, generated from `summary.json` by `scripts/research/tl5_tables.py`. Per-row
errors: results branch `results/timelate-tl-f-val-43613435875`.

## Soundness: passes

The true history with its times held is at 1.14 of the bound on tight rows (band 0.8 to
1.3); every true-history fit converged; 0.12 of references are held (limit 0.25). 58 of 60
periods scored on each split. The study goes on to test seed 344, once.

## Reported, not decided (60 periods a split)

Attainable share of the declared control's gap on the shifted split: 0.64 [0.41, 0.89] at
threshold 10, 0.42 [0.12, 0.68] at 20, 0.17 [-0.23, 0.48] at 40 (tuning seed 342: 0.66,
0.32, -0.11). The dependence on the threshold repeats; the intervals at this size decide
nothing.
