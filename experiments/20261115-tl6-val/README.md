# Spec 018: validation on seed 346 (2026-11-15)

CI run 43667630296 (`timelate/tl-g-val`, commit a9c7500, clean tree, plan
`configs/timelate/tl-g.json` `541aa8b4…` as registered). **Soundness only: nothing here
decides the study.** Tables in `tables.md`, generated from `summary.json` by
`scripts/research/tl6_tables.py`. Per-row errors: results branch
`results/timelate-tl-g-val-43667630296`.

## Soundness: passes

The true history with its times held is at 1.24 of the bound on tight rows (band 0.8 to
1.3; 1.04 on the tuning seed, so this seed sits near the band's upper edge); every
true-history fit converged; 0.08 of references are held (limit 0.25). 54 and 53 of 60
periods scored. The study goes on to test seed 347, once.

## Reported, not decided (60 periods a split)

The scorer prints the conditions on whatever it is given; at this size they decide
nothing, and they are stated here so that the test cannot be read selectively afterwards.

- Shifted: control ÷ adaptive, declared 0.95; hedged 1.04; neither separated (tuning: 1.10
  and 1.16).
- Annex B: declared 0.80 and hedged 0.81, both read as harm (tuning: 0.90 and 0.88).
- Spread, two stated sds: 0.99 of rows on Annex B, 0.94 on shifted (band 0.90 to 0.99).

On this seed the tuning run's gain on busier targets does not appear and the cost on
Annex B targets is larger. The tuning figures were from the second design tried on that
seed; the decision record said they would flatter it.

One shard took 130 minutes (a shifted period of 87 minutes with seven manoeuvres took 22
minutes on its own, a third of it the detectability reading).
