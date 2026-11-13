# Spec 014, validation seed 334: the soundness stop (2026-11-12)

CI run 43302177257 (`timelate/tl-c-val`, commit 78f423f, clean tree; plan and code digests
equal the decision record's). 150 Annex B periods (139 scored) and 150 held-course periods.

## The stop: passed

| Check | Value | Required |
| --- | --- | --- |
| Reference (true history, neutral starts, times held): range efficiency on tightly bounded rows | 1.05 | 0.8 to 1.3 |
| True-history fits with a cost the noise explains | 0.993 | at least 0.90 |

Test seed 335 was launched from the same commit after this reading.

## Reported only (validation decides nothing else)

| | Tuning 333 | Validation 334 |
| --- | --- | --- |
| C″ ÷ search, paired | 1.72 [1.37, 2.15] | 1.77 [1.40, 2.24] |
| Refit's share of the gain (D1) | 0.79 [0.49, 1.26] | **0.30 [−0.06, 0.57]** |
| Refit ÷ search, paired | 1.12 [0.90, 1.40] | 1.49 [1.23, 1.79] |
| Flat-prior search ÷ search, paired | 1.01 [0.84, 1.23] | 1.15 [0.96, 1.37] |
| Wrong-history periods: ambiguous / search failure / evidence failure (D2) | 0.47 / 0.10 / 0.43 | 0.47 / 0.16 / 0.37 |
| Headroom, perfect search (D3) | 1.12 [1.03, 1.25] | 1.08 [1.01, 1.17] |
| Headroom, perfect evidence as well (D3) | 1.31 [1.14, 1.53] | **1.04 [0.92, 1.18]** |
| False manoeuvres on held course: search / C″ / flat / mixed (D4) | 0.81 / 0.03 / 0.01 / – | 0.79 / 0.02 / 0.01 / 0.03 |
| Mixed-prior search ÷ search on Annex B data | – | 0.99 [0.92, 1.04] |

- **D1 and D3 moved a long way between two seeds of 150 periods.** On the tuning seed the
  refit obtained most of the gain and a perfect evidence left 31% to win; on this seed the
  refit obtains a third and a perfect evidence leaves nothing shown. The forecasts in the
  decision record (0.75; material) were written from the tuning seed and may both be wrong.
  The test seed has 400 periods; whatever it says, one seed's share is not a constant.
- **D4 repeats closely**: the informed search declares a manoeuvre on four held-course
  periods in five. The mixed prior removes that (3%) at no measurable cost on Annex B data
  (the search ÷ mixed ratio is 1.01 [0.96, 1.09] there, and 2.29 [1.86, 2.86] on held course).
- On held-course periods one leg and C″ score 0.79 of the bound on tight rows, and the
  tuning seed gave 1.24: a period's rows share one noise draw, so 150 periods carry about
  that much scatter. No fault is claimed and none ruled out; the test seed has 400.
- The smoothed EKF is far worse than C″ on Annex B data (0.49 against 0.086) and somewhat
  worse on held course (0.027 against 0.018): a constant-velocity smoother with small
  process noise cannot follow manoeuvres. As frozen for real-time rows; not re-tuned.
