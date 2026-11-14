# Research notes: spec 018

**R1. What adapts.** One hyperparameter: the leg length (how often the target manoeuvres).
Spec 017 found the control under-counts on busy targets; the kind and size ranges of the
broadened prior already cover the shifted targets' manoeuvres. The grid is the broadened
prior with leg means 600, 1,200 and 2,400 s (sd half the mean, minimum 300 s as before).
Alternatives: a continuous rate fitted by maximising evidence (needs a search per
evaluation; a grid of three is the same thing at fixed cost); adapting turn size as well
(two more searches a period for a quantity not shown to matter). Annex B's own prior is
not a grid member: the standing control beside already runs it.

**R2. How the rate is inferred.** Model evidence of a rate ≈ the sum of the evidences of
the candidates its search found, times a weight beforehand (equal unless tuning shows
harm on quiet targets). A lower limit on the true sum for every rate alike. Empirical
Bayes: the declared history is declared under the most probable rate's prior, by the
standing control's rule (margin 1, quiet probability 0.01). Alternative: full mixture
declaration (a path under a mixture prior) needs the evidence under every rate for every
step of the path: three times the path's cost for a second-order difference.

**R3. The hedged track.** All rates' candidates are one mixture, weight ∝ rate weight ×
exp(evidence), temperature 1 (study L's choice). Mean of Cartesian states. Spread in
range: mixture of each candidate's Laplace sd (posterior curvature, as the evidence uses,
carried through the arc model) and the between-candidate disagreement. Known limits: a
mean of mirror candidates is no target's track; the Laplace sd inherits the evidence's
recorded faults; candidates under 1% weight are dropped.

**R4. The ceiling is not a bound.** The search told the split's own statistics is what a
right prior is worth with this search and evidence. It misses manoeuvres too (0.12 above
40 in spec 017) and invents more. The adaptive control may beat it in places.

**R5. Kinds of period** (spec 017 panel). (a) The standing control misses a whole true
manoeuvre with detectability ≥ 20 at a 120 s match; reported also that the classing uses
truth and a tolerance. (b) Terciles of the period's median bound on relative range.

**R6. Conditions must read cost and be able to fire.** Candidates, to be fixed after
tuning: gain = control ÷ adaptive on the shifted split, interval wholly above 1.00; harm
= the same wholly below 1.00 on Annex B, held course, outliers or correlated errors;
honest spread = two-sd coverage within a registered band on Annex B and shifted. Counts
(false manoeuvres on quiet targets, one-manoeuvre targets called quiet) are reported
beside, at three tolerances, and decide nothing alone.

**R7. Cost.** About seven searches a period (control 2, true prior 1, grid 3) plus
detectability: roughly 1.3 times spec 017's test per period. Test sizes are set from
tuning variances within about five hours of CI at 20 concurrent jobs.

**R8. Quiet split.** Its own statistics allow no manoeuvre, so no true-prior search is
run there (`no_true`); the reference is the one-leg fit told there is none.
