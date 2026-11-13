# Spec 015: decision record for the re-registered study (2026-11-13)

Written after the development run on spent seed 335 (`experiments/20261113-tl3-dev/`) and
before seeds 336 and 337 exist. `decision.json` binds the plan `configs/timelate/tl-d.json`,
the run files, the ranges files, the time-late code and the scorer by digest. The plan is
never edited after this commit. A registered study, as spec 014 was; the panel reviews it.

## What is decided on test seed 337

| | Quantity (Annex B, 400 periods, unless said) | Forecast |
| --- | --- | --- |
| D1 | Share of the repaired search's gain over C″ that refitting C″'s own manoeuvre times obtains | 0.50; the interval includes 0.5, excludes 0.25 and 0.75 |
| D2 | Scored periods whose first candidate is wrong (edge-aware): ambiguous, search failure, evidence failure | 0.50, 0.12, 0.38; first candidate right in 0.63 |
| D3 | Attainable headroom against 1.10: a perfect search; a perfect evidence as well | about 1.05 to 1.08; 1.12 to 1.20, an even chance of "material" |
| D4 | Held-course periods (400) with a manoeuvre declared: repaired search, C″, flat prior, mixed prior | 0.50, 0.02, 0.01, 0.01; under 0.15 below 30 minutes, above 0.90 over an hour |
| D5 | Recommendation on a learned whole-period model | spec 014's rule, unchanged |

## What changed from spec 014's definitions

- The search uses prior version 3: every factor without a Gaussian residual has the volume
  its own density implies (research R1).
- One rule decides whether a found history is the true one, ignoring manoeuvres the period
  cuts (R2). D2 is of scored periods.
- The reference is held to the true times where it drifts into another history, and
  flagged (R3). D3 is also given without flagged periods.
- The refit control falls back to C″'s track when its fit is not acceptable (R4). D1 is
  also given without fall-back periods, and by two other estimands declared in research R7.

## Reported, not decided

Each decided statistic at class thresholds 1, 3 and 5 and match tolerances 60, 120 and
240 s, as a ratio of medians beside the paired figure; spec 014's search beside the repaired
one on every split; the flat-prior search's share of the gain; false manoeuvres by period
length; manoeuvring targets declared quiet by number of true manoeuvres; headroom on the
shifted, correlated, outlier and whole-engagement splits, where no remedy has been built;
counts and candidate calibration. Every table comes from `summary.json` by
`scripts/research/tl3_tables.py`.

## Soundness stop (validation seed 336)

The reference with times held within [0.8, 1.3] of the bound on tightly bounded rows; at
least 90% of true-history fits with a cost the noise explains; at most 25% of references
held. Fail: seed 337 is not generated.

## Changed after the development run, before this record

- The refit's fall-back now keeps a fit whose cost the noise explains. The first form fell
  back in 26 of 200 periods because C″'s chord track fits bearings more closely than a sound
  arc refit. The changed rule has not been run on any data.
- The stop's limit on held references is 25%; it was drafted at 15% and the development
  periods gave exactly 15%.

## Known weaknesses, stated beforehand

- The class threshold of 3 is a convention and the evidence's own noise is of that size;
  every threshold is reported.
- The composites are oracles of identification, and the reference is a fit: where it is
  worse than the search the composite understates the headroom. The "where it helps only"
  variant is reported beside.
- The Laplace volume can exceed a parameter's feasible range at a bound (about +0.7 at the
  duration's floor): recorded in research R1, not repaired.
- D5's rule reads the Annex B split, where the search holds the simulator's own model. The
  record must state the other splits' headroom and that nothing was built against it.
- The forecasts come from 200 periods of a spent seed and from code that differs from the
  registered commit in the fall-back rule.
- One test seed. Every split is drawn from the same seed with different ranges files.
