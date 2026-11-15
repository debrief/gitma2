"""Spec 020: the viewer's engagement rule and data packing."""

from __future__ import annotations

import gzip
import json
import math

import numpy as np

from tma2.gate2.export import INPUTS, OUTPUTS, ROWS
from tma2.viewer.build import Engagement, answered, gz, pack_engagement, state_fields
from tma2.viewer.choose import BUSY, LOSES, ONE, ORDER, QUIET, choose, manoeuvre_class


def meta(n: int, before: int = 0) -> dict[str, object]:
    """``n`` manoeuvres in the shown span (from row 100) and ``before`` ending before it."""
    early = [{"kind": "speed", "start_index": 10, "end_index": 20}] * before
    late = [{"kind": "course", "start_index": 150, "end_index": 160}] * n
    return {"manoeuvres": early + late}


def test_classes_count_the_shown_span_only() -> None:
    assert manoeuvre_class(meta(0), 100) == QUIET
    assert manoeuvre_class(meta(0, before=2), 100) == QUIET
    assert manoeuvre_class(meta(1, before=1), 100) == ONE
    assert manoeuvre_class(meta(2), 100) == BUSY
    assert manoeuvre_class({"manoeuvres": None}, 100) == QUIET
    # a manoeuvre still under way when the span starts counts
    m = {"manoeuvres": [{"kind": "course", "start_index": 90, "end_index": 100}]}
    assert manoeuvre_class(m, 100) == ONE


def test_rule_order_and_loses_asked_lazily() -> None:
    pool = [(j, meta(n), 100) for j, n in ((0, 5), (1, 1), (2, 0), (3, 4), (4, 1), (5, 3))]
    asked: list[int] = []

    def loses(j: int) -> bool:
        asked.append(j)
        return j == 4

    picks, missing = choose(pool, loses)
    assert [(p.ordinal, p.reason) for p in picks] == [
        (2, QUIET),
        (1, ONE),
        (0, BUSY),
        (4, LOSES),
        (3, BUSY),
    ]
    assert missing == [ONE]  # the second "one" slot: ordinal 4 was taken by LOSES
    assert asked == [3, 4]  # in order, stopping at the first that loses, never a taken one
    assert len(ORDER) == 6


def test_answered_is_plausible_row() -> None:
    row = {"x_m": 1.0, "y_m": 2.0, "range_m": 5000.0, "course_rad": 0.1, "speed_mps": 5.0}
    assert answered(row)
    assert not answered(None)
    assert not answered({**row, "range_m": 0.0})
    assert not answered({**row, "range_m": 100_001.0})
    assert not answered({**row, "speed_mps": 25.5})
    assert not answered({**row, "x_m": math.nan})


def test_state_fields() -> None:
    f = state_fields(np.array([3000.0, 4000.0, 0.0, -5.0]), (0.0, 0.0))
    assert f["range_m"] == 5000.0
    assert math.isclose(f["course_rad"], math.pi)
    assert f["speed_mps"] == 5.0


def _engagement(rows: int) -> Engagement:
    rng = np.random.default_rng(0)
    n = 300
    own = np.column_stack([np.arange(n) * 10.0, rng.normal(size=(n, 4))])
    tgt = np.column_stack([np.arange(n) * 10.0, rng.normal(size=(n, 4))])
    obs = np.column_stack([np.arange(n) * 10.0, rng.normal(size=n), np.ones(n)])
    shapes = {
        "own": (ROWS, 2),
        "sigma": (),
        "k": (),
        "theta0": (4,),
    }
    ins = {}
    for name in INPUTS:
        shp = shapes.get(name, (ROWS,))
        a = rng.normal(size=(rows, *shp))
        if name in ("bearing", "own", "t", "sigma"):
            a = np.broadcast_to(a[:1], a.shape).copy()  # the same at every row
        ins[name] = a
    outs = {
        "state": rng.normal(size=(rows, 4)),
        "cov": rng.normal(size=(rows, 4, 4)),
        "plausible": np.ones(rows),
        "cov_ok": np.ones(rows),
    }
    g = Engagement(
        ordinal=7,
        meta={"index": 70, "manoeuvres": [], "parameters": {"dt_s": 10}, "zig_index": 100},
        own=own,
        tgt=tgt,
        obs=obs,
        rows=list(range(130, 130 + 6 * (rows + 1), 6)),
    )
    g.inputs, g.outputs = ins, outs
    g.have_e = [True] * rows + [False]
    g.open_rows = [False] * (rows + 1)
    g.systems = {s: [None] * (rows + 1) for s in ("one_leg", "imm", "c", "c2")}
    return g


def test_pack_round_trip_and_determinism() -> None:
    g = _engagement(5)
    dtypes = {n: ("int64" if n == "k" else "float64") for n in INPUTS}
    js, bn = pack_engagement(g, QUIET, dtypes)
    js2, bn2 = pack_engagement(g, QUIET, dtypes)
    assert (js, bn) == (js2, bn2)  # gzip without a timestamp: reproducible bytes
    doc = json.loads(gzip.decompress(js))
    v = np.frombuffer(gzip.decompress(bn), dtype="<f8")
    assert v.size == doc["binary_values"]
    shared = {L["name"] for L in doc["layout"] if L["shared"]}
    assert shared == {"bearing", "own", "t", "sigma"}
    assert doc["e_rows"] == [0, 1, 2, 3, 4]
    for L in doc["layout"]:
        per = int(np.prod(L["shape"]))
        src = g.inputs[L["name"]] if L["kind"] == "input" else g.outputs[L["name"]]
        for r in range(5):
            start = L["offset"] + (0 if L["shared"] else r * per)
            assert np.array_equal(v[start : start + per], np.asarray(src[r], dtype=float).ravel())
    assert {L["name"] for L in doc["layout"]} == set(INPUTS) | set(OUTPUTS)


def test_gz_has_no_timestamp() -> None:
    assert gz(b"abc") == gz(b"abc")
    assert gz(b"abc")[4:8] == b"\x00\x00\x00\x00"


def test_unusable_engagement_is_skipped() -> None:
    pool = [(0, meta(0), 100), (1, meta(0), 100)]
    picks, _ = choose(pool, lambda _j: False, usable=lambda j: j != 0)
    assert picks[0].ordinal == 1 and picks[0].reason == QUIET
