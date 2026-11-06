# MAN2 reference re-tune, pass 4, and the frozen references (spec 006 T032)

`tma2-tune --criterion g5 --grid man2-pass4` on the same 2,000 scenarios: run 41900416664, eight
shards, branch `results/man2-tune-man2-pass4-41900416664`. The IMM row repeats pass 3's choice.

| Setting | Median range error (G5 rows) |
| --- | --- |
| `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` | 0.5502 |
| `ekf-sa0.00003-p4-r0.25` | 0.5581 |
| `ekf-sa0.00003-p4-r0.125` | 0.5431 |
| `ekf-sa0.00003-p4-r0.0625` | 0.5306 |
| `ekf-sa0.00003-p4-r0.03125` | 0.5095 |

## Frozen

- **IMM (the gated reference, D3): `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`, 0.5502.** Every axis is
  inside its grid after pass 3.
- **EKF (reported): `ekf-sa0.00003-p4-r0.03125`, 0.5095. A recorded deviation from spec 003's
  rule.** The error keeps falling as the measurement-noise scale r goes to 0, with no plateau.
  An r of 1/32 tells the filter the bearing noise is 1/√32 ≈ 0.18 of its true σ. The filter
  becomes ever more confident in the bearings and approaches a sequential least-squares fit, a
  direction with no physical meaning. The search stops here. The setting is frozen at the last
  grid point, with this caveat, and is scored beside the IMM on every reference row (`tma2-gs
  --ekf`). It now beats the IMM.

## Reading

On MAN2 every single-model or two-model tracker sits near batch least squares on one leg. The
best is 0.51–0.55 median relative range error over G5 rows. Segmenter C (preliminary) scores
0.12 and the oracle 0.064. Windows of 40–120 min with several target changes, many before the
zig, defeat filters tuned on a single criterion. The trackers stay required references
(constitution IV), but they are not a competitive baseline here.
