"""Gate 2 on MAN2 (spec 007): the learned model E on the frozen classical segmenter C.

* ``inputs``: per-prefix physics-layer inputs from C's segmentation, with learned log-weights
  added to C's hand-over mask, and C's per-row code at prefix k (causal).
* ``model``: E-w (encoder, per-bearing weights, initial-state correction) and E-s (evidence that
  shifts C's confirmation threshold). Untrained, E equals C (FR-022).
* ``tables``: E-s's decision tables (research R2).
* ``loss``: the bound-normalised downstream loss, robust to absurd prefixes (research R4).
* ``train``, ``predict``: chained resumable training; per-row predictions for scoring.
* ``gate``: G2-a…G2-d, the shuffled rule, the validation rule and the input refusals.

Gate 2 uses a physics layer with ``KNOTS`` knots (research R5: 0.18% of validation G5 prefixes
need more than spec 005's 8).
"""

from __future__ import annotations

KNOTS = 12
