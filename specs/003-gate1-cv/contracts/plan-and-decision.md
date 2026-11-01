# Plan and decision record

**Plan** (`configs/gate1/plan.json`, a `TrainingPlan`): pushed on `train/<plan id>`. The
workflow trains every model, chaining jobs of ≤ 345 minutes; checkpoints go to
`checkpoints/<plan>/<model>` after every epoch; when all are complete, predictions on validation
go to `results/<plan>-<run>` with every job's record.

**Decision record** (`experiments/<date>-g1-decision/decision.json`, a `Gate1Decision`),
committed before the plan branch is pushed. It fixes:

- the plan id and its SHA-256, the three carried seeds and the three controls;
- the carried rule: the seed whose validation median range error at zig + 5 min (σ = 1°) is the
  median of the three;
- the test seed 303, 10⁵ scenarios generated, its 10⁴-scenario test split scored, once;
- the gate rows and criterion of SRD §5 and the statistics (95%, 2,000 resamples, seed 20261011);
- the frozen EKF and IMM settings (from `tma2-tune`);
- a forecast of the result;
- the follow-on if Gate 1 fails: one further pre-registered iteration, then stop and publish.
