# MAN2 reference re-tune, pass 2 (spec 006 T032)

`tma2-tune --criterion g5 --grid man2-pass2` on the same 2,000 σ = 1° seed-314 scenarios as
pass 1. It ran on CI as `tune-sharded.yml`, eight shards, run 41894765079, branch
`results/man2-tune-man2-pass2-41894765079`. Grid names without an `-r` suffix have r = 1.

- **IMM:** `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`, 0.5502. Interior in cv (0.1 is worse), switch
  (0.0001 is worse) and r (1 is worse). On the ct edge with the error still falling: ct 0.3 → 1
  at r 2 goes 0.5685 → 0.5502.
- **EKF:** `ekf-sa0.00003-p4` (r 1), 0.5732. On a plateau in sa (1e-4 gives 0.5733). On the r
  edge still falling: r 2 → 1 goes 0.5824 → 0.5732.

Pass 3 (`--grid man2-pass3`) reaches past the IMM's ct edge and the EKF's r edge.
