# Spec 005 plan research: segmenter C's search and refinement (research.md R1–R2)

Validation seed 304 only (σ = 1° scenarios in file order). Tuning ordinals 0–299, scoring
ordinals 500–799. No test data. The comparison with GLR + confirm uses the knots of note 08's
`glr-q0.2-t13.8` run (`experiments/20261103-leg-detection-spike/`, confirm shards in its work
directory) on the same 300 scoring scenarios.

- `seg-tune300.json`, `seg-score300.json`: `scripts/research/seg_search.py` (penalties 20–100
  and 20/30/45), with per-scenario segmentations, cost-table seconds and search seconds.
- `refine-score-p30.json`: `scripts/research/seg_refine.py --penalty 30`, every nominated
  transition tested on the whole history.
- `refine-score-p{20,30}-h{6,18}.json`: the same, each transition tested on the prefix ending
  6 or 18 rows after it.

Headline (300 scoring scenarios; a turn is found if a transition's midpoint lies in it ± 3 min):

| | Recall | Precision | F1 |
| --- | --- | --- | --- |
| C search, penalty 30 | 0.56 | 0.78 | 0.65 |
| + whole-history refinement | 0.54 | 0.79 | 0.64 |
| + refinement on its own prefix (+ 18 rows) | 0.44 | 0.94 | 0.60 |
| GLR 20% + confirm (note 08) | 0.67 | 0.97 | 0.79 |

Timing: 3.1 s median, 8.3 s at most per full history for the cost table, on one core per
process with four processes. The search takes ≤ 0.01 s.
