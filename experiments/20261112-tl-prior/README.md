# Spec 013: does prior knowledge of manoeuvres separate the histories? (tuning seed 329)

Owner decision 2026-11-11: build a classical estimator that uses Annex B's manoeuvre
statistics. Before a sampler, the cheap test: under those statistics, is the true history
more probable than the wrong one the re-test finds? Never a gate result; same 60 cut periods
as `../20261111-tl-retest/` (57 with determined rows).

Code: `src/tma2/timelate/prior.py` (generator 0.6.0's leg, kind, angle, rate and speed
distributions as a density over a period's history), `retest.log_evidence` (Laplace: fit,
prior at the fit, Occam factor), `retest.choose_kinds`, `retest.ensemble`. Scripts as run:
`scripts/research/tl_retest.py` (now with evidence; `histories.json`), `tl_evidence_read.py`
(`evidence.txt`), `tl_ensemble.py` (first version only: `withdrawn/ensemble.json`, `withdrawn/ensemble.txt`).

## 1. Told only which basin, the fit reaches the bound

The arc model fitted from the truth with every manoeuvre's start and duration **free**:
efficiency 1.03, 1.00, 1.17 (range, course, speed); median period range error 0.021. The
exact times are not needed. What is needed is the right history: how many manoeuvres,
roughly where, turning which way.

## Correction, 12 November (later): sections 2 and 3 as first written are withdrawn

The first version of this record said that under Annex B's prior the true history was no
more probable than the re-test's wrong one, and that the re-test was already near the most
probable history. **That was an artefact and is withdrawn.** Making the evidence figure for
the slides showed a third of the periods with differences in the thousands. Cause: the
evidence evaluated the prior at a fit to the bearings alone. The bearings leave a
manoeuvre's duration loose, the prior on its turn rate is sharp, so the true history's fit
often sat at an implausible rate and was charged thousands of units for it; and some re-test
fits had run away in speed. The first version's files are kept in `withdrawn/`.

Fix (`retest.joint_fit` with `prior`, `prior.prior_residuals`): the fit is now to the
posterior (the prior's Gaussian parts are appended as residuals), and the evidence is
Laplace's approximation at that fit. Re-run on the same 60 periods: `histories.json`,
`evidence.txt`, `pooled.txt`.

## 2. With the prior in the fit, the true history is usually preferred

Log evidence of the true history minus that of the re-test's history (kinds chosen by
evidence), 60 periods:

| Re-test started from | Within 3 | Truth ahead by over 3 | Re-test's history ahead by over 3 |
| --- | --- | --- | --- |
| C″'s transitions | 33 | 19 | 8 |
| Nothing | 29 | 24 | 7 |

On the periods where the re-test's range error is over twice the true-history fit's (28 and
33 of 57): the truth is ahead by over 3 in 0.50 and 0.61, and the wrong history in 0.07 and
0.09. So where the re-test is wrong, the posterior usually says so, and a search that scored
histories by evidence would have something to climb. In roughly a third of those periods
the two are still within 3: there the ambiguity is real.

## 3. Fitting the re-test's history with the prior nearly halves its error

No truth is used below: the re-test's own history, refitted to the posterior, kinds chosen
by evidence. Median period range error, 57 periods:

| Track | Median | Periods over 10% |
| --- | --- | --- |
| C″ read as a track | 0.113 | 0.54 |
| Re-test from C″, fit to the bearings only | 0.141 | 0.56 |
| **Re-test from C″, fit to the posterior** | **0.057** | 0.39 |
| Re-test from nothing, fit to the posterior | 0.085 | 0.42 |
| The higher-evidence of the two | 0.056 | |
| True history, fit to the posterior | 0.027 | 0.16 |
| True history, fit to the bearings only | 0.021 | 0.11 |

Ratios [95% over periods]: C″ ÷ re-test from C″ with the prior **1.99 [1.01, 3.11]**;
C″ ÷ re-test from nothing with the prior 1.33 [0.73, 2.57]; re-test with the prior ÷ true
history with the prior 2.1 [1.5, 4.4]. Told the true history, the prior costs a little
(0.027 against 0.021): it pulls a correct fit toward the usual.

The local evidence-weighted ensemble of the first version (no better than its fitted
history) was computed with the faulty evidence and is not re-run; nothing is read from it.

## 4. Not explained by ownship manoeuvres

True manoeuvres found by the re-test: 0.67 with an ownship turn after them, 0.66 without
(108 manoeuvres; 7 of 60 periods have no ownship turn at all).

## Reading (replaces the first version's)

- Annex B's statistics, used in the fit and in the choice between histories, are worth
  about a factor of two over the standing classical system read as a track, on this tuning
  seed, with nothing trained. The lower end of the interval is at 1.01: 57 periods separate
  it only just.
- The gap that remains to the true-history fit (a factor of about two) is partly search:
  in half or more of the periods where the re-test is wrong, the true history has clearly
  higher evidence and the search did not find it. A search or sampler over histories scored
  by evidence is the direct next step, and it is classical.
- Some ambiguity is real: in about a third of the wrong periods the evidence does not
  separate the histories. Candidate tracks with probabilities remain the honest output there.
- The earlier claim that "no estimator that names one history reaches the reference" is not
  supported either way by this record.

## Limits

- Laplace's approximation at the posterior fit; differences of a few units are within its
  error, which is why the table counts only differences over 3. The first version of this
  record shows how wrong the approximation can be when misused: treat these numbers as
  tuning-seed indications until a sampler checks them.
- The prior here is the generator's own: a factor of two from knowing the simulator's
  manoeuvre statistics exactly says nothing about a target that manoeuvres otherwise.
- The prior treats a cut period as a stationary renewal process and gives a "both"
  manoeuvre one duration; the generator does neither exactly.
- The search may still miss the true basin even as a candidate (section 3): the evidence
  comparison in section 2 used the truth to place it.
- 57 periods, one tuning seed, thresholds untuned.
