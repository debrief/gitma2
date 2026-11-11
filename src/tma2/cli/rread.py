"""``tma2-rread``: the regressor control's readings from one scoring run (spec 012 FR-021,
FR-022). Reads the scorer's ``errors.npz`` and the truth split (for the bound and row labels);
prints and writes the held-course reading per regressor and the differences after manoeuvres.
No gate: exit 0."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-rread", description=__doc__)
    ap.add_argument("--truth", required=True, help="the scored split's f32pack")
    ap.add_argument("--errors", required=True, help="errors.npz of the scoring run")
    ap.add_argument("--regressors", required=True, help="comma-separated estimator names")
    ap.add_argument("--check", default="oracle", help="the least-squares check on held course")
    ap.add_argument("--references", default="c2,imm", help="compared after manoeuvres")
    ap.add_argument("--reach", type=float, default=1.25)
    ap.add_argument("--floor", type=float, default=2.0)
    ap.add_argument("--level", type=float, default=0.95)
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import numpy as np

    from tma2.regress.reading import after_manoeuvres, held_course
    from tma2.segment import score as sc
    from tma2.segment.gate import sha256_file

    z = np.load(a.errors)
    ordinal, ks, settled = z["ordinal"], z["k"], z["settled"].astype(bool)
    errs = {n[4:]: z[n] for n in z.files if n.startswith("err_")}
    regs = a.regressors.split(",")
    refs = [r for r in a.references.split(",") if r]
    missing = [n for n in [*regs, a.check, *refs] if n not in errs]
    if missing:
        raise SystemExit(f"not in {a.errors}: {', '.join(missing)} (have {', '.join(errs)})")
    need = {int(j) for j in ordinal}
    metas, owns, tgts, obss = {}, {}, {}, {}
    for j, m, own, tgt, obs in sc.iter_selected(a.truth, 0, max(need) + 1):
        if j in need:
            metas[j], owns[j], tgts[j], obss[j] = m, own, tgt, obs
    rows = [sc.Row(int(j), int(k), bool(s)) for j, k, s in zip(ordinal, ks, settled, strict=True)]
    sd = sc.bounds(rows, metas, owns, tgts, obss)
    changed = np.array([bool(sc._changes_by(metas[r.ordinal], r.k)) for r in rows])
    range_m = np.array(
        [
            math.hypot(
                float(tgts[r.ordinal][r.k, 1] - owns[r.ordinal][r.k, 1]),
                float(tgts[r.ordinal][r.k, 2] - owns[r.ordinal][r.k, 2]),
            )
            for r in rows
        ]
    )
    held = settled & ~changed
    kw = dict(reach=a.reach, floor=a.floor, level=a.level, resamples=a.resamples)
    out: dict[str, Any] = {
        "truth_sha256": sha256_file(a.truth),
        "errors_sha256": sha256_file(a.errors),
        "rows": len(rows),
        "held_course": {n: held_course(errs[n], sd, ordinal, held, **kw) for n in [a.check, *regs]},
        "after_manoeuvres": {
            n: after_manoeuvres(errs, n, refs, ordinal, changed, range_m, a.level, a.resamples)
            for n in regs
        },
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    for n, r in out["held_course"].items():
        eff = " ".join(
            f"{c} {r[c]['efficiency']:.2f} [{r[c]['lo']:.2f}, {r[c]['hi']:.2f}]"
            for c in ("range", "course_deg", "speed_kt")
            if c in r
        )
        print(f"held course  {n:12} {r['reading']:8} ({r['rows']} rows)  {eff}")
    for n, by in out["after_manoeuvres"].items():
        for ref, rec in by.items():
            d = rec["range"]["all_rows"]
            if d.get("rows"):
                print(
                    f"manoeuvring  {n} - {ref}: range {d['difference']:+.4f} "
                    f"[{d['lo']:+.4f}, {d['hi']:+.4f}] ({d['rows']} rows)"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
