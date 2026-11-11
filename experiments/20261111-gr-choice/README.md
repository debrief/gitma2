# Spec 011: the settings choice on 150 engagements (plan research R4)

Tuning seed 323, the diagnosis's 150 σ = 1° engagements (593 scored rows), primary condition
and no mismatch; CI run 42932633571 (`headroom/gr-choice`, code 04527ca). Every system has the
Gate H robust control in its final solve and C″'s zig veto and fade; they differ only in the
confirmation test. `summary.json` (`scripts/research/gr_pilot.py`), `transitions.json`
(`gr_diagnosis.py`), `paired.json`; intervals paired, scenario-clustered, 95%. The rule applied
was declared in `../20261110-gr-pilot/README.md` before these data. **Tuning, not a result.**

## Downstream (median relative range error)

| Confirmation test | Primary | Share of the gap closed | Clean | Clean cost |
| --- | --- | --- | --- | --- |
| True manoeuvre times (the reference) | 0.116 | 1 | 0.057 | |
| C″ as frozen (the baseline) | 0.254 | 0 | 0.123 | |
| Huber 2.0 | 0.236 | 0.13 [−0.11, +0.38] | 0.115 | −6% [−12, +1] |
| Huber 1.345 | 0.238 | 0.11 [−0.12, +0.37] | 0.116 | −5% [−14, +8] |
| Plain C, threshold × 2 | 0.223 | 0.22 [−0.02, +0.41] | 0.112 | −8% [−20, +4] |
| Plain C, threshold × 3 | 0.213 | 0.29 [+0.05, +0.50] | 0.120 | −2% [−17, +13] |
| Huber 2.0, threshold × 2 | 0.217 | 0.27 [+0.01, +0.52] | 0.112 | −9% [−21, +3] |

## Segmentation against the truth (1,223 true changes begun by their prefix)

| Confirmation test | Primary: false transitions | Primary: misses | Clean: false | Clean: misses |
| --- | --- | --- | --- | --- |
| C″ as frozen | 1,137 | 361 | 223 | 410 |
| Huber 2.0 | 815 | 380 | 220 | 405 |
| Huber 1.345 | 811 | 375 | 223 | 407 |
| Plain C, threshold × 2 | 807 | 383 | 128 | 476 |
| Plain C, threshold × 3 | 600 | 442 | 116 | 538 |
| Huber 2.0, threshold × 2 | 464 | 439 | 114 | 479 |

## What the measurements support

1. **The robust test does what it was built for and no more than a threshold does.** Huber
   costs remove 28% of the false transitions under mismatch and leave clean data as it was;
   doubling the threshold removes the same number. Downstream, Huber alone is not better than
   the baseline (−0.018 [−0.060, +0.012]) and not better than the doubled threshold
   (+0.012 [−0.025, +0.038]).
2. **No pair of variants is separated** (`paired.json`): Huber with a doubled threshold against
   plain C at three times, +0.004 [−0.023, +0.026]; three times against twice, −0.010
   [−0.033, +0.007].
3. **By the declared rule, the robust variant is not carried.** Every variant is within 2% of
   the baseline on clean data (all read better); the lowest primary error is plain C at three
   times its threshold, and no robust variant beats it. "C-r" under the rule is **C with its
   confirmation threshold tripled**: a re-tune, not a robust design. Three is the edge of the
   grid; whether four is better is untested.
4. **False transitions are not most of the gap.** The combination removes 59% of them (1,137 to
   464) and the error moves from 0.254 to 0.217, against 0.116 on the true manoeuvre times. Each
   reduction in false transitions comes with more misses (361 to 439), and about 30% of true
   changes are missed even on clean data. The diagnosis's own measure said as much: C's
   clean-data segmentation would close 0.63 and still sit 43% above the reference.
5. On clean data every raised-threshold variant reads better than the frozen C (none with an
   interval excluding zero): C's threshold, chosen at Gate S, may be low for MAN2 with the
   current final solve. Untested on a fresh seed.

## Where this leaves spec 011

The design the spec asked for (C's tests made robust by classical means) is not shown to beat
a threshold change, on the tuning seed, at the size the plan allowed. A gate would now measure
a re-tuned threshold against the frozen C. That is the owner's call (the spec's purpose was a
robust control); see the PR for the options.
