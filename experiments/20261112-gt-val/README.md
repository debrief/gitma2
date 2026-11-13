# Gate T, validation seed 330: stopped at T-a

Run 43202264676 (`timelate/tl-a-val`, commit 9acc886, clean tree, AMD EPYC 7763), plan
`configs/timelate/tl-a.json` (`6f15a246…`) as bound in `../20261112-gt-decision/`. 150 periods a
split; 141 (Annex B) and 132 (shift) have determined rows. Files: `summary.json`, `score.txt`,
`*.periods.json` (every period's true history and candidates), `plan.json`, `run.json`,
`ci.json`; the per-row errors are on `results/timelate-tl-a-val-43202264676`.

**By the registered rule the gate stops here. Test seed 331 has not been generated.**

## The checks

| Check | Result | Forecast | |
| --- | --- | --- | --- |
| **T-a** reference soundness: range efficiency of the true history fitted to the bearings alone, band [0.8, 1.3] | **0.67** | about 1.0 | **fail** (the stop rule) |
| T-b C″ ÷ search, interval above 1.10 | 2.56 [1.78, 3.51] | about 2.0 | would pass; decided on test only |
| T-c the same under the shifted prior, above 1.00 | 1.70 [1.24, 2.27] | about 1.4 | would pass |
| T-d true history in the first three (at least 0.60); calibration gap (at most 0.10) | 0.76; −0.08 | 0.70; within 0.10 | would pass |
| T-e search ÷ true history with the prior, above 1.10 | 2.00 [1.52, 2.77] | about 2.2 | material, but see below |

The forecast for T-a was wrong: pass at probability 0.90.

## Every system (median over periods of the period's median relative range error)

| System | Annex B | Over 10% | Shift | Over 10% |
| --- | --- | --- | --- | --- |
| C″ read as a track | 0.113 | 0.55 | 0.124 | 0.55 |
| **Search (best history)** | **0.044** | 0.30 | **0.073** | 0.41 |
| Search from C″'s transitions | 0.049 | 0.30 | 0.091 | 0.45 |
| Search from nothing | 0.060 | 0.38 | 0.073 | 0.42 |
| One leg | 0.481 | 0.89 | 0.369 | 0.89 |
| IMM as a track | no state on over half the rows of the median period (0.345 on the rows it answers) | 0.97 | (0.341) | 1.00 |
| EKF as a track | likewise (0.356) | 0.98 | (0.320) | 0.97 |
| True history, bearings only | 0.018 | 0.07 | 0.011 | 0.04 |
| True history, with the prior | 0.022 | 0.11 | 0.024 | 0.14 |

Efficiency against the known-history bound (range, course, speed), Annex B split: C″ 3.55,
5.13, 3.31; search 1.63, 1.90, 1.54; true history bearings only 0.67, 0.76, 0.68; with the
prior 0.97, 0.98, 0.93. Shift split: search 1.90, 2.30, 1.51; true history bearings only
**0.28**, 0.36, 0.26.

Candidates, Annex B split (temperature 3): the first candidate is the true history in 0.61
of periods against a mean stated probability of 0.54; by stated probability (below 0.4,
0.4 to 0.6, 0.6 to 0.8, above 0.8): stated 0.34 / 0.49 / 0.68 / 0.89, right 0.34 / 0.56 /
0.84 / 0.86 (35, 59, 49, 7 periods). **Shift split: the first candidate is the true history
in 0.22, the true history is in the first three in 0.34, and the stated probability is 0.52:
the probabilities are wrong by 0.30 when the prior is wrong.** T-d does not gate the shift
split; this is the more important fact about the candidates.

## Why T-a failed: the reference starts at the truth

An efficiency below 1 is not a good result. An unbiased fit to the bearings cannot beat the
bound, so 0.67 (and 0.28 on the shift split) says the reference is getting something from
outside the bearings. It is: `timelate/run.py` starts the true-history fit **at the truth**,
and where the bearings determine a row only weakly the fit has no reason to move.

Tested on tuning seed 329 (`scripts/research/tl_reference_start.py`, output in
`reference-start-tuning.txt`; 60 fresh periods, never the validation seed): the same true
history fitted from the truth and from starts with range and speed scaled by 0.7 and 1.4.

| Rows, by the bound on relative range | Truth start | Start × 0.7 | Start × 1.4 | Lowest cost of the three |
| --- | --- | --- | --- | --- |
| below 0.05 (3,157 rows) | 1.05 | 3.40 | 1.79 | 1.27 |
| 0.05 to 0.2 (2,012) | 0.27 | 2.08 | 2.06 | 0.43 |
| 0.2 to 0.5 (184) | 0.08 | 1.26 | 1.65 | 1.62 |
| all determined | 0.61 | 2.68 | 1.99 | 1.08 |

Where the bound is tight the truth-started fit is at the bound (1.05), as theory says. Where
it is loose the fit stays where it was put: 0.27 and 0.08. The moved starts end at the same
cost in two cases out of three (within 1) and at several times the error. So:

- **The reference is not sound as built.** Its error is a mixture of an honest fit on
  well-determined rows and the truth handed back on the rest.
- **T-e's headroom is overstated** by an unknown amount: the search is compared with a
  reference that partly knows the answer.
- **An earlier claim is narrowed.** `../20261112-tl-prior/` section 1 said that told only the
  history, with times free, the fit reaches the bound (1.03). That fit also started at the
  truth. It holds on well-determined rows and is not shown elsewhere.
- **"Determined" was too generous.** A row counted when its bound on relative range was
  below 0.5. Between 0.05 and 0.5 the answer depends on where the fit starts, for the
  reference certainly and plausibly for every system. The search's start is nominal and its
  fit includes the prior, so it is not handed the truth; but how much of every system's
  error in those rows is start-dependence has not been measured.

T-b, T-c and T-d do not use the reference. Their validation figures stand as measurements
and agree with the tuning seed (2.12 there, 2.56 here). They are not gate results: the gate
decides them on the test seed, which the stop rule now forbids generating.

## What this record supports

- On a second seed, the evidence search is about two and a half times better than C″ read
  as a track in median range error, and 1.7 times better when targets manoeuvre otherwise
  than it assumes. Not a gate verdict.
- Its candidate probabilities are usable when the prior is right and badly overconfident
  when it is wrong.
- The gate's reference was unsound and the gate's own first check caught it.

## What must change before a gate can be run (owner's decisions; nothing changed here)

Changing a criterion or the reference after a validation result is the owner's call.
Proposals, for a re-registered gate on a fresh validation seed (332; 331 stays unused):

1. **Reference without the truth's start**: the true history's structure only, fitted with
   the prior from the same nominal starts the search uses, lowest evidence-consistent fit.
2. **T-a on well-determined rows** (bound below 0.05), where an efficiency near 1 is what a
   sound scoring must show; and report every system by how well the row is determined.
3. **A candidate check on the shift split**, since that is where the probabilities fail.
4. Seed 330 has now shown T-b to T-d; it is spent as a validation seed for them.
