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
