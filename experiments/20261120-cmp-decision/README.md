# Spec 030 decision record: the carried prior against 2-hour ctl and a joint solve

This record was registered on 2026-11-20, before seeds 365 and 366 existed. It is a registered
study, not a gate: nothing is trained and nothing runs on GPU.

## Bound

`decision.json` holds the registration, and `digests.json` binds:
- the configs: `cmp-val.json`, `cmp-test.json` and `carry2.json`;
- the run files `configs/long/runs/cmp-{val,test}.json`;
- the priors and C's parameters;
- `long.yml`;
- the spec and the plan;
- the code: `e7a1870b…` over `src/tma2/long/`, `src/tma2/timelate/`, `src/tma2/cli/long.py` and
  the simulator's prng and geometry.

## Design

The engagements are spec 029's held-course engagements, contact 1. Each system runs on its own
windows:
- **(a)** `ctl-prior` on 1-hour windows;
- **(b)** `ctl` on 2-hour windows, stitched; `ctl-prior` on 2-hour windows comes from the same
  run;
- **(c)** `ctl` on the union of each turn-free hour and the hour before it.

Each is compared on the rows of every turn-free (held) 1-hour window. The ratios, as geometric
means over held windows with a bootstrap over engagements, are:

| estimand | ratio |
|---|---|
| D1 | (b) `ctl` ÷ (a) |
| D2 | (c) `ctl` ÷ (a) |
| D3 | (b) `ctl-prior` ÷ (a), added on tuning because it led there |

Each estimand is read as one of:
- **"ctl-prior better"** if its lower limit is above 1 (for D3, the 1-hour `ctl-prior` is better
  than the 2-hour one);
- **"ctl-prior worse"** if its upper limit is below 1;
- **"not separated, at this size"** otherwise.

## Validation soundness (seed 365)

The study stops if any check fails:
- **S1:** every engagement is present for (a), (b) and (c).
- **S2:** 1-hour ctl ÷ the true-history fit lies in [0.8, 4].
- **S3:** held-window coverage of the carried prior lies in [0.80, 0.99].

## Forecasts

These are written before seed 365 exists. They come from tuning on 34 windows, which earlier
specs showed to be unreliable.

| estimand | tuning | forecast for the test | probability |
|---|---|---|---|
| D1 | 1.30 [0.78, 2.12] | 1.1–1.3 | "ctl-prior better" with probability 0.4; "worse" 0.05 |
| D2 | 1.28 [0.94, 1.76] | 1.1–1.3 | "ctl-prior better" with probability 0.5 |
| D3 | 0.57 [0.28, 1.08] | 0.6–0.85 | "ctl-prior worse" with probability 0.6 |

For D3, "ctl-prior worse" means the 2-hour `ctl-prior` is better.

- **One-turn windows:** the 2-hour `ctl` beats the 1-hour `ctl-prior` (tuning 0.77, reported).
- **Compute per window:** (b) about 4 times (a); (c) about 2 times (a) per turn-free window.

## Known before any result

- **Placement:** windows are moved past true target manoeuvres. The windows of (b) and (c)
  differ in placement, so (b)'s rows on a held window may come from a window centred elsewhere.
- **The span reference** sees only the union's bearings and is told the true history. It is
  not a ceiling.
- **Population:** one simulator family, contact 1 only. Spec 028's hand-over defect is kept.

## Renumbered after the test (2026-11-20)

This study was registered and run as spec 030. It is now spec 031, because another session's
spec 030 (`specs/030-carried-prior/`) merged to main first. The folder moved from
`specs/030-held-comparators/` to `specs/031-held-comparators/`. `spec.md` and `plan.md` are byte
for byte the files bound in `digests.json`, under their old paths. Code, configs and records
still say "spec 030" where they were bound or written before the rename.
