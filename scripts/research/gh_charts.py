"""Spec 010 slides: Gate H in four SVG charts, from committed records and one seeded engagement.

    uv run python scripts/research/gh_charts.py --out-dir <dir>

* ``mismatch.svg``: the bearing error of one engagement (tuning seed 320, the first with a stated sigma of 1 deg) under each
  mismatch kind at central severity, beside the white noise it replaces.
* ``conditions.svg``: median range error of the plain solve, the robust control and the
  error-model-informed fit on every validation condition (seed 321).
* ``verdict.svg``: R with its 97.5% interval on the test seed (322), every scored condition,
  against the 10% threshold.
* ``range-bands.svg``: R by quartile of true range on the test seed's primary condition.

Writes ``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VAL = Path("experiments/20261110-gh-val")
TEST = Path("experiments/20261110-gh")
CONDITIONS = Path("configs/gateh/conditions.json")
RANGES = Path("configs/man2-ranges.json")
ORDER = [
    "off",
    *[
        f"{k}-{s}"
        for k in ("corr", "bias", "sigma", "out", "all")
        for s in ("mild", "central", "harsh")
    ],
]
TEST_ORDER = ["all-central", "out-central", "corr-central", "bias-central", "sigma-central", "off"]
KINDS = [
    ("off", "white, sigma 1 deg (no mismatch)"),
    ("corr-central", "correlated, 60 s"),
    ("bias-central", "slow bias, 0.5 deg"),
    ("out-central", "outliers, 2%"),
    ("all-central", "all four (primary)"),
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
    from tma2.sim import scenario as sc
    from tma2.sim.generate import KernelBuffers, run_kernel
    from tma2.sim.mismatch import flatten_condition
    from tma2.sim.ranges import flatten_ranges, rows_for

    g = read_git_provenance()  # before writing anything
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    used: dict[str, list[Path]] = {}

    def load(folder: Path, cond: str) -> dict[str, Any]:
        d: dict[str, Any] = json.loads((ROOT / folder / cond / "headroom.json").read_text())
        return d

    conds = {c["id"]: c for c in json.loads((ROOT / CONDITIONS).read_text())["conditions"]}
    ranges = json.loads((ROOT / RANGES).read_text())
    plain, robust, informed = ESTIMATORS[3], ESTIMATORS[0], ESTIMATORS[2]

    with plt.rc_context(STYLE):
        # 1. one engagement's bearing error under each kind
        buf = KernelBuffers.for_rows(rows_for(ranges))
        flat = flatten_ranges(ranges)
        index = 0  # the first engagement of seed 320 whose stated sigma is 1 deg
        while True:
            run_kernel(np.uint64(320), index, flat, buf)
            if abs(float(buf.P[sc.P_SIGMA]) - np.pi / 180) < 1e-6:
                break
            index += 1
        fig, axes = plt.subplots(len(KINDS), 1, figsize=(8.0, 6.6), sharex=True, sharey=True)
        for ax, (cid, label) in zip(axes, KINDS, strict=True):
            cond = flatten_condition(conds[cid])
            run_kernel(np.uint64(320), index, flat, buf, cond)
            n = int(buf.TI[sc.TI_SAMPLES])
            t = np.arange(n) * float(buf.P[sc.P_DT]) / 60.0
            err = np.angle(np.exp(1j * (buf.bearing[:n] - buf.clean[:n])))
            v = buf.valid[:n]
            ax.plot(t[v], np.degrees(err[v]), lw=0.7, color=ESTIMATORS[1 if cid != "off" else 3])
            ax.axhline(0.0, color="#888888", lw=0.6)
            ax.set_ylabel("deg")
            ax.set_title(label, fontsize=9, loc="left")
        axes[-1].set_ylim(-8, 8)
        axes[-1].set_xlabel(f"minutes from window start (tuning seed 320, engagement {index})")
        fig.suptitle("Bearing error of one engagement under each mismatch kind", fontsize=11)
        fig.tight_layout()
        fig.savefig(out / "mismatch.svg")
        plt.close(fig)
        used["mismatch.svg"] = [CONDITIONS, RANGES]

        # 2. every validation condition
        vals = {c: load(VAL, c) for c in ORDER}
        x = np.arange(len(ORDER))
        w = 0.27
        fig, ax = plt.subplots(figsize=(10.0, 4.0))
        for j, (name, label, colour) in enumerate(
            [
                ("nominal@truth", "plain solve", plain),
                ("robust@truth", "robust control", robust),
                ("attainable@truth", "error-model-informed fit", informed),
            ]
        ):
            ax.bar(
                x + (j - 1) * w,
                [vals[c]["estimators"][name]["median_range"] for c in ORDER],
                w,
                color=colour,
                label=label,
            )
        ax.set_xticks(x, ORDER, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("median relative range error")
        ax.set_title("Validation seed 321: 1,000 scenarios per condition, true segmentation")
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(out / "conditions.svg")
        plt.close(fig)
        used["conditions.svg"] = [VAL / c / "headroom.json" for c in ORDER]

        # 3. the verdict statistic on the test seed
        tests = {c: load(TEST, c) for c in TEST_ORDER}
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        y = np.arange(len(TEST_ORDER))[::-1]
        for yi, c in zip(y, TEST_ORDER, strict=True):
            r = tests[c]["R"]["range"]
            ax.plot([100 * r["lo"], 100 * r["hi"]], [yi, yi], color=robust, lw=2.2)
            ax.plot([100 * r["value"]], [yi], "o", color=robust)
        ax.axvline(10.0, color="#c1121f", lw=1.2, ls="--", label="materiality threshold, 10%")
        ax.axvline(0.0, color="#888888", lw=0.8)
        labels = [f"{c} ({tests[c]['scenarios']:,} scenarios)" for c in TEST_ORDER]
        ax.set_yticks(y, labels, fontsize=8)
        ax.set_xlim(-8, 14)
        ax.set_xlabel("R: robust control over the error-model-informed fit, median range error (%)")
        ax.set_title("Test seed 322, 97.5% intervals")
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(out / "verdict.svg")
        plt.close(fig)
        used["verdict.svg"] = [TEST / c / "headroom.json" for c in TEST_ORDER]

        # 4. by range band
        bands = json.loads((ROOT / TEST / "range-bands.json").read_text())["bands"]
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        xs = np.arange(len(bands))
        for xi, b in zip(xs, bands, strict=True):
            r = b["R"]
            ax.plot([xi, xi], [100 * r["lo"], 100 * r["hi"]], color=robust, lw=2.2)
            ax.plot([xi], [100 * r["value"]], "o", color=robust)
        ax.axhline(10.0, color="#c1121f", lw=1.2, ls="--", label="threshold, 10%")
        ax.axhline(0.0, color="#888888", lw=0.8)

        def km(v: float | None) -> str:
            return "" if v is None else f"{v / 1000:.0f}"

        names = []
        for b in bands:
            lo, hi = b["range_lo_m"], b["range_hi_m"]
            if lo == 0:
                names.append(f"under {km(hi)} km")
            elif hi is None:
                names.append(f"over {km(lo)} km")
            else:
                names.append(f"{km(lo)} to {km(hi)} km")
        ax.set_xticks(xs, names, fontsize=8)
        ax.set_ylim(-10, 13)
        ax.set_ylabel("R (%)")
        ax.set_title("Test seed 322, primary condition, by true range (post hoc)")
        ax.legend(fontsize=8, loc="upper right")
        fig.tight_layout()
        fig.savefig(out / "range-bands.svg")
        plt.close(fig)
        used["range-bands.svg"] = [TEST / "range-bands.json"]

    for fig_name, files in used.items():
        side = {
            "command": "uv run python scripts/research/gh_charts.py --out-dir " + a.out_dir,
            "inputs": {str(f): hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files},
            "seed": 320 if fig_name == "mismatch.svg" else None,
            "engagement_index": index if fig_name == "mismatch.svg" else None,
            "code_git_commit": g.commit,
            "code_git_dirty": g.dirty,
        }
        (out / f"{fig_name}.json").write_text(json.dumps(side, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
