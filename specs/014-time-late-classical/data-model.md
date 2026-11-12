# Data model: spec 014

- **Settings (per run)**: `prior_version` (1, 2), `prior_kind` (annex-b, flat, broad),
  `thinning` (form, n, tolerance; none by default), `condition` (clean, or a spec 010
  condition id), `split` (man2, shift, quiet, whole). Recorded in every shard header.
- **Systems** (track per period): Gate T's twelve, plus `search2`, `search-flat`, `c2-refit`,
  `ekf-rts`, and the composites `ident-search`, `ident-all` (built at scoring from the
  true-history fit and `search2`).
- **Period record** (`*.periods.json`): Gate T's fields plus, for each system that states
  manoeuvres, its spans and kinds; the true history's evidence fitted without true states and
  whether that fit converged; the class (right, ambiguous, search failure, evidence failure)
  at thresholds 1, 3, 5 and match tolerances 60, 120, 240 s; run time per system.
- **Counts**: per system and tolerance: matched, missed, false, timing error (median, 90th
  percentile).
- **Errors** (`errors.npz`): per scored row and system: range, course, speed error; the bound;
  period ordinal; split keys (ownship manoeuvres, leg position, range band, true count).
- **Study reading** (`summary.json`): per split: systems; ratios (of medians, geometric mean
  paired, share of periods each side better, share over twice as bad); gain shares; class
  shares; headroom figures; false-manoeuvre rates; efficiency per slice with
  `bound_applies` false for systems that use a prior.
- **`TimeLateStudyCriteria`** (schema): class threshold, match tolerance, materiality,
  soundness band, convergence minimum, forecasts.
- **Decision record**: plan digest, run digests, code digest, criteria, forecasts, the
  recommendation rule.
