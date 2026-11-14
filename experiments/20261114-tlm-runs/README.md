# Spec 016 (study L): the three training runs (2026-11-13 to 14)

Plans `configs/regress/tlm-s1..s3.json` as bound in `experiments/20261113-tl4-decision/`
(config digests `537b1a6b…`, `08370981…`, `36e234b5…`: equal to the record), commit 2c191b2,
clean tree, a Modal T4 each. `tlm-sK.run.json` is each run's record; the weights are on the
results branches.

| Seed | Workflow run | Results branch | Updates | Periods | Periods a second | GPU seconds | Checkpoint |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 43507401545 | `results/gputrain-tlm-s1-43507401545` | 49,000 (complete) | 12,544,000 | 497 | 24,517 | `9767a4a0…` |
| 2 | 43507608865 | `results/gputrain-tlm-s2-43507608865` | 49,000 (complete) | 12,544,000 | 430 | 25,967 | `ebd545a8…` |
| 3 | 43507809179 | `results/gputrain-tlm-s3-43507809179` | 49,000 (complete) | 12,544,000 | 501 | 24,846 | `802cdfcf…` |

On the monitor slice of the training stream (mixed conditions; **not** a validation or test
result), the median absolute error of ln range ended at 0.067, 0.066 and 0.066, and the
manoeuvre term at 0.172, 0.173 and 0.172. The three seeds agree closely.

## Spending

The ledger records $14.22 for the three runs and $40.57 in all; the owner's Modal
dashboard showed $40.96 for November on 14 November (T4 $35.89, CPU $4.37, memory $0.69).
The 39 cents between them are the pilot's replaced container and two failed start-ups,
which the ledger cannot see. About $9 of the owner's $50 is unspent. No further GPU run
is planned in this study.
