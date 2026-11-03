# A steady-leg pre-processor from the arctan law

Status: pilot on validation, 3 November 2026. Asked for by the owner after note 06: "a fresh
trial of a target zig detector … the ATAN optimisation relationship, and how to pre-process
data so that a 'Steady Leg' flag can be added to the incoming data". Nothing here is trained,
pre-registered or scored on test data. Every threshold was tuned on the rows it is scored on, so
the numbers are optimistic until a fresh split confirms them.

Code: `src/tma2/detect/steady_leg.py`; scripts `scripts/research/steady_leg_trial.py`
(detection), `steady_leg_downstream.py` (knots from alarms) and `steady_leg_confirm.py`
(confirmed knots); records in `experiments/20261102-steady-leg-trial/`.

## 1. The relationship

While the target and ownship both hold course and speed, their relative position is linear in
time, so the bearing obeys

  tan b(t) = (A + B t) / (C + D t),

a three-parameter curve, since range is a free scale. Ownship's track is known exactly, so the
general form subtracts it, and stays valid through ownship's own turns:

  b(τ) = atan2(x + vₓτ − oₓ(τ), y + v_yτ − o_y(τ)),  τ = t − t_k,

with (x, y, vₓ, v_y) the target's state at row k. A target manoeuvre inside the window breaks
the law, and nothing else does (apart from noise and dropouts).

## 2. Per-row channels

For each row k, over a sliding window of W = 36 rows (6 min at 10 s):

| Channel | What it is | On a steady leg |
| --- | --- | --- |
| `sl_misfit` | the one-leg fit's cost / σ² / (n − 3); gitma's Levenberg–Marquardt, warm-started from row k − 1 with a grid restart every 6 rows | ≈ 1 |
| `sl_split` | Λ, the window's best two-leg improvement: the linearised split test at the window's own fit (one-leg columns projected out, a velocity change at each candidate row) | χ²-like, median ≈ 4.5 |
| `sl_split_row` | the row of that best split | anywhere |
| `sl_ok` | the fit exists (≥ 6 valid bearings, no collapse onto ownship) | 1 |

The split test is the Gate D GLR with its linearisation point moved from the whole-history fit
(wrong after the first manoeuvre) to the window's own fit. Cost is about 37 ms per 360-row
scenario in numba.

## 3. What did not work

**Detection is not the bottleneck.** At a 5% held-leg false-alarm rate per row, `sl_split`
(W = 36) detects 64% of manoeuvres, against 58% for the Gate D GLR and 48% for the IMM's mode
probability (500 scenarios). Truth knots supplied only for the manoeuvres it detected would
already beat the IMM (9.1% median range error against 9.7%).

**Alarms as knots fail.** One knot per alarm episode at `sl_split_row` gives 11.4–16.2% median
range error, worse than the IMM and at best slightly better than batch least squares (12.6%).
At 1% false alarm, 57% of knots are false and the true ones are a median 235 s from the
manoeuvre. Persistence rules and higher thresholds did not help.

**Restricting windows to ownship legs (Debrief's practice) made it worse.** Detection fell from
36% to 30% at 1% false alarm and the error rose to 12.7%. With the general form, ownship's turn
does not break the law. Instead, a window spanning it is where the split test has its power.

## 4. What worked: nominate, then confirm by the whole history

The window is the right place to *notice* a change but the wrong place to *decide* one. The
decision is taken by the physics layer, the same piecewise solver Gate 2 uses:

1. An alarm episode of `sl_split` (threshold at a per-row held-leg false-alarm rate) nominates
   its first row a.
2. The layer solves the whole history [0, a] with the knots accepted so far, and once more for
   each candidate knot every 3 rows in the window.
3. The best candidate is accepted if it lowers the cost Σ(r/σ)² by more than τ (χ² with 2
   degrees of freedom, the velocity increment). It is used from row a on.

Placement is then within 2 rows (20 s, median) of the true boundary, against 235 s from the
window alone. τ removes chance alarms: at τ = 13.8, 17% of knots are false at any nomination
rate.

Results at σ = 1° G5 rows, validation seed 304, first 500 scenarios (1,663 rows):

| Estimator | Median range error, all | Settled | Course | Speed |
| --- | --- | --- | --- | --- |
| batch least squares (the layer, no knots) | 12.6% | 7.9% | 43° | 1.97 kt |
| IMM (frozen) | 9.7% | 7.8% | 22° | 1.83 kt |
| confirmed knots, 10% nomination, τ = 13.8, speed prior | **9.2%** | **6.5%** | 24° | **1.47 kt** |
| oracle (truth spans) | 5.4% | 4.4% | 9° | 0.78 kt |

The full sweep is in `confirm.json`. The pattern:
- higher τ is better in every row;
- more nominations help once τ is strict;
- the speed prior always helps.

<!-- SWEEP2 -->

## 5. The Steady Leg flag

Per row k, from the channels and the confirmed knots:

| Value | When |
| --- | --- |
| `unknown` | `sl_ok` = 0 (too few bearings, start-up) |
| `steady` | no alarm in progress and no knot accepted within the last W rows |
| `suspect` | `sl_split` above the nomination threshold, not (yet) confirmed |
| `changed` | a knot was confirmed at row r ≤ k within the last W rows; `knot_age` = t_k − t_r |

The flag and the channels are causal: row k uses bearings up to k only. The confirmed knots are
the segmentation the physics layer consumes.

## 6. Critical assessment

- **In-sample.** τ, the nomination rate and W were chosen on the rows scored. The margin over
  the IMM (9.2% against 9.7%) is small and has no interval yet. It needs a fresh validation
  split and a scenario-clustered paired bootstrap before anyone relies on it.
- **Course is worse than the IMM** (24° against 22°), and speed and settled range are better. A
  per-quantity verdict is needed, not an overall one.
- **Most of the oracle's gain is still missing.** At 9.2% against the oracle's 5.4%, about 11%
  of the gap between the IMM and the oracle is closed. Misses dominate now that false knots are
  17%.
- **Cost.** About 13 extra layer solves per alarm episode. That is cheap offline, but heavier
  than a filter for real-time use.
- **It is classical.** This is option A of note 06 done well, not learning. It raises the bar a
  learned detector has to beat (option B), and it is the obvious source of B's inputs.

## 7. Next steps (proposed)

1. Re-score the chosen setting on fresh validation rows (the rest of seed 304, untouched so far)
   with a scenario-clustered paired bootstrap against the IMM and batch least squares.
2. Kind (course or speed change) from the fitted increment, to set the speed prior per knot.
3. Option B: a small learned detector whose inputs are these channels, trained on
   classification only, with the confirmation step kept as the decision.
