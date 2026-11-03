# Steady-leg pre-processor trial (research note 07)

Pilot on validation seed 304 (σ = 1° rows), no test data. Thresholds are tuned on the rows they
score, so these are pilot numbers, not a result.

- `confirm.json`, `confirm.log`: `scripts/research/steady_leg_confirm.py --scenarios 500`
  (split-statistic alarms nominate knots; the physics layer's whole-history cost confirms and
  places them), with batch least squares, the oracle and the frozen IMM on the same rows.
- `confirm2.log`: sweep 2, `--far 0.1,0.2,0.4 --tau 13.8,20,30`. It was stopped by the session's
  2-hour background limit after six of nine configurations (the 40% rows did not run), so it has
  no JSON. The log carries every completed configuration in full.
- `confirm3.json`, `confirm3.log`: `--far 0.4 --tau 13.8`, the configuration sweep 2 did not reach.
