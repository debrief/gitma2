# Spec 011 diagnosis: how the frozen C fails under each mismatch kind

Tuning seed 323 (never a gate result). 150 σ = 1° engagements (ordinals 0–149 of the `train`
split, count 800), 593 scored rows, the same rows in every condition. CI run 42881128653
(`diagnose/gr-diagnose`, plan `configs/diagnose/gr-diagnose.json`, code 02ef937); one folder per
condition with the scorer's `metrics.json`, `run.json`, digests and `report.md`. C is the frozen
segmenter (code `4d2c084f…`, parameters `60e6ee63…`); the final solve is the **plain** one, 12 knots.
`C-truthnom` is C with the true change starts added as nominations (confirmation still decides).

## Downstream: median relative range error (all 593 rows)

| Condition | One leg | True segmentation (plain) | C | C + true nominations | IMM | C: gap recovered [95%] |
| --- | --- | --- | --- | --- | --- | --- |
| off | 0.671 | 0.061 | 0.131 | 0.114 | 0.572 | 0.88 [0.84, 0.93] |
| correlated | 0.677 | 0.111 | 0.214 | 0.188 | 0.610 | 0.82 [0.74, 0.89] |
| bias | 0.663 | 0.070 | 0.128 | 0.117 | 0.578 | 0.90 [0.85, 0.94] |
| untold σ | 0.671 | 0.057 | 0.120 | 0.109 | 0.595 | 0.90 [0.85, 0.94] |
| outliers | 0.669 | 0.074 | 0.236 | 0.218 | 0.700 | 0.73 [0.60, 0.81] |
| all four | 0.692 | 0.133 | 0.306 | 0.277 | 0.734 | 0.69 [0.54, 0.80] |

## Each kind's effect against `off` (`kind-shares.json`; paired, scenario-clustered, 95%)

| Condition | Change in C | Change on the true segmentation | The part that is segmentation's |
| --- | --- | --- | --- |
| correlated | +0.082 [+0.042, +0.117] | +0.050 [+0.028, +0.068] | +0.032 [−0.005, +0.070] |
| bias | −0.004 [−0.019, +0.015] | +0.009 [−0.001, +0.018] | −0.013 [−0.029, +0.008] |
| untold σ | −0.011 [−0.028, +0.008] | −0.003 [−0.009, +0.002] | −0.008 [−0.026, +0.012] |
| outliers | +0.105 [+0.070, +0.161] | +0.013 [+0.002, +0.025] | +0.091 [+0.054, +0.148] |
| all four | +0.175 [+0.130, +0.227] | +0.072 [+0.052, +0.090] | +0.103 [+0.057, +0.159] |

## Segmentation against the truth (`transitions.json`, `scripts/research/gr_diagnosis.py`)

Summed over the 593 scored prefixes; 1,223 true target changes had begun by their prefix.

| Condition | Declared | Matched | False transitions | Misses | Misses begun > 5 min before | Leg count right |
| --- | --- | --- | --- | --- | --- | --- |
| off | 1,065 | 817 | 248 | 406 | 318 | 0.52 |
| correlated | 1,516 | 873 | 643 | 350 | 269 | 0.35 |
| bias | 1,112 | 829 | 283 | 394 | 309 | 0.52 |
| untold σ | 1,064 | 834 | 230 | 389 | 301 | 0.49 |
| outliers | 1,778 | 855 | 923 | 368 | 282 | 0.24 |
| all four | 1,991 | 865 | 1,126 | 358 | 278 | 0.17 |

Boundary hits within 60 s stay at 0.09–0.10 and within 3 min at 0.38–0.44 in every condition
(`metrics.json`, `segmentation`). With true nominations the false transitions barely move (all
four: 1,160 against 1,126; outliers 976 against 923) and matches rise by 15–42.

## What the measurements support

1. **Outliers and correlated error are the kinds that hurt C; bias and an untold σ do not** at
   central severity (their intervals include zero in every column).
2. **The mechanism is false transitions, not misses.** Under outliers C declares 3.7 times the
   false transitions of clean data, under correlated error 2.6 times, under all four 4.5 times;
   misses do not rise in any condition (they fall slightly).
3. **Outliers' loss is segmentation's; correlated error's is mostly not.** Of outliers' +0.105,
   +0.091 is beyond what the true segmentation loses. Of correlated error's +0.082, +0.050 is
   lost on the true segmentation too, and the segmentation part's interval includes zero.
4. **Nomination is not the failure.** Giving C the true change starts recovers 0.02–0.03 of
   range error in every condition, clean included, and does not reduce the false transitions.
   Over-acceptance in confirmation is where the false transitions enter. Which of its tests
   accepts them (the cost drop inflated by wild residuals, or the retest) is **untested**.
5. The kinds are not additive in the segmentation part: outliers +0.091 and correlated +0.032
   against +0.103 together (intervals overlap; not resolved at this size).

## Not delivered here (FR-002, FR-003)

- **Delay** is not measured: segmentation files hold scored prefixes only.
- **The most the design can yield (FR-003)** needs the robust final solve, which this run did
  not use. From validation seed 321 (`experiments/20261110-gh-c2/`): robust control on the true
  segmentation 0.114, C″ with the robust final solve 0.230, under all four. The same two
  figures on this seed, and the robust solve on C's clean-data segmentation applied to the
  mismatched bearings, are the plan's first task.
- **False transitions on held legs** as Annex A defines them: every scored row here has at
  least one true change, so the scorer's `false_split_rate` is empty; the counts above are
  unmatched declarations instead.
- Even clean, C declares 248 false transitions and misses 406 of 1,223 changes; note 08 found
  most changes leave little trace, and how many of these misses are detectable is not measured
  here.

## Consequence for the design (a proposal for the plan, not a result)

C-r's lever is confirmation under outliers: robust (Huber) costs in the confirmation test so a
few wild bearings cannot buy a transition. Correlated error is second: an effective sample
size in the test's threshold. Nothing is needed for bias or σ. Speed: C took about 5 times
longer under outliers in a local trial of 3 engagements; fewer false nominations should also
shorten runs, untested.
