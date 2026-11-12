# Panel review of spec 012's test record (2026-11-12, round 1)

Three independent reviewers read the decision record, the validation and test records and
their JSON. All three: **approve with findings**. The measured readings stand; several
interpretive claims in the README as first written do not. The README's "Corrections after
the panel" section is the answer; this file is the findings.

## Checks that passed (pre-registration and statistics)

- Over 20 README figures match `reading.json` / `headroom.json`, with intervals and row counts.
- `regress/reading.py` is unchanged since before the decision record; thresholds are in
  `decision.json`.
- Relaunch: between 7f77188 and 1194ea2 nothing changed under regress, cli, headroom, segment,
  physics, `rscore.yml`, `configs/rscore`, `pyproject.toml` or `uv.lock`. (The README's
  "`git diff --stat` is empty" was wrong as worded: spec 013 files were added under
  `configs/timelate` and `scripts/research`.)
- Intervals are clustered by engagement. "Rows both answer" does not favour the regressor
  (all rows −0.0393, rows both answer −0.0387).

## Major findings

1. **Not the same information.** The regressor is trained on the simulator's ranges, speeds
   and leg statistics and its loss targets the scored quantity; C″ is a prior-free fit. The
   honest statement is "a prior-informed, error-minimising estimator beats a prior-free fit".
2. **The gain sits where the bearings say least.** On settled rows after manoeuvres
   (`test/man2/headroom.json`), efficiency against the bound, regressor / C″: range 1.71 /
   2.52, course 3.40 / 3.19, speed 2.48 / 2.63. In course the regressor is worse than C″.
   In the nearest range quartile the margin is 0.062 against 0.070, and the tenth-of-data
   model has none there.
3. **"Ranges it never saw" overstates the held-out split.** `configs/man2-heldout.json`
   differs from the training ranges only in initial range (20–30 km against 2–20 km);
   manoeuvre statistics are identical, and realised ranges overlap training. On it the
   margin by range quartile is −0.054, −0.055, −0.044, −0.014 [−0.050, +0.025]: it
   **vanishes at the far end**, the opposite of the test pattern. The regressor no longer
   matches the true-manoeuvre solve (0.115 against 0.084), and its speed is worse than C″'s
   in point estimate (+0.26 kt [−0.13, +0.56]).
4. **Held course "1.13–1.16" is a pooled figure.** By geometry quartile, range 1.81 / 1.20 /
   1.00 / 0.84, course 3.2 in the best quartile. Values below 1 mean a biased estimator, to
   which the bound does not apply.
5. **The hedging explanation is untested and partly contradicted.** Spec 013's evidence is 57
   tuning periods on different data with an approximate evidence; its own section 3 found
   local averaging does not help. The far-range collapse on the held-out split is what a
   range prior predicts and hedging does not. Range prior and shrinkage are the leading
   candidates.
6. **Registered items missing from the README**: seeds pooled; the difference in metres;
   course and speed differences with intervals; efficiency per slice after manoeuvres; the
   naive estimator is not in the scorer output (FR-020).
7. **For an analyst**, a better median with no uncertainty, no manoeuvre times and 1.75
   times the bound in course on a steady target is not something to rely on; and an average
   between two histories is a position where the target probably is not.

## Minor findings

- The tenth-of-data control varies data, not capacity: it does not show a bigger model would
  not help. On held course a tenth costs 1.22 against 1.13.
- Test plans are not digest-bound in the decision record (committed with the validation
  results, unchanged since).
- Unregistered readings on the test seed need labels (all-row medians, the 90th percentile,
  the chord comparison, C at three times its threshold, quartile patterns).
- The IMM column mixes row sets (5,949 rows against 7,796); the ownship-only model equals the
  IMM, so the IMM comparison carries no information.
- Held-out: 276 of 400 engagements contribute rows.
- "Agree to 0.001" is the training loop's validation figure; on test the seeds differ by 0.03
  on held course. The early stop is recorded in `r-runs/README.md`; the tenth control also
  stopped early (41,512 of 42,500 updates).
- `headroom.json` labels the split "tuning" (cosmetic). Quartile cuts are not re-estimated in
  the bootstrap. "Never created a job" has no archived API output.

## Controls the panel asks for before any further learning claim or GPU spend

- **C″ plus the prior, nothing trained**: combine C″'s ln range and its stated uncertainty
  with the ownship-only model's mean and variance by precision weighting. If that closes
  most of −0.039, the margin is shrinkage toward the simulator's ranges.
- **Hedged C″**: average the fits with and without C's last transition, weighted by evidence.
- Score the existing checkpoints split by whether C″ missed a manoeuvre.
- For the next spec: the learned model must beat a classical estimator given the same prior,
  not C″; a prior-shift split (altered leg and turn distributions); calibration of candidate
  probabilities and whether the true history is in the set, not mean error; a held-course
  arm near the bound.
