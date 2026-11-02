# Steady-leg pre-processor trial (research note 07)

Pilot on validation seed 304 (σ = 1° rows), no test data. Thresholds are tuned on the rows they
score, so these are pilot numbers, not a result.

- `confirm.json`, `confirm.log`: `scripts/research/steady_leg_confirm.py --scenarios 500`
  (split-statistic alarms nominate knots; the physics layer's whole-history cost confirms and
  places them), with batch least squares, the oracle and the frozen IMM on the same rows.
