"""Time-late systems (spec 013 research R4, R6): each returns a track for every period.

All run the declared piecewise-constant-velocity solve on 10-second normal points (pairs of
5-second bearings) and read the state at every 5-second row from it (``track.py``).

* ``reference``: knots at the true manoeuvre times (the only use of the truth).
* ``one-leg``: no knots.
* ``c2-end``: the standing C″ run causally to the period's end (frozen C, zig veto, fade),
  its final solve read as a track. ``c2-end-nofade`` drops the fade, which weights recent
  bearings for the estimate *now* and has no purpose over a whole track.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tma2.cli.oracle import run_layer
from tma2.gate2.inputs import prefix_inputs
from tma2.gate2.predict import zig_veto_evidence
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, oracle_inputs
from tma2.references.classical import BearingData
from tma2.segment import TRANSITION, Interval
from tma2.segment.confirm import confirm
from tma2.segment.inputs import segmentation_inputs
from tma2.segment.segmenter import intervals_at, nominations_for
from tma2.types.generated.tma import SegmentParameters

from .periods import Period
from .points import Points, fixed_points
from .track import track

SYSTEMS = ("reference", "one-leg", "c2-end", "c2-end-nofade")
POINT_ROWS = 2
CHUNK = 16  # as cli.segment


@dataclass
class Solved:
    states: np.ndarray  # [rows, 4] at the period's 5-second rows; NaN where the solve failed
    transitions: list[tuple[int, int]]  # in 5-second rows of the period


def c_parameters(gh_plan: str | Path) -> tuple[SegmentParameters, dict[str, Any]]:
    c2 = json.loads(Path(gh_plan).read_text())["c2"]
    raw = json.loads(Path(c2["parameters_from"]).read_text())["segmenter"]["parameters"]
    return SegmentParameters.model_validate(raw), c2


def _times(p: Period) -> np.ndarray:
    a = p.first
    out: np.ndarray = p.own[a : a + p.rows, 0].astype(np.float64) - float(p.own[a, 0])
    return out


def _solve(
    periods: list[Period], pts: list[Points], inputs: list[LayerInputs | None], knots: int
) -> list[np.ndarray]:
    """Tracks [rows, 4] from one batched layer solve (NaN rows where there is no solution)."""
    out = [np.full((p.rows, 4), np.nan) for p in periods]
    live = [i for i, x in enumerate(inputs) if x is not None]
    if not live:
        return out
    items = [(pts[i].data, pts[i].data.n - 1, inputs[i]) for i in live]
    r_max = max(pt.data.n for pt in pts)
    res = run_layer(PhysicsLayer(knots=knots), items, r_max)  # type: ignore[arg-type]
    for b, i in enumerate(live):
        theta = res.theta[b].numpy()
        if not np.isfinite(theta).all():
            continue
        kn = res.knots[b].numpy()
        w = res.knot_weights[b].numpy()
        out[i] = track(theta, pts[i].data.t[kn], w, _times(periods[i]))
    return out


def solve_systems(
    periods: list[Period], systems: list[str], p: SegmentParameters, c2: dict[str, Any]
) -> dict[str, list[Solved]]:
    pts = [fixed_points(x, POINT_ROWS) for x in periods]
    res: dict[str, list[Solved]] = {}

    def spans_of(x: Period) -> list[dict[str, Any]]:
        return [
            {
                **s,
                "start_index": s["start_index"] // POINT_ROWS,
                "end_index": s["end_index"] // POINT_ROWS,
            }
            for s in x.spans()
        ]

    def up(trs: list[tuple[int, int]], rows: int) -> list[tuple[int, int]]:
        return [(a * POINT_ROWS, min(b * POINT_ROWS + POINT_ROWS - 1, rows - 1)) for a, b in trs]

    if "reference" in systems:
        sp = [spans_of(x) for x in periods]
        knots = max(12, 2 * max((len(s) for s in sp), default=0))
        inp = [
            oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, d.n - 1, s, True)
            for d, s in ((pt.data, s) for pt, s in zip(pts, sp, strict=True))
        ]
        tr = _solve(periods, pts, inp, knots)
        res["reference"] = [
            Solved(t, [(s["start_index"], s["end_index"]) for s in x.spans()])
            for t, x in zip(tr, periods, strict=True)
        ]
    if "one-leg" in systems:
        inp = [
            segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, d.n - 1, [], "chord", False)
            for d in (pt.data for pt in pts)
        ]
        res["one-leg"] = [Solved(t, []) for t in _solve(periods, pts, inp, 12)]
    c_names = [s for s in systems if s.startswith("c2-end")]
    if c_names:
        data: list[BearingData] = [pt.data for pt in pts]
        ivs_all: list[list[Interval]] = []
        for s in range(0, len(data), CHUNK):
            part = data[s : s + CHUNK]
            per = periods[s : s + CHUNK]
            noms = [nominations_for(d, d.n - 1, p) for d in part]
            ev = [
                zig_veto_evidence(d, int(c2["window"])) if x.ownship_turns() else np.zeros(d.n)
                for d, x in zip(part, per, strict=True)
            ]
            confs = confirm(PhysicsLayer(), part, noms, p, max(d.n for d in part), evidence=ev)
            ivs_all += [intervals_at(c, d.n - 1, p) for c, d in zip(confs, part, strict=True)]
        for name in c_names:
            inp = []
            for d, ivs in zip(data, ivs_all, strict=True):
                x = prefix_inputs(d, d.n - 1, ivs, c2["mode"], c2.get("open_handover"))
                if x is not None and name == "c2-end":
                    age = (d.n - 1) - np.arange(len(x.log_weight))
                    add = np.clip(c2["fade"][0] - c2["fade"][1] * age, -2.0, 2.0)
                    add[age < 0] = 0.0
                    x.log_weight = x.log_weight + add
                inp.append(x)
            tr = _solve(periods, pts, inp, 12)
            res[name] = [
                Solved(t, up([(iv.start, iv.end) for iv in ivs if iv.kind == TRANSITION], x.rows))
                for t, ivs, x in zip(tr, ivs_all, periods, strict=True)
            ]
    return res
