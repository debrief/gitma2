"""Gate 2's checks (spec 007 FR-030–FR-033).

Input refusals come first: a gate input must be the frozen C (parameter digest and code digest
from the decision record) or the carried E (weights digest), made from a clean tree on the
decision's data. The criteria G2-a…G2-d reuse ``segment.gate``'s intervals; "wholly below" and
"wholly above" are strict (the SRD's wording), unlike Gate S's "within a limit".
"""

from __future__ import annotations

from typing import Any

from tma2.segment.gate import Interval, all_of


class RefusedError(ValueError):
    """An input the gate will not score."""


def _require(h: dict[str, Any], key: str, want: str, what: str) -> None:
    got = h.get(key)
    if got != want:
        raise RefusedError(f"{what}: {key} {str(got)[:12]}… is not the decision's {want[:12]}…")


def check_segmentation(h: dict[str, Any], dataset: str, parameters: str, code: str) -> None:
    """A C segmentation file's header against the decision (FR-001, FR-033)."""
    _require(h, "dataset_digest", dataset, "segmentation")
    _require(h, "segmenter_sha256", parameters, "segmentation")
    _require(h, "code_sha256", code, "segmentation")
    if h.get("git_dirty") is not False:
        raise RefusedError("segmentation: made from a dirty tree")


def check_prediction(h: dict[str, Any], dataset: str, parameters: str, weights: str) -> None:
    """An E prediction file's header against the decision and the carried weights."""
    _require(h, "dataset_digest", dataset, "prediction")
    _require(h, "parameters_sha256", parameters, "prediction")
    _require(h, "weights_sha256", weights, "prediction")
    if h.get("git_dirty") is not False:
        raise RefusedError("prediction: made from a dirty tree")


# ---- verdicts (FR-030–FR-032; T022). An interval with no rows is NaN and falls through every
# comparison to inconclusive.

PASS, FAIL, INCONCLUSIVE = "pass", "fail", "inconclusive"


def below(iv: Interval, limit: float) -> str:
    """Wholly below ``limit``: pass if the point and the upper bound are below it; fail if the
    lower bound is at or above it."""
    if iv.value < limit and iv.hi < limit:
        return PASS
    if iv.lo >= limit:
        return FAIL
    return INCONCLUSIVE


def above(iv: Interval, limit: float) -> str:
    """Wholly above ``limit``: pass if the point and the lower bound are above it; fail if the
    upper bound is at or below it."""
    if iv.value > limit and iv.lo > limit:
        return PASS
    if iv.hi <= limit:
        return FAIL
    return INCONCLUSIVE


def g2a(vs_imm: dict[str, Interval], limit: float) -> str:
    """E / IMM, median range and course over all G5 rows."""
    return all_of([below(vs_imm["range"], limit), below(vs_imm["course_deg"], limit)])


def g2b(vs_one_leg_settled: dict[str, Interval], limit: float) -> str:
    """Settled rows: range, course and speed, E / one leg."""
    return all_of(
        [below(vs_one_leg_settled[c], limit) for c in ("range", "course_deg", "speed_kt")]
    )


def g2c(gap: Interval, limit: float) -> str:
    return above(gap, limit)


def shuffled_rule(shuffled_minus_c: Interval) -> str:
    """Validation: the shuffled control must not beat C (its gap difference wholly above zero)."""
    return FAIL if above(shuffled_minus_c, 0.0) == PASS else PASS


def g2d(e_minus_c: Interval, shuffled: str) -> str:
    """The learning claim; a failed shuffled rule makes a pass a fail (not passed)."""
    v = above(e_minus_c, 0.0)
    return FAIL if v == PASS and shuffled != PASS else v


def validation_rule(points: dict[str, float], limits: dict[str, tuple[str, float]]) -> bool:
    """FR-032: every gated check's point meets its limit (``limits``: name → ("below" |
    "above", limit))."""
    for name, (side, lim) in limits.items():
        v = points[name]
        if not (v < lim if side == "below" else v > lim):
            return False
    return True
