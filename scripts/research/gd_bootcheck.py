"""Spec 038 (research R7): how far a share's bootstrap limits move with the bootstrap's seed.

    uv run python scripts/research/gd_bootcheck.py <errors.npz> --control c2-edit-thr [--seeds 20]

Prints the gap-closed share of ``--control`` against the fine-tuned regressors (comparator
c2-robust), its limits at the registered seed, and the sd of each limit over other seeds. A
decision line closer to a limit than about two of those sds cannot be decided by this sample.
"""

from __future__ import annotations

import argparse

import numpy as np

from tma2.regress import decomp as dc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("errors")
    ap.add_argument("--control", required=True)
    ap.add_argument("--comparator", default="c2-robust")
    ap.add_argument("--regressors", default="ft-s1,ft-s2,ft-s3")
    ap.add_argument("--seeds", type=int, default=20)
    a = ap.parse_args()
    z = np.load(a.errors)
    errs = {k[4:]: z[k] for k in z.files if k.startswith("err_")}
    ft = a.regressors.split(",")
    for c, col in enumerate(("range", "course", "speed")):
        num = dc.pooled_logs(errs, a.comparator, [a.control], z["ordinal"], c)
        den = dc.pooled_logs(errs, a.comparator, ft, z["ordinal"], c)
        base = dc.share(num, den)
        if not base.get("defined"):
            print(f"{col}: not defined")
            continue
        lim = np.array(
            [
                [s["lo"], s["hi"]]
                for s in (dc.share(num, den, seed=1000 + i) for i in range(a.seeds))
                if s.get("defined")
            ]
        )
        print(
            f"{col}: share {base['share']:.3f} [{base['lo']:.3f}, {base['hi']:.3f}]; "
            f"limit sd over {len(lim)} seeds: lo {lim[:, 0].std():.4f}, hi {lim[:, 1].std():.4f}"
        )


if __name__ == "__main__":
    main()
