# Research: spec 017 design decisions

## R1 Detectability of a true manoeuvre (FR-002)

**Chosen**: the rise in the bearings' χ² (the stated sd) when the true history is refitted
without that manoeuvre, the other manoeuvres' times held, each fit from the nominal starts
with the turn-start search (`detect.detectability`). No prior, no evidence, no search.
**Why**: it is the likelihood-ratio statistic any detector is bounded by. A system that
weighs fit against complexity cannot declare a manoeuvre whose omission costs less than
the complexity charges. Measuring it on the bearings alone keeps it independent of the
prior under question.
**Considered**: the evidence difference under a prior (depends on the prior and on the
Laplace faults recorded in spec 015); the Fisher information of the change (a local
measure; a missed manoeuvre is not a local error).
**Limits**: with the other manoeuvres held, two close manoeuvres can absorb each other
(each then reads low although the pair is detectable); times held make the omission fit
slightly better than a real system's, which has to find the times. Both push detectability
down or the reference's quality up: toward calling the gap identifiability. Stated in the
record.

## R2 References told only the detectable manoeuvres (FR-004, FR-005)

**Chosen**: `ref-dT`: the true history without the manoeuvres whose detectability is below
T, times held, fitted with Annex B's prior (version 3), for T = 10, 20, 40; `ref-full` is
T = 0. Both built the same way, so their ratio isolates the manoeuvres left out.
The gap from a system S to `ref-full` splits as log(S ÷ ref-full) = log(S ÷ ref-dT) +
log(ref-dT ÷ ref-full): the first is attainable by a system that found every detectable
manoeuvre and timed it perfectly, the second is identifiability at T.
**Thresholds**: the evidence charges an extra manoeuvre about 11 nats net under Annex B's
prior (spec 013: about −17 in log prior, +6 in volume), which is 22 in χ². T = 20 is the
primary; 10 and 40 bracket it. The tuning run reads what the control actually finds by
band, to check 20 means what it should.
**Why times held**: a reference with free times drifts into other histories in a quarter
of shifted periods (study L); held times make `ref-dT` an upper limit on what detection
alone could win, so the attainable part is an upper limit and the identifiability part a
lower limit.

## R3 The true prior (FR-006)

**Chosen**: `true`: the control's search on the control's bearings (edited, effective sd)
with the split's own ranges file as the prior, declared by the control's rule (margin 1,
quiet probability 0.01). On Annex B data it is the control with one prior, not two.

## R4 Owed to study L's record (FR-008 to FR-012)

- Weights' digests: a small workflow (`headers/**`) downloads the test run's shard
  artefacts with the run's own token and commits each shard's `learned` header to a
  results branch; the record then lists the distinct `weights_sha256` per seed.
- Export check: `regress.period_predict`'s ONNX check run on the three checkpoints,
  recorded under the training records.
- IMM and EKF as tracks: in this study's runner (Gate T's code), on every split.
- Edited reference: on the outlier split, `ref-full-edit` and `ref-dT-edit`.
- Tests: `study_split4` and the controls-record guard on synthetic shards; `run_shard4`
  on one short fixture period.

## R5 The rule (FR-007)

On the shifted split, with S the declared control: the **attainable share** A =
Σ log(S ÷ ref-d20) ÷ Σ log(S ÷ ref-full) over scored periods, 95% period bootstrap.
- A's interval wholly below 0.5: **mostly identifiability**. The learned-proposer option
  is not taken; the time-late track is written up.
- Wholly above 0.5: **mostly attainable**. A proposer study using study L's three trained
  models is proposed to the owner.
- Otherwise **mixed**: reported; the owner decides.
Reported at T = 10 and 40, on shifted 2 and Annex B, and for the standing search and the
true-prior search. The decision record states the interval's expected half-width from
tuning data and a forecast; if the tuning share is within one half-width of 0.5 the rule
is not registered as a decision and the study reports the share only (spec 015's lesson).

## R6 Sizes and seeds

Tuning 342: Annex B 100, shifted 150, shifted 2 100, outliers 60. Validation 343 (L-a
soundness only): 60 each. Test 344: Annex B 300, shifted 400, shifted 2 300, outliers 200.

## As registered (2026-11-14, after the tuning run, before seeds 343 and 344)

- **R5 is not registered as a decision rule.** On tuning seed 342 the attainable share at
  threshold 20 is 0.32 [-0.08, 0.56] on 137 scored periods; at the test's size its
  half-width is about 0.17, so the tuning value is one half-width from 0.5; and the share
  runs from 0.66 at threshold 10 to below zero at 40. A rule would be decided by the
  threshold and the sample. The study registers estimands, forecasts and the logic of the
  recommendation instead; `study5.verdict` is still computed and printed, and is not the
  outcome.
- **Estimands** (shifted split, each at thresholds 10, 20 and 40, paired per period with
  the median per-period ratio and the twice-as-bad shares beside):
  E1 the share of whole true manoeuvres with detectability under the threshold;
  E2 the control's miss rate by detectability band;
  E3 `ref-dT` ÷ `ref-full`: what not being told the undetectable manoeuvres costs;
  E4 control ÷ `ref-dT`: what remains for a system that found and timed every detectable
  manoeuvre (an upper limit: the reference's times are the truth);
  E5 control ÷ `true`: what knowing the targets' statistics is worth.
  The same on Annex B and shifted 2 beside.
- **The recommendation's logic, fixed now**: a proposer study (study L's trained models
  inside the search) is recommended to the owner only if, on the test seed, E4 at
  threshold 20 is separated from 1 with a lower limit above 1.10 **and** the control
  misses more than a third of the manoeuvres above 40. Otherwise the recommendation is
  to write the time-late track up, with what would add information (longer periods,
  ownship manoeuvres chosen for observability, a hedged answer) named as the remedy. The
  owner decides either way.
- **Sizes**: validation 343: Annex B 60, shifted 60 (soundness only). Test 344: Annex B
  300, shifted 500, shifted 2 200, outliers 150.
