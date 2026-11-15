## Member `L900-s0.35-a60`: its own search against refitting shared candidates

(130 shifted periods of seed 347 scored in both runs; range; a ÷ b, above 1: b is better)

| Reading | Ratio (periods) |
| --- | --- |
| Control ÷ the member with its own search (this run) | 1.03 [0.91, 1.19] (130) |
| Control ÷ the member refitting shared candidates (spec 018's run) | 1.03 [0.91, 1.19] (130) |
| Refit (spec 018's run) ÷ own search (this run), across runs | 0.99 [0.87, 1.12] (130) |
| The control across the two runs (spec 018's ÷ this) | 0.99 [0.93, 1.04] (130) |
| The true-prior search across the two runs (spec 018's `true` ÷ this run's `lad-5`) | 1.00 [0.93, 1.08] (130) |

## How the gain is spread over periods (control ÷ system, range)

(dropping only a system's ten best periods biases any ratio downward when the per-period ratios are widely spread; the symmetric trim drops the ten best and the ten worst)

| System | Run | Periods | All | Without the ten best | Without the ten worst | Without both | System better | Over twice as good | Over twice as bad |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `lad-0` | this run, 130 used periods | 130 | 0.98 | 0.91 | 1.07 | 0.99 | 0.24 | 0.05 | 0.06 |
| `lad-1` | this run, 130 used periods | 130 | 1.05 | 0.92 | 1.19 | 1.04 | 0.45 | 0.15 | 0.11 |
| `lad-2` | this run, 130 used periods | 130 | 1.06 | 0.93 | 1.27 | 1.11 | 0.54 | 0.22 | 0.15 |
| `lad-3` | this run, 130 used periods | 130 | 1.12 | 0.94 | 1.35 | 1.12 | 0.52 | 0.25 | 0.14 |
| `lad-4` | this run, 130 used periods | 130 | 1.10 | 0.95 | 1.32 | 1.14 | 0.58 | 0.22 | 0.14 |
| `lad-5` | this run, 130 used periods | 130 | 1.11 | 0.94 | 1.34 | 1.14 | 0.55 | 0.25 | 0.13 |
| `mem-L900-s0.35-a60` | this run, 130 used periods | 130 | 1.03 | 0.90 | 1.19 | 1.03 | 0.51 | 0.14 | 0.17 |
| `one-angle` | this run, 130 used periods | 130 | 1.00 | 0.88 | 1.13 | 0.99 | 0.42 | 0.14 | 0.15 |
| `one-kinds` | this run, 130 used periods | 130 | 0.92 | 0.85 | 1.05 | 0.97 | 0.25 | 0.05 | 0.08 |
| `one-rate` | this run, 130 used periods | 130 | 0.96 | 0.83 | 1.11 | 0.96 | 0.47 | 0.08 | 0.12 |
| `one-speed` | this run, 130 used periods | 130 | 0.96 | 0.84 | 1.11 | 0.97 | 0.39 | 0.12 | 0.12 |
| `true` | spec 018's test, all shifted periods | 355 | 1.10 | 1.01 | 1.20 | 1.10 | 0.53 | 0.20 | 0.13 |
