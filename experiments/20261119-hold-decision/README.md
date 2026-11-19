# Spec 029 decision record: the carried prior where the ownship holds course

This record was registered on 2026-11-19, before seeds 363 and 364 existed. It is a registered
study, not a gate: nothing is trained and nothing runs on GPU.

## Bound

`decision.json` holds the registration, and `digests.json` binds:
- the configs `hold-val.json`, `hold-test.json` and `carry2.json`;
- the run files `configs/long/runs/hold-{val,test}.json`;
- the priors and C's parameters;
- `long.yml`;
- the spec and the plan;
- the code: `c39cb031…` over `src/tma2/long/`, `src/tma2/timelate/`, `src/tma2/cli/long.py`
  and the simulator's prng and geometry.

Bound files are not edited from here on.

## Design

- **Data:** realistic engagements in which the ownship holds each leg for 1–2 hours, the
  tended contact only.
- **Windows:** 1 hour long, overlapping 15 minutes.
- **Systems:** spec 028's `ctl-prior` at its registered settings (scale 4, tail 1,200 s,
  α 0.001), unchanged. Tuning kept them: held-window coverage was 0.89 against the plan's
  [0.85, 0.99].

## Rule

- **Estimand:** the geometric mean over windows of ctl ÷ ctl-prior, from per-window median range
  error. The interval comes from a bootstrap over engagements.
- **Exclusions:** each chain's first window, and any window with no hand-over.
- **Gain:** the lower limit on held windows (no ownship turn) is above 1.
- **Harm:** an upper limit below 1 on any non-empty class, in range, course or speed.
- **Otherwise:** not shown, at this size.

## Validation soundness (seed 363)

The study stops if any of these fails:
- **S1:** at least 95% of windows ran.
- **S2:** ctl ÷ the true-history fit, per-engagement geometric mean, lies in [0.8, 4].
- **S3:** coverage of the carried 95% region on hand-overs into held windows lies in
  [0.80, 0.99].

## Forecasts (written before seed 363 exists)

Tuning gave 2.10 [1.17, 3.77] on 26 held windows. Spec 028's tuning seed overstated its test
figure by 0.4, so these forecasts are shrunk.

- **Held, range:** 1.5 to 2.0, with the lower limit above 1 with probability about 0.75. The
  mechanism is direct: a turn-free window leaves range open, and the hand-over closes it.
- **One turn, range:** 1.2 to 1.5. No harm in any class or quantity.
- **Reference:** ctl-prior on held windows near the fit told the true history (tuning: 0.108
  against 0.117).
- **Guard:** it falls back on 1–3%.
- **Held-window coverage:** 0.85–0.95.
- **Answered:** about 70% of windows by both systems. The target drifts beyond detection on
  long holds.

## Known before any result

- **The "more" class is empty:** with 1-hour windows and holds of an hour or more, a window
  holds at most one turn. So its harm check is vacuous.
- **Confounding:** holding course costs range keeping, so held windows mix geometry with
  detection at range.
- **Unchanged code:** spec 028's hand-over defect is kept. The refit starts from the full
  window's fit.
