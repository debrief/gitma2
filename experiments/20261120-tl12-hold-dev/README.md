# Spec 033 development, second run: long gaps with the ownship holding course

Development work, not a registered result. CI run 44741196091 (`timelate/tl-q-hold-dev` at
91dc5ac), plan `configs/timelate/tl-q-hold-dev.json`, engagements from
`configs/long/gaps-hold-dev.json`. These are the same 40 engagements as the first run
(`experiments/20261120-tl12-dev/`), with the same target tracks and the same layouts of periods and
gaps. Only the ownship's legs change, from 20–40 min to 1–2 h, so the two runs pair period by
period.

Generated files:
- `tables.md`: `scripts/research/tl10_tables.py`;
- `readings.txt`: `scripts/research/tl12_readings.py`;
- `paired.txt`: `scripts/research/tl12_paired.py`.

## Readings (range; above 1 favours the second)

| | legs 20–40 min (first run) | legs 1–2 h (this run) |
|---|---|---|
| later periods with their own ownship turn | 0.78 | 0.23 |
| median error: alone / joint / k4 | 0.117 / 0.121 / 0.112 | 0.273 / 0.174 / 0.188 |
| alone ÷ joint (all periods) | 1.20 [0.90, 1.60] | **1.34 [1.01, 1.84]** |
| alone ÷ k4 | 0.94 [0.79, 1.10] | 1.05 [0.81, 1.39] |
| k4 ÷ joint | 1.22 [0.90, 1.68] | 1.29 [0.92, 1.83] |
| alone ÷ uninflated carried prior | 0.73 [0.55, 0.96] | 0.84 [0.64, 1.14] |

Alone ÷ joint by the gap before a later period:

| gap | legs 20–40 min | legs 1–2 h |
|---|---|---|
| 30–50 min | 1.40 [0.74, 2.60] | 1.34 [0.80, 2.35] |
| 50–70 min | 1.27 [0.82, 2.18] | **2.85 [1.49, 6.05]** |
| 70–90 min | 0.80 [0.48, 1.28] | 0.71 [0.47, 1.02] |

Paired over the 66 periods scored in both runs, holding course multiplies the error by these
factors (geometric mean; median):
- alone: 1.99; 1.49;
- joint: 1.84; 1.65;
- k4: 1.81; 1.82.

The joint solve costs a median of 625 s an engagement, against 55 s for `ctl` alone. It never
reaches the cap of 10 manoeuvres here. It declares 120 of the 174 true gap manoeuvres.

## What it says, critically

1. **Holding course roughly doubles everyone's error.** Periods without their own ownship turn are
   poorly determined whatever the method. Joining recovers some of that loss (1.34, the lower limit
   just above 1), and k4 does not separate from alone.
2. **Joining's benefit is largest at 50–70 min gaps** (2.85 with long legs) **and reverses beyond 70
   min in both runs** (0.80 and 0.71).
   - The two runs share their targets, gaps and layouts, so the reversal is one observation seen
     twice, not a replication.
   - The 30–50 min band being smaller than the 50–70 min band is not expected. It is within noise
     (28 and 19 periods).
   - A likely mechanism, not tested: beyond about 70 min the joint solve must bridge about three
     unseen manoeuvres with one history and declares fewer than are there. Its errors in the gap
     then pull the observed periods.
3. **The carried prior does not help across long gaps.** k4 says almost nothing after an hour (it
   covers the truth in 0.99 of carried periods, median d² 0.82). The uninflated prior is
   overconfident (it covers 0.35) and leans toward harm.
4. **Small samples:** 40 engagements, about 20 to 30 periods per gap band, one spent seed.

## What would decide it (owner's choice)

A registered study of the operating rule "join periods across gaps up to about an hour, solve them
alone beyond":
- held-course ownship (where it matters);
- fresh seeds 365 (validation) and 366 (test);
- enough engagements for the gap bands to be separated, about 100 at roughly 6 CI hours per run.

The alternative is to stop and write the time-late gap track up as a whole (specs 025, 027, 030,
031).
