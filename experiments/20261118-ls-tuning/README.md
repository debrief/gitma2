# Spec 025: tuning run (seed 349; never a result)

CI run 44245933596 (AMD EPYC 7763; commit 99585de). There were 6 + 6 realistic engagements
of 6 and 12 hours (`configs/long/study-tuning.json`). On both contacts it ran `ctl` and
`ctl-carry` on every window, and the IMM on the 12-hour engagements. The raw outputs are in
`raw/`; `study.json` is from `tma2-long study`.

- **Soundness**:
  - S1: 72 of 72 windows ran;
  - S2: ctl ÷ the true-history fit is 1.40;
  - S3: bearings held 0.85.
  All pass.
- **E1** (contact 1): 1.054 [0.955, 1.177].
  - Per-window median ratio 1.00.
  - Carry better in 25 windows, worse in 14, level in 33; twice better in 4, twice worse in 2.
  - Search CPU: 1.27 h from the carry against 2.04 h from nothing.
- **E1 on contact 2**: 1.087 [0.995, 1.226].
- **E2**: 1.26 [0.62, 2.49], by band:

  | band | contact 1 | contact 2 |
  |---|---|---|
  | 2–10 km | 1.2% | 1.4% |
  | 10–20 km | 1.6% | 1.7% |
  | 20–40 km | 3.6% | 5.5% |

- **E3**: 0.77 [0.51, 1.31]. The IMM is worse early than late.

These figures shaped the decision record's forecasts and nothing else. The design was fixed in
`src/tma2/long/study.py` before this run.
