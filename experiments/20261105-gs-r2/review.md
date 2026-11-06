# Gate S agent review panel

**Decided: S1 pass, S2 pass, S3 pass, S4 inconclusive; reference C; panel round 2, on record r2**
(`experiments/20261105-gs-r2/`). Inconclusive counts as not passed (decision record), so C is
Gate 2's segmenter and control, and learning is recorded as not shown (FR-072).

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
  it cannot help C against GLR + confirm. *Corrected in round 2 (geometry, N1):* the convention
  is shared, but its effect is not neutral between C and L, because L is open at k less often
  (944 rows against 1,148); see round 2. Changing it now would change C's design after results. The algorithm note states it,
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
- *Fixed in part* (e4e550f; completed in round 2 by `slices-extra.json` for zig angle and time
  since the zig). Per estimator: gross rates (no plausible estimate; range error over 50%),
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


## Round 2 (5 November 2026): record r2 at 9957471 (`experiments/20261105-gs-r2/`)

The same five specialities, read-only, given round 1's findings and responses, the r2 record, the
re-made inputs and the code changes since round 1.

| Reviewer | Verdict | Blocker | Major | Minor |
| --- | --- | --- | --- | --- |
| TMA geometry | approve-with-findings | 0 | 0 | 4 |
| Estimation and numerics | approve-with-findings | 0 | 0 | 4 |
| Evaluation statistics | approve-with-findings | 0 | 0 | 4 |
| Reproducibility | approve-with-findings | 0 | 0 | 3 |
| Red team | approve-with-findings | 0 | 0 | 7 |

Every round-1 blocker and major is resolved: R1 fixed and verified (geometry traced every other
path by which a decision after k could reach prefix k and found none; red team re-segmented ten
open-transition prefixes at HEAD with the bearings after k removed, all equal; statistics found
the r1 → r2 change confined to C's and L's open-transition prefixes); R2 answered (with the
correction N1 below); R3 and R4 answered and recorded; R5 resolved in substance; R6 fixed (with
the slices completed in round 2).

### Summaries

**TMA geometry: approve-with-findings.** R1 resolved: the only field changed after acceptance is
start/end/closed_at at close; end and closed_at are used only once closed_at ≤ k; score, drop and
near misses never change; closed-at-acceptance transitions are polished only at acceptance; L's
evidence, O's labels, GLR and the search are causal. Cutting fixture scenario 2 to n = k + 1 for
k = 573–575: new code 0 of 3 differ, old code 3 of 3. r1 → r2: 728 of C's 732 changed prefixes hold
an open transition, each moving its start by −3 to +3 rows (one merge, N3). R2 answered for S1–S3:
on the 1,148 rows open at k C recovers 0.657 against 0.905 elsewhere, GLR + confirm 0.159 against
0.142; without them S2's margin is 0.763. r2 is geometrically plausible (bands monotone; C at 2.7×
and the oracle at 1.6× the bound consistent with the gap hand-over).
- [minor] N1: S4's whole L − C difference sits on open-transition rows (neither open, 18,481 rows:
  C 0.9066, L 0.9065; either open, 1,440 rows: C 0.677, L 0.732), because L is open less often;
  round 1's "the convention is the same for C and L, so S4 is unaffected" is wrong. The verdict
  does not change.
- [minor] N2: the regression tests masked the bearings after k but kept n, so a close scheduled
  after k still ran; the new test failed on the old code only through its pinned value.
- [minor] N3: an open transition reserves [s, s + 1] in `_free`, so transitions can overlap and
  merge; polished transitions reach 42 rows.
- [minor] N4: the 4 changed prefixes away from open transitions (ordinal 3445) are put down to
  runner noise without evidence; segment runs record no CPU model.

**Estimation and numerics: approve-with-findings.** R3 resolved (answered: the README gives the corrected figures and cause; not retraining is correct; s2 no better than C, AUCs 0.42–0.53). R4 resolved as a recorded, deferred defect (C and L share the tables; confirmation re-costs every nomination; Gate 2's record should list the fix with a monotonicity check on the validation tables). Round-1 minors acceptable. New checks: efficiency reproduces exactly on all 5,059 scenarios (oracle 1.631/1.870/1.834, C 2.719/2.949/2.754, one leg 15.60/20.58/14.35, naive 7.987/22.65/6.287); 19 of 19,921 rows have a singular bound; in the 67 change-free rows every estimator scores 1.136 (the bound's scale is right); the oracle's 1.6 is the gap hand-over's floor (it masks bearings the bound uses); naive below one leg is genuine (one leg's constant-velocity fit over several unmodelled changes; naive also lower on one leg's finite rows, 0.399 vs 0.413).
- [minor] `gs.py:41` `_q` raises IndexError on an all-infinite cell (not triggered here).
- [minor] Labels: efficiency counts no-estimate rows as above any finite value (one leg 15.6 vs 9.6 on finite rows); "Range > 50%" includes no-estimate rows; neither stated.
- [minor] Say what the bound assumes (change profiles known), so the oracle's 1.6 reads as the hand-over's floor; give C beside the oracle and naive too.
- [minor] No unit tests for bounds, efficiency_of, naive_errors, strata, glr_confirm_intervals, _q.

**Evaluation statistics: approve-with-findings.** Recomputed S1–S4 for r2 from `errors.npz` and the r2 segmentations with the repo's bootstrap: every number matches `verdict.json` to the last digit (S2 +0.7549249 [0.7112297, 0.7977379]; S3 P90 −0.0012464 [−0.0055556, +0.0036036] on 19,766 paired rows; S4 +0.0011798 [−0.0031191, +0.0049002]); README medians, gross rates and finite-row medians match for all nine estimators; committed files byte-identical to the CI branch. Between r1 and r2 the one-leg, oracle, IMM and GLR + confirm errors are byte-identical; only C (730 rows) and L (582) changed, every changed error row has a changed segmentation, and 728 of C's 732 changed prefixes hold an open transition. Validation recomputed: mode gap (+0.00577 [−0.00284, +0.01267]), S2 +0.63242, carried s3, shuffled −0.00158 [−0.00891, +0.00499] pass. Round-1 findings: median convention resolved; S3 vacuity answered (wording drift below); S1 answered; first run resolved. Re-scoring seed 315: legitimate as the correction of a measurement error (panel-mandated, confined to open-transition prefixes, nothing else changed, identical verdicts, r1 kept), not a new look; a fresh seed would itself amend the decision's bound test seed after results. Conditions: say so in the README, do not present r2 as independent confirmation of r1, Gate 2 takes a fresh seed.
- [minor] Physics-layer errors differ between CI runners: the two r2 validation scorings at the same commit differ (one leg 8,673 of 11,802 values, 12 rows flip finiteness, median 0.581251 vs 0.580468; C-gap gap 0.8914 vs 0.8912); the l run matches round 1's local runs exactly. No rule affected (paired within a run). Record the CPU model; state that byte reproducibility holds only on one CPU family.
- [minor] The algorithm note defines false split as "any transition on a scenario with no target change"; the code counts prefixes with no change begun by k.
- [minor] S1 with no rows raises (`finite_stat` → bootstrap ValueError); only `paired()` returns NaN.
- [minor] The second look at seed 315 is not justified in writing.

**Reproducibility: approve-with-findings.** Round-1 findings resolved: every input fetched from its results branch matches `manifest.json` (C e33a1cd1…, L 02d6807a…, GLR + confirm 66 files → 38bd1f04… as `_input_digests` computes, naive split e8150cb0… = seed 314 validation, truth 1a8d55fe…, decision, plan, carried.json, seed315-digests); the record is byte-identical to `results/score-r2-gate-42068715251`; `score.yml` regenerates the data at its commit, checks the digest and scores from a clean checkout; between 7fe8874 and 9957471 only `cli/gs.py` and `segment/score.py` changed (not used by tma2-segment); 5541e54 and 9957471 have the same `src` tree; the first run's manifest is committed. Headers: C 60e6ee63… = params digest, L a187379e… = expected_l_sha for 1b243020…, both 7fe8874 clean. Validation c/ and l/ byte-identical to their branches; carried and shuffled numbers match. Re-runs of C and L on test ordinals 7 and 25 (six of seven prefixes inside an open transition): all 14 C prefixes and 6 of 7 L prefixes reproduce exactly.
- [minor] L's intervals depend on which scenarios share its physics-layer batch: ordinal 25 alone accepts an extra transition at prefix 245; re-run as 25–26 (CI's padding, r_max 683) all 8 prefixes reproduce. Padding (`r_max` over the chunk, `segmenter.py:145`) changes last bits that flip a near-threshold acceptance. The gate is unaffected (segmentations reproduce from a plan's ordinals and shards with CHUNK = 16), but a subset re-run can differ. State it, or pad to a fixed length.
- [minor] Validation C's segmenter digest (2e05b4b6…, mode chord in the T021 plan) differs from the gate's; `confirm.py` never reads `mode`, so the intervals are the same segmenter's. Say so in the r2-val README.
- [minor] Non-gate scorings write no input digests (bound only by run.json and plan.json branch names).
- [note] `segment.yml`'s run.json has no CPU model; the chunk layout matters more than the CPU for segmentations.

**Red team: approve-with-findings.** R1 resolved: between e648f8b and 9957471 only `Transition.accepted_start`/`start_at` and segmenter.py:103 touch segmentation; r1 vs r2 on all 19,921 test prefixes: C changed on 732 (727 only the start of the final open transition), L on 583 (582); r2's C has exactly 1,148 open-final prefixes; an independent causality check at HEAD (bearings after k masked, 10 prefixes in 6 test scenarios, 9 with the last interval open) gave full = cut = stored r2 on every one. R5 resolved in substance (S2 uses the registered GLR + confirm, not the diagnostic); R6 mostly resolved; median convention, "mostly GLR", empty set, S1 answered. Process clean: decision, plan and carried.json untouched; same digests; ordering 7fe8874 segmentations → 5541e54 validation → 9957471 test; no unrecorded test scoring; the only post-r1 changes reaching the gate statistics are the fix, the registered median convention and NaN for empty criteria, none of which can favour a pass; follow-on matches FR-072.
- [minor] "S2's margin is segmentation, not hand-over" holds on all rows only; on the 14,142 rows every estimator answers the gap hand-over helps GLR + confirm (0.276 vs 0.263). It explains at most ~0.02 of a ~0.57 margin.
- [minor] The decision not to take constitution IV's re-score is not in the README or blog.
- [minor] The 0.90 headline's dependence on failed one-leg rows is not quantified (≈0.84 on rows every estimator answers; 0.839 with naive as the baseline).
- [minor] Slices incomplete: no zig angle or time since zig; the "changes" stratum is uninformative (19,849 of 19,921 rows in "1-5").
- [minor] 4 prefixes changed between r1 and r2 away from open transitions (scenario 3445, a closed transition [18,39] → [18,36]): a polish choice flipped on last-bit cost differences.
- [minor] `segmenter_sha256` binds parameters only, so stale (leaky) segmentations would pass the preflight; Gate 2 should bind the segmenter code commit.
- [minor] S3's result row should say "underpowered".

### Responses

- **Geometry N1**: *accepted.* R2's sentence is corrected above; the write-up and AGENTS.md
  record the open-transition hand-over as the main lever for Gate 2 (C 0.66 on open rows against
  0.91 elsewhere).
- **Geometry N2**: *fixed.* Both invariance tests now cut the scenario to rows 0 … k (`_cut`);
  with `start_at` patched to the old behaviour the equality assertion alone fails (start 538
  against 541), and it passes on the fixed code.
- **Geometry N3**: *recorded* in the algorithm note and AGENTS.md, to fix with the search defect
  before Gate 2.
- **Geometry N4, reproducibility note**: *fixed:* `segment.yml` and `score.yml` runs record the
  CPU model.
- **Numerics**: *fixed:* `_q` on an all-failed cell returns +inf; unit tests for `bounds`,
  `efficiency_of`, `naive_errors`, `strata` and `_q`; the README states how failed rows count in
  efficiency and "Range > 50%", what the bound assumes, and C against the oracle (1.8×) and the
  naive baseline (0.30×). The cost-table fix is a Gate 2 prerequisite, with a monotonicity check
  on the validation tables (AGENTS.md).
- **Statistics**: *fixed:* S1 with no rows is inconclusive; the algorithm note's false-split
  definition is the measure as built; runs record the CPU model and the r2-val README says that
  part of the round-1 → round-2 differences is runner noise; the r2 README says why the same seed
  was re-scored, that r2 is not an independent confirmation of r1, and that Gate 2 takes a fresh
  seed.
- **Reproducibility**: *fixed:* the batch-padding dependence is in AGENTS.md's gotchas and the
  algorithm note; the r2-val README explains validation C's different digest (confirmation does
  not read the mode); every scoring writes `inputs.json` with its input digests.
- **Red team**: *fixed:* the hand-over wording ("at most about 0.02"); the finite-row headline
  (0.838 on the 14,142 rows every estimator answers; 0.839 from the naive baseline) in the
  write-up, README and AGENTS.md; the re-score not taken, with its reason, in the README and
  write-up; zig-angle and time-since-zig slices (`slices-extra.json`,
  `scripts/research/gs_slices_extra.py`); the 4 non-fix prefix changes; the segmenter digest
  binding parameters only, with "bind the code commit" as a Gate 2 prerequisite; S3's row marked
  underpowered in the write-up.

No reviewer rejects and no blocker or major finding is open. The verdict stands as decided above.
