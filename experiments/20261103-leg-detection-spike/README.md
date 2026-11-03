# Leg-detection spike (research note 08)

Validation seed 304 only (σ = 1° scenarios, file order): tuning set ordinals 0–499, scoring set
500–1499. No test data; seed 305 stays reserved. Not a gate and not pre-registered.

- `spike.json`: `scripts/research/leg_spike.py report --configs split:0.2:13.8,glr:0.2:13.8,split:0.1:13.8,split:0.4:13.8,glr:0.2:13.8:18`.
  The last configuration confirms turns as 3-minute windows (note 08 §6). The report also scores
  each confirmed turn at the manoeuvre ±3 min, next to Annex A's ±60 s.
  Thresholds per detector, per-detector detection metrics (Annex A §A.3 plus onset recall, the
  chance floor, detectability and turn-size bands, span F1), matched-control comparisons with
  97.5% scenario-clustered intervals, and the downstream check (LS, oracle, IMM, confirmed
  detectors) with intervals.
- `samples.json`: `leg_spike.py samples --config glr:0.2:13.8 --ordinals 524,527,504,513,932,555`.
  Own and target tracks, true manoeuvres, accepted knots and the per-row Steady Leg flag
  (note 07 §5) for six engagements, used in the results deck.

Reproduce (about 2 h of stats and 4 × 1.5 h of confirmation on 4 cores; shards resume):

```bash
uv run python scripts/research/leg_spike.py stats --validation data/gd-val/validation.f32pack --work <work>
uv run python scripts/research/leg_spike.py confirm --validation data/gd-val/validation.f32pack --work <work> --configs split:0.2:13.8,glr:0.2:13.8,split:0.1:13.8,split:0.4:13.8,glr:0.2:13.8:18
uv run python scripts/research/leg_spike.py report --validation data/gd-val/validation.f32pack --work <work> --configs split:0.2:13.8,glr:0.2:13.8,split:0.1:13.8,split:0.4:13.8,glr:0.2:13.8:18 --out experiments/20261103-leg-detection-spike
```
