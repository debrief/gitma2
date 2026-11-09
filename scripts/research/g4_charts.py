"""Spec 009 slides: Gate 4's course statement as two SVG charts, from committed records.

    uv run python scripts/research/g4_charts.py --out-dir <dir>

Reads ``experiments/20261109-g4-val/calibration.json`` (carried head st-s3-best, temperature) and
``experiments/20261108-g4-base-val/calibration.json`` (E raw, oracle; statements from their sds).

* ``reliability.svg``: stated P against the hit rate in five equal-count bins of P, per estimator
  (the diagonal is an honest statement).
* ``slices.svg``: mean stated P beside the hit rate for the head and the temperature, overall, by
  settled / not settled, open transition at k and G5 minute.

Writes ``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VAL = Path("experiments/20261109-g4-val/calibration.json")
BASE = Path("experiments/20261108-g4-base-val/calibration.json")
REL = [  # (label, file, estimator)
    ("oracle (raw sds)", BASE, "oracle"),
    ("E raw sds", BASE, "e-s3"),
    ("temperature", VAL, "temperature"),
    ("head (st-s3)", VAL, "st-s3-best"),
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
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def est(f: Path, name: str) -> dict:  # type: ignore[type-arg]
        d = data[f]
        r: dict = d.get("estimators", d)[name]  # type: ignore[type-arg]
        return r

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

        groups = [("all", "overall", None)]
        groups += [(f"{lab}", "by_settled", lab) for lab in ("settled", "not_settled")]
        groups += [(f"{lab}", "by_open_at_k", lab) for lab in ("not_open", "open")]
        groups += [(f"min {m}", "by_g5_minutes", m) for m in ("5", "10", "15", "20")]
        fig, ax = plt.subplots(figsize=(8.4, 3.8))
        x = np.arange(len(groups))
        series = [("temperature", "temperature", 2), ("head (st-s3)", "st-s3-best", 3)]
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
        ax.set_title("Stated P and hit rate by slice (validation 314, scoring rows)")
        ax.legend(ncol=2, fontsize=7, loc="upper right")
        fig.tight_layout()
        fig.savefig(out / "slices.svg")
        plt.close(fig)

    inputs = {str(f): hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in (VAL, BASE)}
    for fig_name in ("reliability.svg", "slices.svg"):
        side = {
            "command": "uv run python scripts/research/g4_charts.py --out-dir " + a.out_dir,
            "inputs": inputs,
            "code_git_commit": g.commit,
            "code_git_dirty": g.dirty,
        }
        (out / f"{fig_name}.json").write_text(json.dumps(side, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
