# Gate H references: IMM and EKF re-tuned under mismatch (spec 010 T016)

**Tuning data only.** Run 42744425224 (`tune-h/man2-pass3`, `.github/workflows/tune-h.yml`),
eight shards, results branch `results/gh-tune-man2-pass3-42744425224`. Seed 320 under the
primary condition (`all-central`), count 5,200, the `train` split's first 2,000 σ = 1° scenarios;
`tma2-tune --criterion g5 --grid man2-pass3` (the grid in which the clean-data IMM was frozen).

| Filter | Chosen | Median range error, G5 rows | Clean-data tuning (seed 314) |
| --- | --- | --- | --- |
| IMM | `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` | 0.638 | the same setting, 0.550 |
| EKF | `ekf-sa0.00003-p4-r0.5` | 0.577 | `ekf-sa0.00003-p4-r0.03125`, 0.510 |

## Frozen for Gate H

- **IMM: `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`**, unchanged from the clean-data tuning.
- **EKF: `ekf-sa0.00003-p4-r0.5`.** On clean data the EKF's error kept falling as its
  measurement-noise scale r went to 0, with no plateau, and it was frozen at 1/32 with that
  caveat. Under mismatch r has an interior optimum (1.0: 0.590, 0.5: 0.577, 0.25: 0.586): telling
  the filter the bearings are far better than they are no longer pays.

## Limits

- One pass on one grid. The IMM's chosen values sit at this grid's edges (turn-rate noise 1, the
  lowest of four; r 2, the higher of two), as they did when it was frozen: the earlier passes on
  clean data bounded those axes, and they were not re-explored under mismatch. The EKF's
  process-noise value is at its lower edge.
- Both trackers are about five times worse than the oracle solve (0.115 on this condition) and
  take no part in the gate's statistic. They are references on the same rows, as the
  constitution requires.
