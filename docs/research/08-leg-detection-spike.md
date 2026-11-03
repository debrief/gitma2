# Leg-detection spike: detectors scored as detectors

Status: research spike on validation, 3 November 2026. The owner asked for detection to be judged
on detection, not only through TMA error. SRD Annex A §A.3 already defines the metrics (delay,
miss rate, held-leg false alarms, kind, segmentation F1). Gate D gated three of them. Note 07's
pilot had drifted to downstream error alone. Nothing here is trained, pre-registered or scored on
test data. Test seed 305 stays reserved, and Gate D's verdict and criteria are unchanged.

Code: `scripts/research/leg_spike.py`, with shared confirmation in `src/tma2/detect/confirm.py`.
Records: `experiments/20261103-leg-detection-spike/`.

## 1. Question

Which detector, at which operating point, should segment the history for Gate 2? Annex A §A.6
says Gate 2 uses "the CUSUM/GLR segmenter at an operating point its spec declares". This spike
supplies the evidence for that choice.

## 2. Method

**Data.** The σ = 1° scenarios of validation seed 304, in file order:
- **Tuning set:** the first 500, the rows note 07's pilot was tuned on.
- **Scoring set:** the next 1,000, untouched until now.

Thresholds come from the tuning set only. Every figure below is from the scoring set.

**Candidates.** All are causal: row k uses bearings up to k.

| Detector | What it is |
| --- | --- |
| CUSUM | Gate D's gated control: CUSUM on per-timestep batch least squares innovations |
| GLR | Gate D's gated control: two-leg GLR over the last 30 rows, linearised at the whole-history fit |
| IMM μ_CT | the frozen IMM's coordinated-turn probability |
| split | note 07's steady-leg split statistic (W = 36, linearised at the window's own fit) |
| split + confirm | split alarms nominate; the physics layer's whole-history cost confirms and places a knot (τ = 13.8) |
| GLR + confirm | the same confirmation with GLR nominations |
| Gate D detector | the learned detector, from Gate D's records (it never raised an alarm) |

**Operating points.** Per-row statistics are thresholded at 1%, 3%, 5% and 10% false alarms on
held-leg rows. A held-leg row is not inside a manoeuvre, at least 300 s after the last one
(Annex C §C.5), and k ≥ 36. The confirmed detectors are set by their nomination rate. Their own
false-alarm rate is measured. Each is then compared with the GLR and the split statistic re-tuned
to that same rate. That re-tuning is done on the scoring rows, which favours the controls, as
Annex A §A.2 intends.

**Metrics** (Annex A §A.3, matched at ±60 s):
- **Detection.** A manoeuvre is detected if an alarm falls between its start and 300 s after its
  end (Annex A). Onset detection also requires the alarm episode to *begin* in that window. A
  statistic that is already raised then gets no credit with zero delay. CUSUM is the case in
  point after a first manoeuvre.
- **Delay:** median and P90, by kind and by turn size.
- **False alarms:** the fraction of held-leg rows alarmed, the fraction of held-leg G5 rows
  alarmed (Gate D's D-false), and alarm episodes per hour of held leg.
- **Segmentation, for detectors that export knots:**
  - Annex A's boundary F1. Truth has a knot at each span's start and end. A one-knot-per-
    manoeuvre detector can match only about half of them.
  - A span F1: a span counts as segmented if a knot falls within its extent ±60 s.
  - Localisation.
- **Detectability.** Each manoeuvre's cost drop when its true knots are added to the physics
  layer, with the other spans' knots in place, measured 300 s after it ends. This is χ² with
  4 degrees of freedom. Below 13.3 (the 1% point) the bearings carry almost no evidence of the
  manoeuvre, and no detector should be blamed for missing it.
- **Downstream check:** median range, course and speed error of the physics layer fed by each
  confirmed detector's knots, against the IMM and batch least squares, on all and settled G5
  rows. Scenario-clustered paired bootstrap at 97.5%.

<!-- RESULTS -->
