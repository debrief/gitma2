# 12. Longer engagements: 6 to 48 hours (spec 023, issue #42)

**Status**: investigation, 2026-11-17. Not a gate, nothing trained, no GPU. Record:
`experiments/20261117-long/` (`tables.md` generated from `summary.json`). One simulated
engagement per duration (seed 348), so every figure here is an anecdote about four engagements,
not a rate.

## Question

The owner asked (issue #42) what it would take to apply our TMA to engagements of 6, 12, 24 and
48 hours, and to show such engagements on the viewer and time-late pages.

## What was done

1. **A long-engagement simulator** (`src/tma2/long/sim.py`), separate from generator 0.6.0 so
   that its output stays byte-identical. The target follows Annex B's statistics (legs of
   N(25, 9.1) minutes, at least 5; 80% course, 10% speed, 10% both; 30–120° turns at 0.25–1°/s).
   The ownship runs 20–40 minute legs with a turn at the start of each, alternating the side of
   the line of sight, and keeps the target between 3 and 25 km by closing (sprinting at 11 m/s)
   or opening on the next leg. It steers on the true target position.
2. **Windows** (`src/tma2/long/windows.py`): a long engagement is cut into windows that every
   estimator already reads (time from 0, positions from the ownship's at the window's start,
   truth re-indexed).
3. **Real-time** (`src/tma2/long/realtime.py`): every 10 minutes, E (the carried Gate 2 model,
   its exported graph) and C″ on the last 2 hours, one leg on the last 30 minutes, and the IMM
   over the whole engagement.
4. **Time-late** (`src/tma2/long/timelate.py`): the standing control `ctl` on a chain of 2-hour
   windows overlapping by 30 minutes, stitched at the overlaps' middles; and `ctl` timed on
   single periods of 0.5 to 6 hours.
5. **Pages**: a long-engagement section on `/viewer` and on `/timelate`, precomputed in Python.

RESULTS_PLACEHOLDER
