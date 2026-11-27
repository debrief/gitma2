# Spec 037: the fine-tuning pilot (tuning; not a result)

One run: spec 012's seed 1 checkpoint, fine-tuned for 4,000 updates of 256 scenarios under the
mismatch mix (`configs/regress/ft-mix.json`), stream seed 369 from index 50 million, learning
rate 1e-4 after 300 warm-up updates and cosine to zero. Plan as run: `plan.json`; record:
`run.json` (CI run 45101050454, code 55bac32, a Tesla T4 through Modal). **27.5 minutes, 621
scenarios a second with the overlay** (spec 012 measured 570 to 670 without), about $0.31.

The run's own monitor (512 scenarios of validation seed 370; rows at least 10 min after the zig)
had no reading before the first update, so the starting point was computed afterwards on CPU
from the unchanged checkpoint on the same scenarios (`monitor-by-kind.json`; the pilot's own
last line is reproduced: 0.0907 and 0.102 against the run's 0.0906 and 0.1021). Median absolute
error of ln range:

| Scenarios of the monitor | n | Unchanged | After the pilot |
|---|---|---|---|
| clean, all 512 | 512 | 0.085 | 0.091 |
| under the mix, all 512 | 512 | 0.114 | 0.102 |
| mix: drawn clean | 151 | 0.082 | 0.087 |
| mix: outliers on | 201 | 0.152 | 0.106 |
| mix: correlated error on | 179 | 0.190 | 0.136 |
| mix: bias on | 177 | 0.148 | 0.118 |
| mix: untold level on | 202 | 0.136 | 0.109 |

(The kinds overlap: a scenario with two kinds on is in two rows.)

- **It moved.** By the stop rule the three seeds go ahead.
- Nearly all of it came in the first 500 updates (0.114 to 0.103); from update 500 to 4,000 the
  mixed monitor went from 0.1027 to 0.1021, inside its own noise (the clean monitor wandered
  between 0.088 and 0.094). Whether 26,000 updates buy more than 4,000 is not known.
- **Clean data got worse by about 7%** (0.085 to 0.091). The registered reading M4 will say
  whether that survives a longer schedule.
- Configuration for the seeds: **unchanged** (the one allowed change is not used). A higher
  learning rate might adapt further and would likely cost more on clean data; the pilot gives no
  ground to choose it. Training now records its monitors before the first update.

## The held-out family (T018)

`monitor-heldout.json`: 384 scenarios of spent seed 321 under one condition each, same statistic.

| Condition | Unchanged | After the pilot |
|---|---|---|
| off | 0.085 | 0.089 |
| ho-t3 (Student-t white error) | 0.091 | 0.088 |
| ho-step2 (level doubles or halves) | 0.093 | 0.090 |
| ho-osc (sinusoid, one sd, 300 s) | 0.142 | 0.106 |
| ho-burst (offset bursts) | 0.156 | 0.114 |
| **ho-both** (the registered held-out condition) | 0.255 | 0.133 |
| all-central (in the training ranges, for scale) | 0.293 | 0.135 |

The first family (t3, step2) was scored on CI with every system on 100 engagements
(`../20261122-rmis-dev/heldout/`, with the second stream's first draw order): it hurt nobody
(regressors 0.062 to 0.065, C″-robust 0.121 to 0.108), so it was no test. It was strengthened
once, before registration, with two structured kinds that training never draws: a sinusoidal
error and bursts in which every bearing carries one offset. These hurt the unchanged regressor
by a factor of three, and the pilot model, which never saw them, recovers most of it. Whether
they hurt C″ is read on validation; it was not known when the readings were registered.

A local trap worth recording: numba's cache does not notice a changed callee in another module;
`features.batch._overlay_batch` ran the old overlay until the cache was cleared (CI and Modal
start without a cache).
