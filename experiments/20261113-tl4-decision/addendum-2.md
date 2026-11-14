# Addendum 2 (2026-11-14): the trained seeds

The three training runs completed as registered (`experiments/20261114-tlm-runs/`; config
digests equal to `decision.json`). The test run file `configs/timelate/runs/tl-e-test.json`
now names, for `learned-s1`, `-s2` and `-s3`, the results branch, folder and training plan
of each; its splits, sizes and `controls_record` are unchanged. Its SHA-256 at launch is
in the launch commit's record of the run (`run.json` on the results branch).

Nothing in the plan, the criteria or the code changes. The learned model has been scored
on no validation or test period. The test on seed 341 is launched once, after this commit.
