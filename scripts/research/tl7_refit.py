"""Spec 019: a family member's own search against the same member refitting shared
candidates (spec 018), on the same periods.

    uv run python scripts/research/tl7_refit.py <spec 019 results folder> <spec 018 test results folder> [--out supplement.md]

The two runs are on different CPU families, so each is read against its own run's
standing control; the cross-run ratios are given beside to show how much the runs differ.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from tma2.timelate.study import paired
from tma2.timelate.study6 import medians3, pair3

CTL, MEMBER = "ctl-d1-q0.01", "L900-s0.35-a60"


def ci(v: dict[str, float] | None) -> str:
    return (
        "–"
        if not v
        else f"{v['geometric_mean']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}] ({v['periods']})"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("own")
    ap.add_argument("refit")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    ia, ma, _ = medians3(dict(np.load(Path(a.own) / "shift.errors.npz")))
    ib, mb, _ = medians3(dict(np.load(Path(a.refit) / "shift.errors.npz")))
    keep = np.isin(ib, ia)
    sub = {k: v[keep] for k, v in mb.items()}
    at = {int(i): n for n, i in enumerate(ia)}
    sel = [at[int(i)] for i in ib[keep]]

    def cross(x: str, y: str) -> dict[str, float]:
        p, q = sub[x][:, 0], ma[y][sel, 0]
        ok = np.isfinite(p) & np.isfinite(q) & (p > 0) & (q > 0)
        return paired(p[ok], q[ok])

    own = pair3(ma, CTL, f"mem-{MEMBER}") or {}
    ref = pair3(sub, CTL, f"fam-{MEMBER}") or {}
    out = [
        f"## Member `{MEMBER}`: its own search against refitting shared candidates",
        "",
        f"({int(keep.sum())} shifted periods of seed 347 scored in both runs; range; a ÷ b, above 1: b is better)",
        "",
        "| Reading | Ratio (periods) |",
        "| --- | --- |",
        f"| Control ÷ the member with its own search (this run) | {ci(own.get('range'))} |",
        f"| Control ÷ the member refitting shared candidates (spec 018's run) | {ci(ref.get('range'))} |",
        f"| Refit (spec 018's run) ÷ own search (this run), across runs | {ci(cross(f'fam-{MEMBER}', f'mem-{MEMBER}'))} |",
        f"| The control across the two runs (spec 018's ÷ this) | {ci(cross(CTL, CTL))} |",
        f"| The true-prior search across the two runs (spec 018's `true` ÷ this run's `lad-5`) | {ci(cross('true', 'lad-5'))} |",
    ]
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
