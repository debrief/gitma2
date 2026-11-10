# Gate 5 validation (spec 010 T016): stopped at validation (G5-d void)

Seed 314 validation, scoring ordinals 500–1499 (1,000 scenarios, 3,934 σ = 1° G5 rows). The
decision record is `experiments/20261109-g5-decision/` (plan `configs/gate5/g5-a.json`,
`3febde6f…`; proxy `6248deea…`).

## Provenance

- **Training.** CI run 42712276372 (`results/g5-g5-a-42712276372`, commit 06dd705 = the decision
  commit, clean).
  - Three heads, best epochs 7, 9 and 19.
  - The encoder-only shuffle, best epoch 2 and last epoch 7.
  - The classical rule, fitted on the stream.
  - The temperature, fitted on tuning rows, with β = (0.7, 0.8, 0.4).
- **Stated files.** `tma2-g5predict` at 457b6fd, in a clean worktree, wrote
  `results/g5predict-g5-a-val`. 3,895 rows are stated. The largest |arc mass − P| is 6–7e-8.
- **Scoring.** CI run 42712917053 (`results/score-g5-a-val-42712917053`, commit 457b6fd, AMD EPYC
  7763). The references were reused from the Gate 5 baseline.
- **Verdict.** `tma2-g5 --split validation` at 25653e0 (clean; Intel Xeon) wrote `validation.json`
  (`5d2f296a…`). The `by-head/` folder holds the same checks run with other statements in the
  head's role. They are for information only and decide nothing.

## The carried seed and the checks

**Carried-seed rule.** The median standardised summed score on the control of record's scale
picks the carried seed: st5-s1 2.919, st5-s2 2.927, st5-s3 2.906, so **st5-s1**.

**Control of record.** It is the classical rule, which scores 2.969 against the temperature's
3.000 on the temperature's scale.

| Check | Value [97.5% interval] | Band | Verdict |
| --- | --- | --- | --- |
| G5-a coverage, overall | range 0.938 [0.925, 0.949]; speed 0.938 [0.926, 0.949] | wholly in [0.92, 0.98] | pass |
| G5-a coverage, per slice | no gated slice wholly outside [0.90, 0.99] (minute 5: 0.905 / 0.912; 30+ km: 0.903 / 0.885) | — | pass |
| G5-b hit − P, overall | −0.006 [−0.028, +0.016] | wholly in ±0.04 | pass |
| G5-b calibration slope | 1.25 [1.06, 1.47] | wholly in [0.75, 1.33] | inconclusive |
| G5-b hit − P, per slice | every gated slice passes; proxy-flagged −0.038 [−0.072, −0.001]; minute 5 −0.035 [−0.068, 0.000] | not wholly outside ±0.05 | pass |
| G5-c course log gain | +0.80 [0.71, 0.88] | wholly > 0 | pass |
| G5-c AUC of P | 0.654 [0.633, 0.677] | wholly > 0.55 | pass |
| G5-d head − classical | −0.081 [−0.136, −0.028] | wholly < 0 | **void (not passed)** |
| G5-d encoder shuffle − classical | best −0.039 [−0.075, −0.005]; last −0.027 [−0.068, +0.008] | the rule fails if either is wholly < 0 | **rule fails** |
| G5-e points identical; arc mass error | exact; 6.4e-8 | ≤ 1e-6 | pass |

**The validation rule is not met.** G5-d fails: the head beats the classical rule, but the
encoder-only shuffle also does at its best epoch, so the pass is void. G5-b is inconclusive: the
slope's interval reaches 1.47. Seed 320 is not generated and is still unused.

**Follow-on, per the decision record.** If only G5-d fails, the control of record's statement is
carried, which here is the classical rule. Its own checks are in `by-head/classical5.json`:
- G5-a passes;
- G5-b is inconclusive (slope 1.25 [1.06, 1.45]; proxy-flagged −0.054, not wholly outside);
- G5-c passes (AUC 0.669, log gain 0.80).

## Every statement on the same checks (information only)

| Statement | G5-a | G5-b | G5-c | Hit − P | Slope | AUC | Log gain | Proxy-flagged hit − P | − classical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| head st5-s1 (carried) | pass | inconcl. | pass | −0.006 | 1.25 | 0.654 | 0.80 | −0.038 | −0.081 |
| head st5-s2 | pass | inconcl. | pass | −0.005 | 1.24 | 0.654 | 0.80 | −0.035 | −0.073 |
| head st5-s3 | pass | inconcl. | pass | −0.003 | 1.28 | 0.654 | 0.80 | −0.026 | −0.094 |
| encoder shuffle (best) | pass | inconcl. | pass | −0.005 | 1.26 | 0.662 | 0.80 | −0.046 | −0.039 |
| classical rule | pass | inconcl. | pass | −0.004 | 1.25 | 0.669 | 0.80 | −0.054 | 0 |
| sd^β temperature | pass | **fail** | **fail** | −0.004 | n/a | 0.499 | 0.92 | **−0.134** | +0.063 |

The truth's settled split is reported, not gated. Each cell is stated P / hit rate:

| Statement | Settled | Not settled | P 5–95% | Mean X |
| --- | --- | --- | --- | --- |
| head st5-s1 | 0.54 / 0.61 | 0.50 / 0.27 | 0.35–0.71 | 18.1° |
| classical rule | 0.53 / 0.61 | 0.49 / 0.26 | 0.32–0.72 | 17.7° |
| temperature | 0.60 / 0.70 | 0.60 / 0.28 | 0.60–0.61 | 19.9° |
| E raw sds | 0.91 / 0.60 | 0.89 / 0.25 | 0.64–0.95 | 16.7° |

**References**, given the same temperature cross-fitted on the scoring rows
(`scripts/research/g5_refs.py`; `references.txt`):

| Reference | Log gain | Hit − P | Settled P / hit | Not settled P / hit | Rows stated |
| --- | --- | --- | --- | --- | --- |
| oracle | 1.52 | −0.006 | 0.75 / 0.81 | 0.75 / 0.56 | all |
| IMM | 0.21 | −0.003 | — | — | 77% |

## Reading (as corrected by the panel, round 1; `review.md`)

**The stop.** It is correct and applied as written. G5-d is void (not passed), and under the
validation rule G5-d alone blocks: G5-b's slope point, 1.25, lies inside its band. "Only G5-d
fails", so the follow-on carries the control of record, the classical rule. That rule is not the
best statement available (see below).

**What improved.**
- **The statement is consistent.** The arc mass equals P by construction. The panel checked the
  normalisation to 1e-9 for κ from 1e-8 to 1e8 and X up to 45°. The record's 6e-8 is the trapezoid
  check on 200 probed rows.
- **P now varies and ranks hits.** P runs 0.32–0.72 and its AUC is 0.65–0.67 (0.647–0.662 on
  stated rows only). Gate 4's temperature, re-fitted here, has an AUC of 0.50 and fails G5-b and
  G5-c.
- **The range and speed intervals cover 0.94.**

**Not honest where it matters.**
- **The proxy-flagged slice is mildly over-confident.** It is not "honest within the band":
  - head −0.038 [−0.072, −0.001];
  - classical rule −0.054 [−0.087, −0.018].

  Both intervals exclude 0. They pass G5-b only because the per-slice check fails a slice only
  when its interval lies wholly outside ±0.05.
- **The flag mixes two kinds of row.** It catches 42% of the truth-unsettled rows (417 of 1,001),
  and 55% of the rows it flags are settled. Within the flagged rows (head):
  - unsettled: P 0.47 against hit 0.33 (−0.14);
  - settled: P 0.49 against hit 0.53 (+0.04).

  P moves little with the flag: 0.48 flagged against 0.54 unflagged.
- **The 572 unflagged unsettled rows** state P 0.53 and hit 0.22. Of these, 129 state P ≥ 0.6. The
  statement must carry this caveat: **P assumes no undetected target manoeuvre in the last ~5
  min, and the flag misses most manoeuvres.**
- **The flag also reacts to geometry, not only to target manoeuvres.**
  - Its rate falls with time since the zig (0.27 to 0.18) while the unsettled rate stays near 0.26.
  - At 0–2 km it flags 37% of rows against 16% unsettled.
  - Ownship manoeuvres and close-range bearing rate raise the residuals too, and neither is a slice
    here.
- **The statement is under-confident at short range.**
  - classical rule at 2–5 km (215 rows): +0.117 [+0.044, +0.188];
  - head at 2–5 km: +0.075 [0.000, 0.148];
  - 0–2 km (52 rows, ungated): about +0.2.

  Both pass only because their intervals touch the band.
- **The record's claim that "no causal statement can fix the unsettled rows" is withdrawn.** It
  was not tested, and the oracle comparison behind it was unfair: the oracle's statement is the
  temperature (AUC 0.54) and does not use the manoeuvre times it knows.

**The slope (G5-b inconclusive) is the Platt map's doing.** A Platt map is affine in logit P, so the
validation slope equals the unmapped slope times the map's b.
- Unmapped, the classical rule's P has slope 1.06 [0.94, 1.20] on the scoring rows.
- The map's b, fitted on the 1,951 tuning rows (500 scenarios), is 0.85 [0.67, 1.05]. That fit is
  noisy: the minute-10 cell alone gives 0.60 on tuning rows against 1.36 on scoring rows.
- The map therefore made a nearly calibrated P worse. This finding is post hoc and does not change
  the verdict.
- The same 500 tuning scenarios also fitted the proxy and its threshold and the temperature, and
  chose the heads' early-stopping epoch.

**The course arc is badly fitted.** Validation course log scores are:

| Statement | Course log score |
| --- | --- |
| temperature | −0.904 |
| classical rule | −1.028 |
| head | −1.032 |
| shuffle | −1.035 |

- The "failed" temperature has the best course proper score.
- X is tied to the spread a, and the log density jumps by about 1.4 nats when |e| crosses X.
  Gradient fits cannot see that jump.
- Scaling a by 1.5 improves the classical rule on its own training stream from −0.966 to −0.861. The
  temperature reached a wider arc only through its β grid.
- **The head's whole G5-d margin is in the range and speed intervals** (range interval score 1.79
  against 1.88; speed 10.50 against 10.84). On course it is no better: +0.004 [−0.013, +0.021] on
  the classical rule's scale. The earlier reading, "its gain is in the arc width", was wrong.

**Learning: no learning from E-w's encoder state is shown.**
- **Within the bounded-residual head, the encoder helps a little.** Head − encoder shuffle (best) is
  −0.041 [−0.074, −0.012].
- **An encoder-free model beats the head.** The red team trained a plain MLP (64×64, tanh) on the
  stream, early-stopped on tuning rows, with no encoder state; its inputs were the sds, C's code,
  the proxy design and the minute. Nothing was chosen on the scoring rows.
  - MLP − classical: −0.16 [−0.23, −0.10] for both seeds.
  - Head − MLP: +0.082 [+0.025, +0.147] for st5-s1 and +0.069 for st5-s3.
  - One MLP seed passes G5-b outright (slope 1.13 [0.95, 1.31]).

  The head's gain is a nonlinear use of the classical features, and the bounded head underfits it.
- **A richer parametric rule does not match the head.** A 105-term quadratic in the sds, the
  design, the code and the minute gave −0.008 [−0.066, +0.048].

**The carried statement is the classical rule, by the rule.** It is dominated by the encoder-free
MLP by 0.16. It is under-dispersed through its Platt map, under-confident at short range, and its
arc is too narrow.

**The gate's per-slice check is weak** (design; to be revised for the next gate). The synthetic
check did not represent the real data:
- its P spread was logit sd 0.87, against 0.48 on validation;
- it had no within-scenario correlation, against about 0.24 on validation.

Resampling hits from the head's real P, with the real clusters and slices:
- a calibrated statement comes out G5-b inconclusive in about 29% of datasets;
- a −0.08 shortfall on the flagged slice fails in only 5 of 12 datasets.

Slices of about 200 rows have intervals of about ±0.075, so a slice off by 0.12 can pass. An AUC
of 0.55 is reachable with four cells.

**References.** FR-023 asked for the references' temperatures fitted on tuning rows. They were
cross-fitted on the scoring rows instead, because there are no reference files on tuning rows
(`scripts/research/g5_refs.py`). The IMM states only 77% of rows.

Files: `validation.json` (it records G5-d as `fail`: void counts as not passed), `by-head/*.json`,
`references.txt`, `calibration.json`, `metrics.json`, `report.md`, `inputs.json`, `plan.json`,
`run.json`, and `review.md` (the panel). `errors.npz` stays on the results branch.
