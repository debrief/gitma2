# Leg-detection spike: detectors scored as detectors

Status: research spike on validation, complete 3 November 2026. The owner asked for detection to be judged
on detection, not only through TMA error. SRD Annex A §A.3 already defines the metrics (delay,
miss rate, held-leg false alarms, kind, segmentation F1). Gate D gated three of them. Note 07's
pilot had drifted to downstream error alone. Nothing here is trained, pre-registered or scored on
test data. Test seed 305 stays reserved, and Gate D's verdict and criteria are unchanged.

Code: `scripts/research/leg_spike.py`, with shared confirmation in `src/tma2/detect/confirm.py`
(identical knots to note 07's inline version, checked on 12 scenarios).
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

## 3. Results

Scoring set: 1,000 scenarios, 1,761 manoeuvre spans (1,469 course, 292 speed), 3,354 G5 rows
(1,535 settled). Records: `experiments/20261103-leg-detection-spike/spike.json`.

### 3.1 Most spans leave almost no trace in the bearings

| Detectability (χ², 4 dof) | 0–13 | 13–50 | 50–200 | ≥ 200 |
| --- | --- | --- | --- | --- |
| Spans | 714 (41%) | 358 | 378 | 311 |
| of which speed changes | 236 | 39 | 15 | 2 |

81% of speed changes and 33% of course changes fall below the 1% point. No causal detector
can be expected to find them, and their misses should not count against one.

### 3.2 Per-row statistics, tuned on held-leg rows

Onset recall, against what chance alone gives at that alarm rate (a statistic that flickers on
held legs "detects" whatever falls in Annex A's ~36-row window):

| Detector | FA held rows | FA held G5 rows | Alarms / h held | Onset recall | Chance | Median delay |
| --- | --- | --- | --- | --- | --- | --- |
| split @ 5% | 5.0% | 4.7% | 5.9 | 0.65 | 0.58 | 110 s |
| GLR @ 5% | 4.9% | 12.6% | 3.8 | 0.78 | 0.51 | 80 s |
| IMM μ_CT @ 5% | 5.5% | 14.8% | 1.0 | 0.58 | 0.14 | 170 s |
| CUSUM @ 5% | 4.5% | 12.2% | 0.2 | 0.15 | 0.02 | 210 s |
| split @ G5 5% | 4.6% | 4.3% | 5.5 | 0.63 | 0.55 | 110 s |
| GLR @ G5 5% | 2.2% | 5.4% | 2.2 | 0.57 | 0.30 | 110 s |
| IMM μ_CT @ G5 5% | 1.9% | 5.8% | 0.4 | 0.40 | 0.06 | 180 s |

- **CUSUM is not a usable segmenter here.** It stays raised after a first manoeuvre: recall
  0.23 at 5%, onset recall 0.15.
- **GLR and the IMM put their false alarms on G5 rows**, just after the zig, where Gate D's
  D-false counts them. The ranking depends on which rows the false-alarm rate is matched on.
- **The split statistic's recall is mostly chance.** It alarms in short, frequent episodes.
  The IMM's is the most genuine per alarm, but slow.

### 3.3 Confirmation

Each nominator alarms on 20% of the tuning set's held rows. τ = 13.8 for every configuration.

| Configuration | FA held rows | FA held G5 rows | Alarms / h | Onset recall | Chance | Median delay | Knots / scenario | Knot precision | Span F1 | Annex A boundary F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| split 10% + confirm | 0.5% | 1.2% | 0.50 | 0.49 | 0.06 | 190 s | 1.15 | 0.71 | 0.55 | 0.35 |
| split 20% + confirm | 0.6% | 1.6% | 0.53 | 0.55 | 0.07 | 190 s | 1.25 | 0.75 | 0.62 | 0.40 |
| split 40% + confirm | 1.0% | 2.7% | 0.50 | 0.58 | 0.06 | 210 s | 1.29 | 0.76 | 0.63 | 0.42 |
| **GLR 20% + confirm** | 0.9% | 3.1% | 0.33 | **0.59** | 0.04 | 200 s | 1.23 | 0.81 | **0.65** | 0.43 |
| split alarms as knots @ 5% | 5.0% | 4.7% | 5.9 | 0.65 | 0.58 | 110 s | 6.6 | 0.19 | 0.26 | — |

GLR 20% + confirm in more detail:
- **By kind:** onset recall 0.65 for course changes, 0.28 for speed changes.
- **By turn size:** 0.57 at 30°–60°, 0.67 at 60°–90°, 0.71 at 90° or more.
- **By detectability band:** 0.26, 0.75, 0.83, 0.86.
- **Localisation:** the median knot is 20 s from the true one.

The Gate D detector (`experiments/20261102-gd-a-val/gd/metrics.json`) raised no alarm. Its
miss rate is 1.0 and its boundary F1 0.06.

**Against controls re-tuned on the scoring rows to the same false-alarm rate** (miss-rate
difference, confirmed − control, 97.5% interval):

| Matched on | Control | GLR 20% + confirm | split 20% + confirm |
| --- | --- | --- | --- |
| held rows | GLR | −0.28 [−0.31, −0.24] | −0.30 [−0.33, −0.26] |
| held rows | split | −0.26 [−0.29, −0.22] | −0.26 [−0.29, −0.22] |
| held rows | IMM μ_CT | −0.27 [−0.31, −0.24] | −0.28 [−0.31, −0.24] |
| held G5 rows | GLR | −0.15 [−0.19, −0.11] | −0.31 [−0.34, −0.27] |
| held G5 rows | split | **−0.01 [−0.05, 0.02]** | −0.11 [−0.14, −0.07] |
| held G5 rows | IMM μ_CT | −0.26 [−0.29, −0.22] | −0.31 [−0.35, −0.28] |

At the same false-alarm rate, confirmation removes 10–31 percentage points of misses on every comparison but one; against the GLR on held rows, misses fall from 0.67 to 0.39. The
exception: matched on G5 rows (3.1%), the split statistic alone ties GLR + confirm on raw
recall. Of the split statistic's 0.58 onset recall there, chance accounts for 0.48. Of the
confirmed detector's 0.59, chance accounts for 0.04.

### 3.4 Downstream check

These are the physics layer fed by each detector's knots, with the speed prior.

| | Range all | Course all | Speed all | Range settled | Course settled | Speed settled |
| --- | --- | --- | --- | --- | --- | --- |
| batch least squares | 12.8% | 43.4° | 2.10 kt | 7.1% | 3.6° | 1.02 kt |
| frozen IMM | 9.8% | 22.5° | 1.88 kt | 7.9% | 7.0° | 1.36 kt |
| oracle (true knots) | 5.4% | 9.9° | 0.78 kt | 4.2% | 1.8° | 0.56 kt |
| split 10% + confirm | 9.1% | 25.9° | 1.45 kt | 5.7% | 2.6° | 0.84 kt |
| split 20% + confirm | 8.5% | 22.2° | 1.31 kt | 5.4% | 2.4° | 0.78 kt |
| split 40% + confirm | 8.1% | 20.8° | 1.26 kt | 5.2% | 2.4° | 0.75 kt |
| **GLR 20% + confirm** | **7.9%** | 21.3° | **1.18 kt** | **5.0%** | 2.3° | 0.74 kt |

Ratios with 97.5% scenario-clustered intervals:

| | vs IMM: range | vs IMM: course | vs IMM: speed | vs LS, settled: range | course | speed |
| --- | --- | --- | --- | --- | --- | --- |
| split 10% + confirm | 0.93 [0.85, 1.02] | 1.15 [1.02, 1.28] | 0.77 [0.71, 0.85] | 0.80 [0.70, 0.89] | 0.72 [0.48, 0.89] | 0.82 [0.71, 0.91] |
| split 20% + confirm | 0.87 [0.78, 0.95] | 0.99 [0.86, 1.10] | 0.69 [0.64, 0.77] | 0.76 [0.65, 0.85] | 0.66 [0.44, 0.86] | 0.76 [0.63, 0.84] |
| split 40% + confirm | 0.83 [0.75, 0.92] | 0.93 [0.81, 1.06] | 0.67 [0.61, 0.74] | 0.73 [0.62, 0.82] | 0.65 [0.43, 0.84] | 0.74 [0.62, 0.82] |
| **GLR 20% + confirm** | **0.81 [0.74, 0.88]** | 0.95 [0.81, 1.06] | 0.63 [0.58, 0.69] | 0.71 [0.61, 0.79] | 0.63 [0.41, 0.80] | 0.72 [0.61, 0.80] |

GLR 20% + confirm closes 42% of the IMM-to-oracle gap in range: 9.8% → 7.9%, against an oracle
of 5.4%. Course ties the IMM. More nomination helps up to 40%, as in note 07's pilot.

### 3.5 Gate D's criteria, applied informally

Annex A §A.5's tests, applied to GLR 20% + confirm. This is not a gate: these are validation
rows, the configuration was not pre-registered, and the controls were re-tuned on the scoring
rows.

| Criterion | Value | Would pass? |
| --- | --- | --- |
| D-delay (median, / best of CUSUM and GLR at matched FA) | 190 s against 100–110 s (GLR) and 80 s (CUSUM, recall 0.05) | **no** |
| D-miss (− best of CUSUM and GLR) | −0.15 [−0.19, −0.11] on G5 rows | yes |
| D-false (held G5 rows flagged) | 3.1% (point; no interval computed) | likely |
| D-downstream-all (range / IMM) | 0.81 [0.74, 0.88] | yes |
| D-downstream-settled (/ LS, wholly below 1.1) | 0.71, 0.63, 0.72; upper bounds ≤ 0.80 | yes |

Confirmation waits for evidence, and that costs delay. The medians are also taken over different
spans: the confirmed detector finds more of the harder spans, and finds them later.

## 4. Recommendation for Gate 2

**Segmenter: GLR + confirm.**
- **Nominate:** the Gate D GLR (W = 30, at the per-timestep least-squares states). Its
  threshold alarms on 20% of the held-leg rows of a tuning set, taken from validation.
- **Confirm:** the physics layer's whole-history cost.
  - Candidates every 3 rows over the last 36.
  - τ = 13.8.
  - Knots carry the speed-continuity prior.
- **Code:** `tma2.detect.confirm.confirm_knots`.
- **Add:** re-test while an episode stays raised (§5 item 10). It must be measured on
  validation before the Gate 2 spec fixes it.

Annex A §A.6 asks for "the CUSUM/GLR segmenter at an operating point its spec declares". This is
the GLR segmenter with a confirmation step. The Gate 2 spec will declare the step, its
nomination rate and τ. If the owner reads the confirmation step as a departure from §A.6, it
becomes an annex amendment, and the owner merges that.

**Why not the alternatives:**
- **CUSUM** fails as a segmenter.
- **GLR alone at 5%** alarms on 13% of held G5 rows, and half its recall is chance.
- **The split statistic** detects mostly by chance.
- **The IMM** is slow and misses speed changes.
- **Split + confirm** is close behind. It would be the choice if the GLR's per-timestep least-squares states were unavailable.

## 5. Critical assessment

1. **Validation, not a gate.** Thresholds came from the tuning set, but four confirmed
   configurations were compared on the scoring set and the best is recommended. The intervals
   do not include that selection. Gate 2's fresh test seed is the real check.
2. **Only τ = 13.8 and 20% nomination were run for the GLR.** The split statistic still gained
   at 40%, so GLR at 40% may be better. It was not run (≈ 1.5 h of compute).
3. **Delay is the cost.** The median is 190–210 s against 80–110 s for raw statistics. For a
   tracker that must react to a turn, this matters. For Gate 2, which scores at zig + 5 to 20
   min, it matters less.
4. **The headroom is in detectable spans, not in the rest.** Recall is 0.83–0.86 in the bands at
   50 and above, so 14–17% of clearly visible manoeuvres are still missed or rejected. The 41%
   below 13 are out of reach for any detector.
5. **Speed changes are mostly invisible** (onset recall 0.28; 81% below the detectability
   floor). The speed prior is what keeps settled speed at 0.74 kt, not detection.
6. **19% of knots are off-span.** Many are late placements of a real manoeuvre (sample 555 in
   the deck). Some are genuine false knots (sample 932, a held-course scenario: 2 of 138 such
   scenarios got a knot). Each costs a velocity increment's variance.
7. **Annex A's detection window rewards flicker.** [start − 1, end + 30] is about 36 rows, so a
   statistic alarming on 5% of rows in short bursts gets about 0.55 recall by chance. Future
   specs should report onset recall against the chance floor.
8. **Downstream for raw-GLR knots was not run.** That confirmation is needed rests on the
   detection metrics: knot precision 0.19 for raw split alarms, against 0.81 confirmed.
9. **Cost.** Confirmation runs about 5 s per scenario on one core (12 candidate solves per
   episode). A tracker running in real time at 10 s per bearing can afford it. A Gate 2 training
   loop cannot: knots must be computed once, offline, per scenario.
10. **Why detectable spans are missed.** 117 of 689 spans with detectability ≥ 50 have no knot
    on them. The causes:
    - **60 (51%): already raised.** The GLR was already above its threshold when the manoeuvre
      began, often since the ownship zig. Confirmation runs only at an episode's first row, so a
      manoeuvre inside a running episode is never tested. Sample 513 in the deck is one.
    - **45: nominated but not accepted.** Either the confirmation rejected the knot, or it put
      the knot off the span.
    - **12: never nominated.** In 11 of these, the GLR is 0 throughout, because the per-timestep
      least-squares states it is linearised at are invalid (long range).

    Re-testing while an episode stays raised (say every 6 rows) is a cheap fix for the first
    group, and Gate 2's spec should include it.
11. **The detectability measure is an oracle quantity.** It uses true knots, measured 300 s
    after the end. It describes the data, not a detector, and it understates evidence that
    arrives later.
