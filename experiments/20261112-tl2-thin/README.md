# Spec 014: the bearing-rate thinning study (tuning seed 333, 2026-11-12)

The owner's idea of 2026-11-11: where the bearing rate is steady, a run of 5-second bearings
might be replaced by fewer observations. Tested on the whole-period search (`search2`) over
the first 100 Annex B tuning periods (90 scored), each form against the full data on the same
periods. Runs: `timelate/tl-c-thin-*` at commit 58bad9d (`runs.txt` names the results
branches); table by `scripts/research/tl2_thin.py` (`thin-clean.json`). Tuning data.

Cost is the geometric mean per-period ratio of the form's period median range error to the
full data's, with a period bootstrap. The adoption rule was fixed before the runs (research
R6): cost under 2% with an interval excluding 5%, and at least 30% of run time saved.

| Form | Points kept | Cost | Search seconds a period | Manoeuvres missed |
| --- | --- | --- | --- | --- |
| Full data | all | 1 | 21.4 | 16% |
| One bearing in 2 | 1/2 | 1.19 [0.96, 1.48] | 19.6 | 21% |
| One bearing in 4 | 1/4 | 1.59 [1.22, 2.03] | 22.2 | 29% |
| One bearing in 6 | 1/6 | 2.10 [1.68, 2.68] | 21.5 | 29% |
| One bearing in 12 | 1/12 | 2.38 [1.82, 3.12] | 21.3 | 45% |
| Normal points of 2 | 1/2 | 1.09 [0.95, 1.26] | 11.7 | 19% |
| Normal points of 4 | 1/4 | 1.03 [0.89, 1.19] | 9.0 | 17% |
| Normal points of 6 | 1/6 | 1.01 [0.86, 1.20] | 9.1 | 20% |
| Normal points of 12 | 1/12 | 1.07 [0.87, 1.32] | 7.2 | 17% |
| Adaptive bins, tolerance 3 | varies | 1.25 [1.02, 1.51] | 9.5 | 17% |
| Adaptive bins, tolerance 4 | varies | 1.30 [1.05, 1.58] | 5.8 | 21% |
| Adaptive bins, tolerance 6 | varies | 1.50 [1.17, 1.92] | 8.0 | 18% |

## Reading

- **Dropping bearings is a plain loss.** It throws information away (cost 1.2 to 2.4, misses
  rising to 45%) and saves no time: the search's time is in its many fits, not their length.
- **Fixed normal points lose little and halve the run time.** Costs of 1% to 9%, none
  separated from zero, at 45% to 66% less time. A minute of bearings (12) in one point costs
  about as little as ten seconds (2).
- **Bins set by bearing-rate steadiness are worse than fixed ones**: 25% to 50% cost. This is
  the owner's idea in the form research R6 declared, and in that form it does not help. A
  likely reason, not tested: a bin that grows until the bearing bends ends exactly where a
  manoeuvre begins to show, so the evidence of the bend is averaged into the bin's line.
- **By the rule, nothing is adopted.** No form's interval excludes 5%: 90 periods cannot
  decide a 2% cost when the search lands on a different history in some periods (each form is
  "worse" in about half of them). The rule asked more of the sample than it could give; that
  is a fault of the rule, stated here and not repaired after the fact.
- **It does not matter for this spec**: the search takes 21 seconds a period, so the
  registered runs use the full data. If run time ever binds (a larger search, a sampler),
  normal points of 4 to 6 are the form to test first, on enough periods to decide.

## Not shown

One seed, one system. Outlier-condition runs (plain and robust forms) are reported in
`thin-outliers.json` when their baseline run completes; see below if present.
