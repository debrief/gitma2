# Spec 030 tuning (spent seed 364): never a result

## Run and scoring

**Engagements:** spec 029's test engagements 0–5 and 30–35 (`configs/long/hold-test.json`, seed
364, already spent).

**Systems:**
- **(b)** `carry2` on 2-hour windows, overlapping 30 min (tag `hold-test-2h`).
- **(c)** `jointheld`: `ctl` on the union of each turn-free 1-hour window and the one before it.
- **(a)** the 1-hour `carry2` outputs, copied from spec 029's test record.

**CI:** run 44622330685, commit f54bfb7, AMD EPYC 9V74.

Scored with:

    uv run tma2-long study30 --raw experiments/20261119-cmp-tuning/raw \
        --config configs/long/hold-test.json --out experiments/20261119-cmp-tuning

The scorer reports 48 engagements missing. That is expected: only 12 were run.

## Readings (tuning; they set the forecasts and D3)

**Window counts:**

| | turn-free (held) windows |
|---|---|
| total | 43 |
| handed on | 37 |
| decided: answered by (a), (b) and (c) | 34, from 11 engagements |

Every ratio below is held windows, range, the system named over 1-hour `ctl-prior`.

| | geometric mean | interval | median | `ctl-prior` better |
|---|---|---|---|---|
| D1: 2-hour `ctl` | 1.30 | [0.78, 2.12] | 1.21 | 56% |
| D2: joint solve | 1.28 | [0.94, 1.76] | 1.25 | 65% |
| D3: 2-hour `ctl-prior` | 0.57 | [0.28, 1.08] | 0.69 | 38% |

On D3, the 2-hour `ctl-prior` is the better of the two.

**Median range error on held windows:**

| system | median error |
|---|---|
| 1-hour `ctl` | 0.282 |
| 1-hour `ctl-prior` | 0.079 |
| 2-hour `ctl` | 0.104 |
| joint solve | 0.105 |
| 2-hour `ctl-prior` | 0.061 |
| span reference | 0.034 |

The span reference is the true-history fit over the joint union.

**Other readings:**
- **One-turn windows, D1:** 0.77 [0.59, 0.96]. The 2-hour `ctl` beats the 1-hour `ctl-prior`
  there.
- **Spec 029 replicated:** 1-hour ctl ÷ ctl-prior on held windows is 2.32 [1.39, 3.52].
- **Cost per window:**
  - (a) 110 s per 1-hour window;
  - (b) 436 s per 2-hour window;
  - (c) 241 s per turn-free window.

## D3

The 2-hour `ctl-prior` leads on tuning, and it is the natural deployment if the prior helps on
top of the longer window. D3 is added to the registered estimands before validation, with the
same reading rule.

## Caveats

- Only 11 engagements and 34 windows were scored.
- Spec 028's and 029's tuning seeds misjudged their tests in both directions.
