# Research: spec 016 design decisions

Each decision: what was chosen, why, what else was considered. Settings named "tuned" are
chosen on tuning seed 338 only and fixed in the decision record.

## R1 Hedged track (FR-002)

**Chosen**: the mean of the candidates' tracks in Cartesian state (position and velocity
relative to nothing: x, y, vx, vy at each scored row), weighted by the candidates' evidence
at temperature T (tuned from 1, 2, 3, 5), over the search's first K candidates (K = 10;
spec 015 kept 5). Range, course and speed are read from the mean state. Formed in the runner
from the stored fits; no refit.
**Why**: it is the posterior-mean track under the search's own posterior, which is what an
error-minimising learned model approximates. Cartesian averaging keeps bearings consistent.
**Considered**: averaging log range, course and speed (averages across a mirror pair are
meaningless either way; reported as an edge case); a median track (not a mean of anything a
loss targets).

## R2 Declaration margin (FR-003)

**Chosen**: re-rank the search's seen histories: the declared history is the one with the
highest evidence among those whose every manoeuvre "pays": removing any one manoeuvre (the
best seen history with that one removed, within the match tolerance) lowers the evidence by
more than a margin M. Combined with a stated quiet probability q in the mixed prior. M from
0, 1, 2, 3, 5 and q from 0, 0.01, 0.1, tuned on the tuning seed's held-course and Annex B
splits by a declared rule: the smallest M and q with held-course false rate at most 0.10.
The runner stores, for each candidate, the best seen history with each manoeuvre removed.
**Why**: spec 015's panel found false declarations under 45 minutes have margins under 3 in
about 90% of cases, and that a 1% quiet probability gives 0.09 false at little cost.
**Considered**: integrating over the manoeuvre's start (the correct evidence for "some
manoeuvre"; it would declare more, not fewer, under Annex B's prior, and is what the hedged
track already expresses).

## R3 Robust likelihood (FR-004)

**Chosen**: two forms, the better on tuning data carried. (a) Wild-bearing editing before the
search (`thin.edit_wild`, spec 014: restored clean quality under outliers in the thinning
study). (b) Huber cost (constant 2.0, spec 010's grid) by iteratively reweighted fits, with
the evidence computed on the Huber cost and its weighted curvature.
**Why**: (a) exists and is nearly free; (b) is the standard and does not discard data.
**Considered**: a Student-t likelihood (a tuning constant more, no clear gain over Huber).

## R4 Correlated-error likelihood (FR-005)

**Chosen**: a first-order autoregressive error plus white noise, matching the generator's
family in form but with parameters estimated per period from the residual autocorrelation of
a first plain fit (lag-1 to lag-12 at 5 s, fitted to share·exp(−lag/τ)); fits and evidence
use residuals whitened by the implied covariance (banded Cholesky; `headroom/cov.py` builds
the covariance). Also reported: the same with the true parameters told (an upper control).
**Why**: a real system does not know τ; the told variant shows what estimation costs.
**Considered**: inflating σ only (does not change which history wins by much; kept as the
cheapest variant in tuning).

## R5 A prior that can be wrong (FR-006)

**Chosen**: prior kind `broad`: Annex B's form with leg mean 22 min (between Annex B's 25
and the shifted 15), leg sd widened by 1.5, turn sizes 10° to 150°, turn rates and
accelerations to 1.5 times Annex B's maxima, speed-change probability 0.5. Kind `mix2`:
log-sum of Annex B and `broad` at equal weight, with quiet probability q from R2.
Diagnostic: for the declared history, log p(history | Annex B) − log p(history | broad),
reported as a per-period score and as a rate of firing at a threshold tuned to fire in 5% of
Annex B tuning periods.
**Why**: the shifted split's statistics must not be used to design the prior (that would be
telling it the answer); `broad` is set from Annex B's own ranges widened, not from the
shifted file. A second shifted split (`shift2`: longer legs, larger turns) is added so the
broad prior is tested on a shift it was not placed between.
**Considered**: a hierarchical prior with hyperparameters fitted per period (one period has
one to three manoeuvres: nothing to fit).

## R6 Evidence faults at the support edges (FR-008)

**Chosen**: prior version 4, used by every control and by the plain search rerun beside
them: (i) the stand-in volume at a support edge uses the one-sided mass (half-normal of the
shoulder plus the inside density) so density × volume is continuous across the edge;
(ii) a duration's mass inside the solver's box replaces 1; (iii) `_leg_tail` extended to
any period length; (iv) acceleration constrained for combined manoeuvres; (v) speed after a
change paired. Tests integrate at edges and bounds. Spec 015's search (version 3) is run
beside it so the repair's effect is seen on the same periods.
**Why**: the declaration margin and the hedged weights read evidence differences of 1 to 3
nats; the known faults are 1 to 3.5 nats exactly where invented manoeuvres sit.

## R7 The learned model (FR-009 to FR-011, FR-015)

**Chosen**: a bidirectional transformer encoder (spec 012's `Regressor` without the causal
mask): 8 layers, width 256, 8 heads; tokens are patches of 6 rows of 5-second data (30 s),
at most 240 tokens (120 min); features as spec 012's canonical frame (rotated to the first
bearing) plus the row's time from the period's start and the period's length. Outputs per
token: mean and log-variance of ln range, vx, vy at the token's last row, and a logit that a
target manoeuvre is in progress. Loss: β-NLL on the state plus binary cross-entropy on the
logit (weight 0.1). Trained with mixed precision on a T4.
**Why**: spec 012's code, throughput figures and ledger apply directly; patches lose no
bearing; non-causal attention is the time-late setting.
**Considered**: a model that proposes histories to the search (the "proposer" of spec 013;
a second stage, only if the direct model shows promise); a GRU (kept as a possible control,
not trained within this budget).

## R8 The declared read-out (FR-010; constitution: the reported estimate comes from a declared physics layer)

**Chosen**: two reported tracks per model. `learned`: the model's direct per-token state,
interpolated to scored rows. `learned-arc`: the arc-model fit (`joint_fit` with prior
version 4) started from the model's track, with manoeuvre spans taken from runs of the
manoeuvre logit above 0.5 (merged within 60 s, at most 10), no search. The registered
comparison is on `learned-arc`; `learned` is reported beside it and its difference stated.
**Why**: the constitution requires the reported estimate from the declared layer; the arc
fit is the time-late layer since spec 013. The direct output shows what the read-out costs
or adds.

## R9 Training mix and what is held out (FR-011)

**Chosen**: periods cut as Gate T does from 5-second engagements of stream seed 339.
Mix by engagement: 40% Annex B ranges; 20% a randomised-statistics family (each engagement
draws its own leg mean 10 to 40 min, turn range and rate limits between half and 1.5 times
Annex B's: covers `shift` and `shift2` without being either); 15% quiet; 25% of all
engagements also get a bearing-error overlay drawn per engagement: correlated (τ 20 to
240 s, share 0.2 to 0.7), outliers (rate 0 to 6%, spread 5 to 15 sd), or both.
Held out of training entirely: bias (spec 010's `bias-central`) and the unknown-σ factor;
scored as the "absent from training" split.
**Why**: the classical controls are not told the test conditions either (R4 estimates, R5
is not placed on the shift); a randomised family is the learned counterpart of a broad
prior. Bias is the mismatch no classical control here addresses, so it tests transfer for
both sides.
**Feasibility**: the generator's kernel is 20k engagements a second at 720 rows; at 5 s an
engagement has up to 1,440 rows. Spec 012 measured 635 scenarios a second on a T4 at 240
tokens; the token count is the same here. Throughput is measured in a pilot before the plan
is bound.

## R10 Budget (FR-013)

**Chosen**: cap $22 of the $24 unspent (ledger cap in T4-hours at $0.66: 33 h). Pilot at
most 1 h. Three seeds of 10 h each (about 23 million periods at 635 a second, if the pilot
confirms). No other GPU type unless the pilot shows a cheaper dollar per period.
**If Modal's monthly credit is confirmed by the owner** the plan may be extended by an
addendum registered before its runs; nothing depends on it.

## R11 Splits, sizes and criteria the sample can decide (FR-016 to FR-019)

**Splits** (seed 340 validation, 341 test; periods per split in brackets for test):
Annex B (400), shift (300), shift2 (300), quiet (300), correlated mild and central
(200 each), outliers central and harsh (200 each), absent-from-training bias-central (200),
whole engagements (60, reported only).
**Criteria** (each a paired per-period geometric-mean ratio of period median range error,
95% period bootstrap, percentile; "wins" = interval wholly above 1.00, "loses" = wholly
below, else "not separated"):
- **L-a (controls are sound)**: on validation, the true-history reference with times held
  has range efficiency in [0.8, 1.3] on tight rows, and at most 25% of references are held.
  Stops the study before the test seed.
- **L-b (controls)**: for shift, correlated-central and outliers-central, plain search ÷
  best control: reported with the share of the gap to the reference closed. No pass line.
- **L-c (the verdict)**: on each of shift, shift2, correlated-central, outliers-central and
  bias: best classical control ÷ `learned-arc` (median of three seeds' ratios; each seed
  reported). Learning is "shown on a split" if every seed wins against the best control AND
  against the hedged track; "hedging" if it wins against the best control's first candidate
  but not the hedged track; "not shown" otherwise.
- **L-d (no harm)**: on Annex B and quiet, the same ratio; "harm" if every seed loses.
- **Power**: stated in the decision record from tuning data as the smallest paired ratio
  each split can separate from 1 at its size; a split that cannot separate 1.15 is reported
  only.
**What follows**: learning shown on at least two mismatch splits without harm: a gate for a
learned time-late system is proposed. Shown on none: the classical controls stand as the
time-late system and the learned track stops. Otherwise: reported, owner decides.
**Why no materiality line**: spec 015's panel; a sign test against 1.00 with three seeds
agreeing is decidable, and the size is reported with its interval.

## R12 Enforcing the order (FR-014)

**Chosen**: the scoring tool takes `--learned` predictions only with `--controls-record
<dir>`; it refuses unless that folder holds a validation summary whose plan digest equals
the decision record's and whose L-a passed, and unless the folder is committed (clean tree,
file tracked). Training reads only the training stream and its own held-out monitor slice
of seed 339.

## R13 Storing tracks

**Chosen**: the runner stores each system's scored-row states for the first 20 periods of
every split so the slides can carry track plots (three studies had none).

## As built (2026-11-13, before any tuning result): departures from R3 to R6

- **R3**: only wild-bearing editing is built. A Huber cost inside the fits and the evidence
  would change the registered fit code, which takes one sd for all bearings or one per row
  of a problem with every row valid; editing needs neither. Not built, and said so.
- **R4**: the correlated-error control does not whiten residuals. It estimates the
  correlated share and time from the bearings' second differences (no fit needed, robust to
  wild bearings) and gives the search one larger sd with the same spectral density at zero
  frequency (`corr.effective`). It is right for anything slow (range, course, speed) and
  cautious about when a manoeuvre happened. The variant told the true parameters is not
  built.
- **R5**: the broadened prior is a second `ManoeuvrePrior` (`configs/timelate/tl-broad.json`,
  Annex B's ranges widened; not placed from either shifted split). The mixture is formed by
  pooling the candidates of the two searches, each prior equally likely beforehand, which is
  the same posterior and needs no new prior code. The diagnostic is the Bayes factor between
  the two priors' best histories (`log_bayes_broad`), which replaces the per-history density
  ratio.
- **R6 deferred**: prior version 4 is not built in this pass. The declaration margin is
  tuned on data and absorbs an over-credit that is roughly constant where invented
  manoeuvres sit; the faults stay recorded in `experiments/20261113-tl3/review.md`. If the
  tuning run shows the margin cannot bring held-course false manoeuvres under 0.10 at an
  acceptable miss rate, version 4 is built before registration.
- **The combined control `ctl`** (new): edit, estimate the correlation (used above a share
  of 0.2), search under both priors and pool. It is what a system not told the conditions
  would run, and it is the classical side of the registered comparison; the single-factor
  controls are scored on their own splits for attribution (FR-020).
