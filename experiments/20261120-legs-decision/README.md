# Spec 032 decision record: the carried prior where the ownship's legs outlast the 2-hour window

This record was registered on 2026-11-20, before seeds 367 and 368 existed. It is a registered
study, not a gate: nothing is trained and nothing runs on GPU.

## Bound

`decision.json` holds the registration, and `digests.json` binds:
- the configs: `legs-val.json`, `legs-test.json` and `carry2.json`;
- the run files `configs/long/runs/legs-{val,test}.json`;
- the priors and C's parameters;
- `long.yml`;
- the spec and the plan;
- the code: `babd25bc…` over `src/tma2/long/`, `src/tma2/timelate/`, `src/tma2/cli/long.py` and
  the simulator's prng and geometry.

## Design

- **Engagements:** spec 024's realism with ownship legs of 2–4 h, contact 1, on the standing
  2-hour windows overlapping 30 min.
- **Held windows** have no ownship turn overlapping them: the window is blind.
- **Systems, each on held windows:**
  - (a) 2-hour `ctl` and 2-hour `ctl-prior` from one `carry2` job;
  - (c) a joint solve: `ctl` on the window and the previous one (3.5 h), past bearings only.
- **Estimands,** geometric means over held windows with a bootstrap over engagements:

  | estimand | ratio |
  |---|---|
  | E1 | `ctl` ÷ `ctl-prior` |
  | E2 | joint ÷ `ctl-prior` |

  Each is read "ctl-prior better" (lower limit above 1), "ctl-prior worse" (upper limit below
  1) or "not separated, at this size".
- **Harm:** E1 on one-turn windows has its upper limit below 1.

## Validation soundness (seed 367)

The study stops if any check fails:
- **S1:** parts present, and at least 95% of windows ran.
- **S2:** `ctl` ÷ the true-history fit lies in [0.8, 4].
- **S3:** coverage on decided held hand-overs lies in [0.80, 0.99]. On 20 engagements this is
  about 25 hand-overs, so a coverage of 0.80 is about one hand-over from failing.

## Forecasts

These are written before seed 367 exists, from 14 tuning windows, which is too few to forecast
well.

| estimand | tuning | forecast for the test | probability |
|---|---|---|---|
| E1 | 1.32 [0.67, 2.37] | 1.1–1.5 | "ctl-prior better" 0.45; "not separated" 0.5; "worse" 0.05 |
| E2 | 1.65 [0.86, 3.25] | 1.0–1.6 | "ctl-prior better" 0.4; "not separated" 0.5; "worse" 0.1 |
| harm | 1.10 [0.61, 1.89] | 0.95–1.2 | "no harm" 0.95 |

**Why E2 could lean to the prior:** the joint solve fits 3.5 hours with the evidence search. That
gives more target manoeuvres to find, and contact is often half lost. The prior summarises the
earlier window's own best answer. This is a guess from 14 windows.

## Known before any result

- **Placement:** windows are moved past true target manoeuvres (spec 023's chain), so hand-overs
  are never inside one. Spec 028's hand-over defect is kept.
- **Range and contact:**
  - Holding course drifts the range out, so the held windows are far-range windows (tuning
    median 27.6 km).
  - About a third of bearings are lost (detected share 0.66).
- **The span reference** is told the true history over the union. It is no ceiling for
  `ctl-prior`, which carries information from before the union.
- **Size:** the test was raised to 50 + 50 engagements on tuning's yield, about 120 decided
  windows, before this record.
- **Population:** one simulator family, contact 1, one realism setting.
