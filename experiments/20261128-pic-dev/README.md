# Spec 039 development run 1: the range-profile read-out (spent seed 370; not a result)

300 engagements of seed 370, in distribution, clean and under the primary mismatch condition.
CI run 46127699276 at commit 25caa874 (one shard's runner died without a log and was re-run once);
plan `configs/headroom/pic-dev-in.json`. `tables.md` by `scripts/research/gd_tables.py`.

The read-out (`headroom/profile.py`) profiles the robust solve's cost over range at the row,
weights it by the generator's distribution of ln range and its speed support, and reports the
posterior median. `-t`: tempered by the fitted error model. `flat`: no prior (the median of the
profile alone).

Plain solve ÷ read-out on the same segmentation, range (above 1: the read-out is better):

| | clean | primary | by bound third (tight, middle, loose), primary |
|---|---|---|---|
| true segmentation, prior | 0.973 [0.896, 1.064] | 1.042 [0.966, 1.122] | 0.88, 0.99, 1.19 [1.01, 1.40] |
| true segmentation, prior, tempered | 0.962 | 0.946 | 0.83, 0.93, 1.02 |
| true segmentation, flat | 0.862 [0.793, 0.935] | 0.903 [0.839, 0.971] | 0.83, 0.90, 0.99 |
| C″'s segmentation, prior | 1.056 [0.995, 1.118] | 0.992 [0.940, 1.046] | 0.93, 0.96, 1.04 |

What it says:
- **It moves the solve** (FR-011): on the true segmentation 14% of engagements are twice as good
  and 16% twice as bad on clean data; 11% and 9% under the primary condition. It is not a null by
  construction, unlike the two earlier prior controls.
- **It nets nothing overall and trades thirds.** Under the primary condition it gains where the
  bound is loose (1.19) and loses where it is tight (0.88). It removes about half of the
  regressor's loose-third advantage over the told-truth solve there (0.51 [0.06, 1.09]; ratio of
  medians 0.21): a wide interval.
- **The median of the profile is a worse estimator than the mode** without a prior (0.86, 0.90):
  the profile is too wide or too skewed to be read as a posterior. The prior repairs that and a
  little more.
- **In a causal system it does nothing**: behind C″'s segmentation it closes 0.11 [0.00, 0.23]
  of the gap to the regressor on clean data and none under mismatch.
- **Choice (research R4)**: untempered (pooled +0.014 against −0.094 tempered).
