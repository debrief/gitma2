"""Spec 010 slides: Gate 5's course statement as two SVG charts, from committed records.

    uv run python scripts/research/g5_charts.py --out-dir <dir>

Reads ``experiments/20261109-g5-val/calibration.json`` (head st5-s1-best, classical rule,
temperature, all in the truncated form) and ``experiments/20261109-g5-base-val/calibration.json``
(E raw).

* ``reliability.svg``: stated P against the hit rate in five equal-count bins of P.
* ``slices.svg``: mean stated P beside the hit rate for the head and the classical rule, overall,
  by the causal proxy's flag, by the truth's settled split, and by range band.

A ``<fig>.svg.json`` sidecar beside each figure names the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VAL = Path("experiments/20261109-g5-val/calibration.json")
BASE = Path("experiments/20261109-g5-base-val/calibration.json")
REL = [
    ("E raw sds", BASE, "e-s3"),
    ("temperature (sd^β)", VAL, "temperature5"),
    ("classical rule (carried)", VAL, "classical5"),
    ("head st5-s1", VAL, "st5-s1-best"),
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import ESTIMATORS, STYLE

    g = read_git_provenance()  # before writing anything
    data = {f: json.loads((ROOT / f).read_text()) for f in (VAL, BASE)}

    def est(f: Path, name: str) -> dict[str, Any]:
        d = data[f]
        r: dict[str, Any] = d.get("estimators", d)[name]
        return r

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(5.2, 4.6))
        ax.plot([0, 1], [0, 1], color="#888888", lw=1, ls="--", label="honest")
        for i, (label, f, name) in enumerate(REL):
            b = [x for x in est(f, name)["reliability_bins"] if x["p"] > 0]
            ax.plot([x["p"] for x in b], [x["hit"] for x in b], marker="o", lw=1.5,
                    color=ESTIMATORS[i], label=label)  # fmt: skip
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("stated P (course within ±X)")
        ax.set_ylabel("hit rate")
        ax.set_title("Validation 314: five equal-count bins of P")
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(out / "reliability.svg")
        plt.close(fig)

        groups: list[tuple[str, str, str | None]] = [("all", "overall", None)]
        groups += [("flagged", "by_proxy", "flagged"), ("not flagged", "by_proxy", "not_flagged")]
        groups += [("settled", "by_settled", "settled"),
                   ("not settled", "by_settled", "not_settled")]  # fmt: skip
        groups += [(f"{b}", "by_range_band", b) for b in ("2-5km", "10-20km", "30+km")]
        fig, ax = plt.subplots(figsize=(8.6, 3.8))
        x = np.arange(len(groups))
        series = [("classical rule", "classical5", 2), ("head st5-s1", "st5-s1-best", 3)]
        w = 0.2
        for j, (label, name, ci) in enumerate(series):
            r = est(VAL, name)
            p, h = [], []
            for _, key, lab in groups:
                m = r["overall"] if lab is None else r[key][lab]
                p.append(m["statement_mean_p"]["value"])
                h.append(m["statement_mean_p"]["value"] + m["statement_reliability"]["value"])
            off = (j - 0.5) * 2 * w
            ax.bar(x + off - w / 2, p, w, color=ESTIMATORS[ci], alpha=0.45,
                   label=f"{label}: stated P")  # fmt: skip
            ax.bar(x + off + w / 2, h, w, color=ESTIMATORS[ci], label=f"{label}: hit rate")
        ax.set_xticks(x, [t for t, _, _ in groups], fontsize=8)
        ax.set_ylim(0, 1)
        ax.set_ylabel("share of rows")
        ax.set_title("Stated P and hit rate: proxy flag (causal), truth's settled split, range")
        ax.legend(ncol=2, fontsize=7, loc="upper right")
        fig.tight_layout()
        fig.savefig(out / "slices.svg")
        plt.close(fig)

    inputs = {str(f): hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in (VAL, BASE)}
    for fig_name in ("reliability.svg", "slices.svg"):
        side = {
            "command": "uv run python scripts/research/g5_charts.py --out-dir " + a.out_dir,
            "inputs": inputs,
            "code_git_commit": g.commit,
            "code_git_dirty": g.dirty,
        }
        (out / f"{fig_name}.json").write_text(json.dumps(side, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
