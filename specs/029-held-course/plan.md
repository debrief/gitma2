# Plan: spec 029

## Code

Only new modules and configs. `ctl`, `ctl-carry`, `ctl-prior` and the simulator are unchanged.

- **`src/tma2/long/study29.py`**: the scorer.
  - Classes by ownship turns overlapping each window: held, one or more.
  - Excludes first windows and windows with no hand-over.
  - The rule, with a bootstrap over engagements (one chain per engagement, since only contact 1
    runs; seed 29).
  - Beside: medians, trimmed means, shares, the prior's own effect, references, guard,
    answered share, search time.
  - Coverage by class, and soundness S1–S3 (S3 is held-window coverage).
- **CLI:** `tma2-long study29 --raw --config --out`.
- **`long.yml`:** passes `window_s` and `overlap_s` to the job command.
- **Configs:** `configs/long/hold-{tuning,val,test}.json`. These are spec 028's realistic configs
  with `ownship.leg_s` 3,600–7,200 s, on seeds 362, 363 and 364.
- **Run files:** `configs/long/runs/hold-*.json`. Each is `carry2`, contact 1, 1-hour windows
  overlapping 15 min, one job per engagement.

## Settings

- **Carried prior:** spec 028's registered settings (`configs/long/carry2.json`: scale 4, tail
  1,200 s, α 0.001), run unchanged as a chain on tuning.
- **Kept or changed:** they stay if tuning's held-window coverage lies within [0.85, 0.99].
  Otherwise the decision record states the change, chosen by spec 028's grid rule, before
  validation.

## Order

1. Tuning (seed 362, 6 + 6 engagements): split sizes, coverage and forecasts.
2. Decision record (`experiments/20261119-hold-decision/`): configs, run files and code by
   digest, plus forecasts.
3. Validation (seed 363): S1–S3.
4. Test (seed 364, 30 + 30), scored once.
5. Panel, then write-up and slides, AGENTS.md and PR.

## Constitution

- Pre-registered decision record and fresh seeds.
- References on the same windows: C″ and the true-history fit.
- Nothing trained.
- The panel reviews the test record.
