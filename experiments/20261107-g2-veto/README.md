# Gate 2 diagnostic: the classical control C′ (panel round 1)

**Pre-registered here before any C′ prediction exists.** This is a diagnostic beside the gate, not
a gate criterion: `experiments/20261107-g2-decision/` and `configs/gate2/g2-a.json` are unchanged,
and G2-a to G2-d are judged as registered.

## Why

The TMA-geometry reviewer (panel round 1, major) found that E-s's evidence concentrates at the
ownship zig: mean evidence about +0.5 per row within 3 rows of the zig, about −0.2 elsewhere, and
no difference between rows inside true target manoeuvres and outside them. So E-s mostly raises
C's threshold for target transitions at the ownship manoeuvre, where a target knot would absorb
the bearing-rate change and make range unobservable. If a classical rule does the same, G2-d's
"E beats C" is a gain from a rule a designer could write, and the write-up must say so.

## The control

C′ is C with one change. A candidate whose evidence rows (start to min(start + length − 1, a), as
E-s's shift) touch the ownship zig ± W rows gets the threshold shift +τ/2, which is E-s's largest.
No other shift. Implemented as fixed evidence in C's own confirmation
(`gate2.predict.zig_veto_evidence`, model kind `veto` in `tma2-g2predict`). It uses only the
ownship's own zig row, which ownship knows and C's data carry.

**Chosen on the validation tuning tables** (seed 314 ordinals 0–499, the tables E-s early-stopped
on), by E-s's own hard decision-table loss (`scripts/research/g2_zig_veto_tables.py`):

| Rule (base shift b; veto window W) | Tuning loss | Stream loss (seed 318, check) |
| --- | --- | --- |
| C (b = 0, no veto) | 52.31 | 50.98 |
| C at τ/2 (b = −τ/2, no veto) | 60.56 | 59.11 |
| b = 0, W = 3 | 51.20 | 50.61 |
| **b = 0, W = 6 (chosen)** | **51.08** | 50.64 |
| b = 0, W = 12 | 51.41 | 50.68 |
| es-s1 / es-s2 / es-s3 (learned) | 50.60 / 51.11 / 51.01 | — |
| es-shuffled (untrained) | 52.31 | — |

So on its own objective the learned E-s is matched by a zig veto with a window chosen on the same
rows (es-s1 is 0.5 better; es-s2 and es-s3 are within 0.07). Halving τ everywhere is far worse.

## What is run (all on CI, same rows as the gate)

- Plan `configs/gate2/g2-a-veto.json` (g2-a's blocks, two models): `veto-w6` (C′) and
  `veto-w6-ew3` (C′ then the carried E-w, ew-s3's weights).
- Predictions `configs/g2predict/g2-veto-val.json` (seed 314 ordinals 500–1499) and
  `g2-veto-test.json` (seed 319, all 4,983 σ = 1° scenarios).
- Scoring with `tma2-g2` without gate mode, beside C, e-s3 and ew-s3 on the same rows.

## How it is read (fixed now)

Paired, scenario-clustered bootstrap (97.5%, 2,000 resamples), gap recovered in range:

1. **C′ − C**: what the zig veto alone buys.
2. **E − C′** (e-s3 against C′ + ew-s3, and against C′): what learning adds beyond the rule.
   If E − C′ + E-w is wholly above zero, the learned evidence adds something beyond the zig veto.
   If it contains zero, the write-up states that G2-d's gain is reproduced by a classical rule
   plus E-w, and that learning beyond the rule is not shown.

The test-split reading is reported whatever it says. The gate's verdict (G2-a to G2-d) is not
changed by it; the panel weighs it in reading G2-d.
