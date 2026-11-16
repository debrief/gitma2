"""Every intermediate of C's and E's segmentation of one scenario, for the JavaScript port's
check (spec 021 FR-005).

The scenario runs alone, padded to the graphs' 720 rows (``r_max`` 720), so Python and the
browser pad identically. Gate 2 ran C in chunks of 16 padded to the chunk's longest scenario; that
segmentation is compared by the check and reported, not gated.

The dump holds, as JSON-ready values:
* the scenario's raw arrays as the pack stores them (float32 values, written as doubles): ownship
  [n, 5] (t, x, y, course, speed) and observations [n, 3] (t, bearing, valid);
* the per-timestep least-squares states and their flags (``ls_states``), the GLR statistic, O's
  online codes, the innovations and E-s's evidence;
* the search's anchor grid and cost table, and its transitions on every prefix it runs;
* the nominations;
* for C (no evidence) and for E (E-s's evidence): every confirmation decision, the transitions
  and near-misses, and the intervals at every scored row.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

ROWS = 720


def _f(a: np.ndarray) -> list[Any]:
    out: list[Any] = np.asarray(a, dtype=np.float64).tolist()
    return out


def _conf(conf: Any, rows: list[int], p: Any) -> dict[str, Any]:
    from tma2.segment.segmenter import intervals_at

    return {
        "decisions": [
            [x.row, x.start, x.length, x.source, x.drop, x.threshold, bool(x.accepted)]
            for x in conf.decisions
        ],
        "transitions": [
            [
                x.start,
                x.end,
                x.accepted_at,
                x.closed_at,
                x.drop,
                x.score,
                x.source,
                x.accepted_start,
            ]
            for x in conf.transitions
        ],  # fmt: skip
        "near_misses": [[x.start, x.end, x.row, x.score] for x in conf.near_misses],
        "solves": conf.solves,
        "intervals": {
            str(k): [[iv.kind, iv.start, iv.end, bool(iv.open)] for iv in intervals_at(conf, k, p)]
            for k in rows
        },
    }


def dump_scenario(
    ordinal: int,
    meta: dict[str, Any],
    own: np.ndarray,
    obs: np.ndarray,
    rows: list[int],
    es_net: Any,
    p: Any,
) -> dict[str, Any]:
    from tma2.detect.controls import ls_states
    from tma2.physics.layer import PhysicsLayer
    from tma2.references.classical import bearing_data_from_arrays, classical_predict
    from tma2.segment.confirm import confirm, glr_nominations, search_nominations
    from tma2.segment.evidence import (
        evidence_for,
        features,
        innovations,
        online_ownship_codes,
    )
    from tma2.segment.search import anchored_grid, cost_table
    from tma2.segment.segmenter import glr, search_by_prefix

    d = bearing_data_from_arrays(meta, own, obs)
    lst, lok = ls_states(d, classical_predict(d, "per_timestep")["rows"])
    stat = glr(d, p.glr_window)
    oc = online_ownship_codes(own[:, 3], own[:, 4], d.n, p)
    innov = innovations(d, lst, lok)
    feats = features(d, oc, innov)
    ev = evidence_for(es_net, [feats])[0]
    anchor = rows[0]
    grid = anchored_grid(d.n - 1, anchor, p.search_step_rows)
    table = cost_table(d, grid, p.l_min_rows)
    by_prefix = search_by_prefix(d, anchor, p)
    noms = sorted(
        glr_nominations(stat, p.glr_threshold, p) + search_nominations(by_prefix, p),
        key=lambda x: (x.row, x.source, x.lo),
    )
    layer = PhysicsLayer()
    c = confirm(layer, [d], [noms], p, ROWS)[0]
    e = confirm(layer, [d], [noms], p, ROWS, evidence=[ev])[0]
    return {
        "ordinal": ordinal,
        "scenario_index": int(meta["index"]),
        "n": d.n,
        "zig_index": d.zig_index,
        "sigma": d.sigma,
        "rows": rows,
        "own": _f(own),
        "obs": _f(obs),
        "ls_state": _f(lst),
        "ls_ok": [bool(x) for x in lok],
        "glr": _f(stat),
        "own_codes": [int(x) for x in oc],
        "innovations": _f(innov),
        "features": _f(feats),
        "evidence": _f(ev),
        "search": {
            "anchor": anchor,
            "grid": [int(x) for x in grid],
            "cost_table": [[v if np.isfinite(v) else None for v in row] for row in _f(table)],
            "by_prefix": [[k, [[s, e_, bool(o)] for s, e_, o in tr]] for k, tr in by_prefix],
        },
        "nominations": [[x.row, x.lo, x.hi, x.source] for x in noms],
        "c": _conf(c, rows, p),
        "e": _conf(e, rows, p),
    }


def write(path: Path, doc: dict[str, Any]) -> None:
    import gzip

    text = json.dumps(doc, separators=(",", ":"), allow_nan=False)
    path.write_bytes(gzip.compress(text.encode(), compresslevel=9, mtime=0))
