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

Paired, scenario-clustered bootstrap (97.5%, 2,000 resamples, the gate's resamples), gap
recovered in range, reported side by side:

1. **C′ − C**: what the zig veto alone buys; **(C′ + ew-s3) − C** beside **e-s3 − C** and
   **ew-s3 − C**.
2. **E − (C′ + ew-s3)** (the carried e-s3 against C′ followed by the same E-w): what E-s's learned
   evidence adds beyond the rule. Both arms carry the same E-w, trained on C's segmentation, so the
   E-w mismatch is symmetric.
   - Wholly above zero: the learned evidence adds something beyond the zig veto.
   - Contains zero: **learning beyond the zig veto is not shown.** This is not a claim that the
     rule reproduces E: no equivalence margin is declared, and the comparison has limited power
     (E-s's own increment over E-w, e-s3 − ew-s3, is about +0.01).
   - Wholly below zero: the classical rule plus E-w beats E.

**Amended before any C′ result existed** (Gate 2 panel round 1, statistics reviewer, minor): the
first version read an interval containing zero as "G2-d's gain is reproduced by a classical rule
plus E-w" (absence of evidence as equivalence) and had no branch for an interval wholly below
zero.

The test-split reading is reported whatever it says. The gate's verdict (G2-a to G2-d) is not
changed by it; the panel weighs it in reading G2-d.

## Addendum: C″, fully classical (panel round 1, red team; registered before any C″ result)

The red team found that E-w's learned weights are mostly a recency profile: Δ log-weight about
+0.73 on the newest bearings, falling linearly to about −0.70 at 180 rows. C′ + ew-s3 still uses
the learned E-w, so no control above is classical end to end. Added:

- **fade**: C with a fixed fading memory, clip(0.73 − 0.0079·age, ±2) added to C's log-weights
  (age = k − row). Its two numbers were read off ew-s3's mean log-weight profile on validation
  ordinals 500–559 (239 prefixes) by the red team; no score was used to choose them. The red team
  has already scored this rule on test (fade − C +0.0107 [+0.0068, +0.0140]; E − fade +0.0143
  [+0.0094, +0.0199]), so on test it is not a fresh look; it is re-run here on CI for the record.
- **C″ = veto-w6-fade**: C′ (the zig veto above) followed by the same fixed fading memory. No
  learned component. Not yet scored anywhere.

Plan `configs/gate2/g2-a-fade.json`; predictions `configs/g2predict/g2-fade-{val,test}.json`;
scored with the C′ files on the same rows.

**Reading (fixed now):** E − C″ (e-s3 against C″), paired as above.
- Wholly above zero: learning adds something beyond both classical rules.
- Contains zero: learning beyond the two classical rules (zig veto, fading memory) is not shown.
- Wholly below zero: the two classical rules beat E.

Reported beside it: fade − C, C″ − C, E − fade and E-w − fade. Caveat (red team): the veto uses
the ownship's planned zig row, which E-s does not see (it sees online ownship codes); this favours
the controls, so a positive E − C″ is conservative.

## Results

Scored on CI (`score.yml`, not gate mode): validation run 42434645201 at ba95b91
(`results/score-g2-veto-val-42434645201`), test run 42440631371 at 21aff2d
(`results/score-g2-veto-test-42440631371`); `report.md`, `metrics.json`, `inputs.json`,
`run.json` copied to `validation/` and `test/`, the paired differences
(`scripts/research/g2_paired_gaps.py` on each run's `errors.npz`, the scorer's resamples) in
`paired.json`. Predictions: `results/g2predict-g2-veto-{val-42417465155,test-42417467154}` and
`results/g2predict-g2-fade-{val-42426461205,test-42426463015}` (all from clean trees, all
ordinals, dataset digests as the gate's).

Gap recovered in range, 97.5% scenario-clustered paired intervals:

| Comparison | Validation (1,000 scenarios) | **Test (4,983 scenarios)** |
| --- | --- | --- |
| E (e-s3) − C | +0.028 [+0.013, +0.041] | +0.025 [+0.018, +0.031] |
| E-w alone (ew-s3) − C | +0.012 [+0.004, +0.023] | +0.015 [+0.010, +0.019] |
| C′ (zig veto) − C | +0.007 [+0.002, +0.017] | +0.008 [+0.004, +0.011] |
| fade − C | +0.014 [+0.005, +0.022] | +0.011 [+0.007, +0.014] |
| C″ (veto + fade, no learning) − C | +0.020 [+0.011, +0.032] | +0.018 [+0.013, +0.022] |
| C′ + E-w − C | +0.022 [+0.011, +0.035] | +0.022 [+0.017, +0.027] |
| **E − C″** | +0.008 [−0.004, +0.017] | **+0.007 [+0.001, +0.012]** |
| E − (C′ + E-w) | +0.006 [−0.005, +0.016] | +0.003 [−0.002, +0.008] |
| E − C′ | +0.021 [+0.005, +0.031] | +0.017 [+0.010, +0.023] |
| E − fade | +0.014 [+0.003, +0.025] | +0.014 [+0.009, +0.019] |
| E-w − fade | −0.003 [−0.009, +0.007] | +0.004 [+0.001, +0.007] |

**Reading, as registered (test):**

- **E − C″ is wholly above zero: learning adds something beyond both classical rules.** It is
  small: the two rules, with nothing learned, recover +0.018 of E's +0.025 over C (about 72%);
  learning adds +0.007 [+0.001, +0.012] beyond them.
- **E − (C′ + E-w) contains zero: E-s's learned evidence adds nothing shown beyond the zig veto**
  (with the same E-w on both sides). The learned increment is E-w's: E-w − fade +0.004 [+0.001,
  +0.007], wholly above zero.
- Validation (five times fewer scenarios) agrees in direction; its intervals contain zero for
  E − C″ and E-w − fade.
- The control uses the ownship's planned zig row, which E-s does not see; this favours the control.

**Cross-CPU note.** The scorer re-solves C, one leg, the oracle and GLR + confirm. This run (Intel
Xeon 8573C) and the gate run (AMD EPYC 9V45) differ in those errors by up to 6e-4 relative for C
(21 one-leg rows change between finite and runaway); E's errors, read from its prediction files,
are identical. G2-d here is +0.024994 [+0.018462, +0.030509] against the gate's +0.025008
[+0.018467, +0.030531].
