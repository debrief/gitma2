# Gate 2 on seed 319 (spec 007 T029)

Machine verdict: **G2-a pass, G2-b pass, G2-c pass, G2-d pass** for the carried E (e-s3), on all
4,983 σ = 1° scenarios of seed 319's test split (19,609 G5 rows, 14,403 settled), every
physics-layer solve at 12 knots. The panel's verdict is in `review.md`.

| Check | Measure | Point [97.5% interval] | Limit | Outcome |
| --- | --- | --- | --- | --- |
| G2-a | E / IMM, median range | 0.182 [0.173, 0.192] | wholly below 1 | pass |
| G2-a | E / IMM, median course | 0.252 [0.236, 0.271] | wholly below 1 | pass |
| G2-b | E / one leg, settled: range | 0.166 [0.157, 0.175] | wholly below 1.1 | pass |
| G2-b | course | 0.136 [0.126, 0.148] | wholly below 1.1 | pass |
| G2-b | speed | 0.212 [0.200, 0.225] | wholly below 1.1 | pass |
| G2-c | E's gap recovered (range) | 0.924 [0.915, 0.931] | wholly above 0.5 | pass |
| G2-d | E − C, gap recovered | +0.025 [+0.018, +0.031] | wholly above 0; shuffled rule pass | pass |

Beside it, on the same rows (`report.md`):

| Estimator | Range | Course ° | Speed kt | Range > 50% | Gap recovered |
| --- | --- | --- | --- | --- | --- |
| One leg | 0.580 | 66.95 | 6.31 | 55.5% | — |
| IMM (gated) | 0.567 | 56.52 | 6.03 | 54.8% | — |
| EKF | 0.520 | 59.87 | 5.59 | 51.3% | — |
| Naive | 0.398 | 90.84 | 3.73 | 37.0% | — |
| GLR + confirm | 0.498 | 47.52 | 4.78 | 49.9% | 0.159 [0.117, 0.204] |
| C | 0.116 | 15.14 | 1.61 | 11.5% | 0.899 [0.891, 0.908] |
| **E (e-s3)** | **0.103** | **14.24** | **1.49** | **10.0%** | **0.924 [0.915, 0.931]** |
| E-w alone (ew-s3, reported) | 0.109 | 14.60 | 1.56 | 11.1% | 0.914 [0.905, 0.922] |
| Oracle | 0.064 | 7.51 | 0.94 | 2.5% | — |

E-w alone − C: +0.015 [+0.010, +0.019]. The forecast (decision record) was E − C +0.005
[−0.005, +0.015] with a pass probability of about 0.25; validation gave +0.028 for e-s3.

**How it was made.** Every input on CI from a clean tree, after `carried.json` (4a0cc63):
- seed 319 generated at 4a0cc63, test split `ceee1a18…` (`test-digest.json` beside the decision);
- C's segmentation `results/segment-g2-test-c-42399020222` (495adf8; code `4d2c084f…`, parameters
  `60e6ee63…`);
- GLR + confirm `results/glr-confirm-g2-test-glr-42399055842`;
- E and E-w predictions `results/g2predict-g2-a-test-42406326175` (e7e76a2; weights `a5485318…`,
  as `carried.json`);
- scoring: `score.yml` run 42413661938 at 237c87b (`results/score-g2-a-test-42413661938`, with
  `errors.npz`, 3.8 MB, kept there). `manifest.json` binds the decision, plan, amendments, inputs
  and metrics by digest.

**A diagnostic beside the gate** (panel round 1, geometry): the classical control C′ (C with a
zig veto) is pre-registered in `experiments/20261107-g2-veto/` and run on the same rows; it does
not change this verdict.
