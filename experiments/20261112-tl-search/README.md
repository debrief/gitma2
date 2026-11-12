# Spec 013: the evidence-scored search over manoeuvre histories (tuning seed 329)

Owner decision 2026-11-12: continue classically. `src/tma2/timelate/search.py` scores a
manoeuvre history by the log evidence of the bearings under Annex B's prior (a fit to the
posterior, Laplace's approximation), and from a start moves to the best single addition,
removal or change of kind while the evidence rises. Two starts: C″'s transitions and no
manoeuvres at all. Every history evaluated is kept; the distinct best five, with probabilities
from their evidence, are the period's candidate tracks.

Never a gate result. **Fresh tuning periods**: ordinals 60 onward of seed 329's σ = 1°
engagements (106 periods, 99 with determined rows); ordinals 0 to 59 were used to develop the
solve, the prior and the search and are not in these figures. Nothing was tuned on these
periods: one run, settings as committed at 001cd4f. Script as run:
`scripts/research/tl_search.py` (four shards), pooled by `tl_arc_pool.py` (`pooled.txt`);
every period's candidates are in `histories.json`. About 68 histories are evaluated per
period, 15 to 60 s on one core.

## Result

Median over periods of each period's median relative range error on determined rows:

| Track | Median | Periods over 10% | Efficiency: range, course, speed |
| --- | --- | --- | --- |
| C″ read as a track | 0.088 | 0.48 | 3.45, 4.80, 4.15 |
| Search from C″'s transitions | 0.048 | 0.32 | 1.79, 2.03, 1.95 |
| Search from nothing | 0.048 | 0.30 | 1.92, 2.08, 2.06 |
| **The higher-evidence history of the two** | **0.042** | 0.23 | 1.69, 1.91, 1.95 |
| Best of the top three candidates (hindsight) | 0.028 | 0.15 | 1.10, 1.64, 1.23 |
| True history, fitted with the prior | 0.018 | 0.03 | 0.68, 0.90, 0.87 |

Ratios [95% over periods]: **C″ ÷ search 2.12 [1.62, 2.96]**; search ÷ true history 2.27
[1.77, 3.03]; search ÷ best of its top three 1.49 [1.20, 2.09].

The search needs neither the physics layer nor C: started from nothing it does as well as
started from C″'s transitions.

## What limits it now

- **Not the search.** The best history found has evidence within 3 of the true history's in
  74 of 99 periods, higher by more than 3 in 23, and lower in 2. Where it is wrong it has
  usually found something the evidence rates above the truth. It names the right number of
  manoeuvres in 71 periods, fewer in 19, more in 9.
- **The evidence itself**, in two ways that these data do not separate: histories really are
  ambiguous in some periods (two explanations, one set of bearings), and Laplace's
  approximation mis-scores some. The true answer is often among the candidates: the best of
  the top three, picked in hindsight, is at 0.028.
- **The probabilities are not yet usable.** The top candidate is the closest of its set to
  the truth in about 30% of periods whether it is given a probability of 0.5 or 0.98. Part of
  that is the test (candidates that differ slightly in timing compete to be "closest"); part
  is that the approximation is overconfident. A gate on candidate tracks needs a calibration
  measure defined beforehand and probably a sampler, not this normalisation.

## Cautions

- The efficiency of the true history fitted with the prior is below 1 (0.68 in range). An
  estimator that uses a prior is biased and the bound does not apply to it; the same is
  true, less visibly, of every "with the prior" row. Efficiencies here compare systems; they
  do not say how near the bound anything is.
- The prior is the generator's own. A factor of two from knowing exactly how the simulated
  target manoeuvres says nothing about a target that manoeuvres otherwise. The gate should
  carry a split with altered leg and turn statistics.
- One tuning seed, 99 periods, σ = 1° only, clean Gaussian bearing errors.
- C″ here is the causal system run to the period's end and read as a track: the standing
  system, but not one designed for this task. It is the baseline, not a strong opponent.

## Next

Register Gate T: the search against C″ read as a track on fresh seeds (validation 330, test
331), with a prior-shift split, and a calibration criterion for the candidate probabilities
defined before any of it is run. CLIs and a CI workflow first (15 to 60 s a period is too
slow for the session at gate size).
