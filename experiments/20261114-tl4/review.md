# Spec 016 (study L): panel review, round 1 (2026-11-14)

Five independent reviewers (numbers and provenance; fairness of the comparison; statistics
and criteria; code; scope and conclusions) read the spec, the decision record and its
addenda, the tuning, validation, training and test records and the code at the registered
commits, and recomputed from the per-row errors. **All five: approve with findings. Decided
in one round.** The registered outcome stands: learning is shown on no split, there is harm
on Annex B data, and by the rule the classical controls stand and the learned track stops.
No bug changes a decided number. What the outcome *means* is narrower than the record
first said, and several of its readings are corrected.

Figures here that are not in the generated files are the reviewers' recomputations from the
per-row errors (results branch `results/timelate-tl-e-test-43563825793`) or, where marked
**tuning**, explorations on spent seed 338 with seed 1's checkpoint. Neither is a
registered result.

## Verdict on each registered item

| | As registered | Panel |
| --- | --- | --- |
| L-a | Passes (0.95; all converged; 0.085 held) | Reproduced. Read on Annex B only: on the outlier splits the true-history fit has a consistent cost in 6% and 0% of periods, and 27% of references are held on the shifted split |
| L-b | Search ÷ control 1.68 outliers, 1.33 correlated, 1.03 shifted, 1.08 shifted 2 | Reproduced, and it replicates over tuning, validation and test. **The classical controls are the result worth carrying.** "Gap closed" is not a meaningful statistic where the reference is not a ceiling; the table mixed the declared and undeclared control in one row |
| L-c | Not shown on any of five splits | Reproduced with independent code; all 42 ratios match; no side changes under BCa, a t-interval or other bootstrap seeds; the nearest losing side is 2.7 standard errors from 1. **But the loss is a tail**: the median per-period ratio is 1.00 on every split, and the whole loss sits in the quarter to half of periods where the model declares fewer manoeuvres than the control |
| L-d | Harm on Annex B; the learned track wins on held course | Harm is robust (sign test p < 0.001; trimmed ratio unchanged). "Harm" misleads as a word: the read-out is level with the control in the median period and 1.8 times better than C″. The held-course "win" is not a learned track: where both declare no manoeuvre the two are the same one-leg fit; the 1.06 is the control's false manoeuvres in 23 of 299 periods |
| What follows | The classical controls stand; the learned track stops | **This model with this read-out stops.** The registered comparison was a thresholded manoeuvre detector against the evidence search, not a learned estimator against a classical one. A learned proposer inside the search was not tested by the registration |

## What was checked and found sound

- All 42 criterion ratios recompute from the per-row errors to four decimals; no period has
  a non-finite median for any system on a criterion split.
- The three generated files reproduce byte for byte; the committed summary equals the
  results branch's.
- Every digest in `decision.json` (14 configurations, 16 files) equals the file at the
  registration commit, at the test's commit and at HEAD. Between registration and test only
  the test run file, the addenda and the validation and training records changed.
- Order: decision record 21:04:22; training runs created 21:04:46 to 21:07:22; validation
  run 21:08:24, committed 23:20; training branches 03:55 to 04:20; one test run, attempt 1,
  05:55 at fbda7fa. No learned track was scored on seed 340 or 341 before it.
- Checkpoints on the three branches hash to the values in the training records; training
  ran at the registered commit to completion, last checkpoint, no selection on a monitor.
- The model's inputs carry no truth; training reads seed 339 only; the learned track's frame
  and rotation are right (exact targets reproduce the truth to 1e-5 on tuning data); the
  trained model's errors on tuning data match the monitor's.
- The second-difference algebra of the correlation estimate is right; `with_quiet` equals
  prior kind "mix"; the search cache serves the right problem and prior; the hedged track
  never mixes problems.
- C, C″ and spec 015's registered modules are unchanged (digests `3b67d026…`, `e5040f5e…`).

## Major findings

1. **"About 20% worse" is a tail, and the tail is the untuned manoeuvre threshold**
   (four reviewers). Control ÷ read-out, seed 1:

   | Split | Paired ratio | Median per-period ratio | Ties (under 0.1%) | Learned over twice as bad / over twice as good | Where both declare the same number | Where the model declares fewer |
   | --- | --- | --- | --- | --- | --- | --- |
   | Annex B | 0.82 | 1.00 | 0.23 | 0.20 / 0.11 | 0.95 [0.88, 1.03] (274) | 0.52 [0.39, 0.68] (95) |
   | Shifted | 0.82 | 1.00 | 0.10 | 0.27 / 0.13 | 1.01 [0.92, 1.13] (170) | 0.62 [0.51, 0.75] (179) |
   | Correlated | 0.83 | 1.00 | 0.21 | 0.23 / 0.12 | 1.04 | 0.51 |
   | Outliers | 0.78 | 1.00 | 0.22 | 0.23 / 0.09 | 0.95 | 0.52 |

   Where the model's manoeuvres agree with the search's, the read-out *is* the classical
   arc fit. The registered comparison measured the model's detector at a threshold of 0.5
   that was never tuned, while the control's margin, quiet probability and temperature were
   tuned on seed 338, and the model was never scored on validation although the order of
   events allowed it once the controls' record existed. A plain sign test separates Annex B
   (p < 0.001), outliers (p 0.003 to 0.02) and correlated errors (p 0.03 to 0.06), but not
   the shifted split (p 0.02 to 0.10) or shifted 2 (p 0.25 to 0.9).

2. **Tuning the read-out would not have rescued it; a search started from the model is a
   cheaper equal, not a better system** (fairness; **tuning**, 53 Annex B and 43 shifted
   periods, seed 1). Lowering the threshold makes the read-out worse on Annex B (0.78 at
   0.5, 0.69 at 0.3, 0.59 at 0.2): the fit can no more remove a false manoeuvre than add a
   missed one. The broad prior in the read-out changes nothing (0.81). The control's own
   search started only from the model's track and spans equals the control (1.00
   [0.81, 1.24] Annex B, 1.06 [0.85, 1.32] shifted) at about a third of the search time.
   At no threshold is the model's detector clearly better than the control's search
   (missed/false at 0.5: 0.31/0.06 against the control's 0.25/0.20). So the registration
   did not leave a win on the table; it left an untested equal.

3. **The model's own track is "level" in range only, and it is a prior-informed hedger**
   (statistics, fairness, scope). On the shifted split control ÷ own track is 1.01 in range
   but 0.79 [0.68, 0.92] in course and 0.77 [0.66, 0.88] in speed; with correlated errors
   0.99, 0.83, 0.86. And the pooled 1.01 hides opposite signs: where the bound is over
   0.05 the own track beats the control on every seed (1.30, 1.40, 1.34; 219 periods) and
   where it is under 0.02 it is at 0.36; by range, 1.36 over 19 km and 0.65 under 12 km.
   The record's "it never wins" is false by slice. This is the pattern of Gate H and spec
   012: a shrinkage estimator wins where the bearings determine little and loses by two to
   three where they determine much. Post hoc, range only (course and speed are not
   separated on the same rows), and so not evidence of learning.

4. **The "mismatch" splits are mismatched for the classical side only** (fairness). The
   correlated, outlier and first shifted conditions all sit inside the model's training
   ranges; shifted 2 mostly. Bias is truly absent from training but is a Gauss–Markov error
   like the trained correlated one with a longer time: the mildest held-out condition
   possible. The model lost in-distribution, which strengthens the negative for *this*
   model and makes "no transfer advantage" a weak transfer test. The other way, the
   correlated-error control knows the generator's error family and editing at 4 sd meets
   only 10-sd outliers.

5. **What the record claims for the control is too wide** (statistics, scope, fairness).
   "Better wherever the bearing errors are not as assumed": under bias it is 1.00
   [0.96, 1.05]. "At no cost on Annex B": 1.06 tuning, 0.96 [0.90, 1.02] validation, 1.09
   test, a spread wider than one interval states, with a median ratio of 1.00 and 70% ties
   on each. And it calls a one-manoeuvre target quiet more often: 0.14 against 0.13 on
   Annex B (0.18 against 0.12 on validation), 0.29 against 0.05 with correlated errors,
   0.17 against 0.04 with 5% outliers. Its clean-data side effects were not stated: the
   correlation estimate fires in 8% of clean periods.

6. **The outlier "gap closed" is read against a broken yardstick, and the L-b table mixed
   systems** (statistics, scope, fairness). The reference is fitted to unedited bearings:
   on the outlier splits its fits have a consistent cost in 6% and 0% of periods and the
   control beats it in over half. The shares 1.20 and 1.55 mean only that. The table's
   ratio column was for the declared control and its gap-closed column for the undeclared
   one (held course: 0.35 against 0.86 declared). Control ÷ reference by how the reference
   is fitted:

   | Split | Held | Times free | Times held | Registered (held where drifted) |
   | --- | --- | --- | --- | --- |
   | Annex B | 0.09 | 1.25 | 1.88 | 1.28 |
   | Shifted | 0.28 | 1.70 | 2.14 | 1.84 |
   | Shifted 2 | 0.06 | 1.15 | 1.52 | 1.17 |
   | Correlated | 0.27 | 1.19 | 1.54 | 1.32 |
   | Outliers | 0.19 | 0.83 | 1.20 | 0.92 |
   | Bias | 0.14 | 1.22 | 1.54 | 1.28 |

   The shifted-prior gap is 1.7 to 2.1 under every convention and nothing closes it: that
   part of the record is robust. But Annex B itself is 1.25 to 1.9, so it is not the only
   gap.

7. **The shifted-prior gap looks like a property of the problem** (scope). The shifted
   split has 3.0 manoeuvres a period against 1.8, smaller turns and 15-minute legs;
   control ÷ reference rises with the number of manoeuvres on every split (Annex B 1.21,
   1.24, 1.43 for one, two, three or more; shifted 1.59, 1.45, 2.08); the control misses
   0.57, 0.49 and 0.41 of manoeuvres at 60, 120 and 240 s; the reference, told the
   structure, drifts in 27% of periods; and two unlike estimators land at the same range
   error. No broader prior or likelihood is likely to close it. Not proved: the classing
   of wrong histories was not rerun on this split, and no bound for unknown times exists.

8. **Delivery gaps the record did not list** (scope, code).
   - The prior-mismatch diagnostic (FR-006) does not work and is not a Bayes factor: it is
     computed after de-duplication, so it compares different histories; it is infinite in
     58 of 300 held-course periods; its median favours the broad prior on quiet targets
     (+4.9) and not under a shifted prior (−1.3). The registered form was not built.
   - Candidate calibration under the broadened prior (user story 3): absent.
   - The export check (FR-015) ran on an untrained toy model only.
   - No naive, IMM or EKF track is scored on the same rows, though the plan's constitution
     check says they are.
   - Counts at 60 and 240 s are in the summary and not tabulated; efficiency is by split,
     not by slice; no single table says classical, hedging or learning per split.
   - `pool` keeps the larger evidence where an equal-weight mixture would add the two (up
     to 0.69 nats against a margin of 1): "the same posterior" in the research note is not
     exact.
   - The read-out's fall-back rule is half vacuous for a learned track: the model's own
     track lies on the smoothed bearing, so its cost is always consistent and the "no
     worse than the start + 9" clause can never rescue a fit.

9. **Provenance weaknesses** (numbers, code).
   - The test record does not state which weights it scored: each shard's header carries
     the checkpoint's digest, the scorer drops it, and the workflow fetches a branch head.
     The chain holds indirectly (each branch has one commit whose checkpoint matches the
     training record).
   - Addendum 2's claim that shard size touches C″ only is wrong in principle: the
     control's searches start from C″'s track, so a last-bit flip there can reach a side of
     the criteria. Not measured; with every losing side at least 2.7 standard errors from
     1 it is not believed to matter.
   - Sixteen cells of the record's medians table were pulled from the summary by hand, and
     the README check tests only that an interval appears somewhere.
   - `run_shard4`, `study_split4`, the controls-record guard and the elimination path on
     real fits have no unit test. The guard does not check the record's seed.
   - `decision.json` does not bind `regress/data.py`, `regress/predict.py`,
     `sim/mismatch.py` or the kernel, which the result depends on.

## Minor findings

- The three seeds are not three tests: they share the training stream in the same order
  and differ in initialisation only; their per-period log ratios correlate 0.73 to 0.85.
  "Every seed" guards training noise, which is small.
- An ensemble of the three would not change the outcome (rough, 20 stored periods a
  split: own track about 5% better).
- The registered power was pessimistic: the realised smallest separable ratio is 1.10 to
  1.16, because the read-out shares fits with the control. Bias is genuinely near 1.
- The L-b forecasts restate the tuning run (1.60, 1.31, 1.04, 1.21): replication, not
  prediction. The rule was near-certain to return "stops": the informative results are
  L-b and the shape of the loss.
- Reading 6 is wrong for shifted 2: declared ÷ hedged is 0.96 [0.92, 1.00], separated.
- Reading 4 quotes the model's own spans; the read-out's are 0.34 missed and 0.08 false
  on Annex B, 0.62 missed on the shifted split.
- Read-out against own track, paired: better on shifted 2, held course and both outlier
  splits (and Annex B on one seed of three); worse on shifted and correlated; not
  separated on three. The forecast's "No" stands.
- With the same, right history the read-out is still about 10% behind on Annex B and
  outliers; not explained.
- Missed manoeuvres carry diffuse probability (tuning: median peak 0.18): a per-token
  threshold cannot use a manoeuvre the model suspects and cannot time.
- Efficiencies below 1 on held course (speed 0.79 to 0.89 for every system and the
  reference): by the repository's own lesson a fault to explain; not explained.
- Training budget: the flat end of the monitor curve is the cosine schedule, not
  saturation; from 10,000 to 40,000 updates the error fell about as data^−0.3. Four times
  the budget might give 30% less error, which would not reach the control where the bound
  is tight (the own track is 2.8 times behind there).
- Paired position ratios in the summary are clipped at 100 m by `study._log` and are
  artefacts; none is quoted.
- `corr.estimate` misreads a true σ below the stated one as a large correlated share; the
  σ-factor conditions are untested.
- The ledger loses a killed container's time (disclosed; 39 cents against the dashboard).
- The local pre-launch check on seed 338 is not a breach of the order, but it left no
  artefact; commit the command and output digests next time.
- `tl4_supplement.py` was written after the results; its choice of what to show is post
  hoc.

## What was and was not tested about learning, specs 012 to 016

- **Tested**: a causal direct regressor (012) and a non-causal one of 12.5 million periods
  (016). Both beat C″; neither matches least squares on held course; the second loses to
  the evidence search by 0.71 as an estimator on Annex B and wins nowhere as registered.
- **Not tested**: a learned proposer or learned candidates inside the search; the model's
  manoeuvre probabilities as a prior; a learned evidence or calibration; training through
  the arc or physics layer (016's read-out is bolted on after training); a larger budget
  or another architecture; a combination of the control and the own track (in hindsight
  the better of the two per period is 1.26 to 1.49 times the control: an upper limit).
- **The founding question**: a learned component has not matched least squares on held
  course except by reducing to it; learning beyond classical rules was small where it was
  isolated (Gate 2: +0.007); each large gain has gone to a classical element (the arc
  model, the prior, the evidence search, editing). The answer so far is "not shown, at
  small budgets, with direct models", not "no".

## What the panel wants next (the owner's choice)

1. **(Recommended) Adopt `ctl` as the standing time-late system and close the direct-model
   line.** Finish the record (below), then one cheap classical study of the shifted split:
   class the wrong histories and score by manoeuvre size and count, to settle whether the
   1.8 is identifiability. No GPU.
2. **A learned proposer registered against `ctl`**: the three trained checkpoints' spans
   and probabilities as starts or candidates of the search, threshold tuned on seed 340.
   CPU only, no new training. Worth doing only if option 1's study shows search or
   evidence failures and not ambiguity; on tuning data it reached parity, not a win.
3. **Stop time-late work and write up.** Defensible; leaves the proposer question open.

Owed to the record either way: the weights' digests from the shard headers; the export
check on the trained checkpoints; IMM and EKF tracks beside; a reference fitted to edited
bearings on the outlier splits; unit tests for the runner and the scorer.

## What should not be concluded

- That learning cannot help the time-late consumer, or that a larger model would lose.
- That the read-out's 20% is a typical loss, or that "harm" means the model is poor.
- That the model's own track is level with the control under a shifted prior: in range
  only, and by a cancellation.
- That the shifted-prior gap is closable, or that it is not.
- That the control handles bearing errors outside the generator's families, or that it is
  free on clean data.
- That three seeds are three independent confirmations.
