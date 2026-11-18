# Plan: spec 026

- `src/tma2/long/study.py`: the estimands (E1–E3, soundness), the bootstrap over engagements.
- `src/tma2/long/realtime.py` `imm_states`: the IMM over a whole engagement, read every 10 min.
- `tma2-long imm --indices a-b` and `tma2-long study --raw --config --out`.
- `configs/long/study-{tuning,val,test}.json`; `configs/long/run.json` per run; `long.yml`
  passes `--indices`.
- Records: `experiments/20261118-ls-tuning/`, `experiments/20261118-ls-decision/`,
  `experiments/20261118-ls-val/`, `experiments/20261118-ls/` (test), each with `study.json` and
  raw outputs.
- Constitution: pre-registered decision record and fresh seeds (349–351); references beside
  (C″, the true-history fit; the IMM is itself a reference); the panel reviews the test record.
