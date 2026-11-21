"""Spec 035: golden manoeuvre spans for the demonstrator's legs read-out.

From the committed ``demo/golden-tlm.json`` (seed 1's logits per token on the golden problems,
from torch), Python's ``tma2.timelate.learned.spans_from_logit`` at spec 016's settings
(threshold 0.5, merge 60 s) with at most ten spans and with the page's cap of four. The
JavaScript port (``tlm.js`` ``spansFromLogit``) is checked against this file in
``demo_node.mjs``; ``tests/unit/test_demo_golden.py`` checks the file is Python's.

    uv run python demo_spans_golden.py demo/golden-tlm.json demo/golden-spans.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from tma2.timelate.learned import spans_from_logit, token_times

DT = 5.0
PATCH = 6


def spans_of(golden: dict) -> dict:
    out: dict = {"problems_sha256": golden["problems_sha256"], "cases": {}}
    for cid, g in golden["cases"].items():
        rows = int(g["rows"])
        logit = np.asarray(g["logit"], dtype=np.float64)
        prob = 1.0 / (1.0 + np.exp(-logit))
        tt = token_times(rows, DT, PATCH)
        out["cases"][cid] = {
            "rows": rows,
            "spans": spans_from_logit(prob, tt).tolist(),
            "spans_max4": spans_from_logit(prob, tt, max_manoeuvres=4).tolist(),
        }
    return out


def main(argv: list[str]) -> int:
    src, dst = Path(argv[0]), Path(argv[1])
    dst.write_text(json.dumps(spans_of(json.loads(src.read_text()))) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
