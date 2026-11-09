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
| G5-d head − classical | −0.081 [−0.136, −0.028] | wholly < 0 | **void** |
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

## Reading

- **The statement is now consistent and causally gated.**
  - The arc mass equals P to within 7e-8 on every probed row.
  - On the rows the causal proxy flags, P is honest within the band (−0.038 for the head, −0.054
    for the classical rule), where Gate 4's statements were off by about −0.3 on the truth's
    unsettled rows.
  - P now varies (0.32–0.72) and ranks hits (AUC 0.65–0.67).
- **The truth's unsettled rows are still far off.** They state 0.50 and hit 0.27. The proxy's
  held-out AUC for those rows is about 0.65, so it lowers P on the flagged rows, but most
  truth-unsettled rows are not flagged. No causal statement built from these signals can fix that.
  Even the oracle, which knows the manoeuvre times, states 0.75 and hits 0.56 there.
- **Learning beyond the classical rule is not shown.** The head beats the classical rule by 0.08,
  but a head with E-w's encoder state shuffled beats it by 0.04. At least half of the margin is a
  better nonlinear use of the sds, the proxy and C's code, which a richer classical rule might
  match. The head's AUC (0.654) is no better than the classical rule's (0.669). Its gain is in the
  arc width and the interval widths, not in P's resolution.
- **P is under-dispersed out of sample** for every learned or classical statement: the slope is
  1.24–1.28. The Platt map fitted on the 1,951 tuning rows shrank P (slope 0.85 for the classical
  rule). The validation rows say it should have stretched P. With a two-parameter map, the tuning
  set was too small to tell.
- **The temperature has almost no resolution.** P sits between 0.60 and 0.61, its AUC is 0.50, and
  its flagged slice is off by −0.134. Gate 4's control fails Gate 5.

Files: `validation.json`, `by-head/*.json`, `references.txt`, `calibration.json`, `metrics.json`,
`report.md`, `inputs.json`, `plan.json` and `run.json`. `errors.npz` stays on the results branch.
