# Gate D reference tuning (spec 004 T008, research R7)

`tma2-tune --criterion g5` on validation seed 304 (`data/gd-val/validation.f32pack`, digest in the
manifest), the first 2,000 σ = 1° scenarios, median relative range error over every G5 row
(zig + 5/10/15/20 min where reached), rows converged under the one plausibility definition.

**Pass 1** (commit e040639, `grid-pass1.csv`): the R7 grid around P0's phase-4 setting (243 IMM, 21
EKF settings). The IMM chose cv 0.003, ω 0.003, r 16, three edges with the error still falling
(ω 0.01 → 0.003: 0.1003 → 0.0970; r 8 → 16: 0.0985 → 0.0970). Not frozen.

**Pass 2** (commit 09aa39c, `grid.csv`, `choice.json`, the manifest): every edge axis extended
past its edge at the interior values of the others (cv and ω down to 0.0003, r up to 64; 26 new
settings). Frozen:

| Reference | Setting | Median range error, G5 rows |
| --- | --- | --- |
| IMM | `imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16` | 9.69% |
| EKF | `ekf-sa0.03-p4-r8` | 10.32% |

ω (0.001: 9.78%, 0.01: 10.03%) and r (8: 9.85%, 32: 10.31%) are now interior. cv 0.0003 is on the
extended edge, on a plateau: 9.688% / 9.691% / 9.696% at cv 0.0003 / 0.001 / 0.003, so the rule
(spec 003: a setting on an edge must sit on a plateau) is met. The EKF's choice is interior
(σ_a 0.01: 10.97%, 0.1: 11.18% at its best r).
