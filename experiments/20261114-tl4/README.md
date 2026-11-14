# Spec 016 (study L): the test on seed 341 (2026-11-14)

CI run 43563825793 (`timelate/tl-e-test`, commit fbda7fa, clean tree, plan
`configs/timelate/tl-e.json` `82cd70ee…` as registered), scored once, with the controls'
validation record (`experiments/20261113-tl4-val/`) as the scorer requires. 2,860 periods;
the classical controls and the three trained seeds on the same periods. **Every table is
generated**: `tables.md` (`scripts/research/tl4_tables.py`), `learned.md`
(`tl4_learned_tables.py`) and `supplement.md` (`tl4_supplement.py`), all from `summary.json`
and the period records; the figures below are copied from them and
`tests/unit/test_timelate4.py` checks that every interval quoted here is in one of them.
Per-row errors (and tracks for the first 20 periods of each split) are on the results
branch `results/timelate-tl-e-test-43563825793`.

Ratios are paired per period (geometric mean of the per-period ratio of median relative
range error, 95% period bootstrap). "Control ÷ learned" above 1 means the learned track is
better.

## The registered outcome

**Learning is shown on no split, and there is harm on Annex B data. By the registered
rule: the classical controls stand as the time-late system and the learned track stops.**

| | Split | Verdict | Declared control ÷ learned (three seeds) | Hedged track ÷ learned (three seeds) |
| --- | --- | --- | --- | --- |
| L-c | Shifted prior | not shown | 0.82 [0.73, 0.91], 0.80 [0.71, 0.90], 0.82 [0.73, 0.91] | 0.76 [0.67, 0.85], 0.74 [0.66, 0.83], 0.75 [0.67, 0.85] |
| L-c | Shifted prior 2 | not shown | 0.87 [0.79, 0.96], 0.87 [0.79, 0.95], 0.94 [0.85, 1.05] | 0.91 [0.83, 1.01], 0.90 [0.82, 0.99], 0.99 [0.89, 1.09] |
| L-c | Correlated errors | not shown | 0.83 [0.74, 0.92], 0.83 [0.74, 0.92], 0.84 [0.75, 0.94] | 0.82 [0.73, 0.92], 0.82 [0.73, 0.92], 0.83 [0.74, 0.93] |
| L-c | Outliers | not shown | 0.78 [0.70, 0.89], 0.77 [0.68, 0.88], 0.81 [0.71, 0.91] | 0.80 [0.71, 0.91], 0.79 [0.70, 0.90], 0.83 [0.73, 0.93] |
| L-c | Bias (absent from training) | not shown | 0.98 [0.88, 1.09], 1.00 [0.90, 1.09], 0.97 [0.86, 1.07] | 0.98 [0.88, 1.09], 0.99 [0.90, 1.09], 0.97 [0.87, 1.07] |
| L-d | Annex B | **harm** | 0.82 [0.74, 0.90], 0.81 [0.73, 0.89], 0.82 [0.75, 0.91] | 0.84 [0.76, 0.93], 0.83 [0.75, 0.93], 0.85 [0.77, 0.94] |
| L-d | Held course | no harm; the learned track wins | 1.06 [1.01, 1.11] for every seed | 1.51 [1.36, 1.67] for every seed |

The reported learned track (the arc model fitted from the model's output) is about 20%
worse than the classical control on Annex B data, under a shifted prior, with correlated
errors and with outliers, for every seed; equal to it under a bias neither side was built
for; and better on targets that never manoeuvre. The three seeds agree to within their
intervals everywhere.

**L-a** (soundness) holds on this seed too: 0.95 of the bound on tight rows, every
true-history fit converged, 0.085 of references held on Annex B.

## Median period range error

| Split (scored periods) | C″ as a track | Standing search | Declared control | Hedged control | Learned, own track (seed 1) | Learned, arc read-out (seeds 1, 2, 3) | True history |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Annex B (374) | 0.085 | 0.041 | 0.040 | 0.040 | 0.050 | 0.047, 0.049, 0.046 | 0.029 |
| Shifted (365) | 0.141 | 0.094 | 0.088 | 0.078 | 0.084 | 0.112, 0.117, 0.110 | 0.044 |
| Shifted 2 (375) | 0.068 | 0.029 | 0.027 | 0.029 | 0.043 | 0.033, 0.033, 0.032 | 0.024 |
| Held course (263) | 0.016 | 0.031 | 0.017 | 0.024 | 0.025 | 0.015, 0.015, 0.015 | 0.015 |
| Correlated, mild (186) | 0.324 | 0.115 | 0.082 | 0.083 | 0.093 | 0.110, 0.111, 0.113 | 0.064 |
| Correlated (278) | 0.272 | 0.136 | 0.102 | 0.101 | 0.106 | 0.133, 0.129, 0.125 | 0.076 |
| Outliers (278) | 0.248 | 0.077 | 0.042 | 0.040 | 0.062 | 0.060, 0.057, 0.055 | 0.046 |
| Outliers, harsh (186) | 0.468 | 0.125 | 0.054 | 0.054 | 0.071 | 0.056, 0.058, 0.059 | 0.070 |
| Bias (278) | 0.117 | 0.059 | 0.058 | 0.060 | 0.065 | 0.064, 0.059, 0.065 | 0.049 |
| Whole engagements (60) | 0.073 | 0.037 | 0.039 | 0.039 | 0.043 | 0.044, 0.046, 0.048 | 0.021 |

## L-b: what the classical controls did (standing search ÷ declared control)

| Split | Ratio | Gap to the reference closed | Forecast | Held? |
| --- | --- | --- | --- | --- |
| Outliers | 1.68 [1.46, 1.94] | 1.20 [0.89, 1.61] | about 1.5; over 0.6 | Yes |
| Outliers, harsh | 2.44 [2.03, 3.00] | 1.55 [1.23, 2.08] | – | – |
| Correlated | 1.33 [1.16, 1.53] | 0.51 [0.30, 0.69] | about 1.3; about 0.5 | Yes |
| Correlated, mild | 1.28 [1.11, 1.48] | 0.46 [0.20, 0.69] | – | – |
| Shifted | 1.03 [0.96, 1.09] | 0.08 [-0.01, 0.18] | 1.0 to 1.1; under 0.2 | Yes |
| Shifted 2 | 1.08 [1.03, 1.14] | 0.29 [0.09, 0.58] | 1.1 to 1.2 | Just under |
| Held course | 1.70 [1.48, 1.95] | 0.35 [0.20, 0.48] | – | – |
| Annex B | 1.09 [1.02, 1.18] | 0.24 [0.06, 0.41] | – | – |
| Bias | 1.00 [0.96, 1.05] | -0.11 [-0.48, 0.09] | – | – |

Editing wild bearings removes the outlier gap (the control is at or below the reference,
which is fitted to the bearings as given). The effective sd closes half the
correlated-error gap. Under a shifted prior the control gains almost nothing and stays at
1.79 [1.61, 1.99] times the reference: **the one large gap is still open, and the learned
model did not close it either.**

## Reading

1. **The learned model is a good estimator that the classical system beats.** Its arc
   read-out is better than C″ read as a track on every manoeuvring split (by 1.4 on the
   shifted split to 6.6 with 5% outliers; `learned.md`), on 12.5 million simulated periods
   and $14 of GPU time. It is still about 20% behind a search that knows the motion model.
2. **The forecast was right about the outcome and wrong about the read-out.** "Shown on
   none" and "harm on Annex B more likely than not" held. But the record forecast that the
   arc read-out would improve on the model's own track "on most splits"; it does so on
   Annex B, shifted 2, held course and harsh outliers, and makes it *worse* under the
   first shifted prior (own track 0.084, read-out 0.112) and with correlated errors (0.106
   against 0.133). The read-out fits Annex B's prior and the arc model at the model's
   manoeuvre times; where the model missed manoeuvres, the fit has nowhere to put them.
3. **The model's own track, not the registered comparison, equals the control where the
   control is weakest**: declared control ÷ own track is 1.01 [0.90, 1.13] under the
   shifted prior and 0.99 [0.88, 1.13] with correlated errors (seed 1; the others agree),
   against 0.71 [0.63, 0.80] on Annex B and 0.60 [0.53, 0.68] on shifted 2. Against the
   hedged track it is not separated on the shifted split (0.93 [0.84, 1.04]). It never
   wins. This is "reported beside" and decides nothing.
4. **The model is cautious about manoeuvres.** At a probability threshold of 0.5 (never
   tuned) it misses more manoeuvres than the control (0.31 against 0.25 on Annex B, 0.58
   against 0.49 shifted), declares far fewer false ones (0.03 a period against 0.20), and
   calls a one-manoeuvre target quiet in 0.29 of cases against 0.14. On targets that never
   manoeuvre it declares one in 0.01 of periods (control 0.08, standing search 0.49).
5. **Bias**: neither side was built or trained for it, and they are equal. The held-out
   condition shows no transfer advantage for the model and no collapse.
6. **Hedging**: the hedged classical track is better than the declared one under the
   shifted prior (1.08 [1.04, 1.13]), worse on held course (0.70 [0.64, 0.77]), and not
   separated elsewhere.

## Forecasts

| Forecast (decision record) | Result | Right? |
| --- | --- | --- |
| L-a passes | 0.95; passes | Yes |
| Search ÷ control: outliers about 1.5, correlated about 1.3, shifted 1.0 to 1.1, shifted 2 1.1 to 1.2 | 1.68, 1.33, 1.03, 1.08 | Three of four (shifted 2 just under) |
| Gap closed: outliers over 0.6, correlated about 0.5, shifted under 0.2 | 1.20, 0.51, 0.08 | Yes |
| Learning shown on no split; one chance in four on the shifted split | Shown on none; every seed loses there | Yes |
| Harm on Annex B more likely than not; the read-out may avoid it | Harm, with the read-out | Outcome yes; "may avoid" no |
| The read-out improves on the own track on most splits | Clearly better on four splits, worse on three, about equal on three (`supplement.md`) | No |

## Not delivered, and weaknesses

- **The manoeuvre threshold of the model (0.5) was never tuned**, while the control's
  margin and quiet probability were tuned on seed 338. A tuned threshold might reduce the
  misses that hurt the read-out. The registration fixed 0.5; the asymmetry is real.
- **The read-out used Annex B's prior only**, while the control pools a broadened prior.
- **The budget**: 12.5 million periods a seed on a T4. The monitor curve was still falling
  slowly at the end. This is a null at $14, not a limit on what a larger model or longer
  training could do.
- **A Huber cost and a whitened fit were not built** (editing and an effective sd stand in
  for them); the correlated-error control knows the generator's error family; the evidence
  faults at the edges of the prior's support are not repaired (decision record).
- The reference is held to the true times in 18% to 27% of periods on the shifted,
  correlated and outlier splits; the "gap closed" shares there read against it.
- Efficiency by slice is in `learned.md`; the tracks stored for plotting are on the
  results branch and not yet drawn.
- One simulator, one test seed, splits drawn from one seed, the error splits being the
  same engagements under different errors.

## What this supports

- The classical control (`ctl`, declared at margin 1 with a 1% quiet probability) is a
  better time-late system than the standing search wherever the bearing errors are not as
  assumed, and on quiet targets, at no cost on Annex B data.
- A learned whole-period model of this size and training does not beat it anywhere, and
  loses to it where the simulator's assumptions hold.
- It does **not** show that learning cannot help under a shifted prior: the model's own
  track is level with the control there, the read-out is what loses, and the gap to the
  reference (1.8) is open for both.

## Corrections after the panel (2026-11-14; `review.md`, five approve with findings)

The registered outcome stands. The following statements above are corrected; figures
marked "panel" are the reviewers' recomputations and are in `review.md`, not in the
generated files.

- **"About 20% worse" is a tail.** The median per-period ratio of control to read-out is
  1.00 on every split (`summary.json`, `median_ratio`); the read-out is over twice as bad
  in 20% to 27% of periods and over twice as good in 9% to 13% (`learned.md`). The whole
  loss is in the periods where the model declares fewer manoeuvres than the control;
  where the counts agree the two are level (panel). The untuned threshold of 0.5 is
  therefore the headline, not a footnote: **the registered comparison measured the
  model's manoeuvre detector against the evidence search.**
- **"The learned track stops" means this model with this read-out.** A search started
  from the model was not registered; on tuning data it equals the control at a third of
  the search time and does not beat it (panel).
- **"Harm"** is the rule's word. The read-out is level with the control in the median
  period and 1.8 times better than C″.
- **The held-course "win" is not a learned track**: where both declare no manoeuvre the
  two are the same fit; the 1.06 is the control's false manoeuvres in 23 of 299 periods.
- **Reading 3 and the last "supports" bullet**: the own track is level with the control
  under a shifted prior in range only (course 0.79, speed 0.77; panel), and the pooled
  figure hides a win where the bound is loose and a loss by nearly three where it is
  tight. "It never wins" is false by slice; the slices are post hoc.
- **The control's claims are narrowed.** It is better with outliers and with correlated
  errors of the generator's family and on quiet targets; under bias it is 1.00
  [0.96, 1.05]. "At no cost on Annex B" becomes "no range cost separated over three seeds
  (0.96 to 1.09)"; it calls a one-manoeuvre target quiet more often, markedly so with
  correlated errors (0.29 against 0.05; `supplement.md`).
- **The L-b table** gave the ratio for the declared control and the gap closed for the
  undeclared one; on the outlier splits the "gap closed" is read against a reference
  fitted to unedited bearings and means only that the control beats it. The 1.79 times
  the reference on the shifted split is 1.7 to 2.1 by how the reference is fitted (panel).
- **The mismatch splits** lie inside the model's training ranges (bias excepted, and bias
  is the mildest held-out condition): the model lost in-distribution.
- **Reading 4** quotes the model's own spans; the read-out's are 0.34 missed and 0.08
  false on Annex B. **Reading 6**: on shifted 2 the hedged track is worse than the
  declared one (0.96 [0.92, 1.00]), separated.
- **"Every table is generated"** is not true of the medians table: its declared and hedged
  control columns were taken from `summary.json` by hand (all correct).
- **Addendum 2** is wrong that shard size can reach C″ only: the control's searches start
  from C″'s track. Not measured.
- **Not delivered, added to the list above**: a working prior-mismatch diagnostic (the one
  computed is not a Bayes factor and is not cited); candidate calibration under the
  broadened prior; the export check on the trained models; IMM and EKF tracks beside; the
  weights' digests in the record; unit tests for the runner and the scorer.
- **The three seeds** share the training stream and differ in initialisation only.

## Made good afterwards (spec 017, 2026-11-14)

- **The weights scored** (`shard-headers.json`, from the test run's shard artefacts by the
  workflow `headers/**`, results branch `results/headers-tl-e-test-43604889022`): all 241
  shards scored the same three checkpoints, `9767a4a0…`, `ebd545a8…` and `802cdfcf…`, which
  are the training records' (`experiments/20261114-tlm-runs/`); one plan digest, one code
  digest, one commit, clean, 2,860 periods.
- **The export check on the trained models**
  (`experiments/20261114-tlm-runs/export-check.json`, `scripts/research/tlm_export_check.py`):
  the ONNX export of each seed, run by onnxruntime on CPU on 32 periods of the training
  stream's monitor slice, agrees with the trained model to 8.3e-5, 4.4e-5 and 3.4e-5 (the
  toy model's test asks 1e-5; the bound here was set at 1e-4 before the check ran).
- **Tests** for the split readings and the controls-record guard:
  `tests/unit/test_timelate5.py`. `run_shard4` itself still has no unit test (a single
  period takes about a minute); spec 017's runner calls it on every period it scores.
- IMM and EKF tracks beside, and a reference fitted to edited bearings under outliers, are
  in spec 017's runs, not added to this record.
