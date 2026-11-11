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

# Step 2: the learning curve (a fifth of the schedule)

Plan `configs/regress/pilot-curve.json` (the carried configuration, 17,000 updates, a fifth of
every batch held course); CI run 42973800868, results branch
`results/gputrain-pilot-curve-42973800868`, code 397ba8b; `curve/run.json`. Nothing is scored:
the figures are the training loop's own validation measures on 512 MAN2 scenarios of seed 327,
on every folded row at least 10 minutes after the ownship zig (not the scorer's rows).

| Updates | Scenarios seen | Median abs. error of ln range | Median velocity error (m/s) |
| --- | --- | --- | --- |
| 1,000 | 0.26 M | 0.200 | 3.44 |
| 4,000 | 1.02 M | 0.146 | 2.66 |
| 8,000 | 2.05 M | 0.131 | 2.36 |
| 12,000 | 3.07 M | 0.108 | 2.13 |
| 17,000 | 4.35 M | 0.103 | 2.00 |

- Complete and stable: no divergence, 2.08 hours of training, 581 scenarios a second (635
  without the held-course share and with fewer validation passes).
- Both errors fall throughout and flatten only as the cosine schedule brings the learning rate
  to zero, so the full schedule (five times the updates) should go further; how far is what
  the seeds measure. The validation loss itself is not monotone (it is a β-weighted likelihood,
  not an error).
- GPU time so far: 0.17 + 2.08 = 2.25 hours, about $1.50.
- The carried configuration stands; the three seeds and the two controls are launched from the
  plans bound in `../20261111-r-decision/`, side by side (their limits sum to 38.2 hours).
