# Research: spec 037

## R1 The uncertainty: the head the model already has

- **Decision**: no new head. The regressor already outputs a log-variance for ln range and
  the two velocity components (trained by a β-weighted likelihood, β = 0.5). The stated 95%
  intervals are: range, exp(±1.96 · s_r · sd) about the estimate; speed and course from the
  velocity Gaussian by a fixed 256-point quadrature (course as the shortest arc holding 95%,
  "undetermined" when it exceeds a half circle). One scale s per quantity, fitted on the
  validation seed only, multiplies the model's sd.
- **Rationale**: the checkpoints load unchanged, so every GPU second goes to the mismatch;
  step 1 can already report the unchanged model's coverage for nothing. The spec's "quantile or
  mixture heads" was a means; the end is an interval that can be scored.
- **Alternatives**: quantile heads (new parameters to train from zero inside 2 hours a seed);
  a mixture (the same, and spec 009's machinery). Both recorded as not built.
- **Risk**: β-weighting is not a proper score, so the raw sds may be mis-scaled; that is what
  the scale and the temperature control measure.

## R2 The held-out family

- **Decision**: two kinds added to the overlay, never drawn in training or tuning:
  `white_t_df` (the white part is Student-t with that many degrees of freedom, scaled to the
  same sd) and `sigma_step_factor` (the bearing-error level is multiplied by a factor, or its
  inverse, from a time uniform in the engagement). Held-out conditions: `ho-t3` (df 3),
  `ho-step2` (factor 2), `ho-both`; the registered one is `ho-both`.
- **Byte identity**: the new kinds draw from a second stream (its own SplitMix64 output
  number); the first stream's draws and their order are untouched, so mismatch off and all
  sixteen existing conditions reproduce byte for byte (tested against committed digests).
- **Alternatives**: a harsher outlier rate (inside the family's shape; the model would have
  seen its neighbours); sensor drop-outs (the generator already has them).
- **Check before registering**: that the held-out conditions hurt C″ at all (Gate H lesson:
  see what a grid can yield). Read on validation, not test.

## R3 The training mix

- **Decision**: a condition per scenario index from its own stream: a quarter clean; otherwise
  each of the four existing kinds on with probability one half, severities log-uniform from
  the mild to the harsh grid value (correlation time 30–180 s, share 0.3–0.7; bias sd
  0.25–1°; level factor up to 1.25–2; outlier rate 0.5–5%, spread 5–15). The held-course fifth
  of each batch keeps spec 012's share and takes the same mix.
- **Rationale**: the model must not be handed the exact test conditions; the grid's values
  are interior points of the ranges, and the record says so (they are in range, not a
  mismatch for the model).
- **Alternatives**: the sixteen grid points only (memorisable); always-on mismatch (the clean
  cost M4 would be certain).

## R4 Budget

- **Fact**: the ledger reads $40.57. `gputrain.yml` refuses a plan past $45. Modal's own total
  for November is about $41, so the ledger is close to complete.
- **Decision**: plan inside the $45 guard: pilot at most 1 T4-hour ($0.66), three fine-tunes
  of at most 1.8 hours each ($3.56), total $4.22. If the owner raises the guard to $49, the
  fine-tunes become 3.5 hours each; the decision record binds whichever plans exist then.
- **Fine-tune**: learning rate 1e-4 after 300 warm-up updates, cosine to zero; batch 256;
  about 4 million scenarios a seed at 600 a second in 1.8 hours. The first tokens of the
  schedule and the rate are the pilot's to change once.
- **Alternatives**: one seed for longer (no seed spread; rejected by the constitution).

## R5 Step 1's rule and size

- **Rule** (committed before the run, FR-012), on `all-central`, three seeds pooled: "holds
  up" if the regressor's median range error is within 10% of its own with mismatch off and
  C″-robust ÷ regressor is wholly above 1. Otherwise step 2 proceeds.
- **Size**: 300 σ = 1° engagements per condition (ordinals 0–299 of seed 321), all sixteen
  conditions, every system. C″ runs twice per condition (plain and robust final solve):
  32 classical runs in shards of 100, queued so that at most 16 jobs run at once.
- **Deviation from Gate H's 1,000**: for cost; intervals are reported and a condition whose
  ratio is not separated is called that.

## R6 Readings and statistics

- Per scenario, each system's median relative range error over its scored rows; the paired
  log ratio per scenario; geometric mean with a scenario bootstrap (2,000 resamples), the
  median ratio, shares better, twice as good, twice as bad; three seeds pooled by averaging
  the log ratios within a scenario, and each alone.
- All rows and rows every system answers; counts beside every ratio.
- Course and speed: efficiency against the known-manoeuvre bound and the same paired ratios.
- Coverage: per quantity, by scenario bootstrap; with the median of |error| ÷ stated sd
  ÷ 0.6745 beside it; by range band and by time since the last target change (true times;
  a reporting slice only).
- Thresholds as in the spec (FR-030, FR-042). Forecasts are written in the decision record
  after step 1 and the pilot, and labelled by what they were based on.

## R7 The hybrid

- **Decision**: a subclass of the physics layer (as `headroom/gls.py`; `physics/layer.py` is
  not edited) whose final solve on C″'s segmentation adds three prior residuals at row k: ln
  range and the two velocity components, each (layer − regressor) ÷ (w · stated sd), and
  starts from the regressor's state. w is chosen on validation from a small grid; the row
  falls back to C″ when the regressor states no finite sd or the solve fails.
- **Comparator**: the same residual on ln range only with the static prior of spec 012's
  control.
- **Limit known beforehand**: C″'s final solve keeps C″'s segmentation; where that is wrong
  the prior fights a wrong model, and the fixed fade already down-weights old bearings.

## R8 Fragilities of the regressor worth watching under mismatch

- Its frame is rotated to the first valid bearing and its position is placed along the last
  valid bearing: a wild first or last bearing turns the frame or the position. Range, course
  and speed are read separately so this shows as course error, not as range error. Reported
  by whether the first bearing is an outlier (truth side file); not repaired in step 1.
