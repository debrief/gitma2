# MAN2 reference re-tune, pass 1 (spec 006 T032)

`tma2-tune --criterion g5` on seed 314 validation (2,000 σ = 1° scenarios; spec 004's G5 grids).
The criterion is the median relative range error over all G5 rows.

**Runs.** The record is from CI run 41843465989 (`tune.yml`, one 4-core runner, about 5 h,
branch `results/man2-tune-41843465989`). The sharded workflow (`tune-sharded.yml`, eight shards,
run 41883127320, branch `results/man2-tune-41883127320`) gave a byte-identical `grid.csv` and
`choice.json`.

**Result.** The landscape is flat and poor:
- every IMM and EKF setting scores 0.58–0.70;
- the best IMM, `imm-cv0.03-ct0.1-w0.01-s0.0003-p4-r2`, scores 0.585;
- the best EKF, `ekf-sa0.0003-p4-r2`, scores 0.583;
- by contrast, the 0.5.0 IMM tuned on seed 304 reached about 0.10 (spec 004).

On MAN2 the long windows hold several target changes, often before the zig, and a single-model
tracker does no better than one leg (batch least squares, 0.580 on the spec 005 scoring rows).

**Edges.** Both choices sit on grid edges with the error still falling, though by under 1%.

| Axis | First pass, nearest step | Median range error |
| --- | --- | --- |
| IMM cv | 0.01 → 0.03 | 0.5913 → 0.5852 |
| IMM ct | 0.03 → 0.1 | 0.5876 → 0.5852 |
| IMM r | 8 → 2 | 0.601 → 0.585 |
| IMM switch | 0.001 → 0.0003 | 0.5858 → 0.5852 |
| EKF sa | 0.001 → 0.0003 | 0.5886 → 0.5833 |
| EKF r | 8 → 2 | 0.616 → 0.583 |

Spec 003's rule applies: a frozen setting on an edge must sit on a plateau. Pass 2
(`--grid man2-pass2`, `experiments/20261104-man2-tune-pass2/`) reaches past each edge.
