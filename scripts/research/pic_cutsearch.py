"""Spec 039 part 3 (research R6): the time-late control cut at a scored row.

    uv run python scripts/research/pic_cutsearch.py --in <split.f32pack> --start 0 --count 50 \
        --rows last --out cut.json

For each engagement (bearing sd 1 degree, as the scorer selects) and each chosen scored row k,
``ctl-d1-q0.01`` (spec 016; `timelate.carry.solve_ctl`, started from nothing) is run on the
bearings up to k and read at its last moment: a causal estimator told Annex B's manoeuvre prior.
Writes per estimate the errors (relative range, course degrees, speed knots) and the seconds.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--rows", default="last", help="last, first or all scored rows")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from tma2.long.timelate import settings_and_priors
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment.score import g5_rows, iter_selected
    from tma2.timelate.carry import solve_ctl

    settings, priors, *_ = settings_and_priors()
    out = []
    for j, m, own, tgt, obs in iter_selected(a.inp, a.start, a.count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if not ks:
            continue
        ks = ks[-1:] if a.rows == "last" else ks[:1] if a.rows == "first" else ks
        for k in ks:
            n = k + 1
            t = d.t[:n] - d.t[0]
            ox, oy = d.ox[:n] - d.ox[0], d.oy[:n] - d.oy[0]
            pb = (t, ox, oy, d.z[:n], d.valid[:n] > 0, float(d.sigma))
            t0 = time.time()
            res = solve_ctl(pb, priors, np.full((n, 4), np.nan), np.zeros((0, 2)), settings)
            sec = time.time() - t0
            rec = {"ordinal": j, "k": int(k), "seconds": sec, "answered": res is not None}
            if res is not None:
                st, spans = res
                x, y, vx, vy = (float(v) for v in st[-1])
                tr = math.hypot(tgt[k, 1] - own[k, 1], tgt[k, 2] - own[k, 2])
                er = math.hypot(x - ox[-1], y - oy[-1])
                dc = (math.atan2(vx, vy) - float(tgt[k, 3]) + math.pi) % (2 * math.pi) - math.pi
                rec |= {
                    "range": abs(er - tr) / tr,
                    "course_deg": abs(math.degrees(dc)),
                    "speed_kt": abs(math.hypot(vx, vy) - float(tgt[k, 4])) * 3600 / 1852,
                    "declared": int(np.asarray(spans).shape[0]),
                }
            out.append(rec)
            print(json.dumps(rec), flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
