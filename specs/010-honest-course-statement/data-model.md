# Data model: spec 010

## PredictionRow (schema 0.31.0; all new fields optional)

- `course_arc_rad` (X), `course_arc_prob` (P): as in spec 009. In the truncated form, P is exactly
  the arc mass.
- `course_kappa`: the concentration of the truncated von Mises inside the arc (rad⁻²).
- `course_form`: `"mixture"` (spec 009) or `"truncated"` (spec 010). The scorer computes the log
  score by form.
- `unsettled_score`, `unsettled_flag`: the causal proxy's score and state at the row.
- `range_ratio_q95` and `speed_q95_mps`: unchanged.

## Proxy cache (`.npz` per shard, beside spec 008's feature cache)

- **Row keys:** `ordinal`, `k` (the same rows as the feature cache).
- **Residual statistics:** `bias6`, `bias12`, `bias30`, `chi60`. These are E's state propagated back
  at constant velocity against the bearings in the last W rows, normalised by σ.
- **From C:** `c_open` (C has a transition open at the row) and `c_since_min` (minutes since C's
  last closed transition; inf if none).
- **Header:** the data digest, E's file or cache digest, C's segmentation digest, the commit and the
  dirty flag.

## StatementConfig5

The form (`truncated`), `xmax_rad`, the feature list for P, the head width, bound, learning rate,
batch rows, epochs, patience, min improvement and seed, plus a `shuffle: none | errors | encoder`
field.

## ClassicalRuleConfig

The quadratic and linear terms, the fitting data (stream), the L2 penalty and the steps.

## TemperatureConfig5

The slices, the β grid, `xmax_rad` and the Platt map's fitting rows.

## ProxyDefinition

The logistic coefficients and standardisation on the R1 features, fitted on tuning rows for truth
"unsettled". The threshold is the quantile that matches the tuning base rate. It is bound by the
decision record.

## Gate5Criteria / Gate5Decision

- **Criteria:**
  - `coverage95_overall` [lo, hi] and `coverage95_slice` [lo, hi];
  - `reliability_overall`, `reliability_slice` and `reliability_slice_point`;
  - `slope` [lo, hi];
  - `auc_min`;
  - `min_slice_rows`;
  - `consistency_tol`.
- **Decision:** as Gate 4's, plus:
  - `controls`: the temperature, the classical rule and the encoder shuffle, with digests;
  - `proxy`: the ProxyDefinition's digest;
  - `slices`: the gated slice definitions.
