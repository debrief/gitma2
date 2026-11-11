"""Spec 011 pilot (plan research R4): C-r's settings on the tuning seed.

Reads the two `errors.npz` of a `headroom/gr-pilot` run (primary condition and off) and gives,
on the same rows: each system's median relative range error; baseline − system with a paired,
scenario-clustered 95% interval; the share of the baseline-to-reference gap closed (primary);
and the cost on clean data, system ÷ baseline − 1.

    uv run python scripts/research/gr_pilot.py --primary <errors.npz> --off <errors.npz> --out <json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

BASE, REF = "robust@c2", "robust@truth"


def _draws(ordinal: np.ndarray, n: int, seed: int) -> list[np.ndarray]:
    uniq = np.unique(ordinal)
    rows = [np.flatnonzero(ordinal == u) for u in uniq]
    rng = np.random.default_rng(seed)
    return [
        np.concatenate([rows[i] for i in rng.integers(0, uniq.size, uniq.size)]) for _ in range(n)
    ]


def table(path: str, seed: int) -> dict[str, dict[str, list[float] | float]]:
    z = np.load(path)
    e = {n[4:]: z[n][:, 0] for n in z.files if n.startswith("err_")}
    draws = _draws(z["ordinal"], 2000, seed)
    every = np.arange(z["ordinal"].size)

    def med(n: str, i: np.ndarray) -> float:
        return float(np.median(e[n][i]))

    out: dict[str, dict[str, list[float] | float]] = {}
    for n in e:
        rec: dict[str, list[float] | float] = {"median": med(n, every)}
        stats = {
            "gain": lambda i, n=n: med(BASE, i) - med(n, i),
            "share": lambda i, n=n: (med(BASE, i) - med(n, i)) / (med(BASE, i) - med(REF, i)),
            "cost": lambda i, n=n: med(n, i) / med(BASE, i) - 1.0,
        }
        for key, f in stats.items():
            b = np.array([f(i) for i in draws])
            lo, hi = np.quantile(b[np.isfinite(b)], [0.025, 0.975])
            rec[key] = [f(every), float(lo), float(hi)]
        out[n] = rec
    out["_rows"] = {"median": float(every.size), "scenarios": float(np.unique(z["ordinal"]).size)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", required=True)
    ap.add_argument("--off", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {"primary": table(a.primary, 21), "off": table(a.off, 22)}
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(
        f"{'system':14} primary  gain [95%]                share closed [95%]        clean   cost [95%]"
    )
    for n, p in res["primary"].items():
        if n.startswith("_") or n not in res["off"]:
            continue
        o = res["off"][n]
        g, s, c = p["gain"], p["share"], o["cost"]
        assert isinstance(g, list) and isinstance(s, list) and isinstance(c, list)
        print(
            f"{n:14} {p['median']:.3f}   {g[0]:+.3f} [{g[1]:+.3f}, {g[2]:+.3f}]   "
            f"{s[0]:+.2f} [{s[1]:+.2f}, {s[2]:+.2f}]   {o['median']:.3f}   "
            f"{100 * c[0]:+.1f}% [{100 * c[1]:+.1f}, {100 * c[2]:+.1f}]"
        )


if __name__ == "__main__":
    main()
