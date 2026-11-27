# Research: spec 038

## R1 The raised-threshold control

**Decision**: `--segmentation c2r --robust-confirm {"robust": false, "tau_factor": X}`, which
exists since spec 011 (C's own confirmation with its threshold multiplied; C's digests asserted
by `tests/unit/test_segment_robust.py`). Grid X ∈ 1.5, 2, 3, 4 on seed 321.
**Why**: no new code touches the segmenter. Spec 011 found doubling removed 28% of false
transitions on 150 engagements and was not separated; spec 012 found 3× worse than C″ on clean
data. Forecast: closes little.
**Alternative rejected**: the Huber confirmation test (spec 011: no better than doubling).

## R2 The editing control

**Decision**: `headroom/edit.py` builds, for each scenario, a copy of its `BearingData` for the
segmenter only: `valid` without bearings more than 4 sd from the running median of 9
(`timelate.thin.edit_wild`, unchanged), and `sigma` replaced by the effective sd from the
correlated share and time estimated from second differences (`timelate.corr.estimate`,
`effective_sigma`; used above a share of 0.2, as spec 016). Three variants on seed 321: edit
only, effective sd only, both. C″'s veto and fade are unchanged. The final robust solve reads
the original bearings, so a variant differs from C″-robust in its segmentation only.
**Causality**: C is run on prefixes; the edit at row i reads 4 bearings after i, and the
correlation estimate reads the whole window. For a real-time system that is a 40-second
look-ahead and a non-causal sd. The control is therefore computed per scored prefix: the data
are cut at k before editing and estimating (the last 4 rows of a prefix use a one-sided
median). Cost: C runs once per scored row and not once per scenario; measured before the grid
is launched, and if over twice C″'s cost the estimate is made on the prefix at the first scored
row and the edit stays per prefix.
**Risk**: `LAGS` were chosen at 5-second bearings; MAN2 is at 10 s. The fit is in seconds, so
it stands; checked on seed 321's correlated conditions against the truth side file.
**Alternative rejected**: spec 016's whole `ctl` (a time-late system, not a real-time one).

## R3 The pure prior

**Finding**: the ownship-only regressor (`results/gputrain-r-a-own-42990062999`, checkpoint
`47e10c0e…`) reads no bearing feature, but two bearings still reach its rows: the first valid
bearing sets the frame its velocity is stated in, and the last valid bearing gives the
direction its range is laid along. Its range and speed depend on the bearings only through the
frame's rotation of the ownship track; its course and position depend on those two bearings
directly.
**Decision**: scored as it is, named "prior given the ownship track, the first bearing and the
current bearing". The test (FR-010) asserts: with the first and last valid bearings held,
changing every other bearing changes nothing; and reports how far range and speed move when the
frame is rotated. Under mismatch a wild first bearing reaches its course: read in part 4.
**Own-prior hybrid**: `--kind hybrid --prior-from own`, weight grid 0.25, 0.5, 1, 2, 4 on seed
321 clean and primary; a best value at an edge extends the grid. The rule: the pooled log range
ratio against C″-robust over clean and primary.
**The share**: s = ln(C″-robust ÷ own-hybrid) ÷ ln(C″-robust ÷ fine-tuned), per bootstrap
resample of engagements (ratio of pooled means, not a mean of ratios); reported with the
denominator's interval, and not at all where the denominator's interval contains 0.

## R4 Splits

- **In-distribution**: `configs/man2-ranges.json`, as spec 037.
- **Shifted manoeuvre prior**: `configs/gd/shift-ranges.json` = MAN2 with the time-late track's
  four shifts (legs mean 900 s sd 300; turns 15–75°; faster turn rates; kinds 0.6/0.25/0.15).
  Checked locally on a spent seed: the generator accepts it, and the count of engagements with
  scored rows is recorded.
- **Far ranges**: `configs/man2-heldout.json` (initial range 20–30 km), the `heldout` split of
  the same generation. Spec 012's panel: it moves one scalar. It is named "far initial ranges",
  not "unseen geometry"; the fine-tuned models met those ranges in a fifth of their stream
  (the held-course ranges file), which is stated.
- Each clean and under `all-central`. The kinds outside the mix (`ho-both`) on the
  in-distribution split only.
- `headroom.yml` takes `ranges` and `heldout` from the plan when given.

## R5 Readings (`regress/decomp.py`)

Per-engagement median error over scored rows, paired log ratios, engagement bootstrap (2,000),
three training seeds pooled for the fine-tuned regressor, as `mread`. New:
- **Gap closed** by a control H: g = 1 − ln(H ÷ ft) ÷ ln(C″-robust ÷ ft), bootstrap interval.
- **Split difference**: ln ratio on a split minus ln ratio in distribution; the engagements are
  different, so the two bootstraps are independent.
- **Owed slices**: time since the last true target change (thirds); first valid bearing an
  outlier (truth side file); C″'s segmentation right or wrong, classified from C″'s dumped
  segmentation at the first scored row and read on the later rows; efficiency by thirds of the
  bound; rows every system answers; shares answered.
- Beside every ratio: median, shares better, twice as good, twice as bad; course and speed;
  absolute medians.

## R6 Size and cost

Test: 500 engagements per split-condition, 7 split-conditions (in-distribution: off,
all-central, ho-both; shifted: off, all-central; far: off, all-central). Runs with C per shard:
c2, c2-robust, the chosen threshold control, the chosen edit control, own-hybrid, hyb-s1 (one
seed; stated), and robust-true, plain-true without C. About 70 shards × 6 = 420 jobs with C.
At spec 037's 1,000 engagements M1's interval was ±6%; at 500 about ±9%: a gap share's interval
will be about ±0.1 where the gap is a factor of two, and uninformative where the gap is under
about 1.2 (clean data). That is said in the registration.

## R7 Thresholds to register (set after development, checked over bootstrap seeds)

- Hardened control "closes most" ≥ 0.5 wholly; "closes little" ≤ 0.2 wholly; else stated.
- Prior share likewise.
- Split difference: "shrinks" wholly below 0; "holds" within ±ln 1.15.
- Clean-data cost of a control: reported, no line.
