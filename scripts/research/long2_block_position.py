"""Spec 024: the incremental C's error by an estimate's position in its 2-hour block, against spec
023's per-window run at the same rows (24- and 48-hour engagements of configs/long/long.json).
Position 0 has the per-window run's inputs exactly; later positions see up to two more hours of
history in C's and E-s's confirmation before the crop.

    uv run python scripts/research/long2_block_position.py > experiments/20261117-long2/block-position.txt
"""

import glob
import json
import sys

import numpy as np

sys.path.insert(0, "scripts/research")
from long_report import plausible

from tma2.timelate.score import row_errors


def load(pattern):
    parts = []
    for f in sorted(glob.glob(pattern)):
        z = np.load(f)
        h = json.load(open(f[:-4] + ".json"))
        if z["rows"].size:
            parts.append((h.get("shard", [0, 1]), z))
    return parts


for i in (2, 3):
    inc = load(f"experiments/20261117-long2/raw/realtime-inc-{i}*.npz")
    old = load(f"experiments/20261117-long/raw/realtime-{i}*.npz")
    o = {}
    for _, z in old:
        for q, k in enumerate(z["rows"]):
            o[int(k)] = (z["state_e"][q], z["state_c2"][q], z["truth"][q])
    pos_err = {}
    for _sh, z in inc:
        for q, k in enumerate(z["rows"]):
            pos = q % 12
            if int(k) not in o:
                continue
            se, sc, tr = o[int(k)]
            ei = row_errors(
                plausible(z["state_e"][q : q + 1], z["truth"][q : q + 1]), z["truth"][q : q + 1]
            )[0, 0]
            eo = row_errors(plausible(se[None], tr[None]), tr[None])[0, 0]
            same = np.allclose(z["state_e"][q], se, atol=1e-3, equal_nan=True)
            pos_err.setdefault(pos, []).append((ei, eo, same))
    print("engagement", i)
    for pos in sorted(pos_err):
        a = np.array([(x, y) for x, y, _ in pos_err[pos]])
        s = np.mean([z for *_, z in pos_err[pos]])
        mi, mo = np.nanmedian(a[:, 0]), np.nanmedian(a[:, 1])
        print(f" pos {pos:2d} n={len(a)} inc median {mi:.3f} per-window {mo:.3f} identical {s:.2f}")
