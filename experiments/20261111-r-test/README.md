# Spec 012: test-seed scoring (seed 328) and the held-out-ranges split

## Launch record

- 2026-11-11 20:34 UTC: `rscore/r-a-test` (run 43096825862) and `rscore/r-a-test-heldout`
  (run 43096829248) pushed at commit 7f77188. GitHub Actions was stalled; both runs stayed
  "queued" and **never created a job** (checked 21:30, 22:36 and 00:10 UTC; `updated_at`
  unchanged from the push). GitHub refused to cancel them (409, "not been queued yet").
  No result branch exists. The test seed has not been generated or scored by them.
- 2026-11-12 00:15 UTC: relaunched by pushing this commit to the same trigger branches (the
  plan is chosen by the branch name, so the name cannot change). Nothing under
  `src/tma2/regress`, the CLIs, the scorer, the workflow, `configs/rscore` or C's code differs
  between 7f77188 and this commit (the only additions are spec 013 files; corrected after the
  panel, which checked).
- If an orphaned run later starts and publishes, the result of the relaunch is the record
  and the duplicate is noted here, not read.

Results follow below when the runs publish.

## Results so far (collected 2026-11-12 01:50 UTC; no duplicate: the orphaned runs never ran)

Run 43125383838 (`r-a-test`): the held-course half is published (`test/held/`); the
after-manoeuvres half (`man2`) had not published at collection and is added below when it does.
Run 43125508014 (`r-a-test-heldout`): both halves published (`heldout/`). Scored at commit
1194ea2 on AMD EPYC 9V74 runners. Prediction rows and `errors.npz` stay on the result branches
`results/rscore-r-a-test-held-43125383838` and `results/rscore-r-a-test-heldout-{held,man2}-43125508014`.

### Registered reading 1: held course, test seed 328 (7,816 rows, 1,990 engagements)

Efficiency against the bound (reaches below 1.25 on all three, floor above 2.0):

| System | Reading | Range [95%] | Course | Speed | Range by geometry, best to worst quartile |
| --- | --- | --- | --- | --- | --- |
| Least squares (oracle) | reaches | 0.99 [0.95, 1.03] | 0.97 | 0.98 | 0.98, 1.01, 0.93, 1.02 |
| Regressor, seed 1 | partial | 1.13 [1.08, 1.18] | 1.75 | 1.42 | 1.81, 1.20, 1.00, 0.84 |
| Regressor, seed 2 | partial | 1.16 [1.12, 1.21] | 1.81 | 1.43 | 1.78, 1.23, 1.04, 0.87 |
| Regressor, seed 3 | partial | 1.13 [1.09, 1.18] | 1.74 | 1.42 | 1.75, 1.21, 1.03, 0.82 |
| A tenth of the data | partial | 1.22 [1.18, 1.27] | 2.05 | 1.57 | 2.04, 1.34, 1.08, 0.87 |
| Ownship only | floor | 11.5 | 28.7 | 15.6 | 42.7, 16.1, 10.3, 6.3 |

**Outcome: partial, on all three seeds**, as on validation (1.15 to 1.19, 1.8, 1.4). Against
the forecast in the decision record ("partial; range between 1.3 and 2.5, worse for speed, and
improving with geometry rather than flat"): the reading was forecast correctly; range is
better than forecast (1.13 to 1.16, below the 1.25 line on every seed); speed is worse than
range, as forecast; and the geometry pattern is the opposite of the forecast. The model is
furthest from the bound where the geometry is best (1.8 in the best quartile) and below 1 in
the worst, where the bound is loose and knowledge of the ranges helps: it has learnt the
prior better than the geometry. A tenth of the data is worse than the carried seeds by more
than their spread (1.22 against 1.13 to 1.16), as forecast.

### Held-out ranges, after manoeuvres (reported, not registered; 400 engagements)

Median relative range error on rows both systems answer; difference regressor minus other:

| Regressor | C″ | Difference [95%] | IMM | Difference |
| --- | --- | --- | --- | --- |
| Seed 1: 0.114 | 0.151 | −0.037 [−0.056, −0.016] | 0.419 | −0.306 |
| Seed 2: 0.114 | 0.151 | −0.036 [−0.058, −0.017] | 0.419 | −0.308 |
| Seed 3: 0.113 | 0.151 | −0.038 [−0.059, −0.018] | 0.419 | −0.308 |
| A tenth of the data: 0.114 | 0.151 | −0.036 [−0.058, −0.016] | 0.419 | −0.306 |
| Ownship only: 0.428 | 0.151 | +0.277 | 0.419 | −0.001 |

C at three times its threshold: 0.180 (worse than C″ again). On ranges the training stream
never drew, the regressor still beats C″ by about the same absolute margin as on validation
(−0.042), with both systems worse (validation: 0.065 against 0.105). Two cautions: the model
trained on a tenth of the data does exactly as well here, so the margin is not coming from
scale; and the ownship-only model equals the IMM, which says how weak the IMM is on these
rows, not how strong the model is.

The held-course half of the held-out split has 3 rows from 2 engagements (the held-out ranges
file is a MAN2 file; almost nothing holds course at the scored prefixes): **no reading**. The
plan should not have included it; recorded as a planning error, nothing is read from it.

### Registered reading 2: after manoeuvres, test seed 328 (collected 02:37 UTC)

`test/man2/` (run 43125383838; rows on `results/rscore-r-a-test-man2-43125383838`). Median
relative range error on rows both systems answer; difference regressor minus other [95%]:

| Regressor | C″ | Difference | IMM | Difference | C at 3 × threshold |
| --- | --- | --- | --- | --- | --- |
| Seed 1: 0.066 | 0.105 | −0.039 [−0.045, −0.033] | 0.416 | −0.348 [−0.372, −0.330] | 0.118 |
| Seed 2: 0.067 | 0.105 | −0.038 [−0.044, −0.033] | 0.416 | −0.346 [−0.370, −0.328] | 0.118 |
| Seed 3: 0.067 | 0.105 | −0.038 [−0.044, −0.032] | 0.416 | −0.347 [−0.370, −0.329] | 0.118 |
| A tenth of the data: 0.071 | 0.105 | −0.033 [−0.040, −0.028] | 0.416 | −0.343 | 0.118 |
| Ownship only: 0.335 | 0.105 | +0.230 [+0.217, +0.244] | 0.416 | −0.075 [−0.101, −0.052] | 0.118 |

All rows (scorer's medians): regressor 0.066 to 0.067 in range, 9.5° to 9.7° in course, 1.34
to 1.36 kt in speed; C″ 0.105, 12.7°, 1.48 kt; the true-manoeuvre chord solve 0.062, 6.9°,
0.95 kt; IMM 0.579; one leg 0.596. 90th percentile of range error: regressor 0.217, the
true-manoeuvre solve 0.243, C″ 0.488. By true-range quartile (seed 1 against C″): 0.062 / 0.070,
0.062 / 0.097, 0.065 / 0.112, 0.075 / 0.157: the margin is small at short range and grows
with range.

**Outcome: the regressor beats C″ on the test seed on all three seeds** (−0.038 to −0.039,
intervals well clear of zero), as on validation (−0.042). **The forecast ("worse than C″,
better than the IMM") was wrong in its first half**, on validation and now on test. The
model matches the true-manoeuvre chord solve in range (0.066 against 0.062) and has a
shorter tail, and is worse than it in course and speed.

### What this does and does not support

- A direct learned model, with no physics layer and no segmenter, is better than the
  standing classical system after manoeuvres, on a fresh seed and on ranges it never saw.
  That is the first clear result for learning in this project.
- It is a control, never carried: no covariance, no declared physics layer, no stated
  manoeuvre times, and 1.75 times the bound in course on held course, where least squares
  is at 1.0.
- Why it wins is not established here. Spec 013's tuning results (`../20261111-tl-retest/`,
  `../20261112-tl-prior/`) give the likeliest reason: about half the difficult cases have two
  manoeuvre histories the bearings cannot separate; C″ commits to one, and a model trained to
  minimise error learns to hedge between them and to use the simulator's ranges. Its
  advantage growing with range, its shorter tail, and its sub-bound efficiency in poor
  geometry all fit that reading; none of them tests it.
- "Matches the true-manoeuvre solve" is weaker than it sounds: that solve is the chord
  model, which spec 013 measured at about twice the bound.
- A tenth of the data loses little (0.071 against 0.066), so more data or a bigger model
  (addendum 1, not run) is unlikely to move this much.
- Seeds 2 and 3 stopped at 91% and 97% of the planned updates (decision-record deviation);
  the three seeds agree to 0.001.

## Corrections after the panel (2026-11-12; `review.md`, three approve with findings)

The readings above stand. These statements above are withdrawn or narrowed:

- **"The first clear result for learning"** is narrowed to: *a prior-informed estimator
  trained to minimise the scored error beats a prior-free fit, in median range error*. The
  regressor knows the simulator's ranges, speeds and manoeuvre statistics; C″ uses none.
- **"On ranges it never saw"** is withdrawn. The held-out split differs only in initial
  range (20–30 km against 2–20 km), its realised ranges overlap training, and 276 of the 400
  engagements contribute rows. There the margin by true-range quartile is −0.054, −0.055,
  −0.044 and −0.014 [−0.050, +0.025]: it vanishes at the far end, where on the test seed it
  grows with range. The regressor does not match the true-manoeuvre solve there (0.115
  against 0.084) and its speed is not better than C″'s (+0.26 kt [−0.13, +0.56]).
- **The hedging explanation** is withdrawn as "likeliest". It is untested, spec 013's
  evidence is 57 tuning periods of other data, and the far-range collapse above is what a
  range prior predicts and hedging does not. Leading candidates, untested: a range prior and
  shrinkage toward it.
- **"More data or a bigger model is unlikely to move this"**: the tenth-of-data control
  varies data only. It says nothing about capacity, and on held course a tenth costs 1.22
  against 1.13.
- **"The three seeds agree to 0.001"** was the training loop's own validation figure. On the
  test seed they differ by up to 0.03 on held course (1.13, 1.16, 1.13). The tenth-of-data
  control also stopped early (41,512 of 42,500 updates).

Registered items the first write-up left out (test seed 328, seed 1 against C″, rows both
answer, [95%]): range −0.039 [−0.045, −0.033]; **in metres −657 m [−765, −565]**; course
−3.1° [−4.0, −2.3]; speed −0.14 kt [−0.23, −0.05]. Efficiency against the bound on settled
rows after manoeuvres, regressor seeds / C″ / true-manoeuvre solve: range 1.71–1.73 / 2.52
/ 1.65; **course 3.40–3.57 / 3.19 / 2.04**; speed 2.48–2.55 / 2.63 / 1.86. In course
efficiency the regressor is worse than C″. The three seeds are reported singly, not pooled;
the naive estimator was not in this scorer's output (a gap against FR-020).

Not registered, read off the test seed, and to be treated as description only: the scorer's
all-row medians, the 90th percentiles, the comparison with the chord solve, C at three times
its threshold, the range-quartile and geometry-quartile patterns. The IMM column uses fewer
rows (5,949); on those rows the regressor is at 0.068. The ownship-only model equals the IMM
on the held-out split, so the IMM comparison says nothing about the regressor.

Plan digests (SHA-256; committed at 7f77188 with the validation results, before any test
result, unchanged since; they were not bound in the decision record):
`configs/rscore/r-a-test.json` `e27862aa…5ea8b0c`, `r-a-test-heldout.json` `5e0cd254…4c1783b`.
`headroom.json` labels the split "tuning": a label from the scorer's default, the data are
seed 328.

**For a reader who would use this**: the regressor gives no uncertainty and no manoeuvre
times, is 1.75 times the bound in course on a steady target (3.2 in the best geometry), and
is below the bound in poor geometry, which means it is biased toward what the simulator
usually does. It is a control. Nothing here supports a claim outside the simulator.

**Control run after the panel** (`../20261112-r-control/`, registered on validation before
the test seed): combining C″ with a range prior by precision weighting does not explain the
margin (C″ 0.103, C″ + prior 0.102 to 0.104, regressor 0.066). Simple shrinkage toward the
usual range is ruled out; the source of the margin is still not established.
