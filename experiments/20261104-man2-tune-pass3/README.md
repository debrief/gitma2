# MAN2 reference re-tune, pass 3 (spec 006 T032)

`tma2-tune --criterion g5 --grid man2-pass3`, same 2,000 scenarios, run 41898494693 (eight shards,
branch `results/man2-tune-man2-pass3-41898494693`).

- **IMM, frozen:** `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`, 0.5502. ct is now interior: 3 gives
  0.5670, 10 gives 0.5731 and 30 gives 0.5633, all worse. The other axes were interior after
  pass 2.
- **EKF:** `ekf-sa0.00003-p4-r0.25`, 0.5581, still falling at the r edge (r 0.5 → 0.25:
  0.5669 → 0.5581). An r scale below 1 tells the filter the bearing noise is smaller than it is,
  which is physically wrong, but the rule is empirical; pass 4 reaches further. The EKF is
  reported, not gated (the IMM is the gated reference, D3).
