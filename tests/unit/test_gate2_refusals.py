"""Gate 2 refuses inputs that are not the frozen C or the carried E (spec 007 T007, FR-033)."""

from __future__ import annotations

from typing import Any

import pytest

from tma2.gate2.gate import RefusedError, check_prediction, check_segmentation

DIG = "d" * 64
PAR = "p" * 64
CODE = "c" * 64
W = "w" * 64


def _seg(**kw: Any) -> dict[str, Any]:
    h = {"dataset_digest": DIG, "segmenter_sha256": PAR, "code_sha256": CODE, "git_dirty": False}
    h.update(kw)
    return h


def _pred(**kw: Any) -> dict[str, Any]:
    h = {"dataset_digest": DIG, "parameters_sha256": PAR, "weights_sha256": W, "git_dirty": False}
    h.update(kw)
    return h


def test_segmentation_accepted() -> None:
    check_segmentation(_seg(), DIG, PAR, CODE)


@pytest.mark.parametrize(
    "bad",
    [
        {"dataset_digest": "x" * 64},
        {"segmenter_sha256": "x" * 64},
        {"code_sha256": "x" * 64},
        {"code_sha256": None},
        {"git_dirty": True},
    ],
)
def test_segmentation_refused(bad: dict[str, Any]) -> None:
    with pytest.raises(RefusedError):
        check_segmentation(_seg(**bad), DIG, PAR, CODE)


def test_prediction_accepted_and_refused() -> None:
    check_prediction(_pred(), DIG, PAR, W)
    for bad in ({"weights_sha256": "x" * 64}, {"parameters_sha256": "x" * 64}, {"git_dirty": True}):
        with pytest.raises(RefusedError):
            check_prediction(_pred(**bad), DIG, PAR, W)
