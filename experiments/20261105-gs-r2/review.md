# Gate S agent review panel

Gate S (spec 005, Annex A §A.9), pre-registered in `experiments/20261104-gs-decision/`, judged on
seed 315. Records:

| Record | Folder | Commit | Machine verdict | Status |
| --- | --- | --- | --- | --- |
| r1 | `experiments/20261105-gs/` | e648f8b (segmentations 90dcbc4) | S1–S3 pass, S4 inconclusive | reviewed in round 1; superseded (R1) |
| r2 | `experiments/20261105-gs-r2/` | 9957471 on CI (segmentations 7fe8874) | S1–S3 pass, S4 inconclusive | after the round-1 fixes; reviewed in round 2 |

## Round 1 (5 November 2026): record r1 at e648f8b (`experiments/20261105-gs/`)

Five read-only reviewers in parallel, each given the code and records, not a conclusion.

| Reviewer | Verdict | Blocker | Major | Minor |
| --- | --- | --- | --- | --- |
| TMA geometry | approve-with-findings | 0 | 2 | 6 |
| Estimation and numerics | approve-with-findings | 0 | 2 | 7 |
| Evaluation statistics | approve-with-findings | 0 | 0 | 4 |
| Reproducibility | approve-with-findings | 0 | 0 | 3 |
| Red team | **reject** | 1 | 2 | 4 |

### What the reviewers confirmed

- **Statistics** recomputed S1–S4 from `errors.npz` and the CI segmentations with the repo's
  bootstrap: every number matches `verdict.json`. Pairing and clustering are right; gap recovered
  is a ratio of medians within each resample. Carried rule (s1 0.88682, s3 0.88771, s2 0.89105:
  median s3) and shuffled rule (−0.00202 [−0.00926, +0.00469]) applied as registered. Order:
  decision a38f61b (11-04 22:15) → `carried.json` 83b2bc5 (11-05 06:12) → test plans 90dcbc4
  (06:13) → test results (07:56, 08:26, 09:02); CI run ids increase in the same order.
- **Reproducibility** verified every manifest digest; recomputed C's and L's segmenter digests;
  re-ran C and L on test ordinals 0–1 and 3001 (intervals identical, cost/margin differ in the
  last bits); regenerated seed 315 byte for byte at a38f61b (test 1a8d55fe…); confirmed the
  two-run claim (metrics, report, verdict, errors.npz identical; manifests differ only in commit
  and dirty flag) and the provenance fix.
- **Geometry** checked truth labels on 300 test scenarios (no course or speed change outside the
  spans), the oracle's and C's knots (same rows), the gap hand-over (the oracle's `mask_turns`
  convention), the search's causality, and the detectability bands (monotone, threshold the χ²(4)
  1% point). The IMM sitting at one leg is structural: it initialises from a one-leg fit on
  [0, zig] that contains about half the target's changes.
- **Numerics** checked the CRF (log Z = enumeration, gradients = finite differences, NEG masking,
  the truth-path tie-break, the head is not dead), τ (13.8 is the 2-dof point; 18.45 its 4-dof
  equivalent for closed transitions), and that the cap ±τ/2 does not hold L near C (1.5% of
  windows reach it). L changes C's segmentation on 36% of test prefixes; per-row errors move
  symmetrically (better on 18.3%, worse on 17.7%).
- **Red team** found no leakage: GLR threshold, penalty, τ and mode fixed on validation; L trained
  on stream 317 and early-stopped on tuning ordinals 0–499; seed 315 untouched before scoring;
  decision, plan and gate code unchanged after the decision.

### Findings and responses

**R1 [blocker, red team; major, geometry] C and L read later bearings on prefixes inside an open
transition.** `confirm.py` rewrote an open transition's start in place when it closed (a ±3-row
polish with bearings up to the closing row), and `intervals_at` used that start for every prefix
from acceptance on. FR-002 broken on 1,148 of C's 19,921 test prefixes (5.8%) and 944 of L's.
- *Response: fixed* (7fe8874). `Transition.accepted_start` is kept and `intervals_at` uses it
  until the close. Tests: the interval logic, and a fixture scenario (seed 316, scenario 2, Gate S
  parameters) whose open transition is accepted at row 573 with start 541 and closed at 576 with
  start 538, segmented with and without the bearings after k = 574 (it fails on the old code).
- *Bug-fix re-run, not a change of criteria:* every segmentation the gate depends on is redone at
  the fixed commit on CI with the same parameters, weights and data (`segment/man2-val-c`,
  `segL-val-{s1,s2,s3,shuffled}`, `gs-test-c`, `gs-test-l`); validation is re-scored (the mode
  choice, S2 on validation, the carried rule and the shuffled rule are applied again to the
  corrected segmentations), then the test split. The decision record, plan, limits and rows are
  unchanged. GLR + confirm (note 08's point knots, `leg_spike.py`) has no close-and-polish step
  and is not re-run.

**R2 [major, geometry] An open transition gets a knot and the speed prior at the scored row k.**
- *Answer: intended, now declared.* FR-030 hands over "knots at both ends of each transition", and
  a prefix's segmentation of [0, k] ends an open transition at k, so `segmentation_inputs` puts
  the second knot at k. The oracle and confirmation treat an open span as a start knot only. Under
  either convention the state at k is weakly determined (the transition's bearings are masked);
  the convention is the same for C and L, so S4 is unaffected, and it cannot help C against GLR +
  confirm. Changing it now would change C's design after results. The algorithm note states it,
  and Gate 2's decision record must fix one convention for open transitions across the oracle and
  segmenters before any result.

**R3 [major, numerics] One validation prefix decides L's loss and early stopping.** Ordinal 225,
k = 394, scores 96,196 nats (48.8 of the 55.5 mean); without it the mean is 6.709, s2 lowers it by
11.7% and s3 by 6.2%. Early stopping's relative 1e-3 asked for 0.055 nats where 0.0067 was meant,
so s1 and s3 stopped early.
- *Answer: accepted; the reading is corrected, the gate is not changed.* L was trained exactly as
  pre-registered; retraining it would be a new L and needs a new decision record and a fresh
  seed. The L validation README, the write-up and the deck now say: training was cut short by an
  outlier, so S4 says "not shown with this training", not "no headroom". The best-trained seed
  (s2) is no better than C downstream on validation (−0.0003 [−0.0099, +0.0086]), and the evidence
  barely separates steady from transition rows (AUC 0.53 / 0.42 / 0.48), so a pass was unlikely.

**R4 [major, numerics] The search's cost table has frequent fit failures.** 3,191 adjacent
nested-leg pairs on validation break monotonicity by more than 100 χ²; 345 of 500 scenarios have
one. Cause: warm starts propagated forward, a fresh grid start every fourth step only
(`search.py`).
- *Answer: recorded as a known defect of C's search nominator, fixed before Gate 2.* C and L share
  the tables, so S4 is not biased; the defect weakens C's search nominations, which can only make
  C look worse against GLR + confirm (conservative for S2). Fixing it changes C's nominations and
  L's training tables, so it cannot be done inside Gate S without a new L. C carries into Gate 2
  with the fix (re-solve from a fresh grid start when a longer leg costs less than a nested
  shorter one), re-validated on validation under Gate 2's decision record.

**R5 [major, red team] S2's margin mixes segmentation with the hand-over.** GLR + confirm keeps
note 08's point knots (13,438 on test, no turn windows); its segmentation measures are close to
C's, its downstream error is not.
- *Answer: S2 stands as pre-registered (the reference was frozen by name before any result); the
  record now separates the two.* `tma2-gs` scores `glr_confirm_gap`, GLR + confirm's knots handed
  over as C's segmentations are (gap mode, a point knot as T_min rows), reported, not gated
  (b404c8d). The write-up says C's gain combines transition modelling, the gap hand-over and the
  extra nominator, with the split from `glr_confirm_gap`.

**R6 [major, red team] Gross rows and the slices the constitution requires are missing.**
- *Fixed* (e4e550f). Per estimator: gross rates (no plausible estimate; range error over 50%),
  medians over the rows it answers, efficiency against the known-manoeuvres bound, and strata by
  range band, number of changes, latest change kind, speed-only and transition duration (FR-063);
  the naive baseline (training-set means fitted on seed-314 tuning ordinals 0–499) on the same
  rows. The headline is stated with the finite-row figures beside it.

**Minors.**
- *Median convention (statistics):* the record names `inverted_cdf`; the gap and S1/S3 used
  `np.median`/linear quantiles. Fixed to `inverted_cdf` throughout (e4e550f); points were
  identical, interval ends moved in the 4th decimal.
- *S3 false split close to vacuous (statistics, red team, numerics):* 67 change-free prefixes from
  49 scenarios, 0 for both; the percentile interval is degenerate and an exact one-sided bound on
  0/49 clusters is about 0.085. The code counts prefixes with no change begun by k; the record's
  words ("scenarios with no target change") would give one scenario, also 0 for both, so the
  verdict is the same under either reading. A criterion with no rows now returns inconclusive,
  not [0, 0] (e4e550f). Gate 2 should declare a minimum count or an exact bound.
- *S1 trivially satisfied (all):* acknowledged; it is a declared sanity check, and every MAN2
  ownship turn is a zig of 30° or more.
- *Inputs not bound (reproducibility):* the manifest now records the SHA-256 of every
  segmentation file, the GLR + confirm shards and the naive training split (e4e550f); the README
  names the results branches.
- *Commits during the run (reproducibility):* harmless here (only `segment/train.py`, a mkdir,
  not imported by `tma2-gs`); the re-score runs from a separate worktree, and AGENTS.md gains the
  gotcha.
- *First run's evidence (reproducibility, statistics):* `first-run-manifest.json` committed.
- *Re-score rule (red team):* the decision record counts inconclusive as not passed for the
  follow-on (Annex A §A.9: "otherwise"); constitution IV's one re-score on a larger seed is not
  taken, because S4 has no minimum effect size and +0.0014 on a seed ten times larger would pass
  without mattering. Stated in the README.
- *Mechanism stated without a count (red team):* not counted (two attempts were killed by container restarts); the sentence now says the share was not counted.
- *Speed prior across speed changes, unknown rows scored as steady, one steady row in the truth
  transition (geometry):* conservative and shared by C and L; declared in the algorithm note.
- *Band by the latest change (geometry):* the new strata include the number of changes; a stratum
  by the least detectable change is left to Gate 2.
- *Evidence scale differs between stages; float32 training features; one noise draw (numerics):*
  no effect at present; recorded for a successor.
- *Strict JSON:* `metrics.json` writes Infinity/NaN as Python does; left as is (all readers are
  Python), noted.

### Outcome of the bug-fix re-run (record r2)

- **Validation** (`experiments/20261105-gs-r2-val/`): mode gap (gap − chord +0.0058
  [−0.0028, +0.0127]), S2 +0.632 [+0.561, +0.734], carried model s3 again (s1 0.8867, s3 0.8873,
  s2 0.8908), shuffled rule pass (−0.0016 [−0.0089, +0.0050]). `carried.json` is unchanged.
- **Test** (`experiments/20261105-gs-r2/`, CI run 42068715251 at 9957471, `git_dirty: false`,
  every input file bound by SHA-256): S1 pass (0 [0, 0]), S2 pass (+0.755 [+0.711, +0.798]), S3
  pass (contamination P90 −0.0012 [−0.0056, +0.0036], false split 0 [0, 0]), S4 inconclusive
  (+0.0012 [−0.0031, +0.0049]). The same verdicts as r1.
- **R5's diagnostic:** GLR + confirm handed over in gap mode recovers 0.108 on test (0.143 with
  its own hand-over), so S2's margin is C's segmentation, not the hand-over.
- **R6's reporting:** the references give no plausible estimate on 20–25% of test rows; the naive
  baseline's median range error (0.397) is below one leg's (0.589) and the IMM's (0.577); C is at
  2.7× the known-manoeuvres bound in range, the oracle at 1.6×.
