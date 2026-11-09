# Gate 5 decision record (spec 010 T014)

`decision.json` (a `Gate5Decision`) is committed before any spec 010 training on CI and before
test seed 320 is generated. It binds `configs/gate5/g5-a.json` by SHA-256 (`3febde6f…`), and the
plan is never edited after this. It also binds the unsettled proxy, `proxy.json`
(`6248deea…`). Later additions are new files in this folder: `carried.json` after validation, and
`test-digest.json` after seed 320. Neither may change a criterion once any test result exists.

## Fixed here

- **The SRD:** the §5 Gate 5 row, proposed on this branch; the owner merges.
- **The carried estimator:** Gate 2's E, e-s3, frozen. Its points are copied (G5-e).
- **The statement** (research R2, R3), in the truncated form:
  - the arc X = min(45°, 1.96 · a · sd);
  - a von Mises of concentration κ = 1/(a · sd)², truncated to ±X and carrying exactly P;
  - a uniform remainder outside the arc;
  - P after a Platt map fitted on tuning rows;
  - range and speed half-widths c · sd.
- **The proxy** (R1): a logistic score on these features:
  - the residual bias over the last 1, 2 and 5 min;
  - the residual χ² over 10 min;
  - C's open flag;
  - E's three log sds;
  - the minute.

  It was fitted on tuning rows for the truth "not settled". Its threshold flags 26.8% of tuning
  rows, the tuning base rate.
- **The controls (R6):**
  - **The temperature:** per cell (minute × open), stated on sd^β with β per quantity from the
    grid 1.0…0.3, fitted on tuning rows.
  - **The classical rule:** quadratics in E's three log sds, plus linear proxy terms for P, fitted
    on the training stream (seed 318, 39,054 rows).
  - **The encoder-only shuffled head**, scored at best and last epoch.
- **The head:** the classical rule plus bound · tanh(MLP). The MLP has width 32 and bound 1, and
  reads E-w's encoder state, the sds, C's code and the proxy design. Training:
  - trained on the stream;
  - early-stopped on tuning ordinals 0–499;
  - Adam at 1e-3, 1,024 rows per batch, at most 50 epochs, patience 5;
  - three seeds.
- **Inputs:**
  - feature caches `results/g2predict-g3-feat-stream-42472098077` and
    `results/g2predict-g3-feat-val-42472096319`;
  - proxy caches `results/g5proxy-stream` and `results/g5proxy-val` (`tma2-g5proxy` at 733de07,
    clean);
  - E's validation file `results/g2predict-g3-base-val-42471500526`.
- **Criteria** (R7, as revised by the synthetic check; the "slices" field names the gated slices,
  and the proxy's two states are added from the head's own flags):
  - **G5-a:** range and speed coverage overall wholly within [0.92, 0.98], and per slice not wholly
    outside [0.90, 0.99].
  - **G5-b:**
    - hit − P overall wholly within ±0.04;
    - the slope wholly within [0.75, 1.33];
    - per slice, hit − P not wholly outside ±0.05.
  - **G5-c:** the log gain wholly above 0, and the AUC wholly above 0.55.
  - **G5-d:** the head minus the control of record (the better of the temperature and the
    classical rule) wholly below 0. It is void by the encoder-shuffle rule.
  - **G5-e:** the points identical, and the arc-mass error at most 1e-6.

  Intervals are 97.5%, from 2,000 scenario-clustered resamples, computed by `tma2-g5`.
- **Rules:** the carried seed, the encoder-shuffle rule and the validation rule, as in
  `decision.json`.

## Evidence for the forecast

- **Validation baseline** (`experiments/20261109-g5-base-val/`): Gate 4's statements re-reported
  against Gate 5's bands.
- **Synthetic check** (research R7): a calibrated statement passes G5-b in 100 of 100 datasets, and
  a slice off by 0.15 fails it in 100 of 100.
- **Tuning rows (in sample):**
  - the classical rule scores 2.557 and the temperature 2.667;
  - the classical rule's P spreads 0.29–0.77, with AUC 0.63;
  - an 8-epoch head reaches 2.492.

## Forecast

G5-a pass 0.7, G5-b 0.45, G5-c 0.85, G5-d 0.35, G5-e 1.0; overall about 0.1.

## Disclosures

These are as in `decision.json`. They cover the R1–R4 fits on tuning rows, the smoke run of the
temperature, the classical rule and an 8-epoch head (a dirty tree, outputs not kept), and the
proxy fit. The proxy was fitted under the draft plan (`5b785c8d…`). The fields it reads (the
tuning ordinals, the caches and the proxy caches) are unchanged in the bound plan.
