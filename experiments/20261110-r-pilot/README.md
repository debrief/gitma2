# Spec 012 pilot, step 1: throughput on a T4

Not a result about the estimator: nothing is scored. Plan `configs/regress/pilot-throughput.json`
(the planned model: 8 layers, width 256, 6.39 million parameters, batch 256, mixed precision);
CI run on `gputrain/pilot-throughput`, results branch `results/gputrain-pilot-throughput-42911778716`, code b313c62.
The first run with real credentials; it worked without a fix.

| Measure | Value |
| --- | --- |
| GPU | Tesla T4 (torch 2.15.0, CUDA 13.2) |
| Training time | 600 s (the plan's limit) |
| Updates | 1,489 |
| Scenarios seen | 381,184 |
| Scenarios per second | 635 (validation passes every 200 updates included) |

- Research R3's rule: at 250 a second or more the plan stands. At 635 a second, 10 hours is
  about 23 million scenarios and the 10 million target takes about 4.4 hours.
- The estimate before the run was 100–300 a second; it was low by a factor of two to six.
- Validation loss was still falling at 10 minutes (median absolute error of ln range 0.185 at
  update 1,400, on 512 scenarios of seed 327, tokens at least 10 min after the zig). That says
  the loop learns on the GPU; it says nothing about where it ends.
- `gpu_seconds` (600.5) counts the training call; container start-up and the image build are
  not in it. The cost per hour (GPU, CPU and memory) is to be read from Modal's usage page and
  sets the hours that $50 buys.
