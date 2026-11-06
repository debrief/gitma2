"""Gate 2's checks (spec 007 FR-030–FR-033).

Input refusals come first: a gate input must be the frozen C (parameter digest and code digest
from the decision record) or the carried E (weights digest), made from a clean tree on the
decision's data. The criteria G2-a…G2-d reuse ``segment.gate``'s interval logic.
"""

from __future__ import annotations

from typing import Any


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
