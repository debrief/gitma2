"""The scaled end-to-end regressor (spec 012): a control, never the project's estimator.

A causal transformer maps bearings and the ownship track straight to the target's state, with no
physics layer. It exists to test whether gitma's floor at about 3 × the Cramér–Rao bound was
compute and data or architecture. It is not exported and not carried (constitution III).
"""
