"""Spec 014 thinning study (research R6): each form against the full data on the same
tuning periods, from the results branches of the `timelate/tl-c-thin-*` runs.

    uv run python scripts/research/tl2_thin.py <dir of fetched runs> --out <experiment dir>

`<dir>` holds one folder per run (`tl-c-thin-<slug>-<run id>`, as on its results branch) with
`summary.json`, `run.json` and `<split>.errors.npz`. Writes `thin.json` and prints a table:
the search's period median range error, its paired ratio to the full data (geometric mean,
period bootstrap), seconds per period, manoeuvres missed, and the adoption rule's outcome.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from tma2.timelate.gate import period_medians
from tma2.timelate.study import paired

COST_MAX, COST_EXCLUDED, SAVING_MIN = 1.02, 1.05, 0.30  # research R6, fixed before the runs


def load(d: Path) -> dict[str, Any]:
    run = json.loads((d / "run.json").read_text())
    split = next(iter(run["splits"]))
    s = json.loads((d / "summary.json").read_text())["splits"][split]
    z = np.load(d / f"{split}.errors.npz")
    ids, med = period_medians(
        z["err_search2"].astype(np.float64), z["period"], z["bound"].astype(np.float64)
    )
    sec = s["seconds_per_period"]
    return {
        "form": run.get("thinning", "none"),
        "split": split,
        "commit": s["git_commit"],
        "ids": ids,
        "med": med,
        "seconds": float(sec["search2"]),
        "missed": float(s["counts"]["search2"]["120"]["missed_share"]),
        "false": int(s["counts"]["search2"]["120"]["false"]),
        "median": float(np.median(med)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    runs = [load(d) for d in sorted(Path(a.runs).iterdir()) if (d / "summary.json").exists()]
    out: dict[str, Any] = {
        "rule": {"cost_max": COST_MAX, "cost_excluded": COST_EXCLUDED, "saving_min": SAVING_MIN},
        "splits": {},
    }
    for split in sorted({r["split"] for r in runs}):
        base = next(r for r in runs if r["split"] == split and r["form"] == "none")
        rows = []
        for r in sorted((r for r in runs if r["split"] == split), key=lambda r: r["form"]):
            common, ia, ib = np.intersect1d(r["ids"], base["ids"], return_indices=True)
            p = paired(r["med"][ia], base["med"][ib])
            saving = 1.0 - r["seconds"] / base["seconds"]
            ok = p["geometric_mean"] < COST_MAX and p["hi"] < COST_EXCLUDED
            rows.append(
                {
                    "form": r["form"],
                    "periods": int(common.size),
                    "median": r["median"],
                    "cost": p,
                    "seconds": r["seconds"],
                    "saving": saving,
                    "missed": r["missed"],
                    "false": r["false"],
                    "passes_cost": bool(ok),
                    "passes_rule": bool(ok and saving >= SAVING_MIN),
                    "commit": r["commit"],
                }
            )
            print(
                f"{split:9s} {r['form']:20s} median {r['median']:.4f}  cost "
                f"{p['geometric_mean']:.3f} [{p['lo']:.3f}, {p['hi']:.3f}]  worse in "
                f"{1 - p['a_better']:.2f}  {r['seconds']:5.1f} s ({saving:+.0%})  missed "
                f"{r['missed']:.2f} false {r['false']:3d}  "
                f"{'PASS' if ok and saving >= SAVING_MIN else ''}"
            )
        out["splits"][split] = rows
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "thin.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
