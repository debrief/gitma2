# Gate D validation report (spec 004 T023): the phase stops at validation

Train run 41423163916 (`train/gd-a`, plan `configs/gate-d/plan.json`, decision
`experiments/20261102-gd-decision/decision.json`), validation run on `validate-gd/41423163916`
(`gd-validation.yml`). Validation seed 304, σ = 1° G5 rows, 10,000-scenario split.

**Validation rule (Annex A §A.5): no variant is carried.** Test seed 305 is not generated and
stays reserved. The models are in `../20261102-gd-a-models/`.

| | Median range error, all G5 rows | Settled G5 rows |
| --- | --- | --- |
| batch least squares | 12.10% | 6.76% |
| IMM (frozen) | 9.52% | 7.50% |
| EKF (frozen) | 10.01% | 7.37% |
| causal detector (gd-causal-s1, carried seed) → physics layer | 11.48% | 6.58% |
| time-late detector (gd-late-s2) → physics layer | 26.83% | 16.04% |
| oracle (truth spans, speed prior) | 5.21% | 4.03% |

What failed, for the carried causal seed:

- **D-delay and D-miss.** p_change never reached the registered threshold 0.5 on any row of any
  of the seven detectors. They raised no alarm, detected no manoeuvre and flagged no held-leg row.
  The controls were tuned to that 0% rate, so their thresholds went to their maxima and they are
  silent too (CUSUM 1, EKF CUSUM 3, GLR 0 and IMM 34 detections out of 8,943 spans). D-delay is
  therefore +∞ and D-miss is inconclusive.
- **D-downstream-all.** The ratio to the IMM is 1.207 [1.151, 1.265]: the detector beats batch
  least squares (0.95×, recovering 9% of the least-squares → oracle gap) but not the IMM.
- **Passed:** D-false (0%), and D-downstream-settled on range 0.974, course 0.982 and speed 0.975
  × batch least squares.

The time-late variant fails everything downstream (2.8× the IMM; settled 2.4× batch least
squares). It is fed by the last row's question and the whole window: with almost no exported
knot, that is one leg fitted across later manoeuvres. FR-015 (time-late at least as good as
causal) fails.

**Why no alarms** (`pchange-gd-causal-s1.json`, from `scripts/research/gd_pchange.py` on the first
1,000 validation scenarios). The maximum p_change in a scenario has median 0.057 and maximum
0.187. Inside the manoeuvre windows its median is 0.055, about the same, and only 2.7% of spans
reach 0.1. The now head learned close to the base rate, so it has no usable detection skill at the
60 s scale. ECE stays about 0.02, so p_change is calibrated and uninformative. Segmentation recall
at the 0.5 export threshold is 3–7%.

For comparison, the frozen IMM's mode probability at its natural threshold 0.5 detects 7.5% of
spans (669 of 8,943) at a 0.28% held-leg false-alarm rate.

The follow-on is fixed by the decision record (Annex A §A.6): Gate D fails otherwise than on D-false
only, so the result is published and Gate 2 proceeds with the CUSUM/GLR segmenter.
