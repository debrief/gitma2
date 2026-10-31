# Oracle segmentation: the ceiling for "segment, then solve"

A bounded experiment run on 31 October 2026 to test the premise of
[04-proposal.md](04-proposal.md) before anything is built: **if a learned component could tell
batch least squares only *when* the target manoeuvred, how would a piecewise-constant-velocity
batch fit compare with gitma's frozen IMM reference and with plain batch least squares?**

Script: [`scripts/research/oracle_segmented_ls.py`](../../scripts/research/oracle_segmented_ls.py).
Raw output: [`data/`](data/).

## Setup

- **Data.** gitma at commit `d0aec60`, `tma-generate --seed 777 --count 3000` with
  `configs/phase4-ranges.json` (generator 0.5.0: 0–3 target course changes, a speed change in
  30%, 20–60 min windows). The 2,400-scenario train split was used as a scratch set; seed 777 is
  not one of gitma's reserved seeds, and nothing here is a gate result.
- **Rows.** gitma's G5 rows: σ = 1° scenarios at zig + 5, 10, 15 and 20 min where the window
  reaches them. 4,083 rows from 1,193 scenarios. *Settled* rows follow Annex C §C.5 (no
  manoeuvre in progress, and the last one ended at least 5 min earlier): 1,750 rows.
- **IMM.** gitma's `tma-track --filter imm` with the frozen phase-4 reference settings
  (σ_cv 0.01, σ_ct 0.03, σ_ω 0.01, switch 0.001, P0 × 4, R × 8). Its median range error over all
  rows here is 9.56%, against 9.24% on gitma's seed-211 validation split, so the sample is
  representative.
- **Batch least squares.** gitma's `tma-solve --per-timestep` (single constant-velocity model,
  grid start, plausibility bounds).
- **Oracle.** A causal piecewise-constant-velocity batch solve in NumPy/SciPy: at row k it uses
  bearings 0..k and the truth manoeuvre spans whose start ≤ k. Velocity is constant between knots
  at each span's start and end (a rate-limited turn is approximated by its chord). A ridge prior
  (σ = 3 m/s) ties each new segment's velocity to the previous one, so a leg a few samples old does
  not blow up. Initialised from gitma's grid, then Levenberg–Marquardt. Two variants:
  - **no speed prior:** the oracle knows *when*, nothing else;
  - **speed prior:** across a *course-only* manoeuvre a soft prior (σ = 1 m/s) says speed carried
    through. This is knowledge gitma's networks demonstrably learned (phase 3: "the target's speed
    is unchanged through a turn"), so a learned segmenter that also classifies the manoeuvre kind
    could supply it.
- **Gross error:** range error > 50% or no estimate (non-converged), as gitma.

## Results (σ = 1°, medians unless stated)

**All G5 rows, n = 4,083**

| Estimator | Range | Range P90 | Course | Speed | Gross |
| --- | --- | --- | --- | --- | --- |
| Oracle, speed prior | **5.09%** | 23.5% | **9.9°** | **0.76 kt** | 2.40% |
| Oracle, no speed prior | 6.11% | 24.9% | 13.9° | 1.70 kt | 2.35% |
| IMM (frozen reference) | 9.56% | 39.5% | 23.5° | 1.90 kt | 6.27% |
| Batch least squares | 10.97% | 67.2% | 42.8° | 1.72 kt | 20.96% |

**Settled rows, n = 1,750**

| Estimator | Range | Range P90 | Course | Speed | Gross |
| --- | --- | --- | --- | --- | --- |
| Oracle, speed prior | **3.90%** | 18.6% | **2.0°** | **0.58 kt** | 1.83% |
| Oracle, no speed prior | 4.33% | 20.8% | 2.4° | 0.80 kt | 2.17% |
| IMM | 7.78% | 36.0% | 8.1° | 1.33 kt | 5.09% |
| Batch least squares | 6.30% | 62.9% | 2.8° | 0.90 kt | 18.06% |

**Paired, scenario-clustered bootstrap (2,000 resamples), median ratio oracle / IMM, 97.5% intervals**

| Rows | Quantity | Speed prior | No speed prior |
| --- | --- | --- | --- |
| all | range | 0.531 [0.486, 0.574] | 0.639 [0.595, 0.687] |
| all | course | 0.422 [0.378, 0.469] | 0.590 [0.534, 0.649] |
| all | speed | 0.398 [0.367, 0.429] | 0.890 [0.825, 0.969] |
| settled | range | 0.501 [0.450, 0.557] | 0.556 [0.508, 0.628] |
| settled | course | 0.244 [0.215, 0.282] | 0.298 [0.252, 0.345] |
| settled | speed | 0.433 [0.372, 0.490] | 0.603 [0.526, 0.701] |

**By gate time** (median range; full tables in `data/`)

| zig + | n | Oracle, speed prior | IMM | Batch LS |
| --- | --- | --- | --- | --- |
| 5 min | 1,216 | 3.9% | 5.8% | 5.2% |
| 10 min | 1,182 | 4.9% | 9.6% | 10.1% |
| 15 min | 1,014 | 6.0% | 13.6% | 21.1% |
| 20 min | 671 | 7.6% | 18.1% | 29.6% |

Before any manoeuvre has started (951 rows) the oracle and batch least squares are identical by
construction (2.57% range, 0.73°, 0.33 kt) and the IMM is 4.06%, 4.3°, 0.75 kt.

## Reading it

- **Every G5 check would pass by a wide margin for the oracle**, with both variants, including the
  settled-speed check that gitma forecast as the hardest (0.43 × the IMM with the speed prior).
  gitma's two phase-4 trackers were forecast at 1.1–1.5 × on that check.
- **Knowing *when* is worth about a third of the IMM's range error; knowing that speed carried
  through a turn is worth most of the rest on speed** (1.70 → 0.76 kt overall; 2.54 → 0.91 kt on
  unsettled rows). The second is a classification the network has already shown it can make.
- **The gain grows with time since the zig**, from 0.67 × the IMM at 5 min to 0.42 × at 20 min,
  because a batch solve keeps using the old legs where a filter has forgotten them. Plain least
  squares goes the other way (0.9 × to 1.6 ×) because its single-leg model is increasingly wrong.
- **Batch least squares' gross-error rate (21%) is mostly the plausibility bound firing** on
  post-manoeuvre fits, not divergence; the oracle's 2.4% is close to the IMM's pre-manoeuvre
  rate. The learned weighting and initialisation heads in the proposal are aimed at that
  residual.
- **Course right after a manoeuvre is still poor for everyone** (oracle 24°, IMM 44° on unsettled
  rows): a leg a few minutes old is nearly unobservable whatever the model. The proposal should
  report error against time since the manoeuvre, not only the pooled medians.

## What this does and does not show

- It is an **upper bound**, not a result. The oracle reads the truth manoeuvre spans. A learned
  segmenter will detect late, miss some, and false-alarm on others. The project's open question
  is how much of the gap between plain least squares and this ceiling a learned segmenter
  recovers; the proposal's Gate B asks for at least half.
- A **CUSUM-style detector on least-squares residuals** may recover a good fraction of it without
  learning. That is why the proposal keeps a CUSUM-segmented solve as a control: the learned
  component must beat it, not just the IMM.
- The ridge and speed-prior strengths (3 m/s, 1 m/s) were chosen once, not tuned on this set; the
  speed prior was tried at two values (off, 1 m/s) on a 150-scenario subset before the full run.
  A tuned reference on a held-out split would be fairer to the IMM too; gitma's reference was tuned
  on a different seed and is used here as frozen.
- One sample, 2,400 scenarios, no re-run. The intervals above are wide enough to be honest about
  that and narrow enough that the direction is not in doubt.
- Chord approximation of rate-limited turns and the ridge prior are model mismatches the oracle
  carries; a learned solver layer could do better (for example by excluding bearings inside a
  detected turn, or by fitting a coordinated-turn segment).
