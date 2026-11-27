# Data model: spec 038

- **Plan (headroom)**: new optional keys `ranges`, `heldout` (paths; default the Gate H
  plan's); a run's `segmentation: "c2e"` with `edit: {wild: bool, effective_sd: bool,
  per_prefix: bool}`; `decomp: {comparator, regressors, own, own_hybrid, hybrids, hardened}`.
- **Prediction header**: `edit` settings and counts (`edited_bearings`, `effective_sd_used`).
- **decomp.json** (per scoring run): `condition`, `split`, `engagements`, `ratios` (name →
  point, interval, median, shares, course, speed, absolute), `gap_closed`, `prior_share`,
  `slices`, `answered`.
- **Protocol** `configs/gd/protocol.json`: seeds, sizes, splits, conditions, chosen settings,
  thresholds; bound by digest in the decision record.
