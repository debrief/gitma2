"""Spec 008 slides: Gate 3's calibration measures as one bar chart (SVG), from committed records.

    uv run python scripts/research/g3_calibration_chart.py --out <fig.svg>

Reads ``experiments/20261108-g3-val/calibration.json`` (E raw, temperature, carried head) and
``experiments/20261108-g3-base-val/calibration.json`` (oracle, IMM) and draws, per estimator, the
95% coverage of log range, course and speed and the share within the χ²₄ 95% NEES point, with
Gate 3's band [0.92, 0.98] shaded. Writes ``<fig.svg>.json`` naming the inputs' digests and the
commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VAL = Path("experiments/20261108-g3-val/calibration.json")
BASE = Path("experiments/20261108-g3-base-val/calibration.json")
ROWS = [  # (label, file, estimator)
    ("oracle", BASE, "oracle"),
    ("IMM (frozen)", BASE, "imm"),
    ("E raw", VAL, "e-s3"),
    ("temperature", VAL, "temp"),
    ("head (cal-s3)", VAL, "cal-s3"),
]
MEASURES = [
    ("coverage95_log_range", "95% cov. log range"),
    ("coverage95_course", "95% cov. course"),
    ("coverage95_speed", "95% cov. speed"),
    ("nees_within95", "within χ²₄ 95%"),
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import ESTIMATORS, STYLE

    data = {f: json.loads(f.read_text()) for f in (VAL, BASE)}
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(8.0, 3.8))
        x = np.arange(len(MEASURES))
        w = 0.8 / len(ROWS)
        ax.axhspan(0.92, 0.98, color="#2a9d8f", alpha=0.12, label="Gate 3 band")
        for i, (label, f, name) in enumerate(ROWS):
            o = data[f][name]["overall"]
            v = [o[m]["value"] for m, _ in MEASURES]
            ax.bar(x + (i - (len(ROWS) - 1) / 2) * w, v, w, label=label, color=ESTIMATORS[i])
        ax.set_xticks(x, [t for _, t in MEASURES])
        ax.set_ylim(0, 1.02)
        ax.set_ylabel("share of rows (3,934)")
        ax.set_title(
            "Validation 314: stated uncertainty against the errors (missing rows count out)"
        )
        ax.legend(ncol=3, fontsize=8, loc="lower right")
        fig.tight_layout()
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out)
        plt.close(fig)
    g = read_git_provenance()
    side = {
        "command": "uv run python scripts/research/g3_calibration_chart.py --out " + a.out,
        "inputs": {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in (VAL, BASE)},
        "code_git_commit": g.commit,
        "code_git_dirty": g.dirty,
    }
    Path(str(out) + ".json").write_text(json.dumps(side, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
