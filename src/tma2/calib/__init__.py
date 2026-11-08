"""Uncertainty calibration of the Gate 2 estimator (spec 008).

A calibration changes only the stated covariance of E's estimate, never the estimate:
the calibrated covariance is e^(2s) times the physics solve's, with one log-scale s per row.

* ``head``: the learned s, a small MLP on E-w's frozen encoder state at the row, its raw
  log standard deviations and C's code (research R5); zero output is the identity.
* ``temperature``: the classical control, one s per declared slice (research R8).
* ``loss``: β-NLL on the 4-state Gaussian (research R6).
* ``data``: the feature cache written by ``tma2-g2predict --features``.
* ``train``, ``predict``, ``gate``: training, calibrated prediction files, Gate 3.
"""
