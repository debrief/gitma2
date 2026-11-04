# MAN2 reference: GLR + confirm on seed 314 (spec 006 T033)

This repeats note 08's leg-detection reference on MAN2 validation data:
- data: `data/man2-val/validation.f32pack`, seed 314 (digest in `experiments/20261104-g0-man2/dataset-digests/`);
- σ = 1° scenarios in file order, tuning ordinals 0–499 and scoring ordinals 500–1499;
- the frozen MAN2 IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` (`experiments/20261104-man2-tune-pass4/`).

Commands (work directory `<W>`, about 45 min on four cores):

```
uv run python scripts/research/leg_spike.py stats   --validation data/man2-val/validation.f32pack --work <W> --tune 500 --score 1000 --workers 4
uv run python scripts/research/leg_spike.py confirm --validation data/man2-val/validation.f32pack --work <W> --tune 500 --score 1000 --configs glr:0.2:13.8 --workers 4
uv run python scripts/research/leg_spike.py report  --validation data/man2-val/validation.f32pack --work <W> --tune 500 --score 1000 \
    --imm imm-cv0.03-ct1-w0.01-s0.0003-p4-r2 --configs glr:0.2:13.8 --out experiments/20261104-man2-refs/spike.json
```

`spike.json` holds everything: the detector thresholds, the detection measures, the strata by
kind, size and detectability, and the downstream errors with their clustered 97.5% intervals.

## Downstream: 3,934 G5 rows (2,933 settled), 1,000 scenarios

Each cell is the median relative range error, course error (°) and speed error (kt).

| Estimator | All G5 rows | Settled rows |
| --- | --- | --- |
| batch least squares, one leg | 0.581 / 66.0 / 6.21 | 0.592 / 59.4 / 6.48 |
| frozen IMM | 0.539 / 52.3 / 5.79 | 0.546 / 47.2 / 5.84 |
| **GLR + confirm** (`glr-q0.2-t13.8`) | **0.447 / 44.4 / 4.57** | **0.447 / 36.4 / 4.56** |
| oracle (true change times) | 0.064 / 7.4 / 0.97 | 0.063 / 4.7 / 0.89 |

**Baseline ratios for S2.** These are GLR + confirm's ratios with 97.5% scenario-clustered
bootstrap intervals (2,000 resamples).

| Ratio | Value [97.5%] |
| --- | --- |
| range vs IMM | 0.829 [0.757, 0.924] |
| course vs IMM | 0.848 [0.776, 0.922] |
| speed vs IMM | 0.789 [0.707, 0.870] |
| range vs batch least squares | 0.769 [0.703, 0.862] |
| settled range vs batch least squares | 0.756 [0.683, 0.865] |
| settled course vs batch least squares | 0.612 [0.546, 0.685] |
| settled speed vs batch least squares | 0.704 [0.627, 0.789] |

As a share of the gap between one leg and the oracle, GLR + confirm recovers
(0.581 − 0.447) / (0.581 − 0.064) ≈ 0.26 of the median range error.

## Detection

These are scored at note 08's ±60 s tolerance, over 2,961 truth changes.

| Measure | GLR + confirm |
| --- | --- |
| span recall (± 60 s) / knot precision / F1 | 0.253 / 0.300 / 0.275 |
| the same at ± 3 min | 0.324 / 0.428 / 0.369 |
| knots per scenario | 2.60 |
| onset delay, median | 240 s |
| held-row false alarm | 0.028 |

Recall by detectability band (the oracle cost drop of each change, `by_detect`; bands 13.28, 50,
200) is in `spike.json`. Most of the misses are changes the bearings barely show. At the matched
held-row false-alarm rate:
- the plain windowed split statistic recalls 0.55 of changes;
- the confirmed GLR recalls 0.27;
- confirmation trades recall for knots the downstream solve can use.

## Comparison with note 08 (0.5.0, seed 304)

Against the IMM, the downstream ratio barely moves: range 0.83 [0.76, 0.92] here, 0.81
[0.74, 0.88] in note 08. In absolute terms MAN2 is far harder: the IMM's median range error is
0.54 here, against 0.098 on 0.5.0. The share of the IMM-to-oracle gap that GLR + confirm closes
falls from 42% to 19%.

MAN2 has longer windows (40–120 min), more target changes (93.5% of engagements hold two or
more, many before the zig), slower turns and course wander, so changes are less sharp. Detection
F1 is not compared: note 08 and spec 005's research scored detection on different definitions.

## Caveats

- **The trackers were tuned on rows that include these.** `tma2-tune` used the first 2,000 σ = 1°
  scenarios, which contain scoring ordinals 500–1499. This favours the IMM and EKF, so ratios
  against them are conservative for any segmenter. Gate S scores on fresh seed 315.
- **SC-002 checks this record.** `tma2-gs --glr-confirm` must reproduce these figures on the same
  rows (spec 005 T020).
