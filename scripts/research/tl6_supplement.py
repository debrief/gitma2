"""Spec 018: readings the README quotes that ``tables.md`` does not carry.

    uv run python scripts/research/tl6_supplement.py <results folder> <plan> [--out supplement.md]

From the per-row errors of a scored run:

* the periods whose log model evidence is not of the order of the others (a fit that ran
  away under every member), and, per split, the member a whole split chooses with and
  without them, with control ÷ that choice in range;
* the coverage of the hedged track's stated spread at the registered factor and at the
  factor that would have given 0.95 on this run's Annex B and shifted rows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tma2.timelate.study import paired
from tma2.timelate.study6 import medians3

SPLITS = [
    ("man2", "Annex B"),
    ("shift", "Shifted"),
    ("shift2", "Shifted 2"),
    ("quiet", "Held course"),
    ("man2-out", "Outliers"),
    ("man2-corr", "Correlated"),
]
WILD = 1e4  # a period whose best member's log evidence is below minus this is set aside


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("plan")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    ad, st = plan["adaptive"], plan["adaptive_study"]
    keys = [
        f"L{float(m):g}-s{float(r):g}-a{float(x):g}"
        for m in ad["leg_means_s"]
        for r in ad["leg_sd_ratios"]
        for x in ad["angle_max_deg"]
    ]
    out = ["## A whole split choosing one member, with and without runaway periods", ""]
    out += [
        f"(a runaway period: the best member's log evidence is below -{WILD:g}; such a period's evidence differences swamp the sum over the split)",
        "",
        "| Split | Periods | Runaway periods (ordinals) | Member, all periods | Control ÷ it | Member, runaways set aside | Control ÷ it |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    cover = []
    for k, lab in SPLITS:
        p = Path(a.dir) / f"{k}.errors.npz"
        if not p.exists():
            continue
        z = dict(np.load(p))
        ids, med, _b = medians3(z)
        order = {int(o): r for r, o in enumerate(z["logz_period"])}
        rows = np.array([order[int(i)] for i in ids])
        logz = np.where(np.isfinite(z["logz"][rows]), z["logz"][rows], -1e6)
        wild = logz.max(axis=1) < -WILD
        stack = np.stack([med[f"fam-{m}"][:, 0] for m in keys], axis=1)
        ctl = med[st["control"]][:, 0]

        def ratio(choice: int) -> str:
            b = stack[:, choice]  # noqa: B023
            ok = np.isfinite(ctl) & np.isfinite(b) & (ctl > 0) & (b > 0)  # noqa: B023
            v = paired(ctl[ok], b[ok])  # noqa: B023
            return f"{v['geometric_mean']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}]"

        every = int(np.argmax(logz.sum(axis=0)))
        kept = int(np.argmax(logz[~wild].sum(axis=0)))
        out += [
            f"| {lab} | {ids.size} | {int(wild.sum())} ({', '.join(str(int(i)) for i in ids[wild]) or '–'}) | "
            f"`{keys[every]}` | {ratio(every)} | `{keys[kept]}` | {ratio(kept)} |"
        ]
        from tma2.timelate.score import UNDETERMINED

        bound = z["bound"].astype(np.float64)
        det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
        h = st["hedged"]
        mean, sd = z[f"hrange_{h}"].astype(np.float64), z[f"spread_{h}"].astype(np.float64)
        ok = det & np.isfinite(mean) & np.isfinite(sd) & (sd > 0)
        cover.append((k, lab, np.abs(mean - z["true_range"].astype(np.float64))[ok] / sd[ok]))
    scale = float(st.get("spread_scale", 1.0))
    pool = np.concatenate([zz for k, _lab, zz in cover if k in ("man2", "shift")])
    own = float(np.quantile(pool, 0.95)) / 2.0
    out += ["", "## The stated spread: coverage of two stated sds", ""]
    out += [
        f"(registered factor {scale:g}; the factor that gives 0.95 on this run's own Annex B and shifted rows pooled is {own:.2f})",
        "",
        f"| Split | Rows | Mixture sd as it comes | Registered factor {scale:g} | This run's own factor {own:.2f} |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _k, lab, zz in cover:
        out += [
            f"| {lab} | {zz.size} | {np.mean(zz <= 2):.2f} | {np.mean(zz <= 2 * scale):.3f} | {np.mean(zz <= 2 * own):.2f} |"
        ]
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
