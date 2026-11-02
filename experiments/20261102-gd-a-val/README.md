# Gate D validation report (spec 004 T023): the phase stops at validation

Sources:

- train run 41423163916 (`train/gd-a`, plan `configs/gate-d/plan.json`, decision
  `experiments/20261102-gd-decision/decision.json`);
- validation run on `validate-gd/41423163916` (`gd-validation.yml`, commit 501907b).

The data is validation seed 304: its 10,000-scenario split, scored on the σ = 1° G5 rows (5,014
scenarios, 16,780 rows; 7,620 of them are held-leg or settled rows). The models are in
`../20261102-gd-a-models/`. The panel review is in `review.md`.

**Validation rule (Annex A §A.5): no variant is carried.** Test seed 305 is not generated and
stays reserved. Annex A §A.6 is worded for a Gate D fail; this record reads the validation stop
as a fail, as gitma did for its phase-3 stops. D-delay and D-downstream-all fail outright and
D-false passed, so the branch is "fails otherwise": publish, and Gate 2 proceeds with the
CUSUM/GLR segmenter.

## Results

| Estimator | Median range error, all G5 rows | Settled G5 rows |
| --- | --- | --- |
| batch least squares | 12.10% | 6.76% |
| IMM (frozen) | 9.52% | 7.50% |
| EKF (frozen) | 10.01% | 7.37% |
| causal detector (gd-causal-s1, carried seed) → physics layer | 11.48% | 6.58% |
| time-late detector (gd-late-s2, carried seed) → physics layer | 26.83% | 16.04% |
| oracle (truth spans, speed prior) | 5.21% | 4.03% |

Ratio of median range error over all G5 rows to the IMM's, per seed:

| Variant | Seeds | Ratio |
| --- | --- | --- |
| causal | s2, s1, s3 | 1.193, **1.207**, 1.273 |
| classification-only control (gd-cls) | — | 1.267 |
| time-late | s1, s2, s3 | 2.003, **2.819**, 2.834 |

The carried seed of each variant (the median of three) is in bold. The causal ratios are point
estimates; only the carried seed has an interval.

Checks for the carried causal seed:

| Check | Value | 97.5% interval | Result |
| --- | --- | --- | --- |
| D-downstream-all | 1.207 | [1.151, 1.265] | fail: the detector beats batch least squares (0.95× as a point) but not the IMM, and recovers 9% of the least-squares → oracle gap |
| D-delay | +∞ | — | fail: no detection |
| D-miss | — | — | inconclusive and degenerate (see below) |
| D-false | 0% | — | pass |
| D-downstream-settled, range / course / speed | 0.974 / 0.982 / 0.975 × batch least squares | — | pass |

The classification-only control scores inside the causal range, so as scored (with hard knots)
the downstream loss shows no benefit at this budget. In the soft segmentation it was trained
on, it does help (cause 3).

The time-late variant fails everything downstream: 2.8× the IMM, and 2.4× batch least squares on
settled rows. Its solve uses the whole window and reports the state at the scored row. With
almost no exported knot, that is one leg fitted across the later manoeuvres, which is worse than
batch least squares by construction. FR-015 (time-late at least as good as causal) fails.

**Every detector and every gated control is silent.** No detector reached p_change ≥ 0.5 on a
held-leg row or inside a span's detection window: 0 detections of 8,943 spans and 0 of 7,620
held-leg rows flagged. For gd-causal-s1 the panel confirmed it on every row: the maximum over all
10,000 scenarios is 0.219.

The controls were tuned to that 0% rate, so their thresholds went to their maxima:

| Control | Detections, of 8,943 spans |
| --- | --- |
| CUSUM | 1 |
| EKF CUSUM | 3 |
| GLR | 0 |
| IMM | 34 |

So D-delay and D-miss compare silent with silent. The control thresholds were tuned on the same validation held-leg rows they are
scored on, so their 0% rate is in-sample by construction. These matched thresholds are Gate D comparison
artefacts. They are not a setting for Gate 2's segmenter, whose operating point is for the next
spec to declare. At a 5% held-leg false-alarm rate, research R6 measured the GLR detecting 57% of
spans and CUSUM 10%.

The frozen IMM's mode probability at its natural threshold 0.5 detects 7.5% of spans at its own
0.28% held-leg rate. Swept against held-leg rows on 500 scenarios (TMA reviewer), it detects:

| Held-leg false-alarm rate | Spans detected |
| --- | --- |
| ≈0.3% | 18% (noisy: about 2 of 745 held rows set this threshold) |
| 1% | 29% |
| 5% | 48% |

So 7.5% is a lower bound on what the IMM can detect.

## Why the detector is silent (panel round 1, verified)

The panel found no pipeline error:

- the training stream and the validation pack are bit-identical on 200 scenarios;
- the labels line up with the truth (389 of 389 spans);
- the physics layer with no knots reproduces batch least squares (gd-causal-s3, 0.1212 against
  0.1210);
- the carried detector's outputs and detection records reproduce byte for byte from the committed
  weights.

The silence has four causes.

1. **No evidence from the bearings in the "now" head.**
   - gd-causal-s1's p_change ranks now rows above held rows (AUC 0.87), but only through timing.
     Median p is 0.0006 on held rows before the first manoeuvre, 0.048 on held rows after one,
     and 0.049 on now rows.
   - After zig + 120 s its AUC is 0.51–0.59, and against held rows after a manoeuvre it is 0.53.
   - It is the same at σ = 2°. The per-span maximum is flat across quartiles of the manoeuvre's
     bearing-rate signal (0.0506 → 0.0511).
   - The classification-only control ranks a little better (AUC 0.65–0.74 after the zig). A rule
     that knows only the time since the zig scores 0.66, so that gain is the prior "no manoeuvre
     before zig + 120 s", not bearing evidence. Against constant base-rate predictors its BCE is 0.611
     against 0.720 in total: now 0.066 against 0.089, boundary 0.128 against 0.200 (floor 0.041)
     and kind 0.418 against 0.430.
   - The time-late variant sees the whole window and is at chance or worse after the zig (AUC
     0.45; over all rows against held rows about 0.79, all of it timing; 0.27
     against held rows after a manoeuvre).
   - So this is a learning failure, not a proof that the manoeuvres cannot be seen. The
     least-squares → oracle gap (12.1% → 5.2%) shows that they are identifiable in hindsight,
     and the top quartile of manoeuvre signal should register.
2. **The objective's balance.** On a training batch the encoder's gradient norm is 15.2 from the
   downstream term against 0.016 from now, 0.31 from boundary and 0.08 from kind. The downstream
   term therefore dominates the shared encoder's gradient about 1000:1; clipping at 1.0 only
   scales each step by about 1/15. gd-causal-s1's boundary and kind losses end above a constant
   predictor's.
3. **Soft against hard segmentation.** Training optimises the soft segmentation; the gate scores
   only the knots exported at w_change ≥ 0.5 (FR-014, FR-027, as registered). On 128 rows the
   downstream training loss is as below. It is the capped CRB-normalised squared error, measured
   without an interval; it is not the gate's median range error.

   | Segmentation | Downstream training loss |
   | --- | --- |
   | untrained (≈ batch least squares) | 35.7 |
   | soft, as trained | 27.7 |
   | knots exported at 0.5 (as scored) | 32.0 |

   So the hard export discards about half the learned gain. Soft w_change at scored rows has a
   median maximum of 0.014, and 4.7% of rows reach 0.5. Segmentation recall at the export
   threshold:

   | Detector | Recall |
   | --- | --- |
   | causal s1, s2, s3 | 3.2%, 6.9%, 0.0% |
   | gd-cls | 0.15% |
   | time-late | 1.1–11.1% |
4. **Thresholds near-unreachable by construction.**
   - The now label is positive only inside a span and for 60 s after its start: a base rate of
     about 10% after the zig.
   - Rows from a span's end to end + 300 s are trained as 0, although matching credits a
     detection there.
   - The held-leg weight of 3 deflates p_change. For gd-cls the observed frequency is 1.6–2.0×
     the mean p in every reliability bin. For gd-causal-s1 the bins run 2.5×, 2.1× and 1.7×, and
     its top bin is not deflated. So p ≥ 0.5 needs a true probability of about 0.75.
   - A 0.5 threshold on a BCE against ±60 s triangular targets needs timing certain to a few rows.
   - p_change is therefore deflated, not calibrated. The pooled ECE of about 0.02 is half the base
     rate and includes the trivially easy rows before the zig.
   - None of this is a logit ceiling: the now head's maximum logit is about −1.5 to −2.1, against
     a bound of about 11.

Two seeds were also under-trained. gd-causal-s1 and s2 stopped at the 20-epoch cap with their
best epoch at 17 and the validation loss still falling (28.7 → 25.9). gd-cls stopped on patience
while still improving.

The decision record's architecture check got two items wrong:

- **(1)** For the time-late variant, a detector with no knots is not batch least squares: it
  fits one leg across later manoeuvres.
- **(2)** A detector that never alarms did not fail D-miss, because controls matched to its 0%
  rate went silent too.

A future detector gate needs a floor on the matched false-alarm rate, or a declared operating
point of its own, so that the comparisons cannot be degenerate.

## Reproduction and provenance

The reproducibility reviewer checked:

- the decision record (785bfef) is an ancestor of every training commit (38b1215) and of the
  validation commit;
- the plan, weights, validation-data and amendment digests all match;
- re-running gd-causal-s1 on the full validation split reproduces the committed detector outputs
  and detection records byte for byte.

Reproduce by re-scoring the committed weights, not by retraining. s1's and s2's jobs ran on two
CPU families, so retraining is not byte-identical.

The baseline and downstream predictions are pinned by digest (`baseline-digests.txt`,
`control-digests.txt`). They are regenerated by `gd-validation.yml` from the same commit and
data.

`gd/manifest.json` records `git_dirty: true`. The validation script wrote `work/`,
`amendment.json` and `validation.json` beside the record before `tma2-gd` ran, and
`Experiment` excluded only `gd/`; the data lives outside the repository. The re-run above is
byte-identical. From the commit that adds this README, the script writes the record into its own folder, so
the next run records the true state.

`gd/verdict.json` contains a bare `Infinity` (the +∞ delay). From the same fix on, non-finite
values are named in the detail, and `verdict.json`, `metrics.json` and `validation.json` are
strict JSON. The committed `validation.json` still has bare NaN.

Diagnostics:

- `pchange-gd-causal-s1.json`, from `scripts/research/gd_pchange.py` on the first 1,000
  validation scenarios: the largest p_change is 0.187, and only 2.7% of span windows reach 0.1.
- The AUC and gradient figures above are the panel's (`review.md`).
