# Addendum 2 (2026-11-14): the trained seeds

The three training runs completed as registered (`experiments/20261114-tlm-runs/`; config
digests equal to `decision.json`). The test run file `configs/timelate/runs/tl-e-test.json`
now names, for `learned-s1`, `-s2` and `-s3`, the results branch, folder and training plan
of each; its splits, sizes and `controls_record` are unchanged. Its SHA-256 at launch is
in the launch commit's record of the run (`run.json` on the results branch).

Nothing in the plan, the criteria or the code changes. The learned model has been scored
on no validation or test period. The test on seed 341 is launched once, after this commit.

**Shard size.** The test's 2,860 periods in shards of 10 would be 286 jobs, above the 256
a workflow matrix allows; the run file's `shard_size` is 12 (240 jobs). The periods, splits
and sizes are unchanged. (C″'s track can differ in the last bits with the shard's
composition, as recorded since Gate S; it is one of the reported systems, not a side of
the criteria.)

**Checked before launch**: the workflow's new step (fetch each checkpoint, predict, score
beside the controls) was run locally through bash against the three real checkpoints on
three periods of the spent tuning seed 338; the checkpoints' digests equal the training
records; no error figure was read from that check.
