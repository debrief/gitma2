# Gate 2 decision record (spec 007 T026)

`decision.json` (a `Gate2Decision`) is committed before any E training (FR-034, FR-050) and
before test seed 319 is generated. It binds `configs/gate2/g2-a.json` by SHA-256
(`plan_digest` `6092c364…`). Later changes are amendments: new files here, listed by digest in
the gate manifest (`carried.json` after validation, `test-digest.json` after seed 319 is made).
None may change a criterion once any test result exists.

## Fixed here

- **The SRD amendment** (§5 Gate 2 row gains G2-d; §7 step 4 names C) is on `main` (PR 16,
  merged by the owner, 2026-11-07): T025.
- **C, the segmenter and the control:**
  - parameters as Gate S (`configs/segment/gs-plan.json`), parameter digest `60e6ee63…`;
  - code digest `4d2c084f…` (`segment/codeid.py`, commit 2a5cf1c), after the Gate S panel's
    fixes and the decision recording;
  - open-transition hand-over `knot_at_k` (`experiments/20261106-c3-val/`);
  - knot cap 12 in every physics-layer solve (research R5).
- **E** (research R1–R3; plan `configs/gate2/g2-a.json`):
  - E-s: spec 005's evidence network on its causal features, shifting C's confirmation
    threshold by clamp(2 Σ e, ± τ/2), trained on decision tables with the relaxed acceptance,
    temperature T = 1, validated on the hard rule;
  - E-w: Gate 1's causal transformer (width 64, 2 layers, 4 heads) plus C's code channel,
    per-bearing log-weights (bound 2) and a start correction, physics layer with 12 knots,
    implicit differentiation, loss capped at 100, trimmed validation loss, patience 3,
    12 epochs at most (research R4: about 45 min per epoch);
  - E = E-s seed s, then E-w seed s (E-w trains on C's segmentation: research R2 as amended);
  - E-w alone is reported, never carried.
- **Inputs, all at C's frozen code:**
  - training stream seed 318 (`experiments/20261106-g2-stream/`), C's segmentation
    `results/segment-g2-stream-c-42268365081`, decision tables
    `results/dtables-g2-stream-42295008170`;
  - validation 314 (`e8150cb0…`): tuning ordinals 0–499 for early stopping
    (`results/segment-c3-val-tune-42268374366`, tables `results/dtables-g2-val-tune-42288137249`);
    scoring ordinals 500–1499 for the validation rule (`results/segment-c3-val-42268379557`).
- **Test seed 319,** generated after this record with `--count 100000` (a 10,000-scenario test
  split, as Gate S); its digests go to `test-digest.json` here.
- **References,** frozen by name: IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` (gated), EKF
  `ekf-sa0.00003-p4-r0.03125` and GLR + confirm `glr-q0.2-t13.8` (reported), the oracle, one
  leg and naive on the same rows.
- **Criteria** (`decision.json` `criterion`): G2-a, G2-b, G2-c as the SRD; G2-d (owner,
  2026-11-06) E − C in gap recovered wholly above zero, void by the shuffled rule. 97.5%
  scenario-clustered paired bootstrap, 2,000 resamples.
- **Rules:** carried seed (median validation gap recovered), shuffled, validation and re-score
  as in `decision.json`.

## C's validation baseline (for the forecast)

`results/score-g2-val-c-42288140230` (scoring ordinals 500–1499, 3,934 G5 rows, 12 knots):

| Estimator | Range | Course ° | Speed kt | Range / IMM | Gap recovered |
| --- | --- | --- | --- | --- | --- |
| One leg | 0.581 | 65.97 | 6.20 | 1.079 | — |
| IMM | 0.539 | 52.32 | 5.79 | — | — |
| GLR + confirm | 0.447 | 44.39 | 4.57 | 0.830 | 0.259 |
| C | 0.120 | 15.54 | 1.62 | 0.223 [0.200, 0.247] | 0.890 [0.869, 0.909] |
| Oracle | 0.064 | 7.41 | 0.96 | 0.118 | — |

## Forecast

G2-a to G2-c pass for E as for C (0.95). E − C in gap recovered +0.005 [−0.005, +0.015]: G2-d
inconclusive is the most likely outcome, a pass about 0.25. Reasons: E-s's ceiling on the
stream's decision rows lowers the mean decision-row error from 51.0 to 44.4, but those rows are
a minority of G5 rows and the learnable share is smaller; E-w's one-epoch run moved the trimmed
validation loss only from 38.10 to 37.86.
