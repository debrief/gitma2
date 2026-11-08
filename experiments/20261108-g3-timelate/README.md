# Time-late E-w (spec 008 T032; constitution IV, Gate 2 panel G7)

The constitution's check that the causal model is not leaving information unused through a design
fault: E-w trained with its encoder's causal mask removed, so its per-bearing weights at rows ≤ k
and its start correction may read every bearing of the scenario, including those after k. The
solve stays C's at prefix k (research R9 as amended: C's knots exist only up to k), so this tests
the learned part only.

- **Model:** ewtl-s1, plan `configs/gate2/g3-timelate.json` (g2-a's settings and seed 1, `causal:
  false`), trained on CI (run 42472497159, `results/g2-g3-timelate-42472497159`): 10 epochs, best 7;
  trimmed validation loss 38.10 untrained → 36.48 (the causal ew-s1 with the same seed: 36.39,
  ew-s3 36.65).
- **Predictions:** validation scoring ordinals 500–1499 (`results/g2predict-g3-timelate-val-42521425376`).
- **Scoring:** run 42525373854 (`results/score-g3-timelate-val-42525373854`, commit ec621e2), beside
  ew-s1 (Gate 2's validation file) and ew-s3; the reference estimators reused from the baseline
  scoring (`--reuse`, rows matched exactly). Paired differences from that run's `errors.npz` with
  `scripts/research/g2_paired_gaps.py` (scenario-clustered, 97.5%, 2,000 resamples).

## Result

| | Gap recovered (range) | Range | Course ° | Speed kt |
| --- | --- | --- | --- | --- |
| C | 0.890 [0.869, 0.909] | 0.120 | 15.54 | 1.62 |
| ew-s1 (causal) | 0.901 [0.882, 0.918] | 0.115 | 14.79 | 1.61 |
| ew-s3 (causal, carried in Gate 2) | 0.902 [0.882, 0.920] | 0.114 | 15.13 | 1.57 |
| **ewtl-s1 (time-late)** | **0.899 [0.881, 0.915]** | 0.116 | 15.32 | 1.61 |

| Paired difference in gap recovered | Value [97.5%] |
| --- | --- |
| ewtl-s1 − ew-s1 (same seed) | −0.0018 [−0.0082, +0.0057] |
| ewtl-s1 − ew-s3 | −0.0027 [−0.0104, +0.0043] |
| ew-s3 − ew-s1 (seed spread, for scale) | +0.0010 [−0.0039, +0.0082] |

## Reading

Rule (research R9): the time-late variant must score at least as well as the causal E-w, or the
shortfall is reported. **It does not score better; its point is 0.002 below the causal model with
the same seed, inside the seed-to-seed spread, with an interval that includes zero.** Seeing the
future gives the learned weights nothing measurable. Two readings, not separable here:

1. The causal E-w is not leaving usable information unused through a design fault (the
   constitution's concern): what E-w learns, a recency profile (Gate 2 panel), needs no future.
2. The design limits both variants alike: the weights act on C's hand-over and C's solve at k,
   so information after k could only enter through re-weighting rows ≤ k. A whole-window solve
   with C's full segmentation (the R9 form as first planned) was not tested.

Not a gate; recorded for spec 008's follow-ons (FR-024) and reported in the Gate 3 slides post.
