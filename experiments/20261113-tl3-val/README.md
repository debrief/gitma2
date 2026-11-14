# Spec 015, validation seed 336: the soundness stop (2026-11-13)

CI run 43393847363 (`timelate/tl-d-val`, commit 30cc410, clean tree; plan and code digests
equal the decision record's). 150 Annex B periods (134 scored) and 150 held-course periods
(130 scored). Every table is in `tables.md`, generated from `summary.json`.

## The stop: passed

| Check | Value | Required |
| --- | --- | --- |
| Reference (true history, neutral starts, times held): range efficiency on tight rows | 1.01 | 0.8 to 1.3 |
| True-history fits with a cost the noise explains | 1.000 | at least 0.90 |
| References held to the true times | 0.147 | at most 0.25 |

Test seed 337 was launched from the same commit after this reading and before this file
was written.

## Reported only (validation decides nothing else)

Read from `tables.md`; the development column is `experiments/20261113-tl3-dev/`.

| | Development (spent 335) | Validation 336 |
| --- | --- | --- |
| C″ ÷ repaired search, paired | 2.39 [1.95, 2.90] | 1.69 [1.37, 2.08] |
| D1: refit's share of the gain | 0.47 [0.32, 0.61] | 0.64 [0.36, 1.01] |
| Refit fall-backs | 26 of 200 (first rule) | 5 of 150 (registered rule) |
| D2: first candidate right; wrong: ambiguous / search / evidence | 0.64; 0.49 / 0.12 / 0.39 | 0.63; 0.48 / 0.12 / 0.40 |
| D3: perfect search | 1.07 [1.02, 1.14] | 1.08 [1.01, 1.19] |
| D3: perfect evidence as well | 1.17 [1.08, 1.27] | 1.30 [1.15, 1.49] |
| ... without held references | 1.11 [1.04, 1.19] | 1.20 [1.09, 1.36] |
| D4: held course, repaired search | 0.50 [0.43, 0.57] | 0.53 [0.45, 0.60] |
| ... under 30 minutes; over 60 | 0.08; 0.93 to 1.00 | 0.03; 0.90 to 1.00 |
| D4: C″ / flat prior / mixed prior | 0.01 / 0.01 / 0.00 | 0.02 / 0.02 / 0.00 |
| Spec 014's search ÷ repaired: Annex B; held course | 1.03; 1.18 | 1.11 [1.00, 1.25]; 1.21 [1.07, 1.38] |
| One-manoeuvre targets declared quiet: repaired; mixed | 0.088; 0.228 | 0.077; 0.135 |

- D2 and D4 repeat closely. D1 again moves between seeds (0.47, 0.64), with an interval on
  134 periods that reaches from a third to all of the gain.
- The headroom with a perfect evidence is **material** on this seed (1.30 [1.15, 1.49]) and
  inconclusive without held references (1.20 [1.09, 1.36]). On the development periods it
  was inconclusive either way. The forecast called it an even chance; the test seed, with
  400 periods, decides.
- The changed fall-back rule fired in 5 of 150 periods, in line with its purpose.
- The held-course split shows the same pattern by length as development: almost no false
  manoeuvres under 30 minutes, almost always over an hour.
