# Spec 028 validation (seed 355): soundness passed

## Run and scoring

- **Engagements:** 10 + 10 realistic engagements of 6 and 12 hours, both contacts
  (`configs/long/cp-val.json`), at the registered settings: scale 4, tail 1,200 s, α = 0.001.
- **CI:** run 44426408724, commit b4d3671, AMD EPYC 9V74. 40 jobs took 24 runner-hours.
- **Raw outputs:** in `raw/`, taken from the run's orphan results branch.

Scored with:

    uv run tma2-long study27 --raw experiments/20261119-cp-val/raw \
        --config configs/long/cp-val.json --out experiments/20261119-cp-val

## Soundness (registered; a failure would stop the study)

| check | value | band | |
|---|---|---|---|
| S1 windows ran | 240 of 240, no engagement missing | ≥ 95% | pass |
| S2 ctl ÷ true-history fit (per-engagement geometric mean) | 1.38 [1.17, 1.62] | [0.8, 4] | pass |
| contact-1 coverage of the carried 95% region | 0.96 [0.93, 0.99] (100 hand-overs) | [0.80, 0.99] | pass |

The test (seed 356) goes ahead.

## Reported, not decided

### ctl ÷ ctl-prior

Per-window median range error, chains' first windows excluded, engagement bootstrap.

| split | windows (engagements) | range | course | speed |
|---|---|---|---|---|
| weak geometry | 82 (33) | 1.07 [0.86, 1.36] | 1.03 [0.84, 1.27] | 1.20 [0.81, 1.82] |
| other | 77 (20) | 1.11 [0.96, 1.27] | 1.21 [1.06, 1.37] | 0.97 [0.80, 1.18] |
| contact 1 | 100 (20) | 1.17 [1.03, 1.34] | 1.21 [1.03, 1.41] | 1.05 [0.91, 1.25] |
| contact 2 | 59 (19) | 0.98 [0.74, 1.30] | 0.97 [0.76, 1.24] | 1.12 [0.69, 2.01] |

### Against the forecasts

Read on this seed, the registered rule would give "not shown". The forecasts, written before
this seed existed, are compared below.

- **Weak split:**
  - Forecast: about 1.2–1.4.
  - Validation: 1.07. Lower, with the interval spanning 1.
  - The tuning seed's weak-split gain (1.52 at scale 2) did not repeat at the registered scale.
- **Other split:**
  - Forecast: about 0.95, with possible harm.
  - Validation: 1.11. The gain sits on contact 1, the tended contact, where it was forecast
    to cost.
- **Prior's own effect:** ctl-carry ÷ ctl-prior on the weak split is 0.95 [0.74, 1.21].
- **Windows near a gap:** 1.10 [0.82, 1.47] over 34 windows.

### Coverage and the guard

- **Contact-2 coverage:** 0.76 [0.67, 0.86] over 72 hand-overs. The untended contact's
  carried prior is overconfident at the registered settings. Only contact 1 is registered.
- **Guard:** it fell back on 1.9% of 157 guarded windows.
- **Share answered:** 0.80 for every system.

Validation is one seed of 20 engagements per contact. None of this decides anything: the
registered rule is read on the test seed only.
