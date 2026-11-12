# Spec 012: test-seed scoring (seed 328) and the held-out-ranges split

## Launch record

- 2026-11-11 20:34 UTC: `rscore/r-a-test` (run 43096825862) and `rscore/r-a-test-heldout`
  (run 43096829248) pushed at commit 7f77188. GitHub Actions was stalled; both runs stayed
  "queued" and **never created a job** (checked 21:30, 22:36 and 00:10 UTC; `updated_at`
  unchanged from the push). GitHub refused to cancel them (409, "not been queued yet").
  No result branch exists. The test seed has not been generated or scored by them.
- 2026-11-12 00:15 UTC: relaunched by pushing this commit to the same trigger branches (the
  plan is chosen by the branch name, so the name cannot change). Nothing under
  `src/tma2/regress`, the scorer, the workflow, the plans or C's code differs between
  7f77188 and this commit (`git diff --stat` is empty for those paths).
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

**Outcome: partial, on all three seeds**, as on validation (1.15 to 1.19, 1.8, 1.4). Forecast
in the decision record: reaches in range, not in course. Range does reach (below 1.25) on every
seed; course (1.75) and speed (1.42) do not, so the registered reading, which needs all
three, is partial. The model is furthest from the bound where the geometry is best (1.8 in
the best quartile) and below 1 in the worst, where the bound is loose and its knowledge of the
ranges helps: it has learnt the prior better than the geometry.

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
