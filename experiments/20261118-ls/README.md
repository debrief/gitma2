# Spec 026: test record (seed 351, scored once)

CI run 44280754516 (commit a37d36d; the shards ran on 7 CPU families, see `review.md`; the collect job on AMD EPYC 7763). Its code digest and run file are the
decision record's (`experiments/20261118-ls-decision/`; digests re-checked unchanged). It ran
30 + 30 realistic engagements of 6 and 12 hours (`configs/long/study-test.json`). On both
contacts it ran `ctl` and `ctl-carry` on every window, and the frozen IMM on the 12-hour
engagements. Outputs are in `raw/`; `study.json` is `tma2-long study`'s output, run once.

## Soundness: passes

- S1: 360 of 360 windows ran, with no engagement missing. One of them (engagement 19, window 3: 46 bearings, under the 60 the runner needs) gave no answer, which is why E1 has 359 windows.
- S2: ctl ÷ the true-history fit is 1.36 (band [0.8, 4]).
- S3: bearings held 0.849 (band [0.6, 0.95]).

## The rules' outputs

| | estimate | 95% interval | rule | output |
|---|---|---|---|---|
| **E1** ctl ÷ ctl-carry, contact 1 (geometric mean over 359 windows) | 1.017 | [0.958, 1.082] | non-inferior if the lower limit ≥ 0.950 | **non-inferior** (0.958) |
| **E2** contact 2 ÷ contact 1, range-banded | 1.466 | [1.119, 2.052] | a magnitude, no rule | about 1.5× worse |
| **E3** IMM, hours 6–12 ÷ hours 0–6 (30 twelve-hour engagements) | 1.056 | [0.819, 1.309] | drift shown if the interval is wholly above 1 | **not shown** |

E1's lower limit is 0.008 above the line.

## Reported beside (deciding nothing)

**E1, window by window (contact 1)**:
- the median ratio is 1.00;
- carry is better in 98 windows, worse in 88 and level in 173;
- twice better in 22, twice worse in 17;
- search CPU: 5.84 h from the carry against 10.12 h from nothing over all windows. On the
  windows that had a carried start (the first window of each chain has none) it is 5.84 h
  against 8.50 h, a 31% saving, about 7% of all windows' CPU (`review.md` finding 5).

**E1 by length**:
- 6 h: 1.044 [0.997, 1.111], 119 windows;
- 12 h: 1.005 [0.923, 1.096], 240 windows.

**E1 on contact 2**: 0.942 [0.880, 1.007] over 216 windows.
- Carry is better in 40 windows, worse in 47; twice worse in 16 against twice better in 7.
- On the untended contact the carried start leans worse, though the interval includes 1.

**E2 by band**, median range error, contact 1 against contact 2:

| band | contact 1 | contact 2 | rows, c1 / c2 |
|---|---|---|---|
| 2–10 km | 0.89% | 1.12% | 13,065 / 3,759 |
| 10–20 km | 1.35% | 2.02% | 27,803 / 7,901 |
| 20–40 km | 2.31% | 3.84% | 22,136 / 15,452 |

**E3 by 2-hour bin**:

| hours | 0–2 | 2–4 | 4–6 | 6–8 | 8–10 | 10–12 |
|---|---|---|---|---|---|---|
| share answered | 0.91 | 0.87 | 0.84 | 0.81 | 0.74 | 0.79 |
| median error | 0.25 | 0.18 | 0.26 | 0.26 | 0.25 | 0.21 |

The median does not rise, but the share answered falls from 0.91 to 0.74–0.79.

**Pooled median range error**, contact 1:

| | ctl | ctl-carry | C″ | true-history fit |
|---|---|---|---|---|
| 6 h | 1.56% | 1.60% | 7.42% | 1.02% |
| 12 h | 1.46% | 1.42% | 6.61% | 1.13% |

## Against the forecasts

- **Soundness**: passed, as forecast.
- **E1**: non-inferior, as forecast (about three in four), but by a hair. The estimate fell from
  tuning's 1.05 and validation's 1.10 to 1.02.
- **E2**: 1.47 [1.12, 2.05]. Higher than forecast (1.2 to 1.4), and the interval excludes 1,
  where the forecast expected it to include 1.
- **E3**: no drift shown, as forecast.

## Panel (round 1: three approve with findings)

`review.md`; the recomputed readings are in `supplement.json`. What the outputs may be taken to
mean is narrowed:
- **E1**: non-inferior by the rule, by 0.008. Without each chain's first window, where carry is
  ctl by construction, it is 1.021 [0.9502, 1.100]. On the windows where the two differ, 1.034
  [0.923, 1.168]: not shown within 5%. The adoption rests on cost (31% of the search), for the
  tended contact on 6–12-hour engagements.
- **E2**: about 1.3 to 1.5 on the rows where the untended contact is held (2-km sub-bands: 1.34
  [1.01, 1.87]). Residual geometry and detection thinning are included.
- **E3**: not shown in answered rows. With unanswered rows counted as failures, 1.26
  [0.88, 1.80]. The IMM answers fewer rows later.

`study.json` records `git_dirty: true` because the record's folder was untracked when it ran;
the scored code equals the bound digest.

**After merging main (2026-11-18).** This study was numbered spec 025 while it ran. Another
session's spec 025 (joined periods) merged first, so this one is now spec 026. Bound files and
raw outputs still say 025, and none of them was edited. The merge added new modules under
`src/tma2/timelate/` (`layout.py`, `run8.py`, `study8.py`), and the code digest's glob picks them
up, so at the merged commit it no longer equals `938ef9a2…`. No module the record bound was
changed. Both sessions claimed seeds 349 and 350, each on its own simulator and stream; the
engagements differ, but the claim was made twice. The next fresh seed is 354.
