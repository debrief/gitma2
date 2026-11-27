# Spec 037 step 1: the rule, written before the run

Plan: `configs/headroom/rm-dev-321.json` (spent seed 321, the first 300 σ = 1° engagements,
sixteen conditions, one scoring run per condition). Development data: nothing here is a result.

Read on the primary condition `all-central`, the three regressors pooled, in range:

- **A** = the pooled regressors' scenario-median range error under `all-central` ÷ the same
  under `off` (per regressor, the median over scenarios of the scenario median; the three
  averaged in the log).
- **B** = the paired ratio C″-robust ÷ regressors, pooled (`reading.json`,
  `paired.c2-robust.range.pooled`).

**Holds up**: A ≤ 1.10 and B's interval wholly above 1. Then no fine-tune for robustness is
launched and the owner is asked whether the uncertainty alone is worth the spend.
**Otherwise**: step 2 proceeds as planned.

Reported beside, deciding nothing: every system on every condition; C″ ÷ regressors; the
coverage of the unchanged models' intervals at scale 1; the first-bearing fragility (research
R8) if the truth side file shows it.

Known before the run: 300 engagements per condition, so a ratio within about 10% of 1 will read
"not separated"; the sixteen conditions are the same engagements under different errors, not
independent samples. A local trial of the pipeline on twelve engagements of `all-central`
(seed 1 only) was seen before this was written: regressor row-median range error 0.23, the plain
solve on the true segmentation 0.11. No C″ figure was seen.
