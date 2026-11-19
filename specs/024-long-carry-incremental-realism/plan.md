# Plan: spec 024

- `src/tma2/long/carry.py` (ctl and ctl-carry per window, chain with warm-up windows at shard starts)
- `src/tma2/long/incremental.py` (block confirmation, crop to the last 720 rows)
- `src/tma2/long/sim.py` `_World` (realism stream; steering hook in `_ownship`; `Engagement.other`)
- `configs/long/realistic.json`; `configs/long/run.json` (the CI run's jobs); `tma2-long realtime-inc|carry
  --config --contact`
- `scripts/research/long2_report.py` (record), `long_viewer_data.py` (pages), `long2_charts.py` (figures)
- Constitution: as spec 023 (an investigation, labelled; references beside: one leg, IMM, the true-history fit).
