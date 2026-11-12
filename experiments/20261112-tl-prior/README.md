# Spec 013: does prior knowledge of manoeuvres separate the histories? (tuning seed 329)

Owner decision 2026-11-11: build a classical estimator that uses Annex B's manoeuvre
statistics. Before a sampler, the cheap test: under those statistics, is the true history
more probable than the wrong one the re-test finds? Never a gate result; same 60 cut periods
as `../20261111-tl-retest/` (57 with determined rows).

Code: `src/tma2/timelate/prior.py` (generator 0.6.0's leg, kind, angle, rate and speed
distributions as a density over a period's history), `retest.log_evidence` (Laplace: fit,
prior at the fit, Occam factor), `retest.choose_kinds`, `retest.ensemble`. Scripts as run:
`scripts/research/tl_retest.py` (now with evidence; `histories.json`), `tl_evidence_read.py`
(`evidence.txt`), `tl_ensemble.py` (`ensemble.json`, `ensemble.txt`).

## 1. Told only which basin, the fit reaches the bound

The arc model fitted from the truth with every manoeuvre's start and duration **free**:
efficiency 1.03, 1.00, 1.17 (range, course, speed); median period range error 0.021. The
exact times are not needed. What is needed is the right history: how many manoeuvres,
roughly where, turning which way.

## 2. The prior does not pick the true history

Log evidence of the true history minus that of the re-test's history (kinds chosen by evidence):

| Re-test started from | Periods | Median | Truth ahead by over 3 | Re-test's history ahead by over 3 |
| --- | --- | --- | --- | --- |
| C″'s transitions | 57 | 0.0 | 0.35 | 0.39 |
| Nothing | 57 | 0.0 | 0.37 | 0.32 |

On the periods where the re-test's range error is over twice the true-history fit's (34
and 35 periods): truth ahead by over 3 in 0.41 and 0.46, the wrong history ahead by over 3
in 0.44 and 0.40. By part, on those periods (truth minus re-test, medians): fit +3.9, legs
−2.9 to −5.2, changes −9.1 to −13.0, Occam +6.1 to +7.1. The true history fits a little
better and pays more than that for its extra manoeuvres. An extra manoeuvre must save
about 12 in log likelihood (24 in cost) to be worth believing, which is where the re-test's
threshold of 20 already was: **the re-test was close to the most probable history all along.**

## 3. Averaging over nearby histories does not help

An evidence-weighted mean over the fitted history, up to two further additions and each
single removal (re-test from nothing, no C″):

| Track | Median period range error | Periods over 10% |
| --- | --- | --- |
| Fitted history | 0.105 | 0.56 |
| Highest-evidence member | 0.111 | 0.53 |
| Evidence-weighted mean | 0.115 | 0.53 |
| True history, times free | 0.021 | 0.11 |

One member holds over 0.9 of the weight in 95% of periods; in 37% it is not the fitted
history. The neighbourhood does not contain the true history, so its mean cannot move
towards it. This says the local ensemble is a poor stand-in for the posterior, not that
the posterior mean would not help.

## 4. Not explained by ownship manoeuvres

True manoeuvres found by the re-test: 0.67 with an ownship turn after them, 0.66 without
(108 manoeuvres; 7 of 60 periods have no ownship turn at all).

## Reading

- The bearings plus Annex B's statistics leave the history ambiguous in roughly half of
  the periods where it matters: the true history and a wrong one with a manoeuvre fewer are
  about equally probable, and they put the target in different places.
- So no estimator that names one history (a test of fit, the causal segmenter, the most
  probable history under the prior) reaches the reference, and the reference (0.02 to 0.035)
  is not a fair target for anything.
- What a system can still do is (a) report that ambiguity, as two or three candidate tracks
  with probabilities, and (b) give the average that minimises error. A model trained on
  millions of engagements may do (b) without being asked; whether spec 012's regressor does
  is untested, and its panel found a range prior the more likely source of its margin
  (`../20261111-r-test/review.md`). A proper sampler over histories would do both classically; the
  local ensemble here does neither.

## Limits

- Laplace's approximation at a likelihood mode, with a diagonal stand-in for the prior's
  curvature; differences of a few units are within its error. The conclusion rests on the
  spread (wide, centred on zero), not on any one period.
- The prior treats a cut period as a stationary renewal process and gives a "both"
  manoeuvre one duration; the generator does neither exactly.
- The search may still miss the true basin even as a candidate (section 3): the evidence
  comparison in section 2 used the truth to place it.
- 57 periods, one tuning seed, thresholds untuned.
